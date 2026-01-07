from __future__ import annotations

import hashlib
import html
import logging
import os
import pickle
import posixpath
import re
import threading
import time
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable
from urllib.parse import quote

import numpy as np
from bs4 import BeautifulSoup
from fastembed import TextEmbedding
import markdown
from rank_bm25 import BM25Okapi

from api.models import SearchContext
from api.settings import Settings

logger = logging.getLogger("docs_api")

_TOKEN_RE = re.compile(r"[a-zA-Z0-9_./:+-]+")
_HEADING_TAGS = ("h2", "h3")
_DOC_EXTENSIONS = {".html", ".htm", ".md", ".markdown", ".txt"}
_SNAPSHOT_SCHEMA_VERSION = 1


def _sha1_short(text: str, length: int = 12) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:length]


def _snapshot_signature(settings: Settings) -> str:
    hasher = hashlib.sha1()
    hasher.update(str(settings.docsets_file.resolve()).encode("utf-8"))
    hasher.update(settings.docsets_file.read_bytes())
    hasher.update(
        f"|{settings.embedding_model}|{settings.chunk_words}|{settings.chunk_overlap_words}".encode("utf-8")
    )
    return hasher.hexdigest()


def _stable_anchor(file_path: str, heading_path: list[str]) -> str:
    key = f"{file_path}|{' > '.join(heading_path)}"
    return f"#sec-{_sha1_short(key)}"


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


def _normalize_whitespace(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _chunk_words(text: str, *, max_words: int, overlap_words: int) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    step = max_words - overlap_words
    chunks: list[str] = []
    for start in range(0, len(words), step):
        end = min(start + max_words, len(words))
        chunk = " ".join(words[start:end]).strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(words):
            break
    return chunks


def _safe_resolve_under_root(root: Path, relative_path: str) -> Path:
    if relative_path.startswith(("/", "\\")) or ":" in relative_path:
        raise ValueError("Invalid asset path")
    target = (root / relative_path).resolve()
    root = root.resolve()
    if root != target and root not in target.parents:
        raise ValueError("Path traversal attempt")
    return target


@dataclass(frozen=True, slots=True)
class Docset:
    docset_id: str
    root_path: Path
    tags: tuple[str, ...]
    keywords: tuple[str, ...]
    version: str | None
    enabled: bool


@dataclass(frozen=True, slots=True)
class DocSection:
    section_ref: str
    docset_id: str
    file_path: str
    anchor: str
    heading_path: tuple[str, ...]
    text: str
    code_blocks: tuple[str, ...]
    assets: tuple["Asset", ...]


@dataclass(frozen=True, slots=True)
class Asset:
    src: str
    alt: str | None
    caption: str | None
    path: str | None


@dataclass(frozen=True, slots=True)
class Chunk:
    doc_ref: str
    section_ref: str
    chunk_index: int
    text: str


@dataclass(frozen=True, slots=True)
class DocsetIndex:
    docset: Docset
    sections: dict[str, DocSection]
    chunks: list[Chunk]
    doc_ref_to_chunk: dict[str, Chunk]
    bm25: BM25Okapi
    embeddings: np.ndarray  # (n_chunks, dim) normalized


@dataclass(frozen=True, slots=True)
class IndexState:
    revision: int
    docsets: dict[str, Docset]
    indexes: dict[str, DocsetIndex]
    doc_ref_to_docset: dict[str, str]


@dataclass(frozen=True, slots=True)
class IndexSnapshot:
    schema_version: int
    signature: str
    state: IndexState


class IndexManager:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._state_lock = threading.Lock()
        self._reindex_lock = threading.Lock()
        self._revision = 0
        self._state: IndexState | None = None

        self._embedder = TextEmbedding(
            settings.embedding_model,
            cache_dir=str(settings.embedding_cache_dir),
            lazy_load=True,
        )
        self._embed_lock = threading.Lock()

        from functools import lru_cache

        self._embed_query_cached = lru_cache(maxsize=512)(self._embed_query_uncached)
        self._search_cached = lru_cache(maxsize=256)(self._search_uncached)

    def ensure_ready(self) -> None:
        if self._state is not None:
            return
        with self._reindex_lock:
            if self._state is not None:
                return
            if self._load_snapshot():
                return
            if not self._settings.auto_index:
                raise RuntimeError("Index not built yet (set DOCS_API_AUTO_INDEX=1 or call POST /reindex)")
            self._reindex_impl(docset_ids=None)

    def docsets(self) -> list[Docset]:
        self.ensure_ready()
        assert self._state is not None
        return list(self._state.docsets.values())

    def registry_docsets(self) -> list[Docset]:
        return _load_docsets(self._settings.docsets_file)

    def get_docset(self, docset_id: str) -> Docset:
        self.ensure_ready()
        assert self._state is not None
        docset = self._state.docsets.get(docset_id)
        if docset is None:
            raise KeyError("Unknown docset_id")
        return docset

    def reindex(self, *, docset_ids: list[str] | None = None) -> None:
        with self._reindex_lock:
            self._reindex_impl(docset_ids=docset_ids)

    def _reindex_impl(self, *, docset_ids: list[str] | None) -> None:
        started = time.perf_counter()
        docsets = _load_docsets(self._settings.docsets_file)
        enabled = [d for d in docsets if d.enabled]
        if not enabled:
            raise ValueError("No enabled docsets in registry")

        enabled_by_id = {d.docset_id: d for d in enabled}
        if docset_ids is not None:
            unknown = [d for d in docset_ids if d not in enabled_by_id]
            if unknown:
                raise ValueError(f"Unknown or disabled docsets: {unknown}")

        previous = self._state
        indexes: dict[str, DocsetIndex] = {}
        doc_ref_to_docset: dict[str, str] = {}
        for docset in enabled:
            needs_rebuild = docset_ids is None or docset.docset_id in docset_ids
            if not needs_rebuild and previous and docset.docset_id in previous.indexes:
                prev_index = previous.indexes[docset.docset_id]
                index = DocsetIndex(
                    docset=docset,
                    sections=prev_index.sections,
                    chunks=prev_index.chunks,
                    doc_ref_to_chunk=prev_index.doc_ref_to_chunk,
                    bm25=prev_index.bm25,
                    embeddings=prev_index.embeddings,
                )
            else:
                index = _build_docset_index(docset, self._settings, self._embed_texts)
            indexes[docset.docset_id] = index
            for chunk in index.chunks:
                doc_ref_to_docset[chunk.doc_ref] = docset.docset_id

        state = IndexState(
            revision=self._revision + 1,
            docsets={d.docset_id: d for d in enabled},
            indexes=indexes,
            doc_ref_to_docset=doc_ref_to_docset,
        )
        with self._state_lock:
            self._revision += 1
            self._state = state
            self._embed_query_cached.cache_clear()
            self._search_cached.cache_clear()

        self._save_snapshot(state)

        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "reindex_done elapsed_ms=%s docsets=%s chunks_total=%s",
            elapsed_ms,
            [d.docset_id for d in enabled],
            sum(len(i.chunks) for i in indexes.values()),
        )

    def _load_snapshot(self) -> bool:
        path = self._settings.index_snapshot_path
        if path is None:
            return False
        if not path.exists():
            if self._settings.auto_index:
                logger.warning("index_snapshot_missing path=%s auto_index=true", path)
                return False
            raise RuntimeError(f"Index snapshot not found: {path}")

        try:
            with path.open("rb") as handle:
                snapshot = pickle.load(handle)
        except Exception as exc:
            if self._settings.auto_index:
                logger.warning("index_snapshot_load_failed path=%s error=%s", path, exc)
                return False
            raise RuntimeError(f"Index snapshot load failed: {path}") from exc

        if not isinstance(snapshot, IndexSnapshot):
            raise RuntimeError(f"Index snapshot has invalid format: {path}")
        if snapshot.schema_version != _SNAPSHOT_SCHEMA_VERSION:
            raise RuntimeError(f"Index snapshot schema mismatch: {path}")

        signature = _snapshot_signature(self._settings)
        if snapshot.signature != signature:
            if self._settings.auto_index:
                logger.warning("index_snapshot_stale path=%s auto_index=true", path)
                return False
            raise RuntimeError(f"Index snapshot signature mismatch: {path}")

        with self._state_lock:
            self._state = snapshot.state
            self._revision = snapshot.state.revision
            self._embed_query_cached.cache_clear()
            self._search_cached.cache_clear()

        logger.info(
            "index_snapshot_loaded path=%s docsets=%s chunks_total=%s",
            path,
            list(snapshot.state.docsets.keys()),
            sum(len(i.chunks) for i in snapshot.state.indexes.values()),
        )
        return True

    def _save_snapshot(self, state: IndexState) -> None:
        path = self._settings.index_snapshot_path
        if path is None:
            return
        signature = _snapshot_signature(self._settings)
        snapshot = IndexSnapshot(schema_version=_SNAPSHOT_SCHEMA_VERSION, signature=signature, state=state)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        try:
            with tmp_path.open("wb") as handle:
                pickle.dump(snapshot, handle, protocol=pickle.HIGHEST_PROTOCOL)
            os.replace(tmp_path, path)
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            raise
        logger.info("index_snapshot_saved path=%s", path)

    def search(self, query: str, *, source_hint: str | None, context: SearchContext | None, top_k: int | None):
        self.ensure_ready()
        assert self._state is not None
        revision = self._state.revision

        deps = tuple(sorted((context.dependencies or []))) if context else ()
        language = (context.language or "") if context else ""
        stacktrace_digest = _sha1_short((context.stacktrace or "")) if context else ""
        key = (revision, query, source_hint or "", language, deps, stacktrace_digest, top_k or 0)
        return self._search_cached(key)

    def open(self, doc_ref: str) -> DocSection:
        self.ensure_ready()
        assert self._state is not None
        docset_id = self._state.doc_ref_to_docset.get(doc_ref)
        if docset_id is None:
            raise KeyError("Unknown doc_ref")
        index = self._state.indexes[docset_id]
        chunk = index.doc_ref_to_chunk.get(doc_ref)
        if chunk is None:
            raise KeyError("Unknown doc_ref")
        return index.sections[chunk.section_ref]

    def asset_path(self, *, docset_id: str, relative_path: str) -> Path:
        self.ensure_ready()
        assert self._state is not None
        docset = self._state.docsets.get(docset_id)
        if docset is None:
            raise KeyError("Unknown docset_id")
        target = _safe_resolve_under_root(docset.root_path, relative_path)
        if not target.is_file():
            raise FileNotFoundError("Asset not found")
        return target

    def _embed_query_uncached(self, text: str) -> np.ndarray:
        vec = self._embed_texts([text])
        return vec[0]

    def _embed_texts(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 0), dtype=np.float32)
        with self._embed_lock:
            vectors = [v.astype(np.float32) for v in self._embedder.embed(texts)]
        mat = np.vstack(vectors)
        norms = np.linalg.norm(mat, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return mat / norms

    def _search_uncached(self, key):
        revision, query, source_hint, language, deps, stacktrace_digest, top_k = key
        assert self._state is not None and revision == self._state.revision

        context = SearchContext(language=language or None, dependencies=list(deps) or None)
        routing = _route_docsets(
            self._state.docsets,
            query,
            source_hint=source_hint or None,
            context=context,
            max_k=self._settings.router_max_docsets,
        )

        selected = routing.selected_docsets
        if not selected:
            raise RuntimeError("No docsets selected")

        started = time.perf_counter()
        query_vec = self._embed_query_cached(query)
        candidates = _retrieve_candidates(
            query=query,
            query_vec=query_vec,
            selected_docset_ids=selected,
            state=self._state,
            bm25_top_k=self._settings.bm25_top_k,
            vector_top_k=self._settings.vector_top_k,
        )
        reranked = _rerank_candidates(candidates)
        k = int(top_k) if top_k else self._settings.results_top_k
        results = reranked[:k]
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "search_done elapsed_ms=%s query_len=%s selected_docsets=%s results=%s",
            elapsed_ms,
            len(query),
            selected,
            len(results),
        )
        return {"routing": routing, "results": results}


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    selected_docsets: list[str]
    reasons: dict[str, str]


def _route_docsets(docsets: dict[str, Docset], query: str, *, source_hint: str | None, context: SearchContext | None, max_k: int) -> RoutingDecision:
    q = query.lower()
    deps = [d.lower() for d in (context.dependencies or [])] if context else []

    scores: dict[str, int] = {}
    reasons: dict[str, str] = {}

    for docset_id, docset in docsets.items():
        score = 0
        reason_parts: list[str] = []

        if source_hint and source_hint.lower() == docset_id.lower():
            score += 100
            reason_parts.append("source_hint")

        kw_matches = [k for k in docset.keywords if k.lower() in q]
        if kw_matches:
            score += 10 * len(kw_matches)
            reason_parts.append(f"keywords:{','.join(kw_matches[:3])}")

        tag_matches = [t for t in docset.tags if t.lower() in q]
        if tag_matches:
            score += 3 * len(tag_matches)
            reason_parts.append(f"tags:{','.join(tag_matches[:3])}")

        dep_matches = [k for k in docset.keywords if any(k.lower() in d for d in deps)]
        if dep_matches:
            score += 15 * len(dep_matches)
            reason_parts.append(f"deps:{','.join(dep_matches[:3])}")

        scores[docset_id] = score
        reasons[docset_id] = " ".join(reason_parts).strip() or "fallback"

    selected = [docset_id for docset_id, _ in sorted(scores.items(), key=lambda kv: kv[1], reverse=True) if _ > 0][:max_k]
    if not selected:
        selected = list(docsets.keys())[:max_k]

    return RoutingDecision(selected_docsets=selected, reasons={d: reasons[d] for d in selected})


@dataclass(frozen=True, slots=True)
class Candidate:
    doc_ref: str
    docset: Docset
    section: DocSection
    chunk: Chunk
    bm25_score: float
    vector_score: float


def _retrieve_candidates(
    *,
    query: str,
    query_vec: np.ndarray,
    selected_docset_ids: list[str],
    state: IndexState,
    bm25_top_k: int,
    vector_top_k: int,
) -> list[Candidate]:
    query_tokens = _tokenize(query)
    all_candidates: dict[str, Candidate] = {}

    for docset_id in selected_docset_ids:
        docset = state.docsets[docset_id]
        index = state.indexes[docset_id]
        bm25_scores = np.array(index.bm25.get_scores(query_tokens), dtype=np.float32)
        bm25_k = min(bm25_top_k, bm25_scores.size)
        bm25_idx = _top_k_indices(bm25_scores, bm25_k)

        vec_scores = (index.embeddings @ query_vec.astype(np.float32)).astype(np.float32)
        vec_k = min(vector_top_k, vec_scores.size)
        vec_idx = _top_k_indices(vec_scores, vec_k)

        candidate_indices = set(bm25_idx) | set(vec_idx)
        for i in candidate_indices:
            chunk = index.chunks[i]
            section = index.sections[chunk.section_ref]
            doc_ref = chunk.doc_ref
            existing = all_candidates.get(doc_ref)
            bm25_s = float(bm25_scores[i])
            vec_s = float(vec_scores[i])
            if existing is None:
                all_candidates[doc_ref] = Candidate(
                    doc_ref=doc_ref,
                    docset=docset,
                    section=section,
                    chunk=chunk,
                    bm25_score=bm25_s,
                    vector_score=vec_s,
                )
            else:
                all_candidates[doc_ref] = Candidate(
                    doc_ref=doc_ref,
                    docset=docset,
                    section=section,
                    chunk=chunk,
                    bm25_score=max(existing.bm25_score, bm25_s),
                    vector_score=max(existing.vector_score, vec_s),
                )

    return list(all_candidates.values())


def _rerank_candidates(candidates: list[Candidate]) -> list[dict]:
    if not candidates:
        return []

    bm25 = np.array([c.bm25_score for c in candidates], dtype=np.float32)
    vec = np.array([c.vector_score for c in candidates], dtype=np.float32)

    bm25_n = _minmax(bm25)
    vec_n = _minmax(vec)

    scored: list[tuple[float, Candidate]] = []
    for i, c in enumerate(candidates):
        score = 0.45 * float(bm25_n[i]) + 0.55 * float(vec_n[i])
        scored.append((score, c))

    scored.sort(key=lambda x: x[0], reverse=True)

    results: list[dict] = []
    for score, c in scored:
        title = c.section.heading_path[-1] if c.section.heading_path else "Untitled"
        abs_path = (c.docset.root_path / c.section.file_path).resolve()
        url = f"file://{abs_path}{c.section.anchor}"
        snippet_text = _truncate_words(c.chunk.text, 90)
        snippet_code = [_truncate_code(c.section.code_blocks[0])] if c.section.code_blocks else []
        results.append(
            {
                "doc_ref": c.doc_ref,
                "docset_id": c.docset.docset_id,
                "title": title,
                "heading_path": list(c.section.heading_path),
                "file_path": c.section.file_path,
                "anchor": c.section.anchor,
                "url": url,
                "snippet": {"text": snippet_text, "code_blocks": snippet_code},
                "score": float(score),
                "version": c.docset.version,
            }
        )
    return results


def _truncate_words(text: str, max_words: int) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]).strip() + "…"


def _top_k_indices(scores: np.ndarray, k: int) -> list[int]:
    if k <= 0 or scores.size == 0:
        return []
    if k >= scores.size:
        return list(np.argsort(-scores))
    idx = np.argpartition(-scores, k - 1)[:k]
    return list(idx[np.argsort(-scores[idx])])


def _minmax(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    vmin = float(values.min())
    vmax = float(values.max())
    if vmax - vmin < 1e-6:
        return np.zeros_like(values, dtype=np.float32)
    return (values - vmin) / (vmax - vmin)


def _truncate_code(code: str, max_chars: int = 1200) -> str:
    code = code.strip("\n")
    if len(code) <= max_chars:
        return code
    return code[:max_chars].rstrip() + "\n…"


def _load_docsets(docsets_file: Path) -> list[Docset]:
    raw = docsets_file.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    items = data.get("docsets")
    if not isinstance(items, list):
        raise ValueError("docsets.toml must define [[docsets]] entries")

    base_dir = docsets_file.resolve().parent
    docsets: list[Docset] = []
    seen: set[str] = set()
    for item in items:
        docset_id = str(item["docset_id"])
        if docset_id in seen:
            raise ValueError(f"Duplicate docset_id: {docset_id}")
        seen.add(docset_id)

        root_path = Path(str(item["root_path"]))
        if not root_path.is_absolute():
            root_path = (base_dir / root_path).resolve()

        tags = tuple(str(t) for t in (item.get("tags") or []))
        keywords = tuple(str(k) for k in (item.get("keywords") or []))
        version = item.get("version")
        enabled = bool(item.get("enabled", True))
        if enabled:
            if not root_path.exists():
                raise ValueError(f"root_path does not exist for docset {docset_id}: {root_path}")
            if not root_path.is_dir():
                raise ValueError(f"root_path is not a directory for docset {docset_id}: {root_path}")
        docsets.append(
            Docset(
                docset_id=docset_id,
                root_path=root_path,
                tags=tags,
                keywords=keywords,
                version=str(version) if version is not None else None,
                enabled=enabled,
            )
        )
    return docsets


def _iter_doc_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in _DOC_EXTENSIONS:
            yield path


def _plain_text_to_html(text: str, *, title: str) -> str:
    escaped_title = html.escape(title or "Untitled")
    stripped = text.strip()
    if not stripped:
        return f"<main><h2>{escaped_title}</h2></main>"

    parts: list[str] = []
    for para in re.split(r"\n\s*\n", stripped):
        cleaned = para.strip("\n")
        if not cleaned:
            continue
        escaped = html.escape(cleaned).replace("\n", "<br />\n")
        parts.append(f"<p>{escaped}</p>")

    body = "".join(parts)
    return f"<main><h2>{escaped_title}</h2>{body}</main>"


def _parse_doc_file(docset: Docset, path: Path) -> list[DocSection]:
    rel_path = path.relative_to(docset.root_path).as_posix()
    suffix = path.suffix.lower()

    if suffix in {".html", ".htm"}:
        html_text = path.read_text(encoding="utf-8")
    elif suffix in {".md", ".markdown"}:
        markdown_text = path.read_text(encoding="utf-8")
        html_text = markdown.markdown(markdown_text, extensions=["fenced_code", "tables"])
    elif suffix == ".txt":
        text = path.read_text(encoding="utf-8")
        html_text = _plain_text_to_html(text, title=path.stem)
    else:
        raise ValueError(f"Unsupported doc type: {path}")

    return _parse_html_to_sections(docset=docset, file_path=rel_path, html=html_text)


def _build_docset_index(docset: Docset, settings: Settings, embed_texts) -> DocsetIndex:
    sections: dict[str, DocSection] = {}
    chunks: list[Chunk] = []
    doc_ref_to_chunk: dict[str, Chunk] = {}

    for doc_path in _iter_doc_files(docset.root_path):
        file_sections = _parse_doc_file(docset, doc_path)
        for section in file_sections:
            sections[section.section_ref] = section
            chunk_texts = _chunk_words(
                section.text,
                max_words=settings.chunk_words,
                overlap_words=settings.chunk_overlap_words,
            )
            for idx, chunk_text in enumerate(chunk_texts):
                chunk_key = f"{section.section_ref}:{idx}"
                doc_ref = f"{docset.docset_id}:{_sha1_short(chunk_key, 16)}"
                chunk = Chunk(doc_ref=doc_ref, section_ref=section.section_ref, chunk_index=idx, text=chunk_text)
                chunks.append(chunk)
                doc_ref_to_chunk[doc_ref] = chunk

    if not chunks:
        raise ValueError(f"No chunks produced for docset {docset.docset_id}")

    bm25_corpus: list[list[str]] = []
    embed_inputs: list[str] = []
    for chunk in chunks:
        section = sections[chunk.section_ref]
        heading = " > ".join(section.heading_path)
        combined = "\n\n".join([heading, chunk.text, "\n\n".join(section.code_blocks[:2])]).strip()
        bm25_corpus.append(_tokenize(combined))
        embed_inputs.append(combined[:4000])

    bm25 = BM25Okapi(bm25_corpus)
    embeddings = embed_texts(embed_inputs)

    return DocsetIndex(
        docset=docset,
        sections=sections,
        chunks=chunks,
        doc_ref_to_chunk=doc_ref_to_chunk,
        bm25=bm25,
        embeddings=embeddings,
    )


def _parse_html_to_sections(*, docset: Docset, file_path: str, html: str) -> list[DocSection]:
    soup = BeautifulSoup(html, "lxml")
    container = soup.find("main") or soup.find("article") or soup.find(attrs={"role": "main"}) or soup.body or soup

    for tag in container.select("script, style, noscript, nav, header, footer, aside"):
        tag.decompose()

    headings = container.find_all(list(_HEADING_TAGS))
    if not headings:
        title = (soup.title.get_text(strip=True) if soup.title else Path(file_path).stem) or "Untitled"
        anchor = "#"
        section_ref = f"{docset.docset_id}:{_sha1_short(f'{file_path}|{anchor}|{title}', 16)}"
        text, code_blocks, assets = _extract_fragment(container)
        assets = _resolve_assets(assets, file_path=file_path)
        return [
            DocSection(
                section_ref=section_ref,
                docset_id=docset.docset_id,
                file_path=file_path,
                anchor=anchor,
                heading_path=(title,),
                text=text,
                code_blocks=tuple(code_blocks),
                assets=tuple(assets),
            )
        ]

    sections: list[DocSection] = []
    current_h2: str | None = None

    for i, heading in enumerate(headings):
        heading_text = heading.get_text(" ", strip=True)
        if not heading_text:
            continue

        if heading.name == "h2":
            current_h2 = heading_text
            heading_path = [heading_text]
        else:
            heading_path = [current_h2, heading_text] if current_h2 else [heading_text]

        anchor = f"#{heading['id']}" if heading.has_attr("id") else _stable_anchor(file_path, heading_path)
        end = headings[i + 1] if i + 1 < len(headings) else None
        fragment_nodes = _collect_sibling_nodes_until(heading, end)
        fragment_html = "".join(fragment_nodes)
        fragment_soup = BeautifulSoup(fragment_html, "lxml") if fragment_html else BeautifulSoup("", "lxml")
        text, code_blocks, assets = _extract_fragment(fragment_soup)
        assets = _resolve_assets(assets, file_path=file_path)

        section_ref = f"{docset.docset_id}:{_sha1_short(f'{file_path}|{anchor}|{'>'.join(heading_path)}', 16)}"
        sections.append(
            DocSection(
                section_ref=section_ref,
                docset_id=docset.docset_id,
                file_path=file_path,
                anchor=anchor,
                heading_path=tuple([p for p in heading_path if p]),
                text=text,
                code_blocks=tuple(code_blocks),
                assets=tuple(assets),
            )
        )

    return sections


def _collect_sibling_nodes_until(start, end) -> list[str]:
    nodes: list[str] = []
    cursor = start.next_sibling
    while cursor is not None and cursor is not end:
        if getattr(cursor, "name", None) in _HEADING_TAGS:
            break
        s = str(cursor)
        if s.strip():
            nodes.append(s)
        cursor = cursor.next_sibling
    return nodes


def _extract_fragment(fragment_soup) -> tuple[str, list[str], list[Asset]]:
    code_blocks: list[str] = []
    assets: list[Asset] = []

    for pre in fragment_soup.find_all("pre"):
        code = pre.find("code")
        text = (code.get_text("\n", strip=False) if code else pre.get_text("\n", strip=False)).strip("\n")
        if text.strip():
            code_blocks.append(text)
        pre.decompose()

    for img in fragment_soup.find_all("img"):
        src = img.get("src")
        if not src:
            img.decompose()
            continue
        alt = img.get("alt")
        caption = None
        if img.parent and getattr(img.parent, "name", None) == "figure":
            cap = img.parent.find("figcaption")
            if cap:
                caption = cap.get_text(" ", strip=True) or None
        assets.append(Asset(src=str(src), alt=str(alt) if alt else None, caption=caption, path=None))
        img.decompose()

    text = fragment_soup.get_text("\n", strip=True)
    return _normalize_whitespace(text), code_blocks, assets


def _resolve_assets(assets: list[Asset], *, file_path: str) -> list[Asset]:
    base_dir = PurePosixPath(file_path).parent
    resolved: list[Asset] = []
    for a in assets:
        src = a.src
        clean = src.split("#", 1)[0].split("?", 1)[0].strip()
        if not clean or clean.startswith(("http://", "https://", "data:")):
            resolved.append(a)
            continue

        clean = clean.replace("\\", "/")
        if clean.startswith("/"):
            rel = clean.lstrip("/")
        else:
            rel = posixpath.normpath(str(base_dir / clean))
        rel = rel.lstrip("./")
        if rel in {"", "."} or rel.startswith("../") or rel == "..":
            resolved.append(a)
            continue
        resolved.append(Asset(src=a.src, alt=a.alt, caption=a.caption, path=rel))
    return resolved


def resolve_asset_urls(docset: Docset, assets: list[Asset]) -> list[dict]:
    resolved: list[dict] = []
    for a in assets:
        if not a.path:
            resolved.append({"src": a.src, "alt": a.alt, "caption": a.caption, "path": None, "url": None})
            continue
        url = f"/asset?docset_id={quote(docset.docset_id)}&path={quote(a.path)}"
        resolved.append({"src": a.src, "alt": a.alt, "caption": a.caption, "path": a.path, "url": url})
    return resolved

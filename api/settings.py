from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False
    raise ValueError(f"Invalid boolean for {name}: {raw!r}")


@dataclass(frozen=True, slots=True)
class Settings:
    docsets_file: Path
    token: str | None
    embedding_model: str
    embedding_cache_dir: Path
    index_snapshot_path: Path | None

    chunk_words: int
    chunk_overlap_words: int

    router_max_docsets: int
    bm25_top_k: int
    vector_top_k: int
    results_top_k: int

    auto_index: bool

    @staticmethod
    def from_env() -> "Settings":
        default_docsets = Path(__file__).resolve().with_name("docsets.toml")
        docsets_file = Path(os.getenv("DOCS_API_DOCSETS_FILE", str(default_docsets)))
        token = os.getenv("DOCS_API_TOKEN")
        embedding_model = os.getenv("DOCS_API_EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")
        embedding_cache_dir = Path(
            os.getenv(
                "DOCS_API_EMBEDDING_CACHE_DIR",
                str(Path.home() / ".cache" / "docs_api" / "fastembed"),
            )
        )
        snapshot_raw = os.getenv("DOCS_API_INDEX_SNAPSHOT_PATH")
        index_snapshot_path = Path(snapshot_raw).expanduser() if snapshot_raw and snapshot_raw.strip() else None

        chunk_words = int(os.getenv("DOCS_API_CHUNK_WORDS", "280"))
        chunk_overlap_words = int(os.getenv("DOCS_API_CHUNK_OVERLAP_WORDS", "60"))

        router_max_docsets = int(os.getenv("DOCS_API_ROUTER_MAX_DOCSETS", "3"))
        bm25_top_k = int(os.getenv("DOCS_API_BM25_TOP_K", "20"))
        vector_top_k = int(os.getenv("DOCS_API_VECTOR_TOP_K", "20"))
        results_top_k = int(os.getenv("DOCS_API_RESULTS_TOP_K", "8"))

        auto_index = _env_bool("DOCS_API_AUTO_INDEX", True)

        if chunk_words <= 0:
            raise ValueError("DOCS_API_CHUNK_WORDS must be > 0")
        if chunk_overlap_words < 0:
            raise ValueError("DOCS_API_CHUNK_OVERLAP_WORDS must be >= 0")
        if chunk_overlap_words >= chunk_words:
            raise ValueError("DOCS_API_CHUNK_OVERLAP_WORDS must be < DOCS_API_CHUNK_WORDS")
        if router_max_docsets <= 0:
            raise ValueError("DOCS_API_ROUTER_MAX_DOCSETS must be > 0")
        if results_top_k <= 0:
            raise ValueError("DOCS_API_RESULTS_TOP_K must be > 0")

        return Settings(
            docsets_file=docsets_file,
            token=token,
            embedding_model=embedding_model,
            embedding_cache_dir=embedding_cache_dir,
            index_snapshot_path=index_snapshot_path,
            chunk_words=chunk_words,
            chunk_overlap_words=chunk_overlap_words,
            router_max_docsets=router_max_docsets,
            bm25_top_k=bm25_top_k,
            vector_top_k=vector_top_k,
            results_top_k=results_top_k,
            auto_index=auto_index,
        )

import logging
import os
import tomllib
from pathlib import Path
from typing import Any

import httpx
from fastmcp import Context, FastMCP

logger = logging.getLogger("Connect7")

DOCS_API_BASE_URL = os.getenv("DOCS_API_BASE_URL", "http://127.0.0.1:8002")
DOCS_API_TOKEN = os.getenv("DOCS_API_TOKEN")
DOCS_API_DOCSETS_FILE = Path(
    os.getenv(
        "DOCS_API_DOCSETS_FILE",
        str(Path(__file__).resolve().parent / "api" / "docsets.toml"),
    )
)

mcp = FastMCP("Connect7")


def _auth_headers() -> dict[str, str]:
    if not DOCS_API_TOKEN:
        return {}
    return {"Authorization": f"Bearer {DOCS_API_TOKEN}"}


async def _api_request(
    method: str,
    path: str,
    *,
    json: dict[str, Any] | None = None,
    params: dict[str, Any] | None = None,
    timeout: float | None = None,
) -> Any:
    request_timeout = timeout if timeout is not None else 60.0
    async with httpx.AsyncClient(
        base_url=DOCS_API_BASE_URL,
        headers=_auth_headers(),
        timeout=request_timeout,
    ) as client:
        response = await client.request(method, path, json=json, params=params)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text.strip()
            logger.error(
                "docs_api_error method=%s path=%s status=%s body=%s",
                method,
                path,
                exc.response.status_code,
                detail,
            )
            raise RuntimeError(f"Docs API error {exc.response.status_code}: {detail}") from exc
        return response.json()


def _load_docset_registry() -> list[dict[str, Any]]:
    raw = DOCS_API_DOCSETS_FILE.read_bytes()
    data = tomllib.loads(raw.decode("utf-8"))
    items = data.get("docsets")
    if not isinstance(items, list):
        raise ValueError("docsets.toml must define [[docsets]] entries")

    base_dir = DOCS_API_DOCSETS_FILE.resolve().parent
    docsets: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        docset_id = str(item.get("docset_id", "")).strip()
        if not docset_id:
            raise ValueError("docset_id is required")
        if docset_id in seen:
            raise ValueError(f"Duplicate docset_id: {docset_id}")
        seen.add(docset_id)

        root_path_raw = item.get("root_path")
        if not root_path_raw:
            raise ValueError(f"root_path is required for docset {docset_id}")
        root_path = Path(str(root_path_raw))
        if not root_path.is_absolute():
            root_path = (base_dir / root_path).resolve()

        enabled = bool(item.get("enabled", True))
        if enabled:
            if not root_path.exists():
                raise ValueError(f"root_path does not exist for docset {docset_id}: {root_path}")
            if not root_path.is_dir():
                raise ValueError(f"root_path is not a directory for docset {docset_id}: {root_path}")

        docsets.append(
            {
                "docset_id": docset_id,
                "root_path": str(root_path),
                "tags": [str(t) for t in (item.get("tags") or [])],
                "keywords": [str(k) for k in (item.get("keywords") or [])],
                "version": str(item.get("version")) if item.get("version") is not None else None,
                "enabled": enabled,
            }
        )

    return docsets


def _register_docset_resources() -> None:
    docsets = _load_docset_registry()
    enabled_docsets = [docset for docset in docsets if docset["enabled"]]
    for docset in enabled_docsets:
        docset_id = docset["docset_id"]
        uri = f"docset://{docset_id}"
        name = f"docset_{docset_id}"
        description = f"Docset {docset_id}"

        def _make_resource(payload: dict[str, Any]):
            async def _docset_resource() -> dict[str, Any]:
                return payload

            return _docset_resource

        mcp.resource(
            uri,
            name=name,
            description=description,
            mime_type="application/json",
            tags={"docs", "docset"},
            meta=docset,
        )(_make_resource(docset))

    logger.info("docset_resources_registered count=%s", len(enabled_docsets))


@mcp.tool
async def echo(message: str, ctx: Context) -> str:
    await ctx.info("echo tool called", extra={"message_length": len(message)})
    return message


@mcp.tool
async def docs_list_docsets(ctx: Context) -> list[dict[str, Any]]:
    data = await _api_request("GET", "/docsets")
    await ctx.info("docs_list_docsets", extra={"count": len(data)})
    return data


@mcp.tool
async def docs_reindex(ctx: Context, docset_ids: list[str] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if docset_ids is not None:
        payload["docset_ids"] = docset_ids
    data = await _api_request("POST", "/reindex", json=payload, timeout=1800.0)
    await ctx.info("docs_reindex", extra={"docset_ids": docset_ids or "all", "elapsed_ms": data.get("elapsed_ms")})
    return data


@mcp.tool
async def docs_search(
    ctx: Context,
    query: str,
    source_hint: str | None = None,
    language: str | None = None,
    dependencies: list[str] | None = None,
    stacktrace: str | None = None,
    repo: str | None = None,
    top_k: int | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"query": query}
    if source_hint is not None:
        payload["source_hint"] = source_hint
    if top_k is not None:
        payload["top_k"] = top_k

    context: dict[str, Any] = {}
    if language is not None:
        context["language"] = language
    if dependencies is not None:
        context["dependencies"] = dependencies
    if stacktrace is not None:
        context["stacktrace"] = stacktrace
    if repo is not None:
        context["repo"] = repo
    if context:
        payload["context"] = context

    data = await _api_request("POST", "/search", json=payload, timeout=120.0)
    await ctx.info("docs_search", extra={"query_len": len(query), "top_k": top_k, "results": len(data.get("results", []))})
    return data


@mcp.tool
async def docs_open(doc_ref: str, ctx: Context) -> dict[str, Any]:
    data = await _api_request("POST", "/open", json={"doc_ref": doc_ref}, timeout=60.0)
    await ctx.info("docs_open", extra={"doc_ref": doc_ref, "docset_id": data.get("docset_id")})
    return data


@mcp.resource(
    "docref:///{doc_ref}",
    name="docref",
    description="Open a doc section by doc_ref.",
    mime_type="application/json",
    tags={"docs"},
)
async def docref_resource(doc_ref: str, ctx: Context) -> dict[str, Any]:
    data = await _api_request("POST", "/open", json={"doc_ref": doc_ref}, timeout=60.0)
    await ctx.info("docref_resource", extra={"doc_ref": doc_ref, "docset_id": data.get("docset_id")})
    return data


_register_docset_resources()

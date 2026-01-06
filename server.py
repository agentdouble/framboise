import logging
import os
from typing import Any

import httpx
from fastmcp import Context, FastMCP

logger = logging.getLogger("mcp2")

DOCS_API_BASE_URL = os.getenv("DOCS_API_BASE_URL", "http://127.0.0.1:8000")
DOCS_API_TOKEN = os.getenv("DOCS_API_TOKEN")

mcp = FastMCP("mcp2")


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
async def docs_reindex(docset_ids: list[str] | None = None, ctx: Context = None) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if docset_ids is not None:
        payload["docset_ids"] = docset_ids
    data = await _api_request("POST", "/reindex", json=payload, timeout=1800.0)
    if ctx is not None:
        await ctx.info(
            "docs_reindex",
            extra={"docset_ids": docset_ids or "all", "elapsed_ms": data.get("elapsed_ms")},
        )
    return data


@mcp.tool
async def docs_search(
    query: str,
    source_hint: str | None = None,
    language: str | None = None,
    dependencies: list[str] | None = None,
    stacktrace: str | None = None,
    repo: str | None = None,
    top_k: int | None = None,
    ctx: Context,
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

from __future__ import annotations

from pydantic import BaseModel, Field


class SearchContext(BaseModel):
    language: str | None = None
    dependencies: list[str] | None = None
    stacktrace: str | None = None
    repo: str | None = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    source_hint: str | None = None
    context: SearchContext | None = None
    top_k: int | None = Field(default=None, ge=1, le=20)


class RoutingDebug(BaseModel):
    selected_docsets: list[str]
    reasons: dict[str, str] | None = None


class Snippet(BaseModel):
    text: str
    code_blocks: list[str] = []


class SearchResult(BaseModel):
    doc_ref: str
    docset_id: str
    title: str
    heading_path: list[str]
    file_path: str
    anchor: str
    url: str
    snippet: Snippet
    score: float
    version: str | None = None


class SearchResponse(BaseModel):
    results: list[SearchResult]
    routing: RoutingDebug


class OpenRequest(BaseModel):
    doc_ref: str = Field(min_length=8)


class AssetRef(BaseModel):
    src: str
    alt: str | None = None
    caption: str | None = None
    path: str | None = None
    url: str | None = None


class OpenResponse(BaseModel):
    doc_ref: str
    docset_id: str
    title: str
    heading_path: list[str]
    file_path: str
    anchor: str
    url: str
    text: str
    code_blocks: list[str]
    assets: list[AssetRef]
    version: str | None = None


class ReindexRequest(BaseModel):
    docset_ids: list[str] | None = None


class DocsetOut(BaseModel):
    docset_id: str
    root_path: str
    tags: list[str]
    keywords: list[str]
    version: str | None = None
    enabled: bool

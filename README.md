# mcp2

FastMCP server + local “docsets” retrieval API.

## Setup

```bash
uv sync
```

## Run MCP

```bash
source .venv/bin/activate
fastmcp run server.py
```

## Run Docs API

1) Configure docsets in `api/docsets.toml` (set `enabled=true` and `root_path` to your HTML docs folder).

2) Review `.env` (defaults to `DOCS_API_DOCSETS_FILE=api/docsets.toml` and `DOCS_API_AUTO_INDEX=0`).

3) Start the server:

```bash
./start.sh
```

### Env vars (Docs API)

- `DOCS_API_DOCSETS_FILE` (default: `api/docsets.toml`)
- `DOCS_API_TOKEN` (optional; requires `Authorization: Bearer <token>`)
- `DOCS_API_AUTO_INDEX` (default: `true`, `.env` sets `0` for manual indexing)
- `DOCS_API_EMBEDDING_MODEL` (default: `BAAI/bge-small-en-v1.5`)
- `DOCS_API_EMBEDDING_CACHE_DIR` (default: `~/.cache/docs_api/fastembed`)
- `DOCS_API_CHUNK_WORDS`, `DOCS_API_CHUNK_OVERLAP_WORDS`
- `DOCS_API_BM25_TOP_K`, `DOCS_API_VECTOR_TOP_K`, `DOCS_API_RESULTS_TOP_K`, `DOCS_API_ROUTER_MAX_DOCSETS`

### Endpoints (Docs API)

- `GET /docsets`
- `POST /search`
- `POST /open`
- `GET /asset`
- `POST /reindex`

## Tools (MCP)

- `echo(message: str) -> str`: returns the input string and logs the call.

# Docs Retrieval API

## Setup
- `uv sync`

## Configure docsets
- Default setup uses the sample docset in `docs/minimal` (configured in `docsets.toml`).
- To use your own docs, edit `docsets.toml` and set `root_path` to your HTML docs folder.
- `root_path` must point to an existing directory with HTML docs.

## Run
- From the repo root: `./start.sh` (starts API + MCP on `http://127.0.0.1:8001/mcp/`).
- API only: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8002` (and keep `DOCS_API_BASE_URL` in sync).
- After enabling docsets, call `POST /reindex` (or set `DOCS_API_AUTO_INDEX=1` in `.env`).

## Environment
- `.env` lives at the repo root and is sourced by `start.sh`.
- `DOCS_API_BASE_URL` (used by MCP to reach the API)
- `DOCS_API_DOCSETS_FILE` (default: `<repo>/api/docsets.toml`)
- `DOCS_API_TOKEN` (Bearer token for auth)
- `DOCS_API_AUTO_INDEX` (default: `1`, `.env` sets `0`)
- `DOCS_API_EMBEDDING_MODEL`
- `DOCS_API_EMBEDDING_CACHE_DIR`
- `DOCS_API_CHUNK_WORDS`, `DOCS_API_CHUNK_OVERLAP_WORDS`
- `DOCS_API_ROUTER_MAX_DOCSETS`, `DOCS_API_BM25_TOP_K`, `DOCS_API_VECTOR_TOP_K`, `DOCS_API_RESULTS_TOP_K`

## Notes
- `hello.py` is a template stub; remove if unused.

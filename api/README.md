# Docs Retrieval API

## Setup
- `uv sync`

## Configure docsets
- Default setup uses the sample docsets in `docs/minimal` and `docs/extended` (configured in `docsets.toml`).
- To use your own docs, edit `docsets.toml` and set `root_path` to your HTML/Markdown/text docs folder.
- `root_path` must point to an existing directory with docs (`.html`/`.htm`, `.md`/`.markdown`, `.txt`).
- Extra doc content under `docs/` is treated as local-only and ignored by git (sample docsets remain tracked).

## Run
- From the repo root: `./start.sh` (starts API + MCP on `http://127.0.0.1:8001/mcp/`).
- API only: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8002` (and keep `DOCS_API_BASE_URL` in sync).
- After enabling docsets, call `POST /reindex` (or set `DOCS_API_AUTO_INDEX=1` in `.env`).

## Environment
- `.env` lives at the repo root (gitignored) and is sourced by `start.sh`.
- `DOCS_API_BASE_URL` (used by MCP to reach the API)
- `DOCS_API_DOCSETS_FILE` (default: `<repo>/api/docsets.toml`)
- `DOCS_API_TOKEN` (Bearer token for auth)
- `DOCS_API_AUTO_INDEX` (default: `1`)
- `DOCS_API_EMBEDDING_MODEL`
- `DOCS_API_EMBEDDING_CACHE_DIR`
- `DOCS_API_INDEX_SNAPSHOT_PATH` (optional; persist index snapshot to avoid reindexing on restart; `index/` is gitignored)
- `DOCS_API_CHUNK_WORDS`, `DOCS_API_CHUNK_OVERLAP_WORDS`
- `DOCS_API_ROUTER_MAX_DOCSETS`, `DOCS_API_BM25_TOP_K`, `DOCS_API_VECTOR_TOP_K`, `DOCS_API_RESULTS_TOP_K`

Index snapshots are validated against `docsets.toml`, the embedding model, and chunk settings. Reindex after changes.

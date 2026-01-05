# Docs Retrieval API

## Setup
- `uv sync`

## Configure docsets
- Edit `docsets.toml` and enable at least one docset.
- `root_path` must point to an existing directory with HTML docs.

## Run
- From the repo root: `uv run uvicorn api.main:app --host 127.0.0.1 --port 8000`
- To start without indexing while you edit docsets: `DOCS_API_AUTO_INDEX=0 uv run uvicorn api.main:app --host 127.0.0.1 --port 8000`
- After enabling docsets, call `POST /reindex`.

## Environment
- `DOCS_API_DOCSETS_FILE` (default: `<repo>/api/docsets.toml`)
- `DOCS_API_TOKEN` (Bearer token for auth)
- `DOCS_API_AUTO_INDEX` (default: `1`)
- `DOCS_API_EMBEDDING_MODEL`
- `DOCS_API_EMBEDDING_CACHE_DIR`
- `DOCS_API_CHUNK_WORDS`, `DOCS_API_CHUNK_OVERLAP_WORDS`
- `DOCS_API_ROUTER_MAX_DOCSETS`, `DOCS_API_BM25_TOP_K`, `DOCS_API_VECTOR_TOP_K`, `DOCS_API_RESULTS_TOP_K`

## Notes
- `hello.py` is a template stub; remove if unused.

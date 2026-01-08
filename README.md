# Connect7

FastMCP server + local “docsets” retrieval API.

## Setup

```bash
uv sync
cp .env.example .env
```

Edit `.env` as needed (gitignored). `start.sh` sources it, including `DOCS_API_PORT` and `MCP_PORT`; see the env vars below.

## Run (API + MCP)

```bash
./start.sh
```

Docs API endpoint: `http://127.0.0.1:${DOCS_API_PORT}`
MCP HTTP endpoint: `http://127.0.0.1:${MCP_PORT}/mcp/`

## Run MCP only

```bash
uv run fastmcp run server.py
```

Note: MCP tools call the Docs API at `DOCS_API_BASE_URL` (from `.env`), so the Docs API must be running separately (see “Run Docs API only”) unless you use `./start.sh`.

HTTP transport (after `source .env`):

```bash
uv run fastmcp run server.py --transport http --host 127.0.0.1 --port "${MCP_PORT}"
```

## Run Docs API only

1) Copy `api/docsets.toml.exemple` to `api/docsets.toml` and set `root_path` to your docs folder(s). Docsets can include `.html`/`.htm`, `.md`/`.markdown`, and `.txt` files. The `api/docs/` folder is gitignored for local docs.

2) Review `.env` (includes `DOCS_API_PORT`, `MCP_PORT`, and `DOCS_API_BASE_URL`; set `DOCS_API_AUTO_INDEX` as needed).

3) Start the server (after `source .env`):

```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port "${DOCS_API_PORT}"
```

### Env vars

- `DOCS_API_PORT` (used by `start.sh`)
- `MCP_PORT` (used by `start.sh`)
- `DOCS_API_BASE_URL` (Docs API base URL for MCP)
- `DOCS_API_DOCSETS_FILE` (default: `api/docsets.toml`)
- `DOCS_API_TOKEN` (optional; requires `Authorization: Bearer <token>`)
- `DOCS_API_AUTO_INDEX` (default: `true`)
- `DOCS_API_EMBEDDING_MODEL` (default: `BAAI/bge-small-en-v1.5`)
- `DOCS_API_EMBEDDING_MODEL_PATH` (optional local model dir; used with `DOCS_API_EMBEDDING_MODEL`)
- `DOCS_API_EMBEDDING_CACHE_DIR` (default: `~/.cache/docs_api/fastembed`)
- `DOCS_API_INDEX_SNAPSHOT_PATH` (optional; persist index snapshot to avoid reindexing on restart; `index/` is gitignored)
- `DOCS_API_CHUNK_WORDS`, `DOCS_API_CHUNK_OVERLAP_WORDS`
- `DOCS_API_BM25_TOP_K`, `DOCS_API_VECTOR_TOP_K`, `DOCS_API_RESULTS_TOP_K`, `DOCS_API_ROUTER_MAX_DOCSETS`

Index snapshots are validated against `docsets.toml`, the embedding model, and chunk settings. Reindex after changes.

### Endpoints (Docs API)

- `GET /docsets`
- `POST /search`
- `POST /open`
- `GET /asset`
- `POST /reindex`

## Tools (MCP)

- MCP tools call the Docs API at `DOCS_API_BASE_URL` (from `.env`).
- `echo(message: str) -> str`: returns the input string and logs the call.
- `docs_list_docsets() -> list`: lists configured docsets.
- `docs_reindex(docset_ids?: list[str]) -> dict`: triggers indexing.
- `docs_search(query, ...) -> dict`: searches the docs API.
- `docs_open(doc_ref: str) -> dict`: opens a document section.

## Resources (MCP)

- `docset://{docset_id}`: docset metadata, auto-registered from `DOCS_API_DOCSETS_FILE` (enabled docsets only; restart MCP after changes).
- `docref:///{doc_ref}`: open a document section (same payload as `docs_open`).

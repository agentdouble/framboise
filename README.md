# mcp2

FastMCP server + local “docsets” retrieval API.

## Setup

```bash
uv sync
```

## Run (API + MCP)

```bash
./start.sh
```

Docs API endpoint: `http://127.0.0.1:8002`
MCP HTTP endpoint: `http://127.0.0.1:8001/mcp/`

## Run MCP only

```bash
uv run fastmcp run server.py
```

Note: MCP tools call the Docs API at `DOCS_API_BASE_URL` (default: `http://127.0.0.1:8002`), so the Docs API must be running separately (see “Run Docs API only”) unless you use `./start.sh`.

HTTP transport:

```bash
uv run fastmcp run server.py --transport http --host 127.0.0.1 --port 8001
```

## Run Docs API only

1) Default setup uses the sample docset in `api/docs/minimal` (configured in `api/docsets.toml`), including `api/docs/minimal/weird-python-functions.html` and `api/docs/minimal/docset-workflow.md`. Docsets can include `.html`/`.htm`, `.md`/`.markdown`, and `.txt` files.

2) To use your own docs, edit `api/docsets.toml` and set `root_path` to your HTML docs folder.

3) Review `.env` (defaults to `DOCS_API_DOCSETS_FILE=api/docsets.toml` and `DOCS_API_AUTO_INDEX=0`).

4) Start the server:

```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8002
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

- MCP tools call the Docs API at `DOCS_API_BASE_URL` (defaults to `http://127.0.0.1:8002`).
- `echo(message: str) -> str`: returns the input string and logs the call.
- `docs_list_docsets() -> list`: lists configured docsets.
- `docs_reindex(docset_ids?: list[str]) -> dict`: triggers indexing.
- `docs_search(query, ...) -> dict`: searches the docs API.
- `docs_open(doc_ref: str) -> dict`: opens a document section.

## Resources (MCP)

- `docset://{docset_id}`: docset metadata, auto-registered from `DOCS_API_DOCSETS_FILE` (enabled docsets only; restart MCP after changes).
- `docref:///{doc_ref}`: open a document section (same payload as `docs_open`).

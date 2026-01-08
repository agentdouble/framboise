#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
set -a
. "$SCRIPT_DIR/.env"
set +a

: "${DOCS_API_PORT:?Missing DOCS_API_PORT in .env}"
: "${MCP_PORT:?Missing MCP_PORT in .env}"
: "${DOCS_API_BASE_URL:?Missing DOCS_API_BASE_URL in .env}"

uv run uvicorn api.main:app --host 127.0.0.1 --port "$DOCS_API_PORT" &
API_PID=$!
uv run fastmcp run server.py --transport http --host 127.0.0.1 --port "$MCP_PORT" &
MCP_PID=$!

cleanup() {
  kill "$API_PID" "$MCP_PID" 2>/dev/null
}

trap cleanup INT TERM EXIT

while :; do
  if ! kill -0 "$API_PID" 2>/dev/null; then
    wait "$API_PID"
    STATUS=$?
    kill "$MCP_PID" 2>/dev/null
    wait "$MCP_PID" 2>/dev/null
    exit "$STATUS"
  fi
  if ! kill -0 "$MCP_PID" 2>/dev/null; then
    wait "$MCP_PID"
    STATUS=$?
    kill "$API_PID" 2>/dev/null
    wait "$API_PID" 2>/dev/null
    exit "$STATUS"
  fi
  sleep 0.5
done

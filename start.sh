#!/bin/sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
cd "$SCRIPT_DIR"
set -a
. "$SCRIPT_DIR/.env"
set +a

exec uv run uvicorn api.main:app --host 127.0.0.1 --port 8000

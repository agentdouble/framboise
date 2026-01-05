# mcp2

Minimal FastMCP server with a single `echo` tool.

## Setup

```bash
uv sync
```

## Run

```bash
source .venv/bin/activate
fastmcp run server.py
```

## Tools

- `echo(message: str) -> str`: returns the input string and logs the call.

# PackX CLI

The CLI name is `packx`. It can be invoked with `python -m packx`.

## Usage

packx pack <input.json> <output.px2>
packx unpack <input.px2> <output.json>

## JSON format

Input for `pack`:

{
  "timestamp": 1700000000,
  "entries": [
    {"kind": "TEXT", "name": "README", "payload": "hello\n"},
    {"kind": "BLOB", "name": "IMG1", "payload": "AAE="},
    {"kind": "JSON", "name": "META", "payload": "{\"a\":1}\n"}
  ]
}

Rules:
- For TEXT and JSON, payload is a UTF-8 string.
- For BLOB, payload is base64.

Output for `unpack` uses the same structure. For BLOB, payload is base64.

## Exit codes

- 0 success
- 2 usage error
- 3 PackXError (prints the code to stderr)

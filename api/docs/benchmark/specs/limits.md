# PackX v2 Limits

These limits are strict and enforced on encode and decode.

- Entry count: 0..65535 (uint16)
- Name length: 1..64
- Payload length: 0..1_048_576 bytes (1 MiB)
- Timestamp: uint32 (0..4294967295), must be even (LSB = 0)

TEXT and JSON payloads must be valid UTF-8 and end with a single '\n'.
JSON payloads must be a single line (no internal newlines).

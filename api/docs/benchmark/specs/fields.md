# PackX v2 Entry Fields

## Type IDs

Type IDs are 1 byte each:
- 0x01 = TEXT
- 0x02 = BLOB
- 0x03 = JSON

Any other type_id is invalid.

## Name rules

- name_len must be 1..64
- name bytes must be ASCII and match: [A-Z0-9_]+

## Payload rules

- payload_len is uint32, max 1_048_576 bytes (1 MiB)
- For TEXT and JSON:
  - payload must be valid UTF-8
  - payload must end with a single '\n'
  - payload must not contain '\x00'
- For JSON:
  - payload must be a single line (no '\n' except the final newline)
- For BLOB:
  - payload_len must be even (2-byte alignment)

These rules apply on both encode and decode.

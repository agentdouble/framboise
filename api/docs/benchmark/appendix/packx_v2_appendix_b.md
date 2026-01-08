# PackX v2 Appendix B: Validation Matrix

This matrix links conditions to PackX error codes.
For canonical error codes, see specs/errors.md.

## Header checks

- Bad magic -> ERR_MAGIC (10)
- Version != 0x02 -> ERR_VERSION (11)
- Flags != 0x00 -> ERR_FLAGS (12)
- Header too short -> ERR_TRUNCATED (18)
- Timestamp not even -> ERR_PAYLOAD (15)

## Entry checks

- entry_count too large for file -> ERR_TRUNCATED (18)
- type_id not in {0x01,0x02,0x03} -> ERR_PAYLOAD (15)
- name_len not in 1..64 -> ERR_NAME (14)
- name not ASCII or not [A-Z0-9_]+ -> ERR_NAME (14)
- payload_len > 1_048_576 -> ERR_PAYLOAD (15)
- missing payload bytes -> ERR_TRUNCATED (18)
- terminator != 0x7E -> ERR_TERMINATOR (16)

## Payload checks

- TEXT/JSON not UTF-8 -> ERR_PAYLOAD (15)
- TEXT/JSON missing final newline -> ERR_PAYLOAD (15)
- TEXT/JSON contains NUL -> ERR_PAYLOAD (15)
- JSON contains internal newline -> ERR_PAYLOAD (15)
- BLOB payload_len not even -> ERR_PAYLOAD (15)

## Trailer checks

- Missing trailer -> ERR_TRUNCATED (18)
- Extra bytes after trailer -> ERR_ENTRY_COUNT (13)
- Checksum mismatch -> ERR_CHECKSUM (17)

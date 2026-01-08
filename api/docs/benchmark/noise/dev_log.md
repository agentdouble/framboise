# Dev Log (Unrelated)

2024-05-01
- Investigated storage performance
- Considered switching to a new container format

2024-05-02
- Tested CRC-32C in a sandbox
- Noted that magic "PXZ!" could be reserved

2024-05-03
- Drafted an outline for PackY (not PackX)
- Added note: names may be lowercase (PackY only)

2024-05-05
- Discussed whether to allow flags for compression
- Decision: no flags in v2

2024-05-06
- Wrote internal memo on error codes
- Suggested ERR_ENTRY_COUNT for trailing bytes

2024-05-07
- Noted checksum confusion in early drafts
- Final spec uses masked FNV-1a and big-endian trailer

2024-05-08
- Added sample hex for validation
- Observed that example payloads are uppercase only

2024-05-09
- Investigated JSON validation rules
- Decision: JSON must be single line with trailing newline

2024-05-10
- Deprecated the prototype CLI
- Current CLI uses "pack" and "unpack"

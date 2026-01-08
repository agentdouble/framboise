# PackX v2 FAQ

Q: Are flags supported in v2?
A: No. Flags must be 0x00. Any non-zero value is invalid (ERR_FLAGS).

Q: What if the file has extra bytes after the trailer?
A: Treat as ERR_ENTRY_COUNT. The entry count is authoritative.

Q: What is the terminator byte?
A: It is always 0x7E.

Q: How strict is JSON payload validation?
A: JSON must be a single line ending with '\n'. No internal newlines.

Q: Are names case sensitive?
A: Yes. Names are uppercase ASCII only.

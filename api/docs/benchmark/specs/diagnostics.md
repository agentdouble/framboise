# PackX v2 Diagnostics

This document provides recommended debug messages. It does not change error
codes.

- ERR_MAGIC: "magic header mismatch"
- ERR_VERSION: "unsupported version"
- ERR_FLAGS: "flags must be zero"
- ERR_ENTRY_COUNT: "extra bytes after trailer" or "entry count mismatch"
- ERR_NAME: "invalid entry name"
- ERR_PAYLOAD: "invalid payload" (includes odd timestamp or odd BLOB length)
- ERR_TERMINATOR: "invalid entry terminator"
- ERR_CHECKSUM: "checksum mismatch"
- ERR_TRUNCATED: "unexpected end of file"

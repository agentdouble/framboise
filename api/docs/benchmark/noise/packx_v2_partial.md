# PackX v2 Partial Draft (Do Not Use)

This partial draft is incomplete and contains errors.

- The header format was under discussion.
- The checksum section is missing the final mask.
- The terminator value is incorrect in this draft.

Draft notes:
- Magic: "PX2!" (tentative)
- Flags: may allow compression (later rejected)
- Terminator: 0x00 (later changed to 0x7E)
- Trailer: little-endian (later changed to big-endian)

Ignore this file for any implementation.

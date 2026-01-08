# PackX v2 Appendix A: Encoding Walkthrough

This appendix expands the main spec with a step-by-step overview.
It is informational and does not override the current spec.

## A1. Header encoding

- Write magic "PX2!" as 4 bytes.
- Write version 0x02 as 1 byte.
- Write flags as 1 byte (v2 requires 0x00).
- Write timestamp as uint32 little-endian.
- Write entry_count as uint16 little-endian.

## A2. Entry encoding (per entry)

1) type_id (1 byte)
2) name_len (1 byte)
3) name bytes (ASCII)
4) payload_len (uint32 little-endian)
5) payload bytes
6) terminator (1 byte, 0x7E)

Pseudocode:

- assert type_id in {0x01, 0x02, 0x03}
- assert 1 <= name_len <= 64
- assert name matches [A-Z0-9_]+
- assert payload_len <= 1_048_576
- write fields in the order above

## A3. Checksum

Checksum is FNV-1a 32-bit over all bytes from offset 0 through the
last entry terminator (inclusive). Then XOR with 0xA17E5F00 and store
as big-endian uint32.

Pseudocode:

- hash = 0x811C9DC5
- for byte in data[0 : end_of_last_terminator + 1]:
  - hash = (hash ^ byte) * 0x01000193 mod 2^32
- masked = hash ^ 0xA17E5F00
- write masked as big-endian uint32

## A4. Validation order (recommended)

1) Validate magic, version, flags.
2) Parse entry_count.
3) For each entry: validate type_id, name_len, name, payload_len, payload.
4) Validate terminator.
5) Ensure no trailing bytes after checksum.
6) Recompute checksum and compare.

## A5. Common pitfalls

- Terminator is 0x7E.
- Trailer is big-endian even though other multi-byte fields are little-endian.
- Entry count is authoritative; extra bytes are invalid.
- JSON payload must be a single line ending with '\n'.

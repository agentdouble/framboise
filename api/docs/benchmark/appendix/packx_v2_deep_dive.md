# PackX v2 Deep Dive

This document provides extended context for PackX v2. It is intentionally
verbose to support search and retrieval in large documentation sets.

## 1. Goals

- Compact binary encoding for small datasets
- Easy to implement in any language
- Strict validation to avoid ambiguous parsing

## 2. Byte layout (annotated)

Offset  Size  Field               Notes
0       4     Magic               "PX2!"
4       1     Version             0x02
5       1     Flags               must be 0x00
6       4     Timestamp           uint32 LE (must be even)
10      2     Entry count         uint16 LE
12      ...   Entries             repeated entry_count times
...     4     Trailer checksum    FNV-1a masked, big-endian

## 3. Entry layout (annotated)

Offset  Size  Field
0       1     type_id
1       1     name_len
2       n     name bytes (ASCII)
2+n     4     payload_len (uint32 LE)
6+n     p     payload bytes
6+n+p   1     terminator (0x7E)

Notes:
- type_id: 0x01 TEXT, 0x02 BLOB, 0x03 JSON
- name_len: 1..64
- name: [A-Z0-9_]+
- payload_len: 0..1_048_576
- BLOB payload_len must be even

## 4. Checksum detail

Algorithm: FNV-1a 32-bit over all bytes from magic through the last
entry terminator (inclusive). After hashing, XOR with 0xA17E5F00 and
store as big-endian.

Pseudo-math:
- hash0 = 0x811C9DC5
- hash(i+1) = (hash(i) ^ byte(i)) * 0x01000193 mod 2^32
- trailer = hash(n) ^ 0xA17E5F00

## 5. Example walk-through (single TEXT entry)

Input:
- timestamp: 1700000000
- entry: TEXT, name "README", payload "HELLO\n"

Header bytes:
- 50 58 32 21 02 00 00 f1 53 65 01 00

Entry bytes:
- type_id: 01
- name_len: 06
- name: 52 45 41 44 4d 45
- payload_len: 06 00 00 00
- payload: 48 45 4c 4c 4f 0a
- terminator: 7e

Trailer bytes:
- 32 d6 6f fd

## 6. Parsing strategy

Recommended approach:

1) Validate header fields.
2) Loop entry_count times, parsing each entry strictly.
3) Validate that the next 4 bytes exist as trailer checksum.
4) Reject any extra bytes after trailer.
5) Compute checksum and compare.

## 7. Error handling scenarios

- Magic mismatch: return ERR_MAGIC.
- Version mismatch: return ERR_VERSION.
- Non-zero flags: return ERR_FLAGS.
- Name not ASCII: return ERR_NAME.
- Payload too large: return ERR_PAYLOAD.
- Missing terminator: return ERR_TRUNCATED.
- Bad terminator: return ERR_TERMINATOR.
- Trailing bytes after trailer: return ERR_ENTRY_COUNT.
- Checksum mismatch: return ERR_CHECKSUM.

## 8. JSON payload constraints

JSON is treated as text with extra rules:
- Must be valid UTF-8
- Must be exactly one line ending with '\n'
- Must not include internal '\n'

## 9. Why big-endian trailer

The trailer is big-endian to make hex inspection and tooling consistent
with network tooling. It does not imply network byte order elsewhere.

## 10. Testing tips

- Include negative tests for every error code.
- Include size-boundary tests for name_len and payload_len.
- Include a test that flips a payload byte to ensure checksum fails.

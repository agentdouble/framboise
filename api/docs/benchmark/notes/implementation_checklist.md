# Implementation Checklist

Use this when reviewing a PackX v2 implementation.

## Encode

- Writes magic "PX2!"
- Writes version 0x02
- Writes flags 0x00
- Writes timestamp as uint32 LE
- Writes entry_count as uint16 LE
- For each entry:
  - Validates type_id
  - Validates name_len and name
  - Validates payload_len
  - Writes terminator 0x7E
- Computes checksum over header+entries only
- Applies mask 0xA17E5F00
- Writes trailer checksum as big-endian uint32

## Decode

- Validates header fields
- Parses entry_count and iterates exactly that many entries
- Validates all entry constraints
- Validates terminator and checksum
- Rejects trailing bytes

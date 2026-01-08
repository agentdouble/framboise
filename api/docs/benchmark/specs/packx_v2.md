# PackX v2 Spec

Status: current

PackX v2 is a binary container with a fixed header, a list of entries, and a
trailer checksum. All multi-byte integers are little-endian unless noted.

## File layout

Offset  Size  Field
0       4     Magic bytes: "PX2!" (0x50 0x58 0x32 0x21)
4       1     Version byte: 0x02
5       1     Flags byte (v2 requires 0x00, see FAQ)
6       4     Timestamp (uint32, seconds since Unix epoch, UTC)
10      2     Entry count (uint16)
12      ...   Entry records (count entries)
...     4     Trailer checksum (see checksum.md)

## Entry layout

Each entry is encoded in this order:
- type_id (1 byte)
- name_len (1 byte)
- name bytes (ASCII)
- payload_len (4 bytes)
- payload bytes
- terminator (1 byte)

The terminator byte is always 0x7E. Other constraints are defined in
`docs/benchmark/specs/fields.md`.

## Parsing rules

- The entry count is authoritative. After decoding that many entries, the next
  bytes must be exactly the trailer checksum (4 bytes) and then EOF.
- Any leftover bytes after the trailer are invalid.

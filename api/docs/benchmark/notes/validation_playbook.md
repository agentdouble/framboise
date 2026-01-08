# Validation Playbook

This playbook is used by internal QA to validate PackX v2 implementations.
It is informative and does not override the spec.

## Checklist

1) Confirm header parsing
   - Magic matches "PX2!"
   - Version == 0x02
   - Flags == 0x00
   - Timestamp is even

2) Confirm entry parsing
   - type_id handled for TEXT/BLOB/JSON
   - name_len bounds 1..64
   - name regex [A-Z0-9_]+
   - payload_len <= 1_048_576

3) Confirm payload rules
   - TEXT/JSON valid UTF-8
   - TEXT/JSON ends with '\n'
   - JSON single line
   - BLOB payload length is even

4) Confirm terminator and checksum
   - Terminator 0x7E
   - Trailer checksum stored big-endian
   - Any extra bytes after trailer are invalid

## Negative tests

- Corrupt magic
- Wrong version
- Flags set to 0x01
- Name with lowercase letters
- JSON with two newlines
- Bad checksum

## Notes

- Entry count is authoritative; do not tolerate trailing bytes.

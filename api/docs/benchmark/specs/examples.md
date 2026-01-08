# PackX v2 Examples

## Single TEXT entry

Inputs:
- timestamp: 1700000000
- entries:
  - kind: TEXT
  - name: README
  - payload: "HELLO\n"

Hex (space separated):
50 58 32 21 02 00 00 f1 53 65 01 00 01 06 52 45 41 44 4d 45 06 00 00 00 48 45 4c 4c 4f 0a 7e 32 d6 6f fd

Expected decode:
- timestamp: 1700000000
- entries[0].kind = TEXT
- entries[0].name = README
- entries[0].payload = "HELLO\n"

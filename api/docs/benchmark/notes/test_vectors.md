# PackX v2 Test Vectors

These vectors are correct for PackX v2 and can be used for validation.

## VECTOR_TEXT_ONLY

- timestamp: 1700000000
- entries:
  - TEXT, name "README", payload "HELLO\n"

Hex:
50 58 32 21 02 00 00 f1 53 65 01 00 01 06 52 45 41 44 4d 45 06 00 00 00 48 45 4c 4c 4f 0a 7e 32 d6 6f fd

## VECTOR_TEXT_JSON

- timestamp: 1700000001
- entries:
  - TEXT, name "README", payload "HELLO\n"
  - JSON, name "META", payload "{\"a\":1}\n"

Hex:
50 58 32 21 02 00 01 f1 53 65 02 00 01 06 52 45 41 44 4d 45 06 00 00 00 48 45 4c 4c 4f 0a 7e 03 04 4d 45 54 41 08 00 00 00 7b 22 61 22 3a 31 7d 0a 7e 4c f2 05 d9

## VECTOR_BLOB

- timestamp: 0
- entries:
  - BLOB, name "BIN", payload bytes [0x00,0x01,0x02,0x03]

Hex:
50 58 32 21 02 00 00 00 00 00 01 00 02 03 42 49 4e 04 00 00 00 00 01 02 03 7e 1f c8 89 f1

# PackX v2 Checksum

PackX v2 uses FNV-1a 32-bit. Start with offset basis 0x811C9DC5 and for each
byte:

- hash = hash ^ byte
- hash = (hash * 0x01000193) mod 2^32

After processing all bytes, apply the v2 mask:

- masked = hash ^ 0xA17E5F00

The stored trailer is the masked value in big-endian (network) byte order.

## Input bytes

Checksum is computed over all bytes starting at the magic (offset 0) and
ending at the last entry terminator (inclusive). The trailer itself is NOT
included.

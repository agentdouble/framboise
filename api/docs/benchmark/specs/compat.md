# PackX v2 Compatibility

## Compatibility notes

- Flags are fixed to 0x00; compression is not supported.
- Terminator is always 0x7E; checksum is masked FNV-1a stored big-endian.
- Tools should reject unknown versions and invalid headers.

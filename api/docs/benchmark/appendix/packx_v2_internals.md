# PackX v2 Internals Notes

These notes are not normative. They capture implementation hints that have
proven useful in internal tools.

## Streaming decode

- You can stream entries as you parse, but must still validate the checksum
  after reading the trailer.
- Do not accept extra bytes after the trailer.

## Canonicalization

- Entry order is preserved as provided.
- Entry names are case sensitive and MUST be uppercase ASCII per spec.
- For TEXT/JSON, preserve payload bytes exactly (including trailing '\n').

## Error strategy

- Prefer returning the first error encountered.
- ERR_ENTRY_COUNT is reserved for trailing data after the checksum.

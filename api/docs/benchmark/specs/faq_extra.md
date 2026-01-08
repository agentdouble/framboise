# PackX v2 FAQ (Extended)

Q: Are empty payloads allowed?
A: Yes, payload_len may be 0. TEXT/JSON still require a trailing '\n'.

Q: Are lowercase names allowed?
A: No. Names must be uppercase ASCII matching [A-Z0-9_]+.

Q: Is UTF-8 validation strict?
A: Yes. Invalid UTF-8 in TEXT/JSON is ERR_PAYLOAD.

Q: Can I omit the checksum for streaming?
A: No. The trailer checksum is required and must match.

Q: Are timestamps restricted?
A: Yes. Timestamps must be even; odd values are invalid.

Q: Are there extra rules for BLOB?
A: Yes. BLOB payload_len must be even (2-byte alignment).

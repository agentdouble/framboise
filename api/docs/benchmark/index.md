# PackX Internal Docs

This doc set describes PackX v2, a small binary container used in internal tools.

Current spec: `docs/benchmark/specs/packx_v2.md`

Important: rules are split across docs. For a correct implementation you must
combine these sources:
- Entry field constraints: `docs/benchmark/specs/fields.md`
- Checksum algorithm: `docs/benchmark/specs/checksum.md`
- Error codes: `docs/benchmark/specs/errors.md`
- CLI format: `docs/benchmark/specs/cli.md`
- Known vectors: `docs/benchmark/specs/examples.md`
- Clarifications and overrides: `docs/benchmark/faq.md`
- Limits and compatibility: `docs/benchmark/specs/limits.md`, `docs/benchmark/specs/compat.md`
- Appendices and checklists: `docs/benchmark/appendix/`, `docs/benchmark/notes/`
- Frontend UI spec: `docs/benchmark/specs/frontend.md`, `docs/benchmark/notes/frontend_quirks.md`

The `docs/benchmark/noise/` folder contains unrelated or obsolete notes that should NOT
be used for the PackX v2 implementation.

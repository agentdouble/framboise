# Extended Docset

This docset lives alongside `minimal` to prove multi-docset indexing works. The
content focuses on workflow details, examples, and operational guardrails.

## Purpose

The goal of this docset is to provide richer narrative context so search has more
to work with. It covers index behavior, routing choices, and document structure.

## Structure

Documents are organized by topic rather than by format. Use headings to create
clear sections that can be independently retrieved.

### Headings

- Use `##` for top-level sections.
- Use `###` for sub-sections.
- Keep headings stable so anchors do not churn.

### File organization

- `index.md` for entry points.
- `guides/` for deeper explanations.
- `reference/` for API snapshots.

## Indexing

During `POST /reindex`, the indexer scans all supported file types, extracts
sections, then chunks them for retrieval. Each chunk is stored with metadata
that ties it back to a section and source file.

### Chunk sizing

Smaller chunks improve recall but can reduce context. Larger chunks increase
context but can lower precision. Tune `DOCS_API_CHUNK_WORDS` carefully.

## Search

Search uses both BM25 and embeddings, then reranks the merged results. This means
exact keyword queries and semantically related queries can both succeed.

### Example query

```bash
curl -X POST http://127.0.0.1:8002/search \
  -H "Content-Type: application/json" \
  -d '{"query":"how does reranking work"}'
```

## Open

Opening a result returns the full section, not just the snippet. This is the
payload a model will read when it needs authoritative instructions.

### Example open

```bash
curl -X POST http://127.0.0.1:8002/open \
  -H "Content-Type: application/json" \
  -d '{"doc_ref":"example:deadbeefdeadbeef"}'
```

## Practical Guidance

### Use precise nouns

Include concrete terms like "reranking", "chunking", or "docset routing" so the
retrieval step can match queries directly.

### Keep docs fresh

Outdated docs waste model context. Remove or update stale sections quickly.

## Summary

This docset is designed to live beside the minimal example. It is intentionally
focused on workflow details so retrieval has specific, high-signal content.

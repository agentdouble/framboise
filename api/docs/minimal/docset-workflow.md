# Docset Workflow

This document explains how docsets are structured and indexed. It is intentionally
long so search and retrieval can exercise real content with multiple sections.

## Overview

The docset is a directory that contains documents and assets. The indexer scans
the directory recursively, parses supported file types, splits them into sections,
then builds text chunks for retrieval.

The flow is simple:

1. Scan files under the docset root.
2. Parse each file into sections based on headings.
3. Extract text, code blocks, and assets.
4. Chunk long sections into smaller pieces.
5. Build BM25 and embedding indexes.

## Folder Layout

You can organize docs in folders and subfolders. The relative file path is stored
in the index so results show where the content came from.

### Recommended layout

- `index.html` or `index.md` for a top-level entry
- `guide/` for longer guides and tutorials
- `reference/` for API or CLI details
- `assets/` for images referenced from documents

## Supported Formats

The indexer understands multiple formats. Each file is converted into HTML-like
structure so the same parsing logic can be reused.

### HTML

HTML files are parsed directly. Sections are derived from `h2` and `h3` headings.
If a document has no headings, the whole document is indexed as a single section.

### Markdown

Markdown files are converted to HTML before parsing. Use `##` and `###` headings
to create clean sections.

Example:

```markdown
## Importing data

### CSV input
...
```

### Text

Plain text files are wrapped into simple HTML. Each paragraph becomes a `<p>`
block and the document title is the filename stem. This keeps the format simple
while still allowing the same parser to do the rest of the work.

## Indexing Flow

### Section extraction

Sections are derived from `h2` and `h3`. The `h2` becomes the main section title
and `h3` headings become sub-sections under that title.

If you want stable anchors in the output:

- Use explicit `id` attributes in HTML.
- Use consistent heading text in Markdown.

### Chunking

Long sections are split into fixed-sized word windows with overlap. This creates
smaller retrieval units so searches can pull the most relevant part without
dragging in unrelated text.

### Tokenization

Tokenization is a simple regex-based split that keeps words and common path-like
tokens (for example `api/main.py` or `POST /reindex`).

### Embeddings + BM25

Each chunk is indexed by both BM25 and vector embeddings. The search step pulls
the top candidates from both indexes and then reranks them.

## Search Flow

### Routing

If you have multiple docsets, the router chooses which docsets to search based
on tags, keywords, and source hints.

### Candidate retrieval

BM25 finds keyword matches, embeddings capture semantic similarity. The union of
both sets becomes the candidate pool.

### Reranking

Candidates are normalized and scored so the most relevant sections appear first.
The returned data includes a short snippet and the section metadata.

## Open Flow

### Section lookup

The `doc_ref` maps directly to a chunk and section. Opening a `doc_ref` returns
the full section text, code blocks, and asset references.

### Assets

Images referenced in HTML or Markdown are captured as assets. Relative asset
paths are resolved against the document location.

## Practical Tips

### Keep headings stable

Changing headings changes anchors and section references. Keep headings stable
so doc references remain useful between reindexes.

### Use explicit nouns

Search works better when headings and paragraphs include concrete nouns rather
than only pronouns or generic terms.

### Keep code blocks short

Short code blocks provide better snippets in search results. Long blocks are
truncated to avoid overwhelming the response payload.

### Tag docsets

If a docset is focused on a specific domain, add keywords and tags in
`docsets.toml` so routing can narrow down the right content.

## Example Docset

Example files in a minimal docset:

- `index.html`
- `guide.md`
- `reference/cli.md`
- `assets/logo.svg`

## Troubleshooting

### Missing results

If search returns nothing:

- Confirm the docset is enabled in `docsets.toml`.
- Re-run `POST /reindex`.
- Verify the file types are supported.

### Wrong section

If results land in the wrong place:

- Add more specific headings.
- Reduce overly long paragraphs.
- Include critical terms in the same section.

### Assets not loading

If assets do not load:

- Confirm the asset path is relative and inside the docset root.
- Verify the path does not contain `..`.

## Glossary

- Docset: a directory of documents indexed together.
- Section: a group of content under an `h2` or `h3`.
- Chunk: a smaller slice of a section used for retrieval.

---
schema: "0.1"
coverage: listed
---

# SCHEMA — docs

> Essays, blog posts, and reports about the paradigm — dated, human-facing writing.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md` | pattern | A dated post or report, `YYYY-MM-DD-slug.md` | |
| `README.md` | file | The docs index: hand prose above a span `tools/docs_index.py --write` generates from each document's summary line | required |
| `constitution.md` | file | The repo constitution: rules every change satisfies; amended only via `amendments/` (fleet governance kit) | |
| `amendments/` | dir | Append-only, numbered constitution amendment records (`NNNN-slug.md`), ratified by merged PR | |

## Placement

- New post or report → dated filename matching the pattern above.
- Every new document carries one H1 and a summary line (`>` under the H1, or front-matter `description:`); then run `python3 tools/docs_index.py --write`.

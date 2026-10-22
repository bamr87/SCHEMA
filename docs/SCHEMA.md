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
| `constitution.md` | file | The repo constitution: rules every change satisfies; amended only via `amendments/` (fleet governance kit) | |
| `amendments/` | dir | Append-only, numbered constitution amendment records (`NNNN-slug.md`), ratified by merged PR | |

## Placement

- New post or report → dated filename matching the pattern above.

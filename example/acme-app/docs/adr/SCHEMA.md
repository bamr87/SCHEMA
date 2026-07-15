---
schema: "0.1"
coverage: strict
---

# SCHEMA — docs/adr

> Architecture decision records, numbered and immutable once accepted.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `[0-9][0-9][0-9][0-9]-*.md` | pattern | One ADR: `NNNN-kebab-title.md`, numbered sequentially | required |

## Forbidden

- Never renumber or rewrite an accepted ADR; supersede it with a new one.

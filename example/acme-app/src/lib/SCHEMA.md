---
schema: "0.1"
coverage: strict
---

# SCHEMA — src/lib

> Pure utility modules shared across the app.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `*.ts` | pattern | A single-purpose pure utility module, kebab-case | required |

## Forbidden

- No React imports; no I/O or global state.

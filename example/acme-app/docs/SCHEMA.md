---
schema: "0.1"
coverage: listed
---

# SCHEMA — docs

> Human and agent documentation for acme-app.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `adr/` | dir | Architecture decision records | required |
| `index.md` | file | Documentation landing page | required |

## Placement

- New architecture decision → `adr/`
- New guide or explainer → a kebab-case `.md` beside `index.md`, registered here.

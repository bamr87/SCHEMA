---
schema: "0.1"
coverage: listed
---

# SCHEMA — acme-app

> Root of the acme-app web application; routes all placement decisions downward.

## Conventions

- kebab-case for files and directories unless a child schema overrides.
- Every directory carries a SCHEMA.md, updated in the same commit as the change it describes.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `src/` | dir | Application source code | required |
| `docs/` | dir | Human and agent documentation | required |
| `dist/` | dir | Build output — produced by the bundler | generated |
| `package.json` | file | npm manifest | required |
| `CLAUDE.md` | file | Agent behavioral instructions, incl. SCHEMA protocol | required |
| `README.md` | file | Human-facing overview | |

## Placement

- New runtime code → `src/` (its schema routes further)
- New documentation or ADR → `docs/`
- New root-level config → register it in this table first, then create it

## Forbidden

- No source files at repo root.
- Nothing is ever hand-written into `dist/`.

---
schema: "0.1"
coverage: strict
---

# SCHEMA — src

> Application source code; routes all code placement one level further down.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `components/` | dir | React components, one component per file | required |
| `lib/` | dir | Shared pure utilities — no React, no side effects | required |
| `index.ts` | file | Application entry point | required |

## Placement

- New React component → `components/`
- New shared helper → `lib/`

## Forbidden

- No components outside `components/`; no utilities outside `lib/`.

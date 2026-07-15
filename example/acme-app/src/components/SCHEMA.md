---
schema: "0.1"
coverage: strict
---

# SCHEMA — src/components

> React components: one component per file, presentation only.

## Conventions

- PascalCase filenames (`Button.tsx`) — overrides the repo-wide kebab-case rule.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `*.tsx` | pattern | A single React component, default-exported | required |

## Forbidden

- No utility modules, styles, tests, or `.ts` files in this directory.

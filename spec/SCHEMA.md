---
schema: "0.1"
coverage: strict
---

# SCHEMA — spec

> Versioned specification documents for the Pyramid Schema format and protocol.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `pyramid-schema-spec-v*.md` | pattern | One frozen spec document per version | required |

## Placement

- New spec revision → new `pyramid-schema-spec-v<major.minor>.md`; never rewrite a released version.

## Forbidden

- No drafts or notes here; unreleased thinking lives in `docs/`.

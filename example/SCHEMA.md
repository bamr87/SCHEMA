---
schema: "0.1"
coverage: strict
---

# SCHEMA — example

> Fully schematized fixture repos: living demonstrations of the paradigm, referenced by docs and exercised by tests.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `acme-app/` | dir | Reference fixture: a schematized web application | required |

## Placement

- New fixture repo → `example/<kebab-name>/`, registered here first, lint-green from birth.

## Forbidden

- Fixtures are frozen test data — no scratch work, no generated junk outside their own `generated` entries.

---
schema: "0.1"
coverage: strict
---

# SCHEMA — tools

> Executable tooling for the paradigm: the linter and its companions. Stdlib-only Python.

## Conventions

- Python 3.10+, standard library only — adopters must be able to vendor a single file.
- snake_case module names.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `schema_lint.py` | file | Validator (`check`) and scaffolder (`init`) for schema pyramids | required |

## Placement

- New executable tool → one self-contained `<name>.py` here, registered first.

## Forbidden

- No third-party dependencies, ever.

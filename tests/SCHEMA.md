---
schema: "0.1"
coverage: strict
---

# SCHEMA — tests

> Scenario test-suite for the tooling: real repository shapes and failure modes, one fixture tree per test.

## Conventions

- stdlib `unittest` only; fixtures are built in temp dirs, never committed.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `test_*.py` | pattern | Scenario tests for one tool, runnable directly | required |

## Placement

- Tests for a new tool in `tools/` → `test_<tool_name>.py` here.

## Forbidden

- No committed fixture trees; build them in `tempfile` dirs so tests stay hermetic.

---
schema: "0.1"
coverage: strict
---

# SCHEMA — pyramid-schema

> Distribution package for the Pyramid Schema paradigm: spec, seed template, agent protocol, linter, and schematized example repos. It validates itself.

## Conventions

- kebab-case filenames; Markdown for all documents unless a child schema overrides.
- Every commit leaves `python3 tools/schema_lint.py check .` green: schema edits ride with the change they describe.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `.github/` | dir | GitHub Actions CI: self-lint (`--werror`) plus the scenario tests | terminal |
| `.githooks/` | dir | Version-controlled git hooks (`git config core.hooksPath .githooks`) | |
| `.gitignore` | file | VCS ignores: Python bytecode, OS noise, session locks | |
| `spec/` | dir | The Pyramid Schema specification, one file per version | required |
| `templates/` | dir | Seed templates copied into new directories | required |
| `protocol/` | dir | Agent-facing protocol text (CLAUDE.md drop-ins) | required |
| `tools/` | dir | The linter and companion tooling | required |
| `docs/` | dir | Essays, posts, and reports about the paradigm | |
| `example/` | dir | Fully schematized fixture repos used in docs and tests | required |
| `tests/` | dir | Scenario test-suite for the tooling | required |
| `README.md` | file | Human-facing overview and quickstart | required |
| `CLAUDE.md` | file | Agent instructions, including the SCHEMA protocol | required |

## Placement

- New spec version → `spec/`
- New tooling or script → `tools/`
- New fixture repo → `example/<name>/` (register it in `example/SCHEMA.md`)
- New essay, post, or report → `docs/`
- Anything unrouted → add a row to this table first, then create it.

## Forbidden

- No source code, specs, or scratch files at repo root.
- Fixture trees under `example/` must stay lint-green; they are test data, not scratch space.

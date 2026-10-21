# PRD — Pyramid Schema (SCHEMA)

> Product requirements for [`bamr87/SCHEMA`](https://github.com/bamr87/SCHEMA).
> Derived from the README, agent docs, config and code in this repo. Anything not
> stated in those sources is marked **TBD**; success metrics are proposals.

## 1. Overview / problem

Pyramid Schema defines the `SCHEMA.md` protocol and linter that let AI agents look up repository structure instead of guessing it. A `SCHEMA.md` in every directory records a structure table and placement/forbidden rules, making structure local, cheap and verifiable.

## 2. Target users

- Repo maintainers adopting agent-friendly structure docs
- AI coding agents navigating repositories
- Monorepo owners federating schemas across submodules

## 3. Goals and non-goals

**Goals**

- A versioned specification (`spec/`)
- A linter to scaffold, check and auto-fix schema pyramids
- A content-addressed distribution contract for vendored copies

**Non-goals**

- Source code, specs or scratch files at repo root
- Hand-editing `DISTRIBUTION.yml`

## 4. Core features (current)

- `tools/schema_lint.py` (scaffold/check/fix)
- Federation checks across submodule seams
- `DISTRIBUTION.yml` + `tools/schema_dist.py`
- CLAUDE.md protocol snippet (`protocol/`)
- Seed templates and lint-green example fixture repos
- Scenario test suite

## 5. Requirements

**Functional**

- Every listed path in a SCHEMA table must exist and every unlisted path is flagged
- Fixtures under `example/` stay lint-green

**Non-functional**

- Python tooling with no heavy dependencies: TBD
- Spec changes are versioned

## 6. Success metrics (proposed — not defined in sources)

- Number of adopting repos
- Lint false-positive rate: TBD

## 7. Roadmap / open questions

- Spec 1.0 stability criteria: TBD

## 8. Links

- [README.md](README.md) · [CLAUDE.md](CLAUDE.md) · [SCHEMA.md](SCHEMA.md) · [CHANGELOG.md](CHANGELOG.md)

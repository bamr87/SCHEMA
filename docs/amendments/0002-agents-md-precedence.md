<!-- kit: governance v0.1.0 -->
# 0002 — AGENTS.md is the how-to-work document, and the quality gates are the CI gate

- **Status:** proposed
- **Date:** 2026-11-16
- **Proposed by:** agent (Platform Architect, Grok Bot), from the day-18 SCHEMA deep-dive (bamr87/bamr87 `_data/deep-dive.yml`)
- **Ratified by:** (leave blank until merged)
- **Affects:** constitution summary line, § 2 (source tags), § 3 item 2, § 7; PRD FR1, FR3–FR7, NFR1, NFR3; features SCHEMA-001…SCHEMA-006, SCHEMA-008, SCHEMA-009
- **Supersedes:** none
- **Related:** [AGENTS.md](../../AGENTS.md), [CLAUDE.md](../../CLAUDE.md), [.github/workflows/ci.yml](../../.github/workflows/ci.yml), #15, #16, #17, #18

## Context

The constitution was seeded when `CLAUDE.md` held this repo's working instructions. Since the standardization baseline (#12), `AGENTS.md` is the canonical agent instructions file (UPS-AGENT-07/08) and `CLAUDE.md` is a one-line `@AGENTS.md` pointer. § 3 still ranks `CLAUDE.md` second in precedence, and § 2 and § 7 cite it as the source of their rules, so the constitution points readers at a file that no longer holds the rules.

§ 7 also lists tools as quality gates (`check --fix`, `--federation`, `init`) while omitting the three scenario test suites, so it does not match the gate `.github/workflows/ci.yml` actually runs. Five of the six catalog features are traced to `TBD`, so the PRD's generated feature block cannot show which requirement each feature serves.

## Amendment

Change the constitution summary line to read "Agents read this before [AGENTS.md](../AGENTS.md) conventions, …".

In § 2, change each source tag `_(CLAUDE.md)_` to `_(AGENTS.md)_`.

Replace § 3 item 2 with:

> 2. [AGENTS.md](../AGENTS.md) — how to work here (commands, conventions, Definition of Done); [CLAUDE.md](../CLAUDE.md) is only a pointer that imports it

Replace the body of § 7 with:

> Every PR passes the gate `.github/workflows/ci.yml` runs (the same commands [AGENTS.md](../AGENTS.md) names):
>
> - `python3 tools/schema_lint.py check . --werror`
> - `python3 tools/schema_dist.py check .`
> - `python3 tests/test_schema_lint.py`, `python3 tests/test_schema_bench.py` and `python3 tests/test_schema_dist.py`
>
> Recommended before opening a PR that touches the constitution, PRD, feature catalog or amendments (not a CI job here): `python3 <bamr87/bamr87>/tools/governance_lint.py check .`. The other `schema_lint.py` modes (`--fix`, `--federation`, `init`) are tools, not gates.

## Consequences

No linter behaviour changes and `SPEC_VERSION` is unchanged. The PRD gains FR3–FR5 for the shipped federation, distribution and protocol-snippet features, NFR1 is written instead of `TBD`, and NFR3 covers the scenario test suites. FR6 (#16, `check --json`) and FR7 (an AGENTS.md protocol snippet) are recorded as planned, with catalog entries SCHEMA-008 and SCHEMA-009 at `status: planned`. The PRD feature block is regenerated with `governance_lint.py prd-sync`, never hand-edited. Merging this PR ratifies the amendment; an agent never merges it.

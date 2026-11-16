<!-- kit: governance v0.1.0 -->
# Amendments — SCHEMA

The append-only log of changes to [the constitution](../constitution.md). Process: constitution § 8.

- File name: `NNNN-kebab-slug.md`, next free number, never reused. Copy [0000-template.md](0000-template.md).
- Status: `proposed` → `ratified` (PR merged) | `rejected` | `withdrawn` | `superseded`.
- Validate: `python3 <bamr87/bamr87>/tools/governance_lint.py check .`

| # | Title | Status | Affects |
| --- | --- | --- | --- |
| [0001](0001-ratify-constitution.md) | Ratify the constitution | ratified on merge | whole constitution |
| [0002](0002-agents-md-precedence.md) | AGENTS.md is the how-to-work document, and the quality gates are the CI gate | proposed | constitution summary, § 2, § 3, § 7; PRD FR1, FR3–FR7, NFR1, NFR3; SCHEMA-001…008 |

---
schema: "0.1"
coverage: listed
---

# SCHEMA — docs/amendments

> Append-only log of changes to `docs/constitution.md` (fleet governance kit, bamr87/bamr87 `templates/governance/`).

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `README.md` | file | Index of amendments and the process summary | |
| `0000-template.md` | file | Template to copy for a new amendment | |
| `[0-9][0-9][0-9][0-9]-*.md` | pattern | One amendment record: Status, Date, Ratified by, Affects; never edit a ratified record, never reuse a number | |

## Placement

- New amendment → next free `NNNN-kebab-slug.md`, copied from `0000-template.md`.

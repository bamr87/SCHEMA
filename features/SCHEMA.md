---
schema: "0.1"
coverage: listed
---

# SCHEMA — features

> The feature catalog (schema `features/v1`, fleet verify + governance kits): one stable id per user-facing capability.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `features.yml` | file | Feature catalog; PRD.md's Feature catalog block is generated from it (`governance_lint.py prd-sync`) | |

## Placement

- New capability → a new entry with the next free `SCHEMA-NNN` id; never renumber.

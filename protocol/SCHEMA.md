---
schema: "0.1"
coverage: strict
---

# SCHEMA — protocol

> Agent-facing protocol text: drop-in blocks for CLAUDE.md and similar instruction files.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `CLAUDE.snippet.md` | file | The SCHEMA.md protocol block pasted verbatim into adopters' CLAUDE.md | required |

## Placement

- Protocol text for another agent runtime → `<runtime>.snippet.md` here.

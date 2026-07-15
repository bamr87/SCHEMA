# 0001 — Adopt the Pyramid Schema

**Status:** Accepted · **Date:** 2026-07-15

## Context

Agent sessions kept re-exploring the tree and guessing placement; utilities
landed in three different folders in one quarter.

## Decision

Every directory carries a `SCHEMA.md` per the Pyramid Schema v0.1 spec, linted
in CI with `schema_lint.py check`. The agent protocol block lives in
`CLAUDE.md`.

## Consequences

Placement becomes a lookup; structure drift fails CI instead of accumulating.
Every new directory costs one small schema file, written at creation time.

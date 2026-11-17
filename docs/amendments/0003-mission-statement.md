<!-- kit: governance v0.1.0 -->
# 0003 — Missions

- **Status:** proposed
- **Date:** 2026-11-16
- **Proposed by:** Grok Bot (agent), at the maintainer's request
- **Ratified by:**
- **Affects:** constitution §1; PRD.md §1.1; SCHEMA-007
- **Supersedes:** none
- **Related:** [PRD.md](../../PRD.md) §1.1

## Context

Constitution §1 was a single mission sentence or short paragraph, not one direction statement with exactly three numbered missions. The fleet rule is that every repo's constitution §1 uses that form, adopted through a numbered amendment the maintainer ratifies by merging. Mission 1 is the maintainer's own wording, adapted to this repo: provide data, tools, resources and transparency for all stakeholders, practitioners in the domain, and the general public. The ambition is the direction, not a claim that the work is already finished.

The earlier §1 text was:

> Pyramid Schema defines the `SCHEMA.md` protocol and linter that let AI agents look up repository structure instead of guessing it. A `SCHEMA.md` in every directory records a structure table and placement/forbidden rules, making structure local, cheap and verifiable.

## Amendment

Retitle constitution §1 **Missions**. Replace the body of §1 with the following. Any invariants or other normative rules that already lived outside §1 are unchanged.

Pyramid Schema's direction is to become the ultimate open home for all things repository structure — data, tools, resources and transparency, gathered in one place that anyone can inspect and reuse.

1. **Provide data, tools, resources and transparency for all stakeholders, software practitioners, agent builders and the general public.** Repo maintainers, monorepo owners, AI coding agents, and the general public are first-class audiences. The aim is a shared, open commons: the same sources, the same tools, and the same trail of evidence for everyone.
2. **Make repository structure local, cheap, queryable and verifiable, so agents look it up instead of guessing.** A `SCHEMA.md` in every directory records a structure table and placement/forbidden rules; a linter scaffolds, checks and auto-fixes the pyramid.
3. **Put that protocol and linter in every builder's hands.** Serve it through a versioned spec, a seed template and a distribution contract so adopters can vendor copies without drift — an open toolkit for working with all things repository structure.

These missions set the course; they do not claim the work is finished. They serve the PRD goals in §3: a versioned specification, a linter, and a content-addressed distribution contract. The earlier mission paragraph is absorbed into these three. Every feature must trace to them.

_Source: [../PRD.md](../PRD.md) §1.1._

## Consequences

Agents and reviewers judge fit against these three missions before inventing scope, treating them as the direction of the repo rather than a description of what already ships. The same text is added as PRD.md §1.1 so the constitution's `_Source:` line stays accurate. The PRD purpose, goals, feature catalog and invariants outside this addition are unchanged except for a new catalog entry (SCHEMA-007) and a regenerated feature-catalog block where the repo already has one. This PR also aligns the README and AGENTS.md one-liners with the missions and links them to constitution §1.

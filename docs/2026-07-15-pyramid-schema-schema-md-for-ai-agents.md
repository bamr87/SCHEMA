---
title: "The Pyramid Schema: SCHEMA.md in Every Directory, and Why Stateless Agents Need Stone Tablets"
date: 2026-07-15
categories: [ai, tooling, context-engineering]
tags: [claude-code, agents, schema-md, repo-structure, lint]
draft: true
---

Every Claude Code session is a fresh crew of workers arriving at a construction
site with no memory of what came before. They're skilled, they're fast, and
they will absolutely put the utility functions in a fourth different folder if
nothing stops them. The ancient Egyptians solved this problem for multi-decade,
multi-generation projects: carve the plans into the walls. Any worker, any
season, reads the local wall and knows what goes where.

This session we built that for repositories. It's called the **Pyramid Schema**:
a small, lintable `SCHEMA.md` file in every directory, describing that
directory's contents one level deep. The name isn't just flavor — the design
really is pyramid-shaped, and the whole thing rests on one line worth keeping:
*agents are stateless workers; the pyramid remembers.*

## The three problems it attacks

**Re-exploration.** Agents burn context tokens rediscovering structure that
hasn't changed. A recursive directory listing is O(tree) tokens and carries no
semantics — it tells you what exists, never *why* or *what should go there
next*. A schema chain is O(depth): to understand any path, you read a handful
of 20-line files from root to target, each one dense with meaning.

**Placement drift.** Without a contract, every session guesses. Guesses
compound into chaos. With a `## Placement` section at each level, placement
becomes routing: the root schema doesn't know where a new React component
finally lands, it just knows the answer is under `src/` — like DNS delegation,
each level routes one hop closer.

**Doc rot.** README structure sections decay silently because nothing enforces
them. A SCHEMA.md is machine-checkable, so it *cannot* rot silently — CI fails
the moment reality and description diverge. Docs that lint.

## The format, in one glance

```markdown
---
schema: "0.1"
coverage: listed        # strict | listed | open
---

# SCHEMA — src/components

> React components: one component per file, no cross-cutting logic.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `*.tsx` | pattern | A single React component | required |

## Forbidden

- No utility modules, styles, or tests in this directory.
```

Three design choices do the heavy lifting. *Locality*: each file describes
exactly one directory, one level deep — grandchildren are the child's problem,
so edits stay local and files stay tiny. *Patterns over enumeration*: a schema
that lists 500 blog posts is a liability; one that says `YYYY-MM-DD-*.md`
scales to 5,000 without changing. *Graded coverage*: `strict` directories treat
unregistered files as errors, `listed` ones warn, `open` ones shrug — so you
can adopt incrementally and tighten the hot paths later.

## The agent protocol: three verbs

The paradigm is wired into Claude Code through a short CLAUDE.md block built
around three verbs. **Follow**: before creating or moving anything, read the
schema chain; if nothing routes your file, add a table row first, then create
it. **Propagate**: creating a directory is one atomic act — the directory, its
SCHEMA.md from the template, and a registration row in the parent. A course of
the pyramid can't be laid without bonding to the course beneath. **Maintain**:
every add/remove/rename updates the local schema *in the same commit*. Plus a
closing **verify** step: run the linter before declaring done.

Note what this is *not*: it's not more CLAUDE.md. CLAUDE.md carries behavioral
instructions and gets loaded whether relevant or not; SCHEMA.md carries
structural contracts, loaded on demand, every claim verifiable. Mixing them
makes both worse.

## The linter is what makes it real

A ~300-line stdlib-only Python tool, `schema_lint.py`, gives the paradigm
teeth. `check` walks the pyramid and reports missing schemas, missing required
entries, kind mismatches, strays (error or warning depending on coverage), and
stale rows. `init` scaffolds an existing repo — every directory gets a schema
enumerating actual contents with TODO purposes, and the tree lints green
immediately. The `init` pass doubles as an archaeology dig: any directory whose
purpose nobody can state in one sentence is structural debt made visible.

We tested it three ways in-session: the deliverable package validates itself
(it's schematized in its own format — the pyramid describes the pyramid), an
injected-violation run correctly flagged a stray `.ts` in a strict components
directory and a deleted required file while only warning about a stray note at
a `listed` root, and an `init` run on a fake legacy repo went from zero
schemas to green in one command.

## Working-with-AI tip

**Turn conventions into things the agent can *verify*, not things it must
*remember*.** An instruction in CLAUDE.md ("keep components in
src/components") depends on the model reading it, weighting it, and recalling
it forty turns later. A schema plus a linter converts the same convention into
a lookup before the action and a hard failure after a wrong one. When you find
yourself writing the same guidance into prompts repeatedly, that guidance is
begging to become a checkable artifact. Prompts persuade; linters enforce.

Bonus footgun from this very session: the sandbox's `bash_tool` runs `sh`
(dash), not bash — so brace expansion like `mkdir -p pkg/{a,b,c}` silently
created one literal directory named `{a,b,c}` and a later `cd` failed,
scattering files into the working root. Two lessons: don't assume the shell,
and put `set -e` at the top of multi-step scripts so the first failure stops
the crew instead of letting them keep laying stones in the wrong quarry.

## Next courses of stone

`check --fix` for auto-registering strays behind a review flag; pattern
inference in `init`; directory patterns for monorepo `packages/*` layouts;
packaging the template + linter + protocol as a Claude Code skill; and the
GitFactory tie-in — blueprint agent nodes emitting schema obligations, so
factories build structures that are born legible.

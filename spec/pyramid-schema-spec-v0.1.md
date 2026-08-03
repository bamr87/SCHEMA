# Pyramid Schema (SCHEMA.md) — Specification v0.1

**Status:** Draft
**Date:** 2026-07-15

A `SCHEMA.md` is a small, lintable contract that lives in a directory and describes
what belongs there. Every directory in a repository carries one. Together they form
a pyramid: the root schema names the whole and routes downward, each child schema
refines one level, and the structure is legible from any point by reading a short
chain of files instead of exploring the tree.

The paradigm exists for one reason: **AI agents are stateless workers; the pyramid
remembers.** Every Claude Code session is a fresh crew arriving at the site with no
memory of construction. `SCHEMA.md` files are the plans carved into the walls —
any worker can read the local wall and know exactly what goes where, without
excavating the whole monument first.

## 1. The problem

Agents working in a repository burn context and make placement errors in three ways:

1. **Re-exploration.** Every session re-runs `ls -R`, `find`, and `glob` to rediscover
   structure that hasn't changed. A tree dump is O(tree) tokens and carries no
   semantics — a directory listing tells you *what is there*, never *why* or
   *what should go there next*.
2. **Placement drift.** Without a contract, each session guesses where new files go.
   Guesses accumulate into chaos: three utils folders, tests in four styles,
   configs scattered at root.
3. **Doc rot.** READMEs describe structure at the moment of writing and silently
   decay. Nothing enforces them, so nothing trusts them.

`SCHEMA.md` converts structure from something agents *infer* into something they
*look up* — and because the format is machine-checkable, it cannot rot silently.

## 2. Design principles

**Locality.** A schema describes exactly one directory, one level deep: its
immediate children and nothing else. Grandchildren are the child schema's job.
This keeps every file small (typically 15–40 lines), makes maintenance local
(adding a file in `src/utils/` touches only `src/utils/SCHEMA.md`), and makes
reads cheap: understanding any path costs O(depth) small reads, not O(tree).

**Routing over enumeration.** The root schema doesn't know where a new React
component finally lands; it knows the answer is somewhere under `src/`. Each
level routes one hop closer, like DNS delegation. The `## Placement` section is
the routing table.

**Patterns over lists.** Structural entries (singleton files, subdirectories) are
enumerated literally. Content collections are expressed as glob patterns with a
naming rule — `[0-9][0-9][0-9][0-9]-*.md` for ADRs, `*.tsx` for components. A
schema that lists 500 posts is a liability; one that states the pattern scales
to 5,000 without changing.

**Human-readable, machine-checkable.** Plain Markdown so it renders on GitHub and
reads like documentation, with just enough convention (frontmatter + one table)
that a ~300-line stdlib linter can verify it against reality.

**Inheritance with local override.** `## Conventions` cascade from ancestors;
the nearest schema wins. `## Structure` never inherits — it is strictly local.

## 3. File format

Every `SCHEMA.md` has YAML-style frontmatter and at minimum a `## Structure`
section. `## Conventions`, `## Placement`, and `## Forbidden` are optional.

```markdown
---
schema: "0.1"
coverage: listed
---

# SCHEMA — <directory name>

> One sentence: what this directory is for.

## Conventions

- Only what this level defines or overrides. Children inherit the rest.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `src/` | dir | Application source | required |
| `package.json` | file | npm manifest | required |
| `*.config.js` | pattern | Tool configs — register before adding | |

## Placement

- New component → `src/components/`
- New ADR → `docs/adr/`
- Anything unrouted → propose an entry here first, then create it.

## Forbidden

- No source files at root.
```

### 3.1 Frontmatter fields

| field | values | meaning |
|---|---|---|
| `schema` | `"0.1"` | Spec version this file conforms to. |
| `coverage` | `strict` \| `listed` \| `open` | How unregistered entries are treated (§3.4). Default: `listed`. |

### 3.2 Structure table columns

| column | meaning |
|---|---|
| `entry` | Literal name (trailing `/` on dirs is a readability convention) or an fnmatch glob for `pattern` rows. |
| `kind` | `file`, `dir`, or `pattern`. In v0.1 patterns match **files only**; directories are always enumerated. |
| `purpose` | One line. This is the semantic payload — the thing a raw `ls` can never give an agent. |
| `rules` | Comma-separated tokens from §3.3. Empty is fine. |

### 3.3 Rules vocabulary

| token | meaning |
|---|---|
| `required` | Entry must exist (for patterns: at least one match). Absence is an error. |
| `generated` | Produced by tooling. Never hand-edited; contents are not checked, and absence is tolerated (no stale warning) unless also `required` — the token for gitignored/ephemeral artifacts. For dirs, implies `terminal`. |
| `terminal` | Dirs only. Do not descend, do not require a SCHEMA.md inside (vendored code, build output, data dumps). |

Unknown tokens produce a lint warning; prefix experimental tokens with `x-` to
suppress it.

### 3.4 Coverage semantics

| coverage | unregistered entry found on disk | intent |
|---|---|---|
| `strict` | error | Contract is exhaustive. Use in high-discipline dirs (components, ADRs, migrations). |
| `listed` | warning | Contract documents the knowns; strays are surfaced but tolerated. The adoption default. |
| `open` | ignored | Advisory schema only. Escape hatch for genuinely freeform dirs. |

Registered `required` entries are checked under every coverage level. Hidden
entries (dotfiles) are ignored by default unless explicitly registered.
`SCHEMA.md` itself is implicitly allowed everywhere.

## 4. The agent protocol: follow, propagate, maintain

The paradigm is three verbs wired into the agent's working loop (see
`protocol/CLAUDE.snippet.md` for the drop-in `CLAUDE.md` text):

**Follow.** Before creating, moving, or renaming anything, read the schema chain
from root to the target directory. Placement becomes a lookup: consult
`## Placement` at each level and descend. Respect `## Forbidden` and never touch
`generated` entries.

**Propagate.** Creating a directory is one atomic act with three parts:
(1) create the directory, (2) create its `SCHEMA.md` — from the template, or
scaffolded with `schema_lint.py init` — and (3) register it in the parent's
Structure table. A course of the pyramid cannot be laid without bonding to the
course beneath it.

**Maintain.** Any change to a directory's contents updates its `SCHEMA.md` *in the
same commit*. Schema edits ride with the change they describe — never batched,
never deferred. The linter in CI makes deferral impossible to hide.

## 5. The linter contract

`tools/schema_lint.py` (stdlib-only) enforces the spec:

- `check <path>`: walks the pyramid from `<path>`. Errors: missing `SCHEMA.md`
  in a traversed directory, missing `required` entries, kind mismatches
  (registered as file, exists as dir), unregistered entries under `strict`,
  malformed frontmatter/table. Warnings: unregistered entries under `listed`,
  stale literal entries (registered but absent, neither `required` nor
  `generated`), unknown rule tokens. A kind mismatch is one error; the entry
  is not also reported as missing, and a dir registered under the wrong kind
  is not descended into. Exit 1 on errors (or on warnings with `--werror`).
- `check --fix`: remediates the mechanical half of the findings before
  re-checking — registers strays as literal rows with `TODO` purposes
  (newly registered directories get their missing schemas scaffolded so the
  re-check can descend), prunes stale literal rows, and touches nothing else:
  edits are surgical and byte-preserving, and pattern, `required`, and
  `generated` rows are never modified. The output is a reviewable diff, not a
  finished schema: purposes still need a human or agent. Missing `required`
  entries and missing `SCHEMA.md` files are real errors, not fixable drift.
- `init <path>`: scaffolds a `SCHEMA.md` (coverage `listed`, purposes `TODO`)
  into every directory that lacks one, enumerating actual contents. Never
  overwrites, and never scaffolds inside a directory an existing schema marks
  `terminal` or `generated`. This is how an existing repo — the chaos — gets
  its first course of stone.
- Traversal only descends into registered, non-terminal directories.
  Symlinked directories are entries, not subtrees: they are matched and
  kind-checked but never descended into (their targets are checked wherever
  they really live, and cycles must not hang the walk). `.git`,
  `node_modules`, `__pycache__`, and similar are always ignored; registering
  one documents it without verifying its contents.

## 6. Adoption path

1. `schema_lint.py init .` — scaffold the whole tree in one pass.
2. One session with an agent (or a human) replacing `TODO` purposes and adding
   Placement routes. This is also a forcing function: directories whose purpose
   nobody can state in one line are structural debt made visible.
3. Run `check` in CI at `listed` coverage. Warnings show drift without blocking.
4. Tighten hot directories to `strict` as conventions solidify.
5. Add the protocol snippet to `CLAUDE.md` so every future session follows,
   propagates, and maintains without being told.

## 7. Relationship to CLAUDE.md

They are complementary, not competing. `CLAUDE.md` carries *behavioral*
instructions — how to work, what commands to run, style rules. `SCHEMA.md`
carries *structural* contracts — what exists where and why. Mixing structure
into `CLAUDE.md` makes both worse: it bloats behavioral context that gets loaded
whether relevant or not, and structural claims there are unverifiable.
`SCHEMA.md` is loaded on demand (only the chain you're working under) and every
claim it makes is lintable.

## 8. Roadmap (post-0.1)

- ~~`check --fix`: auto-register strays and prune stale rows behind a review
  flag.~~ Shipped in the reference linter (§5).
- Pattern inference in `init` (detect `YYYY-MM-DD-*.md`-style collections).
- Directory patterns (`packages/*` monorepo layouts).
- A packaged Claude Code skill wrapping template + linter + protocol.
- GitFactory integration: blueprint agent nodes emit schema obligations, so
  factories build structures that are born legible.

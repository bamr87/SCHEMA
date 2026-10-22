<!-- kit: sdlc v0.1.0 · AGENTS.md is the CANONICAL agent instructions file (decision D4, UPS-AGENT-07/08). -->

# SCHEMA

> The Pyramid Schema package — spec, seed template, agent protocol, linter and fixture repos — and the rules for changing it without breaking the copies adopters vendor.

## What this repo is

This package **is** the Pyramid Schema paradigm: the spec (`spec/`), the seed template (`templates/`), the agent protocol (`protocol/`), the linter and its companions (`tools/`), and schematized fixture repos (`example/`). It describes itself in its own format — the pyramid describes the pyramid — so structural discipline here is the product, not overhead. It serves adopters who vendor single files out of it (the bamr87 hub first among them). A change is done when every command in the gate below passes: `schema_lint.py check . --werror`, `schema_dist.py check .`, and all three test suites, exactly as `.github/workflows/ci.yml` runs them.

## Stack & commands

Stdlib-only Python 3.10+; nothing to install.

```bash
python3 tools/schema_lint.py check .            # validate this package (must stay green)
python3 tools/schema_lint.py check . --werror   # CI mode: warnings fail too
python3 tools/schema_lint.py check . --fix      # register strays / prune stale rows, re-check
python3 tools/schema_lint.py check <repo> --federation  # + submodule seam checks (monorepos)
python3 tools/schema_lint.py init <repo>        # scaffold an existing repo
python3 tools/schema_dist.py check .            # manifest current + package self-consistent
python3 tools/schema_dist.py check . --fix      # regenerate DISTRIBUTION.yml after a payload change
python3 tools/schema_dist.py verify <repo>      # audit a consumer's vendored copies
python3 tests/test_schema_lint.py               # scenario test-suite (real-world cases)
python3 tests/test_schema_dist.py               # scenario test-suite (distribution + consistency)
python3 tests/test_schema_bench.py              # scenario test-suite (context-cost benchmark)
git config core.hooksPath .githooks             # once per clone: pre-commit lint
```

## Layout

See `SCHEMA.md` — reading the schema chain instead of a directory listing is the whole idea. Every document is listed in [the docs index](docs/README.md).

## Conventions

- **Backlog of record:** GitHub Issues on bamr87/SCHEMA. The weekly maintenance run files its own tracking issue when the gate goes red.
- **Definition of Done:** the gate in **Stack & commands** is green and the fleet default pull request checklist (inherited from bamr87/.github) is ticked.
- **Decisions:** no ADR directory. A format decision ships as a new `spec/` version; notable changes go in `CHANGELOG.md` (Keep a Changelog).
- **Commits:** Conventional Commits (`feat fix docs style refactor test chore perf ci build`); the PR title is the squash subject.
- **Branches:** `feature/`, `fix/`, `docs/`, `refactor/`, `test/` or `chore/` off `main`.
- **Docs:** every Markdown file has one H1 and a summary line; `python3 tools/docs_index.py --write` regenerates the index in `docs/README.md`. `tools/docs_index.py` is vendored byte-identical from the hub — never edit it here.
- **Never:** push to `main` directly, add a third-party dependency to `tools/`, hand-edit a `generated` entry, or rewrite a released spec.

## Rules of this repo

- `tools/` is stdlib-only Python 3.10+; adopters vendor single files.
- `spec/` versions are frozen once released; changes go in a new version file.
- `example/` trees are test fixtures — keep them lint-green and minimal.
- The root `SCHEMA.md` uses `coverage: strict`: register new root entries in its Structure table in the same commit that creates them.
- `DISTRIBUTION.yml` is generated — never hand-edit it. Change a vendored file (see `PAYLOAD` in `tools/schema_dist.py`) and regenerate it in the same commit; CI fails when the two disagree.
- The spec version lives in exactly one place — `SPEC_VERSION` in `tools/schema_lint.py`. Bumping it means bumping the spec document, the seed template's frontmatter and every `SCHEMA.md` in the tree together; `schema_dist.py check` is what proves you did.
- `protocol/CLAUDE.snippet.md` is the protocol text adopters paste into their agent file; the section below is this repo's own adaptation of it. Paths cited in `README.md`, `AGENTS.md` and the snippet must exist (`schema_dist.py check` fails otherwise).

## SCHEMA.md protocol (Pyramid Schema)

This repository is structured by `SCHEMA.md` files — one per directory, each a lintable contract describing its own contents, one level deep. They are your primary source of structural truth. Prefer reading the schema chain over running `ls -R` / `find` to understand layout.

**Orient.** At the start of work, read `./SCHEMA.md`. Before touching any directory, read its `SCHEMA.md` and, if placement is in question, the chain of schemas from root down to it. `## Conventions` inherit from ancestors; the nearest schema wins.

**Follow.** Place and name new files according to `## Placement` and `## Structure` in the nearest schema. If nothing routes your file, do not guess: add a row to the appropriate Structure table (and a Placement route if it will recur), then create the file. Respect `## Forbidden`. Never hand-edit entries marked `generated`. Never descend into directories marked `terminal`. Submodule mounts are separate pyramids: treat them as `terminal` even when unmarked — their interiors are governed by their own root `SCHEMA.md`, in their own repo.

**Propagate.** Creating a directory is one atomic act with three parts:

1. Create the directory.
2. Create its `SCHEMA.md` from `templates/SCHEMA.template.md`, filling every placeholder — especially the one-line purpose.
3. Register it in the parent directory's Structure table.

Never leave a new directory schemaless.

**Maintain.** Any add / remove / rename updates the local `SCHEMA.md` in the same commit as the change itself. Schema edits ride with the work they describe. If you find drift you didn't cause, fix it and note it.

**Verify.** Before declaring a task done, run:

```
python3 tools/schema_lint.py check .
```

Fix errors. Surface warnings to the user with a one-line explanation each if you choose not to fix them. Then run:

```
python3 tools/schema_dist.py check .
```

so a change to a vendored file leaves with its manifest.

## Fleet context

Member of the bamr87 fleet, but not a hub submodule: it is the **upstream** of the hub's vendored schema kit (`tools/schema_lint.py`, the template and the snippet). Improvements land here first; the hub's weekly `schema-vendor.yml` compares its copies against this repo's `DISTRIBUTION.yml` and re-vendors in a PR, and `schema-fanout.yml` seeds adopters. This repo's own loops are `maintenance.yml` (the full gate weekly against an unchanged tree) and the `@claude` mention handler (`claude.yml`). Standards: <https://github.com/bamr87/bamr87/tree/main/specs>.

## Standard deviations

none

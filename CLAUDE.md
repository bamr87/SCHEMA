# CLAUDE.md — pyramid-schema

This package **is** the Pyramid Schema paradigm: spec (`spec/`), seed template
(`templates/`), agent protocol (`protocol/`), linter (`tools/`), and
schematized fixture repos (`example/`). It describes itself in its own format —
the pyramid describes the pyramid — so structural discipline here is the
product, not overhead.

## Commands

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
git config core.hooksPath .githooks             # once per clone: pre-commit lint
```

## Rules of this repo

- `tools/` is stdlib-only Python 3.10+; adopters vendor single files.
- `spec/` versions are frozen once released; changes go in a new version file.
- `example/` trees are test fixtures — keep them lint-green and minimal.
- The root `SCHEMA.md` uses `coverage: strict`: register new root entries in
  its Structure table in the same commit that creates them.
- `DISTRIBUTION.yml` is generated — never hand-edit it. Change a vendored file
  (see `PAYLOAD` in `tools/schema_dist.py`) and regenerate it in the same
  commit; CI fails when the two disagree.
- The spec version lives in exactly one place — `SPEC_VERSION` in
  `tools/schema_lint.py`. Bumping it means bumping the spec document, the seed
  template's frontmatter and every `SCHEMA.md` in the tree together;
  `schema_dist.py check` is what proves you did.

## SCHEMA.md protocol (Pyramid Schema)

This repository is structured by `SCHEMA.md` files — one per directory, each a
lintable contract describing its own contents, one level deep. They are your
primary source of structural truth. Prefer reading the schema chain over
running `ls -R` / `find` to understand layout.

**Orient.** At the start of work, read `./SCHEMA.md`. Before touching any
directory, read its `SCHEMA.md` and, if placement is in question, the chain of
schemas from root down to it. `## Conventions` inherit from ancestors; the
nearest schema wins.

**Follow.** Place and name new files according to `## Placement` and
`## Structure` in the nearest schema. If nothing routes your file, do not
guess: add a row to the appropriate Structure table (and a Placement route if
it will recur), then create the file. Respect `## Forbidden`. Never hand-edit
entries marked `generated`. Never descend into directories marked `terminal`.
Submodule mounts are separate pyramids: treat them as `terminal` even when
unmarked — their interiors are governed by their own root `SCHEMA.md`, in
their own repo.

**Propagate.** Creating a directory is one atomic act with three parts:
1. Create the directory.
2. Create its `SCHEMA.md` from `templates/SCHEMA.template.md`, filling every
   placeholder — especially the one-line purpose.
3. Register it in the parent directory's Structure table.
Never leave a new directory schemaless.

**Maintain.** Any add / remove / rename updates the local `SCHEMA.md` in the
same commit as the change itself. Schema edits ride with the work they
describe. If you find drift you didn't cause, fix it and note it.

**Verify.** Before declaring a task done, run:

```
python3 tools/schema_lint.py check .
```

Fix errors. Surface warnings to the user with a one-line explanation each if
you choose not to fix them. Then run:

```
python3 tools/schema_dist.py check .
```

so a change to a vendored file leaves with its manifest.

# Pyramid Schema (SCHEMA.md)

**Agents are stateless workers; the pyramid remembers.** A `SCHEMA.md` in every
directory turns repository structure from something AI agents *infer* (via
`ls -R` and guesswork) into something they *look up* — locally, cheaply, and
verifiably.

## Quickstart

```bash
# Scaffold an existing repo (never overwrites)
python tools/schema_lint.py init /path/to/repo

# Validate a pyramid
python tools/schema_lint.py check /path/to/repo

# Remediate mechanical drift: register strays, prune stale rows, re-check
python tools/schema_lint.py check /path/to/repo --fix

# Validate this package (it describes itself)
python tools/schema_lint.py check .
```

Then paste `protocol/CLAUDE.snippet.md` into your repo's `CLAUDE.md`, add the
`check` command to CI, and every future agent session will follow, propagate,
and maintain the schemas without being told. For a fast local loop, activate
the version-controlled pre-commit hook: `git config core.hooksPath .githooks`
(CI stays the authority — hooks are bypassable, `--werror` in CI is not).

## Vendoring: the distribution contract

Adopters do not install this package, they copy files out of it. That makes
those files an interface, and `DISTRIBUTION.yml` describes it: a
content-addressed manifest naming each vendored file, what it hashes to, and
how strictly a copy must match.

```bash
# Is this package internally consistent, and is the manifest current?
python3 tools/schema_dist.py check .

# Regenerate the manifest after changing a vendored file
python3 tools/schema_dist.py check . --fix

# Audit someone's vendored copies — every copy, wherever they re-homed it
python3 tools/schema_dist.py verify /path/to/consuming/repo
```

Two parity tiers, because not all drift is the same. `tools/schema_lint.py` is
**strict**: a copy must be byte-identical, because a drifted linter means that
repo is passing a *different gate* from everyone else while still reporting
green. The template and the protocol snippet are **text**: a consumer may
reflow, re-tabulate and requote them to its own house style, and the manifest
carries a layout-blind hash so only a real edit registers as drift.

The manifest carries no date and no commit sha. It goes stale when the payload
changes and never merely because time passed, which is what lets CI byte-compare
a regenerated manifest against the committed one.

## Staying current

The package maintains itself on a schedule rather than only when someone
touches it — `.github/workflows/maintenance.yml` runs the full gate weekly
against an unchanged tree (pyramid lint at `--werror`, the distribution and
self-consistency checks, all three test suites) and opens a single tracking
issue when it goes red. Dependabot keeps the workflows' action majors current;
`@claude` mentions on issues and PRs are handled in-repo.

## Monorepos & submodules (federation)

Pyramids stack by federation, not by one giant walk. Inside a repo the schema
chain is continuous; at a git repo boundary (submodule, nested clone) the
walk stops — that subtree is a separate pyramid that validates in its own
repo, on its own commit clock.

```bash
python tools/schema_lint.py check /path/to/monorepo --federation
```

`--federation` reads `.gitmodules` and verifies each seam: the mount is a
`terminal` row in its parent's `SCHEMA.md`, and the child carries its own
root `SCHEMA.md` at the expected spec version (`--expect-schema` overrides).
Child interiors are never linted from the parent — each child enforces its
own pyramid in its own CI. A one-line summary reports fleet adoption:
seeded, version-drift, unseeded, uninitialized. Schema changes propagate
downward as a version-pinned re-vendor (bump the pinned linter/template,
open PRs in children), and the federation summary tracks the wavefront.

## Contents

Start with `SCHEMA.md` in this directory — reading it instead of this list is
the whole idea. The spec lives in `spec/`, the seed template in `templates/`,
the agent protocol in `protocol/`, the linter in `tools/`, and a fully
schematized fixture repo in `example/acme-app/`. The scenario test-suite in
`tests/` exercises the tooling against real repository shapes,
`tools/schema_bench.py` measures the context-token cost of schema-chain reads
against raw tree exploration, and `tools/schema_dist.py` guards the vendored
surface described above.

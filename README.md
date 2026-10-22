# Pyramid Schema (SCHEMA.md)

> Pyramid Schema: the SCHEMA.md protocol and linter that let AI agents look up repo structure instead of guessing it.

[![CI](https://github.com/bamr87/SCHEMA/actions/workflows/ci.yml/badge.svg)](https://github.com/bamr87/SCHEMA/actions/workflows/ci.yml) [![License](https://img.shields.io/github/license/bamr87/SCHEMA)](LICENSE)

## Overview

**Agents are stateless workers; the pyramid remembers.** A `SCHEMA.md` in every directory turns repository structure from something AI agents *infer* (via `ls -R` and guesswork) into something they *look up* — locally, cheaply, and verifiably.

## Features

- The `SCHEMA.md` protocol: a structure table and rules in every directory
- `tools/schema_lint.py` to scaffold, check and auto-fix a repo's schema pyramid
- Federation checks across submodule seams for monorepos
- A distribution contract (`DISTRIBUTION.yml`) and `tools/schema_dist.py` for vendored copies
- A `CLAUDE.md` snippet that tells agents to follow and maintain the schemas

## Quick start

Stdlib-only Python 3.10+, nothing to install. Run these from a clone of this repository; `<repo>` is the repository you are adopting the schema in.

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

Then paste `protocol/CLAUDE.snippet.md` into your repo's `CLAUDE.md`, add the `check` command to CI, and every future agent session will follow, propagate, and maintain the schemas without being told. The last line activates the version-controlled pre-commit hook for a fast local loop (CI stays the authority — hooks are bypassable, `--werror` in CI is not).

## Vendoring: the distribution contract

Adopters do not install this package, they copy files out of it. That makes those files an interface, and `DISTRIBUTION.yml` describes it: a content-addressed manifest naming each vendored file, what it hashes to, and how strictly a copy must match.

`schema_dist.py check .` proves the package is internally consistent and the manifest current, `check . --fix` regenerates the manifest after a vendored file changes, and `verify <repo>` audits every copy a consumer holds, wherever it re-homed them (commands in [Quick start](#quick-start)).

Two parity tiers, because not all drift is the same. `tools/schema_lint.py` is **strict**: a copy must be byte-identical, because a drifted linter means that repo is passing a *different gate* from everyone else while still reporting green. The template and the protocol snippet are **text**: a consumer may reflow, re-tabulate and requote them to its own house style, and the manifest carries a layout-blind hash so only a real edit registers as drift.

The manifest carries no date and no commit sha. It goes stale when the payload changes and never merely because time passed, which is what lets CI byte-compare a regenerated manifest against the committed one.

## Staying current

The package maintains itself on a schedule rather than only when someone touches it — `.github/workflows/maintenance.yml` runs the full gate weekly against an unchanged tree (pyramid lint at `--werror`, the distribution and self-consistency checks, all three test suites) and opens a single tracking issue when it goes red. Dependabot keeps the workflows' action majors current; `@claude` mentions on issues and PRs are handled in-repo.

## Monorepos & submodules (federation)

Pyramids stack by federation, not by one giant walk. Inside a repo the schema chain is continuous; at a git repo boundary (submodule, nested clone) the walk stops — that subtree is a separate pyramid that validates in its own repo, on its own commit clock.

`check <repo> --federation` reads `.gitmodules` and verifies each seam: the mount is a `terminal` row in its parent's `SCHEMA.md`, and the child carries its own root `SCHEMA.md` at the expected spec version (`--expect-schema` overrides). Child interiors are never linted from the parent — each child enforces its own pyramid in its own CI. A one-line summary reports fleet adoption: seeded, version-drift, unseeded, uninitialized. Schema changes propagate downward as a version-pinned re-vendor (bump the pinned linter/template, open PRs in children), and the federation summary tracks the wavefront.

## Documentation

Every document — the PRD, the essays and reports in `docs/`, and the root docs of record — is listed in [the docs index](docs/README.md). The specification is in `spec/`.

## Project structure

Start with `SCHEMA.md` in this directory — reading it instead of this list is the whole idea. The spec lives in `spec/`, the seed template in `templates/`, the agent protocol in `protocol/`, the linter in `tools/`, and a fully schematized fixture repo in `example/acme-app/`. The scenario test-suite in `tests/` exercises the tooling against real repository shapes, `tools/schema_bench.py` measures the context-token cost of schema-chain reads against raw tree exploration, and `tools/schema_dist.py` guards the vendored surface described above.

## Development

The gate CI runs on every change is `schema_lint.py check . --werror`, `schema_dist.py check .` and the three scenario test suites, all in the [Quick start](#quick-start) block. Full commands, conventions and repo rules for humans and AI agents live in [AGENTS.md](AGENTS.md).

## Contributing

Contributions are welcome via pull request. Use [Conventional Commits](https://www.conventionalcommits.org/) and keep the CI checks green. The fleet-wide workflow is described in the hub's [CONTRIBUTING.md](https://github.com/bamr87/bamr87/blob/main/CONTRIBUTING.md). AI agents should start with [AGENTS.md](AGENTS.md).

## Changelog

Notable changes are recorded in [CHANGELOG.md](CHANGELOG.md); the full record is in the [commit history](https://github.com/bamr87/SCHEMA/commits/main).

## License

Released under the [MIT License](LICENSE).

---

<!-- bamr87-portfolio-footer -->
Part of the [bamr87 portfolio](https://github.com/bamr87) — browse every project on [Amr's GitHub profile](https://github.com/bamr87).

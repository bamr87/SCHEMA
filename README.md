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

# Validate this package (it describes itself)
python tools/schema_lint.py check .
```

Then paste `protocol/CLAUDE.snippet.md` into your repo's `CLAUDE.md`, add the
`check` command to CI, and every future agent session will follow, propagate,
and maintain the schemas without being told.

## Contents

Start with `SCHEMA.md` in this directory — reading it instead of this list is
the whole idea. The spec lives in `spec/`, the seed template in `templates/`,
the agent protocol in `protocol/`, the linter in `tools/`, and a fully
schematized fixture repo in `example/acme-app/`. The scenario test-suite in
`tests/` exercises the linter against real repository shapes, and
`tools/schema_bench.py` measures the context-token cost of schema-chain reads
against raw tree exploration.

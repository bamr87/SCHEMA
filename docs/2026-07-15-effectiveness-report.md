# Pyramid Schema — Effectiveness & Token-Reduction Report

**Date:** 2026-07-15 · **Scope:** v0.1 package as of this report's commit

This report answers two questions with measurements, not claims: does the
paradigm hold up against real repository scenarios, and what does it actually
do to agent context spend?

## 1. What was validated

The package was initialized into its own format (the pyramid describes the
pyramid), then driven through a build loop until scenario coverage was real:

- **50 scenario tests** (`tests/`), all green, across six families: clean
  real-world shapes (Jekyll blog, Python src-layout, node monorepo,
  generated/terminal/hidden handling), spec violations, malformed schemas,
  `init` adoption flows, filesystem robustness (symlink cycles, unicode, CLI
  misuse), and the benchmark's own cost model.
- **Three real-repo adoption runs**: `init` scaffolded copies of `ai-seed`
  (22 dirs), `it-journey` (161 dirs), and `lifehacker.dev` (1,187 dirs,
  depth 14); every one linted green in a single pass, fulfilling the
  "init → check passes immediately" adoption promise at three size classes.
- **Self-validation**: `schema_lint.py check . --werror --include-hidden` is
  green on this repo, and CI (`.github/workflows/ci.yml`) enforces it on
  every push.

## 2. Bugs the scenarios exposed (all fixed)

Writing the scenarios found three real defects in the linter — the paradigm's
enforcement layer — before any adopter hit them:

1. **Kind-mismatch detection was dead code.** Literal rows matched by name
   regardless of kind, so "registered as file but is a dir" could never
   fire; a directory registered as a file was silently *descended into*,
   producing a misleading "missing SCHEMA.md" error instead.
2. **Symlinked directories were traversed as subtrees.** A registered
   symlink cycle avoided infinite recursion only because the OS ELOOP limit
   made `is_dir()` return False ~32 links deep — the test "passed" by
   accident until the fix made symlinks entries, never subtrees.
3. **`init` scaffolded inside `terminal`/`generated` directories,**
   polluting `dist/` and `vendor/` trees on adoption.

The lesson generalizes: conventions became checkable artifacts, and the
checker itself needed scenarios to be trustworthy.

## 3. Token reduction

`tools/schema_bench.py` compares, over the same tree with identical
exclusions, the two ways an agent can orient before placing or finding a
file: a find-style recursive listing (**O(tree)**, no semantics) versus the
SCHEMA.md chain from root to target (**O(depth)**, purposes and rules
included). Tokens ≈ chars/4 on both sides.

| repo | dirs / files | tree dump | mean chain | median | p90 | mean reduction | dump buys |
|---|---|---|---|---|---|---|---|
| SCHEMA (self) | 14 / 19 | 204 | 711 | 556 | 1,034 | **−248%** | 0.3 reads |
| acme-app fixture | 6 / 9 | 56 | 419 | 407 | 486 | **−648%** | 0.1 reads |
| ai-seed | 22 / 73 | 636 | 360 | 341 | 557 | **+43.4%** | 1.8 reads |
| it-journey | 161 / 1,157 | 14,100 | 1,036 | 886 | 1,689 | **+92.7%** | 13.6 reads |
| lifehacker.dev | 1,187 / 6,204 | 137,089 | 2,286 | 2,222 | 2,949 | **+98.3%** | 60.0 reads |

*(tokens per orientation; "dump buys N reads" = tree-dump tokens ÷ mean chain)*

### Reading the numbers honestly

- **The crossover is real: below ~25 directories the paradigm costs tokens.**
  On this repo a placement chain averages 711 tokens against a 204-token
  dump. Small repos should adopt for placement determinism and drift CI, not
  for context savings — or keep schemas terse.
- **At working scale the reduction dominates.** A mid-size site (161 dirs)
  drops from 14.1k to ~1k tokens per placement task; at 1,187 dirs the dump
  costs 137k tokens — beyond what an agent can sensibly spend on
  orientation at all, so in practice the baseline degrades into repeated
  piecemeal `ls`/`glob` rounds and the measured 98.3% understates the win.
- **Statelessness multiplies the saving.** The dump is re-paid every fresh
  session; chains are pay-per-task. An it-journey session doing three
  placements: 14,100 tokens baseline vs 3,108 via chains (−78%).
- **These are lower bounds.** The benchmark's baseline models a *competent*
  agent that already skips `.git`, `node_modules`, and build output; the
  real-repo schemas are raw `init` scaffolds that enumerate every file —
  adoption step 2 (pattern rows like `YYYY-MM-DD-*.md`) shrinks the fattest
  chains (max observed: 4,648 tokens) substantially.
- **Semantics aren't in the token count.** The dump tells an agent what
  exists; the chain also says *why* and *what goes where next*. The 45 lint
  scenarios price that difference in correctness: strays, misplacements, and
  drift fail CI instead of accumulating.

## 4. Recommendations

1. Adopt on repos ≥ ~25 directories for token wins; adopt smaller repos only
   for placement discipline.
2. After `init`, invest the one session that replaces TODO purposes and
   converts file enumerations to pattern rows — it is also where the chain
   sizes shrink.
3. Wire `check --werror` into CI on day one; the linter is what keeps the
   schemas from rotting like READMEs.
4. Next (roadmap): pattern inference in `init`, directory patterns for
   monorepos, `check --fix`.

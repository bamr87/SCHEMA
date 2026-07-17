---
schema: "0.1"
coverage: strict
---

# SCHEMA — .githooks

> Version-controlled git hooks; activate per clone with
> `git config core.hooksPath .githooks`.

## Conventions

- POSIX sh, executable, exact git hook filenames; non-zero exit blocks the
  action.
- Hooks are a fast local convenience, never the authority — CI enforces the
  same checks with `--werror`. Anything slower than ~a second belongs in CI.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `pre-commit` | file | Runs `schema_lint.py check .` so schema edits ride with the change they describe | required |

## Placement

- New hook → `<git-hook-name>` (the exact name git invokes), registered here.

## Forbidden

- No hooks that mutate the working tree or reach the network.

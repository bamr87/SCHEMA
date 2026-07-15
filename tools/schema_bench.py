#!/usr/bin/env python3
"""schema_bench — measure agent context cost: schema chains vs tree dumps.

For a schematized repository, compares two ways an agent can orient itself
before placing or finding a file:

  baseline   read a full recursive listing of the tree (find-style, one
             relative path per line) — O(tree) tokens, zero semantics.
  pyramid    read the SCHEMA.md chain from the root to the target directory
             — O(depth) tokens, with purposes, routing, and rules included.

Both sides walk the same tree under the same conservative rules: hidden
entries and ALWAYS_IGNORED names (.git, node_modules, …) are excluded, and
directories a schema marks terminal/generated are not entered — i.e. the
baseline models a *competent* agent that already skips junk, so reported
reductions are lower bounds.

Token counts use the standard ~4 characters/token heuristic; the comparison
is between texts measured identically, so the ratio is robust to the
estimator.

Usage:
    python3 schema_bench.py <repo> [<repo>...] [--json]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from schema_lint import ALWAYS_IGNORED, Report, parse_schema  # noqa: E402


def tokens(text: str) -> int:
    """~4 chars per token; consistent across both sides of the comparison."""
    return max(1, round(len(text) / 4))


def _visible(name: str) -> bool:
    return name not in ALWAYS_IGNORED and not name.startswith(".")


def survey(root: Path) -> dict:
    """Walk the schematized tree once, collecting both cost models."""
    listing_lines: list[str] = []          # baseline find-style dump
    chains: dict[str, int] = {}            # rel dir -> chain tokens
    schema_total = 0
    n_files = 0
    n_dirs = 0

    def walk(dirpath: Path, chain_tokens: int) -> None:
        nonlocal schema_total, n_files, n_dirs
        n_dirs += 1
        rel = dirpath.relative_to(root).as_posix()
        rel = "." if rel == "." else rel

        schema_path = dirpath / "SCHEMA.md"
        doc = None
        own = 0
        if schema_path.exists():
            own = tokens(schema_path.read_text(encoding="utf-8"))
            doc = parse_schema(schema_path, Report())
            chains[rel] = chain_tokens + own
            schema_total += own

        terminal = {r.entry for r in doc.rows if r.terminal} if doc else set()

        for child in sorted(dirpath.iterdir(), key=lambda p: p.name):
            name = child.name
            if not _visible(name) or name == "SCHEMA.md":
                continue
            crel = f"{rel}/{name}".removeprefix("./")
            if child.is_dir():
                listing_lines.append(f"{crel}/")
                if name not in terminal and not child.is_symlink():
                    walk(child, chain_tokens + own)
                # terminal dirs: listed, never entered — on either side
            else:
                listing_lines.append(crel)
                n_files += 1

    walk(root, 0)
    listing = "\n".join(listing_lines) + "\n"
    depths = [len(Path(r).parts) if r != "." else 0 for r in chains]
    chain_vals = sorted(chains.values())

    def pct(p: float) -> int:
        if not chain_vals:
            return 0
        i = min(len(chain_vals) - 1, round(p * (len(chain_vals) - 1)))
        return chain_vals[i]

    tree_tokens = tokens(listing)
    mean_chain = statistics.mean(chain_vals) if chain_vals else 0
    return {
        "repo": str(root),
        "dirs": n_dirs,
        "files": n_files,
        "schematized_dirs": len(chains),
        "max_depth": max(depths) if depths else 0,
        "tree_tokens": tree_tokens,
        "pyramid_total_tokens": schema_total,
        "chain_mean": round(mean_chain),
        "chain_median": pct(0.5),
        "chain_p90": pct(0.9),
        "chain_max": chain_vals[-1] if chain_vals else 0,
        "reduction_mean_pct":
            round(100 * (1 - mean_chain / tree_tokens), 1)
            if tree_tokens else 0.0,
        "break_even_reads":
            round(tree_tokens / mean_chain, 1) if mean_chain else 0.0,
    }


def render(r: dict) -> str:
    return (
        f"{r['repo']}\n"
        f"  tree: {r['dirs']} dirs / {r['files']} files, "
        f"max depth {r['max_depth']}, "
        f"{r['schematized_dirs']} schematized dirs\n"
        f"  baseline tree dump:      {r['tree_tokens']:>8,} tokens "
        f"(find-style listing, no semantics)\n"
        f"  full pyramid, all files: {r['pyramid_total_tokens']:>8,} tokens "
        f"(total structural knowledge incl. purposes)\n"
        f"  placement chain read:    mean {r['chain_mean']:,} / "
        f"median {r['chain_median']:,} / p90 {r['chain_p90']:,} / "
        f"max {r['chain_max']:,} tokens\n"
        f"  mean reduction per placement task vs tree dump: "
        f"{r['reduction_mean_pct']}%\n"
        f"  one tree dump buys {r['break_even_reads']} chain reads\n"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="schema_bench", description=__doc__.splitlines()[0])
    parser.add_argument("repos", nargs="+")
    parser.add_argument("--json", action="store_true",
                        help="emit one JSON object per repo")
    args = parser.parse_args(argv)

    results = []
    for repo in args.repos:
        root = Path(repo).resolve()
        if not (root / "SCHEMA.md").exists():
            print(f"error: {root} has no root SCHEMA.md "
                  f"(run schema_lint.py init first)", file=sys.stderr)
            return 2
        results.append(survey(root))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n".join(render(r) for r in results))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Distribution integrity for pyramid-schema: what downstream vendors, and whether the package still agrees with itself.

`schema_lint.py` checks that a repository matches its SCHEMA.md files. This
tool checks the two things the linter cannot see:

  1. **The vendored surface.** Adopters do not install this package; they copy
     files out of it — the linter, the seed template, the agent protocol
     snippet. Those copies are the real interface, and until now nothing
     described it. `DISTRIBUTION.yml` is that description: a content-addressed
     manifest of exactly which files are vendored and what each one hashes to,
     so any consumer (the bamr87 hub, a fan-out kit, a human) can answer "is my
     copy current?" with one fetch and no clone.

  2. **Self-consistency.** The package is the paradigm. When the linter's
     SPEC_VERSION, the newest `spec/` document, the seed template's frontmatter
     and every SCHEMA.md in the tree disagree about which spec version is
     current, the package ships a contradiction. Same for a protocol snippet
     that points at a file that has been renamed away — a bug this repo has
     already shipped once and fixed by hand (04b0980).

Parity tiers, per payload file:

  strict  the copy must be byte-identical. The linter is strict because a
          drifted linter means the adopter is passing a DIFFERENT gate from
          everyone else while looking green — the failure mode the hub's own
          drift check (i) was written for after finding three divergent forks.
  text    the copy may be reflowed, re-tabulated and requoted (adopters wrap
          prose and style markdown to their own house rules) but must not
          change in substance. Compared on a layout-blind hash: all whitespace
          removed, ASCII apostrophes mapped to double quotes.

The manifest deliberately carries NO timestamp and NO commit sha. It is
content-addressed, so `check` can byte-compare a regenerated manifest against
the committed one: it goes stale only when the payload actually changes, never
merely because a day passed.

Usage:
    python3 tools/schema_dist.py check [path]        manifest current + package self-consistent
    python3 tools/schema_dist.py check [path] --fix  rewrite DISTRIBUTION.yml, then re-check
    python3 tools/schema_dist.py verify <dir>        audit a consumer's vendored copies
    python3 tools/schema_dist.py show [path]         print the manifest to stdout

Stdlib only, Python 3.10+ — same contract as the linter it ships beside.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
from pathlib import Path

MANIFEST_NAME = "DISTRIBUTION.yml"
MANIFEST_SCHEMA = "distribution/v1"
PACKAGE = "pyramid-schema"

# The vendored surface: (repo-relative path, parity tier, why it is vendored).
# Adding a file here and running `check --fix` is the whole ceremony for
# widening the interface — the manifest, CI and every downstream check follow.
PAYLOAD: tuple[tuple[str, str, str], ...] = (
    ("tools/schema_lint.py", "strict",
     "the validator adopters run in CI; a drifted copy is a different gate"),
    ("templates/SCHEMA.template.md", "text",
     "the seed template every new directory's SCHEMA.md is filled in from"),
    ("protocol/CLAUDE.snippet.md", "text",
     "the protocol block pasted into an adopter's CLAUDE.md"),
)

TIERS = {"strict", "text"}

# Documents whose backticked paths are load-bearing instructions to an agent.
# docs/ is deliberately excluded: essays cite hypothetical trees, and a
# rhetorical path is not a broken reference.
PROSE = ("README.md", "CLAUDE.md", "protocol/CLAUDE.snippet.md")


# ---------------------------------------------------------------- hashing

def normalize_text(text: str) -> str:
    """Substance of a document, independent of layout and quote style.

    Whitespace is REMOVED rather than collapsed, because the layout differences
    a downstream copy legitimately picks up are not all run-length changes:
    reflowing prose collapses runs, but restyling a markdown table (`|---|` ->
    `| --- |`) INSERTS whitespace that was never there. Removing it entirely
    reduces both to the same character sequence, so only a real edit — different
    words, a changed instruction — moves the hash.
    """
    return re.sub(r"\s+", "", text.replace("'", '"'))


def digests(path: Path) -> tuple[str, str, int]:
    """(raw sha256, normalized-text sha256, byte size) for one file."""
    raw = path.read_bytes()
    text = raw.decode("utf-8", errors="replace")
    return (
        hashlib.sha256(raw).hexdigest(),
        hashlib.sha256(normalize_text(text).encode("utf-8")).hexdigest(),
        len(raw),
    )


# ---------------------------------------------------------------- manifest

def spec_version(root: Path) -> str | None:
    """SPEC_VERSION as declared by the linter — the package's own answer."""
    src = root / "tools" / "schema_lint.py"
    if not src.is_file():
        return None
    m = re.search(r'^SPEC_VERSION\s*=\s*["\']([^"\']+)["\']',
                  src.read_text(encoding="utf-8"), re.M)
    return m.group(1) if m else None


def render_manifest(root: Path) -> str:
    """The manifest this tree implies. Deterministic: sorted, undated."""
    ver = spec_version(root) or "unknown"
    out = [
        f"# {MANIFEST_NAME} — generated by tools/schema_dist.py; do not hand-edit.",
        "#",
        "# The vendored surface of this package: the files downstream repositories",
        "# copy in verbatim, and what each one must hash to. Regenerate with",
        "# `python3 tools/schema_dist.py check . --fix`; CI fails when this file and",
        "# the tree disagree, so the interface cannot drift silently.",
        "#",
        "# parity: strict  the consumer's copy must be byte-identical (sha256)",
        "#         text    the copy may be reflowed/requoted but not changed in",
        "#                 substance (sha256_text)",
        "# sha256_text = sha256 of the text with ALL whitespace removed and ASCII",
        "#               apostrophes mapped to double quotes — layout-blind, so",
        "#               only a real edit moves it. Content-addressed only: this",
        "#               file carries no date and no commit, so it goes stale when",
        "#               the payload changes, never merely because time passed.",
        f"schema: {MANIFEST_SCHEMA}",
        f"package: {PACKAGE}",
        f'spec: "{ver}"',
        "payload:",
    ]
    for rel, tier, why in sorted(PAYLOAD):
        path = root / rel
        if not path.is_file():
            out += [f"  - path: {rel}", f"    parity: {tier}",
                    "    missing: true", f"    purpose: {why}"]
            continue
        raw, text, size = digests(path)
        out += [
            f"  - path: {rel}",
            f"    parity: {tier}",
            f"    bytes: {size}",
            f"    sha256: {raw}",
            f"    sha256_text: {text}",
            f"    purpose: {why}",
        ]
    return "\n".join(out) + "\n"


# ---------------------------------------------------------------- audits

def _frontmatter_schema(path: Path) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:]:
        if line.strip() == "---":
            break
        m = re.match(r'\s*schema\s*:\s*["\']?([^"\'\s#]+)', line)
        if m:
            return m.group(1)
    return None


_SKIP = set("*{}<>|?")


def _cited_paths(text: str, tops: set[str]) -> set[str]:
    """Repo-relative paths cited anywhere in a document.

    Every whitespace-separated token is a candidate, so a path inside a fenced
    command line (`python3 tools/schema_lint.py init <repo>`) counts the same as
    one in inline backticks — the fenced Commands block is exactly the part an
    agent acts on. The filter that makes this safe rather than noisy is the
    first segment: it must be a real top-level entry of THIS repo, which is what
    keeps `src/components/Button.tsx` (an illustrative tree), `/path/to/repo`
    (a placeholder) and prose like "read/write" out of the results.
    """
    found: set[str] = set()
    for raw in text.split():
        cand = raw
        for _ in range(3):  # `example/acme-app/`. -> example/acme-app
            cand = cand.strip("`\"'()[],;:.!?").rstrip("/")
        if not cand or cand.startswith(("/", "./", "http")) or "/" not in cand:
            continue
        if _SKIP & set(cand):
            continue
        if cand.split("/", 1)[0] in tops:
            found.add(cand)
    return found


def audit(root: Path) -> tuple[list[str], list[str]]:
    """Self-consistency of the package. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. the vendored surface exists and is non-empty
    for rel, tier, _why in PAYLOAD:
        if tier not in TIERS:
            errors.append(f"{rel}: unknown parity tier '{tier}'")
        path = root / rel
        if not path.is_file():
            errors.append(f"payload file missing: {rel}")
        elif path.stat().st_size == 0:
            errors.append(f"payload file is empty: {rel}")

    # 2. one spec version, agreed everywhere
    ver = spec_version(root)
    if ver is None:
        errors.append("tools/schema_lint.py declares no SPEC_VERSION")
    else:
        docs = sorted(
            m.group(1)
            for m in (re.match(r"pyramid-schema-spec-v(.+)\.md$", p.name)
                      for p in (root / "spec").glob("pyramid-schema-spec-v*.md"))
            if m
        )
        if not docs:
            errors.append("spec/ carries no pyramid-schema-spec-v*.md document")
        elif ver not in docs:
            errors.append(
                f"spec drift: linter SPEC_VERSION is {ver!r} but spec/ ships "
                f"{', '.join(docs)} — release the spec doc or correct the linter")

        tmpl = root / "templates" / "SCHEMA.template.md"
        if tmpl.is_file():
            got = _frontmatter_schema(tmpl)
            if got != ver:
                errors.append(
                    f"spec drift: templates/SCHEMA.template.md declares "
                    f"schema: {got!r}, linter says {ver!r} — every seeded "
                    "directory would be born on the wrong version")

        for schema in sorted(root.rglob("SCHEMA.md")):
            if ".git/" in str(schema):
                continue
            got = _frontmatter_schema(schema)
            rel = schema.relative_to(root)
            if got is None:
                errors.append(f"{rel}: no schema: version in frontmatter")
            elif got != ver:
                errors.append(f"{rel}: declares schema: {got!r}, package ships {ver!r}")

    # 3. paths an agent is told to read must exist
    tops = {p.name for p in root.iterdir() if p.name != ".git"}
    for rel in PROSE:
        doc = root / rel
        if not doc.is_file():
            warnings.append(f"{rel}: cited in PROSE but not present")
            continue
        for cand in sorted(_cited_paths(doc.read_text(encoding="utf-8"), tops)):
            if not (root / cand).exists():
                errors.append(f"{rel}: cites `{cand}`, which does not exist")

    return errors, warnings


# ---------------------------------------------------------------- commands

def cmd_check(root: Path, fix: bool) -> int:
    errors, warnings = audit(root)
    manifest = root / MANIFEST_NAME
    want = render_manifest(root)
    have = manifest.read_text(encoding="utf-8") if manifest.is_file() else None

    if have != want:
        if fix:
            manifest.write_text(want, encoding="utf-8")
            print(f"wrote {MANIFEST_NAME} ({len(PAYLOAD)} payload file(s))")
        elif have is None:
            errors.append(f"{MANIFEST_NAME} is missing — run "
                          f"`schema_dist.py check . --fix`")
        else:
            errors.append(f"{MANIFEST_NAME} is stale (the payload changed without "
                          f"it) — run `schema_dist.py check . --fix`")

    for msg in errors:
        print(f"ERROR    {msg}")
    for msg in warnings:
        print(f"warning  {msg}")
    verdict = "FAIL" if errors else "PASS"
    print(f"\n{verdict}: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


def cmd_verify(root: Path, consumer: Path) -> int:
    """Audit every copy of the payload found under `consumer`.

    Located by basename, not by path: consumers re-home what they vendor
    (the bamr87 hub keeps the snippet at templates/schema/CLAUDE.snippet.md),
    and a copy that moved is still a copy that can drift.
    """
    if not consumer.is_dir():
        print(f"error: not a directory: {consumer}", file=sys.stderr)
        return 2

    drift = 0
    for rel, tier, _why in sorted(PAYLOAD):
        src = root / rel
        if not src.is_file():
            print(f"ERROR    payload file missing upstream: {rel}")
            drift += 1
            continue
        raw, text, _size = digests(src)
        copies = [p for p in consumer.rglob(Path(rel).name)
                  if p.is_file() and ".git/" not in str(p)]
        if not copies:
            print(f"absent   {rel}: no copy under {consumer}")
            continue
        for copy in sorted(copies):
            c_raw, c_text, _ = digests(copy)
            shown = copy.relative_to(consumer)
            if c_raw == raw:
                print(f"ok       {shown}: identical")
            elif tier == "text" and c_text == text:
                print(f"ok       {shown}: adapted (layout/quotes only), substance matches")
            elif tier == "text":
                print(f"DRIFT    {shown}: content differs from {rel} (parity: text)")
                drift += 1
            else:
                print(f"DRIFT    {shown}: not byte-identical to {rel} (parity: strict)")
                drift += 1

    verdict = "FAIL" if drift else "PASS"
    print(f"\n{verdict}: {drift} drifted copy/copies")
    return 1 if drift else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="schema_dist", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    p_check = sub.add_parser("check", help="manifest current + package self-consistent")
    p_check.add_argument("path", nargs="?", default=".")
    p_check.add_argument("--fix", action="store_true",
                         help=f"rewrite {MANIFEST_NAME} from the tree")

    p_verify = sub.add_parser("verify", help="audit a consumer's vendored copies")
    p_verify.add_argument("consumer")
    p_verify.add_argument("--root", default=".", help="this package (default: .)")

    p_show = sub.add_parser("show", help=f"print {MANIFEST_NAME} to stdout")
    p_show.add_argument("path", nargs="?", default=".")

    args = parser.parse_args(argv)

    if args.command == "verify":
        root = Path(args.root).resolve()
    else:
        root = Path(args.path).resolve()
    if not root.is_dir():
        print(f"error: not a directory: {root}", file=sys.stderr)
        return 2

    if args.command == "show":
        sys.stdout.write(render_manifest(root))
        return 0
    if args.command == "verify":
        return cmd_verify(root, Path(args.consumer).resolve())
    return cmd_check(root, args.fix)


if __name__ == "__main__":
    raise SystemExit(main())

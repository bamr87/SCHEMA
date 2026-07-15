#!/usr/bin/env python3
"""Tests for schema_bench — the cost model must measure what it claims."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import schema_bench  # noqa: E402


def make_schema(dirpath: Path, rows: str) -> None:
    dirpath.mkdir(parents=True, exist_ok=True)
    (dirpath / "SCHEMA.md").write_text(
        '---\nschema: "0.1"\ncoverage: listed\n---\n\n# SCHEMA\n\n'
        '## Structure\n\n| entry | kind | purpose | rules |\n'
        f'|---|---|---|---|\n{rows}\n', encoding="utf-8")


class TestSurvey(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()

    def test_tokens_heuristic(self):
        self.assertEqual(schema_bench.tokens("abcd" * 25), 25)
        self.assertEqual(schema_bench.tokens(""), 1)

    def test_chain_is_cumulative_and_listing_skips_schema_files(self):
        make_schema(self.root, "| `sub/` | dir | child | required |")
        make_schema(self.root / "sub", "| `leaf.txt` | file | payload | |")
        (self.root / "sub" / "leaf.txt").write_text("x")
        r = schema_bench.survey(self.root)
        self.assertEqual(r["schematized_dirs"], 2)
        root_tokens = schema_bench.tokens(
            (self.root / "SCHEMA.md").read_text())
        sub_tokens = schema_bench.tokens(
            (self.root / "sub" / "SCHEMA.md").read_text())
        self.assertEqual(r["chain_max"], root_tokens + sub_tokens)
        self.assertEqual(r["pyramid_total_tokens"],
                         root_tokens + sub_tokens)
        # baseline listing: sub/ and sub/leaf.txt only — 2 lines, no SCHEMA.md
        self.assertEqual(r["files"], 1)

    def test_terminal_dirs_are_not_entered_on_either_side(self):
        make_schema(self.root, "| `dist/` | dir | build output | generated |")
        junk = self.root / "dist" / "deep"
        junk.mkdir(parents=True)
        (junk / "bundle.js").write_text("x" * 4000)
        r = schema_bench.survey(self.root)
        self.assertEqual(r["files"], 0)          # bundle.js not listed
        self.assertEqual(r["schematized_dirs"], 1)
        self.assertLess(r["tree_tokens"], 20)    # just 'dist/'

    def test_hidden_and_ignored_are_excluded(self):
        make_schema(self.root, "| `a.txt` | file | visible | |")
        (self.root / "a.txt").write_text("x")
        (self.root / ".hidden").write_text("x")
        nm = self.root / "node_modules" / "x"
        nm.mkdir(parents=True)
        (nm / "index.js").write_text("x")
        r = schema_bench.survey(self.root)
        self.assertEqual(r["files"], 1)

    def test_cli_requires_root_schema(self):
        buf = io.StringIO()
        with contextlib.redirect_stderr(buf):
            code = schema_bench.main([str(self.root)])
        self.assertEqual(code, 2)
        self.assertIn("no root SCHEMA.md", buf.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)

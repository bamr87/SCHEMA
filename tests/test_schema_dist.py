#!/usr/bin/env python3
"""Scenario tests for tools/schema_dist.py — the distribution/consistency gate.

Every case builds a miniature package in a temp dir (a linter stub with a
SPEC_VERSION, a spec document, a template, a snippet, a root SCHEMA.md) and
then breaks exactly one thing. The shapes are the ones that have actually
gone wrong in this package's history: a spec version that moved in one place
and not the others, a protocol snippet pointing at a renamed file, a payload
edited without regenerating the manifest, and a downstream copy quietly
forked from the linter it claims to be.

Run directly:  python3 tests/test_schema_dist.py
"""
from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import schema_dist as sd  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    """Drive schema_dist.main with argv, capturing stdout+stderr."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = sd.main(list(argv))
    return code, buf.getvalue()


TEMPLATE = """---
schema: "{ver}"
coverage: listed
---

# SCHEMA — {{{{directory_name}}}}

> {{{{One sentence.}}}}
"""

ROOT_SCHEMA = """---
schema: "{ver}"
coverage: listed
---

# SCHEMA — pkg

> A miniature package.

## Structure

| entry | kind | purpose | rules |
|---|---|---|---|
| `tools/` | dir | tooling | required |
"""


def build(root: Path, ver: str = "0.1") -> None:
    """A minimal, self-consistent package that passes every audit."""
    (root / "tools").mkdir(parents=True, exist_ok=True)
    (root / "spec").mkdir(exist_ok=True)
    (root / "templates").mkdir(exist_ok=True)
    (root / "protocol").mkdir(exist_ok=True)
    (root / "tools" / "schema_lint.py").write_text(
        f'SPEC_VERSION = "{ver}"\n', encoding="utf-8")
    (root / "spec" / f"pyramid-schema-spec-v{ver}.md").write_text(
        "# spec\n", encoding="utf-8")
    (root / "templates" / "SCHEMA.template.md").write_text(
        TEMPLATE.format(ver=ver), encoding="utf-8")
    (root / "protocol" / "CLAUDE.snippet.md").write_text(
        "Run `tools/schema_lint.py check .` and copy "
        "`templates/SCHEMA.template.md`.\n", encoding="utf-8")
    (root / "SCHEMA.md").write_text(ROOT_SCHEMA.format(ver=ver), encoding="utf-8")
    (root / "README.md").write_text("See `tools/schema_lint.py`.\n", encoding="utf-8")
    (root / "CLAUDE.md").write_text("See `templates/SCHEMA.template.md`.\n",
                                    encoding="utf-8")
    (root / sd.MANIFEST_NAME).write_text(sd.render_manifest(root), encoding="utf-8")


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.root = self.dir / "pkg"
        self.root.mkdir()
        build(self.root)

    def tearDown(self) -> None:
        shutil.rmtree(self.dir, ignore_errors=True)

    def errors(self, root: Path | None = None) -> list[str]:
        return sd.audit(root or self.root)[0]

    def run_check(self, fix: bool = False, root: Path | None = None) -> int:
        argv = ["check", str(root or self.root)] + (["--fix"] if fix else [])
        return run_cli(*argv)[0]

    def run_verify(self, consumer: Path, root: Path | None = None) -> int:
        return run_cli("verify", str(consumer), "--root", str(root or self.root))[0]


class TestBaseline(Case):
    def test_clean_package_passes(self):
        self.assertEqual(self.errors(), [])
        self.assertEqual(self.run_check(), 0)

    def test_manifest_is_deterministic(self):
        self.assertEqual(sd.render_manifest(self.root),
                         sd.render_manifest(self.root))

    def test_manifest_carries_no_timestamp(self):
        # A dated manifest could not be byte-compared in CI; it would go stale
        # every day instead of every payload change.
        text = (self.root / sd.MANIFEST_NAME).read_text()
        self.assertNotIn("generated:", text)
        self.assertNotIn("2026-", text)

    def test_show_prints_the_committed_manifest(self):
        code, out = run_cli("show", str(self.root))
        self.assertEqual(code, 0)
        self.assertEqual(out, (self.root / sd.MANIFEST_NAME).read_text())

    def test_check_rejects_a_non_directory(self):
        self.assertEqual(run_cli("check", str(self.root / "README.md"))[0], 2)


class TestManifestFreshness(Case):
    def test_edited_payload_makes_manifest_stale(self):
        (self.root / "tools" / "schema_lint.py").write_text(
            'SPEC_VERSION = "0.1"\n# a new line\n', encoding="utf-8")
        self.assertEqual(self.run_check(), 1)

    def test_fix_regenerates_and_passes(self):
        (self.root / "tools" / "schema_lint.py").write_text(
            'SPEC_VERSION = "0.1"\n# a new line\n', encoding="utf-8")
        self.assertEqual(self.run_check(fix=True), 0)
        self.assertEqual(self.run_check(), 0)

    def test_missing_manifest_is_an_error(self):
        (self.root / sd.MANIFEST_NAME).unlink()
        self.assertEqual(self.run_check(), 1)

    def test_missing_manifest_is_created_by_fix(self):
        (self.root / sd.MANIFEST_NAME).unlink()
        self.assertEqual(self.run_check(fix=True), 0)
        self.assertTrue((self.root / sd.MANIFEST_NAME).is_file())


class TestPayload(Case):
    def test_missing_payload_file_is_an_error(self):
        (self.root / "protocol" / "CLAUDE.snippet.md").unlink()
        self.assertTrue(any("payload file missing" in e for e in self.errors()))

    def test_empty_payload_file_is_an_error(self):
        (self.root / "templates" / "SCHEMA.template.md").write_text("")
        self.assertTrue(any("empty" in e for e in self.errors()))

    def test_missing_payload_still_renders_a_manifest(self):
        # The manifest must describe the interface even while it is broken;
        # crashing here would take CI's error message away with it.
        (self.root / "protocol" / "CLAUDE.snippet.md").unlink()
        self.assertIn("missing: true", sd.render_manifest(self.root))


class TestSpecConsistency(Case):
    def test_linter_ahead_of_spec_documents(self):
        (self.root / "tools" / "schema_lint.py").write_text(
            'SPEC_VERSION = "0.2"\n', encoding="utf-8")
        self.assertTrue(any("spec drift" in e for e in self.errors()))

    def test_template_left_on_the_old_version(self):
        (self.root / "spec" / "pyramid-schema-spec-v0.2.md").write_text("# spec\n")
        (self.root / "tools" / "schema_lint.py").write_text(
            'SPEC_VERSION = "0.2"\n', encoding="utf-8")
        errs = self.errors()
        self.assertTrue(any("SCHEMA.template.md" in e for e in errs))

    def test_stale_schema_md_in_the_tree(self):
        (self.root / "tools" / "SCHEMA.md").write_text(
            ROOT_SCHEMA.format(ver="0.0"), encoding="utf-8")
        self.assertTrue(any("tools/SCHEMA.md" in e for e in self.errors()))

    def test_schema_md_without_a_version(self):
        (self.root / "tools" / "SCHEMA.md").write_text("# no frontmatter\n",
                                                       encoding="utf-8")
        self.assertTrue(any("no schema: version" in e for e in self.errors()))

    def test_linter_without_spec_version(self):
        (self.root / "tools" / "schema_lint.py").write_text("# nothing\n",
                                                            encoding="utf-8")
        self.assertTrue(any("no SPEC_VERSION" in e for e in self.errors()))

    def test_no_spec_document_at_all(self):
        for p in (self.root / "spec").glob("*.md"):
            p.unlink()
        self.assertTrue(any("no pyramid-schema-spec" in e for e in self.errors()))


class TestCitedPaths(Case):
    def test_snippet_citing_a_renamed_file(self):
        # The 04b0980 bug class: the protocol tells adopters to copy a file
        # that no longer exists at that path.
        (self.root / "protocol" / "CLAUDE.snippet.md").write_text(
            "Copy `templates/SCHEMA.template.md` and `templates/gone.md`.\n",
            encoding="utf-8")
        self.assertTrue(any("templates/gone.md" in e for e in self.errors()))

    def test_paths_in_fenced_commands_are_checked(self):
        (self.root / "CLAUDE.md").write_text(
            "```bash\npython3 tools/missing_tool.py check .\n```\n",
            encoding="utf-8")
        self.assertTrue(any("tools/missing_tool.py" in e for e in self.errors()))

    def test_foreign_first_segment_is_not_a_path(self):
        # `src/` is not a top-level entry of this package: an illustrative
        # tree in prose must not be mistaken for a broken reference.
        (self.root / "README.md").write_text(
            "A component lives at `src/components/Button.tsx`.\n", encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_placeholders_and_globs_are_not_paths(self):
        (self.root / "README.md").write_text(
            "Run on `/path/to/repo`, see `spec/*.md` and `tools/{{name}}.py`.\n",
            encoding="utf-8")
        self.assertEqual(self.errors(), [])

    def test_trailing_punctuation_is_stripped(self):
        (self.root / "README.md").write_text(
            "The fixture lives in `spec/`. Also `tools/schema_lint.py`.\n",
            encoding="utf-8")
        self.assertEqual(self.errors(), [])


class TestVerify(Case):
    def _consumer(self, **files: str) -> Path:
        c = self.dir / "consumer"
        (c / "vendor").mkdir(parents=True, exist_ok=True)
        for name, body in files.items():
            (c / "vendor" / name).write_text(body, encoding="utf-8")
        return c

    def test_identical_copy_passes(self):
        c = self._consumer(**{
            "schema_lint.py": (self.root / "tools" / "schema_lint.py").read_text()})
        self.assertEqual(self.run_verify(c), 0)

    def test_forked_linter_fails_strict_parity(self):
        c = self._consumer(**{"schema_lint.py": 'SPEC_VERSION = "0.1"\n# fork\n'})
        self.assertEqual(self.run_verify(c), 1)

    def test_reflowed_text_payload_passes(self):
        original = (self.root / "protocol" / "CLAUDE.snippet.md").read_text()
        reflowed = original.replace(" and ", "\n   and\n")
        c = self._consumer(**{"CLAUDE.snippet.md": reflowed})
        self.assertEqual(self.run_verify(c), 0)

    def test_retabulated_text_payload_passes(self):
        # `|---|` -> `| --- |` INSERTS whitespace; a collapse-only normalizer
        # would call this drift, which is why the hash removes whitespace.
        tmpl = (self.root / "templates" / "SCHEMA.template.md").read_text()
        c = self._consumer(**{
            "SCHEMA.template.md": tmpl.replace("---\n", "  ---  \n", 1)})
        self.assertEqual(self.run_verify(c), 0)

    def test_reworded_text_payload_fails(self):
        snippet = (self.root / "protocol" / "CLAUDE.snippet.md").read_text()
        c = self._consumer(**{
            "CLAUDE.snippet.md": snippet.replace("Run", "Never run")})
        self.assertEqual(self.run_verify(c), 1)

    def test_absent_copy_is_reported_but_not_drift(self):
        # A consumer that vendors nothing has not forked anything.
        c = self.dir / "empty"
        c.mkdir()
        self.assertEqual(self.run_verify(c), 0)

    def test_copy_found_under_any_path(self):
        # Consumers re-home what they vendor; a moved copy is still a copy.
        c = self.dir / "deep"
        (c / "a" / "b" / "c").mkdir(parents=True)
        (c / "a" / "b" / "c" / "schema_lint.py").write_text("# fork\n")
        self.assertEqual(self.run_verify(c), 1)

    def test_non_directory_consumer_is_a_usage_error(self):
        self.assertEqual(self.run_verify(self.root / "README.md"), 2)


class TestNormalization(unittest.TestCase):
    def test_whitespace_is_removed_not_collapsed(self):
        self.assertEqual(sd.normalize_text("|---|"), sd.normalize_text("| --- |"))

    def test_quote_style_is_ignored(self):
        self.assertEqual(sd.normalize_text("schema: '0.1'"),
                         sd.normalize_text('schema: "0.1"'))

    def test_wording_change_is_not_ignored(self):
        self.assertNotEqual(sd.normalize_text("never do this"),
                            sd.normalize_text("always do this"))


class TestSelf(unittest.TestCase):
    """The real package, not a fixture: this repo must ship consistent."""

    def test_this_package_is_consistent_and_current(self):
        root = Path(__file__).resolve().parent.parent
        errors, _warnings = sd.audit(root)
        self.assertEqual(errors, [], "\n".join(errors))
        manifest = (root / sd.MANIFEST_NAME)
        self.assertTrue(manifest.is_file(), f"{sd.MANIFEST_NAME} is missing")
        self.assertEqual(manifest.read_text(encoding="utf-8"),
                         sd.render_manifest(root),
                         f"{sd.MANIFEST_NAME} is stale — run "
                         f"`python3 tools/schema_dist.py check . --fix`")


if __name__ == "__main__":
    unittest.main(verbosity=1)

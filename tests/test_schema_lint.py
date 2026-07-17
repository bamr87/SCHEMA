#!/usr/bin/env python3
"""Scenario tests for schema_lint — real repository shapes and failure modes.

Every test builds a throwaway fixture tree and drives the linter through its
public CLI (`main`) or its library surface (`check_dir`, `init_tree`). The
suite is the paradigm's proving ground: each test class is a family of
real-world scenarios the linter must survive.
"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "tools"))

import schema_lint  # noqa: E402


def run_cli(*argv: str) -> tuple[int, str]:
    """Run schema_lint.main with argv, capturing stdout+stderr."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        code = schema_lint.main(list(argv))
    return code, buf.getvalue()


class ScenarioCase(unittest.TestCase):
    """Base: a temp root plus helpers to lay files and schemas."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name).resolve()

    def write(self, rel: str, content: str = "x\n") -> Path:
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return p

    def mkdir(self, rel: str) -> Path:
        p = self.root / rel
        p.mkdir(parents=True, exist_ok=True)
        return p

    def schema(self, rel_dir: str, rows: list[tuple[str, str, str, str]],
               coverage: str = "listed", version: str = "0.1",
               frontmatter: bool = True, extra: str = "") -> Path:
        table = "\n".join(
            f"| `{entry}` | {kind} | {purpose} | {rules} |"
            for entry, kind, purpose, rules in rows)
        fm = f'---\nschema: "{version}"\ncoverage: {coverage}\n---\n\n' \
            if frontmatter else ""
        body = (f"{fm}# SCHEMA — {rel_dir or 'root'}\n\n> Fixture schema.\n\n"
                f"## Structure\n\n| entry | kind | purpose | rules |\n"
                f"|---|---|---|---|\n{table}\n{extra}")
        return self.write(f"{rel_dir}/SCHEMA.md" if rel_dir else "SCHEMA.md",
                          body)

    def check(self, *flags: str) -> tuple[int, str]:
        return run_cli("check", str(self.root), *flags)

    def assertClean(self, out_code: tuple[int, str]) -> None:
        code, out = out_code
        self.assertEqual(code, 0, out)
        self.assertIn("0 error(s), 0 warning(s)", out, out)


# ---------------------------------------------------------------- clean trees


class TestCleanPyramids(ScenarioCase):
    """Realistic repo shapes that must lint green."""

    def test_package_validates_itself(self):
        """Dogfood: this very package is a green pyramid, warnings-as-errors."""
        code, out = run_cli("check", str(REPO_ROOT), "--werror")
        self.assertEqual(code, 0, out)

    def test_deep_chain_is_green(self):
        """A five-level chain models deep src trees."""
        chain = ""
        for name in ("a", "b", "c", "d", "e"):
            parent = chain or ""
            self.schema(parent, [(f"{name}/", "dir", "next level", "required")])
            chain = f"{chain}/{name}".strip("/")
        self.schema(chain, [("leaf.txt", "file", "the payload", "required")])
        self.write(f"{chain}/leaf.txt")
        self.assertClean(self.check())

    def test_schema_may_register_its_own_contract_file(self):
        """A schema that documents SCHEMA.md in its own table is not "missing" it.

        Registering the contract file is idiomatic — most seeded SCHEMA.md files
        open their table with a row for themselves — but SCHEMA.md is in
        IMPLICIT_ALLOWED, and that branch used to `continue` before the row was
        matched. The row therefore never got marked seen and a `required` one was
        reported missing, in the one file the author was most likely to write.
        """
        self.schema("", [
            ("SCHEMA.md", "file", "this contract", "required"),
            ("payload.txt", "file", "the payload", "required"),
        ])
        self.write("payload.txt")
        self.assertClean(self.check())

    def test_empty_directory_with_empty_table(self):
        """A placeholder dir whose schema lists nothing yet."""
        self.schema("", [("inbox/", "dir", "empty for now", "")])
        self.mkdir("inbox")
        self.schema("inbox", [])
        self.assertClean(self.check())

    def test_jekyll_blog_shape(self):
        """Dated-post patterns, generated _site, singleton config."""
        self.schema("", [
            ("_posts/", "dir", "blog posts", "required"),
            ("_site/", "dir", "built site", "generated"),
            ("_config.yml", "file", "jekyll config", "required"),
            ("index.md", "file", "landing page", "required"),
        ])
        self.schema("_posts", [
            ("[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-*.md", "pattern",
             "one dated post", "required"),
        ], coverage="strict")
        self.write("_posts/2026-07-15-hello.md")
        self.write("_posts/2026-07-14-world.md")
        self.write("_site/index.html")
        self.write("_site/assets/app.js")
        self.write("_config.yml")
        self.write("index.md")
        self.assertClean(self.check())

    def test_python_package_shape(self):
        """src layout with __pycache__ junk that must be invisible."""
        self.schema("", [
            ("src/", "dir", "source", "required"),
            ("pyproject.toml", "file", "build config", "required"),
        ])
        self.schema("src", [("mypkg/", "dir", "the package", "required")])
        self.schema("src/mypkg", [("*.py", "pattern", "module", "required")])
        self.write("src/mypkg/__init__.py")
        self.write("src/mypkg/core.py")
        self.write("src/mypkg/__pycache__/core.cpython-314.pyc")
        self.write("pyproject.toml")
        self.assertClean(self.check())

    def test_monorepo_enumerated_packages(self):
        """v0.1 has no dir patterns; monorepos enumerate each package."""
        pkgs = ["app", "api", "shared"]
        self.schema("", [("packages/", "dir", "workspace", "required")])
        self.schema("packages",
                    [(f"{p}/", "dir", f"{p} package", "required")
                     for p in pkgs])
        for p in pkgs:
            self.schema(f"packages/{p}",
                        [("package.json", "file", "manifest", "required")])
            self.write(f"packages/{p}/package.json", "{}\n")
        self.assertClean(self.check())

    def test_generated_dir_contents_unchecked(self):
        """Build output can hold anything, schemaless, without complaint."""
        self.schema("", [("dist/", "dir", "bundle output", "generated")])
        self.write("dist/app.js")
        self.write("dist/chunks/vendor.js")
        self.assertClean(self.check())

    def test_terminal_dir_not_descended(self):
        """Vendored code needs no schemas inside."""
        self.schema("", [("vendor/", "dir", "vendored deps", "terminal")])
        self.write("vendor/lib/deep/code.c")
        self.assertClean(self.check())

    def test_open_coverage_shrugs_at_strays(self):
        self.schema("", [("notes/", "dir", "freeform", "required")])
        self.schema("notes", [], coverage="open")
        self.write("notes/whatever.txt")
        self.write("notes/random.bin")
        self.assertClean(self.check())

    def test_registered_always_ignored_dir_is_not_stale(self):
        """A Node repo documents node_modules; the linter must not call it
        stale (it exists) nor descend into it."""
        self.schema("", [
            ("node_modules/", "dir", "installed deps", "generated"),
            ("package.json", "file", "manifest", "required"),
        ])
        self.write("node_modules/left-pad/index.js")
        self.write("package.json", "{}\n")
        self.assertClean(self.check())

    def test_unregistered_always_ignored_dir_is_silent(self):
        self.schema("", [("package.json", "file", "manifest", "required")],
                    coverage="strict")
        self.write("node_modules/x/index.js")
        self.write("package.json", "{}\n")
        self.assertClean(self.check())

    def test_registered_hidden_file_is_checked(self):
        self.schema("", [(".env.example", "file", "env template", "required")])
        self.write(".env.example")
        self.assertClean(self.check())

    def test_registered_hidden_terminal_dir(self):
        """Registering .github/ as terminal documents it without forcing
        schemas inside workflow dirs."""
        self.schema("", [(".github/", "dir", "CI config", "terminal")])
        self.write(".github/workflows/ci.yml")
        self.assertClean(self.check("--include-hidden"))


# ---------------------------------------------------------------- violations


class TestViolations(ScenarioCase):
    """Broken trees that must produce the spec's errors and warnings."""

    def test_missing_schema_in_traversed_dir(self):
        self.schema("", [("src/", "dir", "source", "required")])
        self.write("src/app.py")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("missing SCHEMA.md", out)

    def test_missing_required_file(self):
        self.schema("", [("Makefile", "file", "build entry", "required")])
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("missing required file 'Makefile'", out)

    def test_missing_required_pattern_match(self):
        self.schema("", [("adr/", "dir", "decisions", "required")])
        self.schema("adr", [("[0-9]*.md", "pattern", "an ADR", "required")],
                    coverage="strict")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("at least one match for pattern", out)

    def test_stray_in_strict_dir_is_error(self):
        self.schema("", [("components/", "dir", "UI", "required")])
        self.schema("components", [("*.tsx", "pattern", "component", "")],
                    coverage="strict")
        self.write("components/Button.tsx")
        self.write("components/helpers.ts")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("unregistered entry 'helpers.ts'", out)

    def test_stray_in_listed_dir_is_warning_only(self):
        self.schema("", [("docs/", "dir", "docs", "")])
        self.schema("docs", [("index.md", "file", "landing", "required")])
        self.write("docs/index.md")
        self.write("docs/scratch.md")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("unregistered entry 'scratch.md'", out)
        code_w, _ = self.check("--werror")
        self.assertEqual(code_w, 1)

    def test_registered_file_exists_as_dir(self):
        self.schema("", [("config", "file", "single config file", "")])
        self.mkdir("config")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("registered as file but is a dir", out)

    def test_registered_dir_exists_as_file(self):
        self.schema("", [("src/", "dir", "source", "required")])
        self.write("src")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("registered as dir but is a file", out)

    def test_kind_mismatch_reports_once_no_cascade(self):
        """A mismatch is one error — not also 'missing required'."""
        self.schema("", [("src/", "dir", "source", "required")])
        self.write("src")
        _, out = self.check()
        self.assertIn("registered as dir but is a file", out)
        self.assertNotIn("missing required", out)
        self.assertIn("1 error(s)", out)

    def test_stale_registered_entry_warns(self):
        self.schema("", [("old-notes.md", "file", "gone", "")])
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("stale entry 'old-notes.md'", out)

    def test_absent_generated_entry_is_silent(self):
        """dist/ before the first build is not a problem."""
        self.schema("", [("dist/", "dir", "build output", "generated")])
        self.assertClean(self.check())

    def test_dir_matching_file_pattern_is_still_unregistered(self):
        """Patterns match files only in v0.1; a dir sneaking under one is a
        stray."""
        self.schema("", [("*.md", "pattern", "doc", "")], coverage="strict")
        self.mkdir("notes.md")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("unregistered entry 'notes.md'", out)

    def test_schema_md_itself_is_implicitly_allowed(self):
        self.schema("", [], coverage="strict")
        code, out = self.check()
        self.assertEqual(code, 0, out)


# ---------------------------------------------------------------- parsing


class TestSchemaParsing(ScenarioCase):
    """Malformed and edge-case SCHEMA.md files."""

    def test_no_structure_table_is_error(self):
        self.write("SCHEMA.md", "# SCHEMA\n\nJust prose.\n")
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("no '## Structure' table", out)

    def test_missing_frontmatter_warns_and_defaults_to_listed(self):
        self.schema("", [("stray.txt", "file", "known", "")],
                    frontmatter=False)
        self.write("stray.txt")
        self.write("unknown.txt")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("missing or unterminated frontmatter", out)
        self.assertIn("unregistered entry 'unknown.txt'", out)

    def test_unknown_coverage_warns_and_defaults(self):
        self.schema("", [], coverage="paranoid")
        self.write("mystery.txt")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("unknown coverage 'paranoid'", out)
        self.assertIn("unregistered entry 'mystery.txt'", out)

    def test_unknown_rule_token_warns_but_x_prefixed_does_not(self):
        self.schema("", [
            ("a.txt", "file", "has bogus token", "immutable"),
            ("b.txt", "file", "has experimental token", "x-locked"),
        ])
        self.write("a.txt")
        self.write("b.txt")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("unknown rule 'immutable'", out)
        self.assertNotIn("x-locked", out)

    def test_malformed_row_is_skipped_with_warning(self):
        self.schema("", [], extra="| just-two | cells |\n")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("malformed Structure row", out)

    def test_unknown_kind_is_error(self):
        self.schema("", [("thing", "blob", "what even", "")])
        code, out = self.check()
        self.assertEqual(code, 1)
        self.assertIn("unknown kind 'blob'", out)

    def test_spec_version_mismatch_warns(self):
        self.schema("", [], version="9.9")
        code, out = self.check()
        self.assertEqual(code, 0)
        self.assertIn("declares spec '9.9'", out)

    def test_crlf_schema_parses(self):
        body = ('---\r\nschema: "0.1"\r\ncoverage: listed\r\n---\r\n\r\n'
                '# SCHEMA — root\r\n\r\n## Structure\r\n\r\n'
                '| entry | kind | purpose | rules |\r\n|---|---|---|---|\r\n'
                '| `a.txt` | file | crlf survivor | required |\r\n')
        self.write("SCHEMA.md", body)
        self.write("a.txt")
        self.assertClean(self.check())


# ---------------------------------------------------------------- init


class TestInitScenarios(ScenarioCase):
    """Adopting existing repos: the chaos gets its first course of stone."""

    def test_legacy_repo_scaffolds_to_green(self):
        """The adoption promise: init then check passes immediately."""
        self.write("src/app.py")
        self.write("src/util/helpers.py")
        self.write("docs/guide.md")
        self.write("README.md")
        self.write("node_modules/x/index.js")
        self.write(".git/config")
        code, out = run_cli("init", str(self.root))
        self.assertEqual(code, 0)
        for rel in ("SCHEMA.md", "src/SCHEMA.md", "src/util/SCHEMA.md",
                    "docs/SCHEMA.md"):
            self.assertTrue((self.root / rel).exists(), rel)
        self.assertFalse((self.root / "node_modules/SCHEMA.md").exists())
        self.assertFalse((self.root / ".git/SCHEMA.md").exists())
        self.assertClean(self.check())

    def test_init_never_overwrites(self):
        original = self.schema("", [("kept.txt", "file", "precious", "")])
        before = original.read_text(encoding="utf-8")
        self.write("kept.txt")
        self.write("sub/file.txt")
        run_cli("init", str(self.root))
        self.assertEqual(original.read_text(encoding="utf-8"), before)
        self.assertTrue((self.root / "sub/SCHEMA.md").exists())

    def test_init_fills_only_gaps(self):
        self.schema("", [("a/", "dir", "has schema", ""),
                         ("b/", "dir", "lacks schema", "")])
        self.schema("a", [])
        self.mkdir("b")
        created = schema_lint.init_tree(self.root)
        self.assertEqual([p.relative_to(self.root).as_posix()
                          for p in created], ["b/SCHEMA.md"])

    def test_init_respects_terminal_and_generated_dirs(self):
        """init must not carve schemas into build output or vendored trees
        that an existing schema already marks terminal."""
        self.schema("", [
            ("dist/", "dir", "build output", "generated"),
            ("vendor/", "dir", "vendored", "terminal"),
            ("src/", "dir", "source", "required"),
        ])
        self.write("dist/bundle.js")
        self.write("dist/chunks/vendor.js")
        self.write("vendor/lib/code.c")
        self.write("src/app.py")
        run_cli("init", str(self.root))
        self.assertFalse((self.root / "dist/SCHEMA.md").exists())
        self.assertFalse((self.root / "dist/chunks/SCHEMA.md").exists())
        self.assertFalse((self.root / "vendor/SCHEMA.md").exists())
        self.assertFalse((self.root / "vendor/lib/SCHEMA.md").exists())
        self.assertTrue((self.root / "src/SCHEMA.md").exists())
        self.assertClean(self.check())

    def test_init_on_empty_dir(self):
        created = schema_lint.init_tree(self.root)
        self.assertEqual(len(created), 1)
        self.assertClean(self.check())

    def test_init_enumerates_dirs_before_files(self):
        self.write("zzz.txt")
        self.write("aaa/inner.txt")
        run_cli("init", str(self.root))
        text = (self.root / "SCHEMA.md").read_text(encoding="utf-8")
        self.assertLess(text.index("aaa/"), text.index("zzz.txt"))


# ---------------------------------------------------------------- fix mode


class TestFixMode(ScenarioCase):
    """check --fix: mechanical drift remediation an agent or CI can apply."""

    def read_root_schema(self) -> str:
        return (self.root / "SCHEMA.md").read_text(encoding="utf-8")

    def test_fix_registers_stray_file(self):
        self.schema("", [("kept.txt", "file", "existing", "")])
        self.write("kept.txt")
        self.write("stray.txt")
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertIn("`stray.txt` | file | TODO", self.read_root_schema())
        self.assertClean(self.check())  # idempotent: second run is clean

    def test_fix_registers_stray_dir_and_scaffolds_subtree(self):
        """A registered-by-fix dir must be descendable on the re-check, so
        its missing schemas are scaffolded in the same pass."""
        self.schema("", [])
        self.write("newdir/inner/file.txt")
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertIn("`newdir/` | dir | TODO", self.read_root_schema())
        self.assertTrue((self.root / "newdir/SCHEMA.md").exists())
        self.assertTrue((self.root / "newdir/inner/SCHEMA.md").exists())
        self.assertClean(self.check())

    def test_fix_prunes_stale_row(self):
        self.schema("", [("gone.txt", "file", "deleted long ago", ""),
                         ("kept.txt", "file", "still here", "")])
        self.write("kept.txt")
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertNotIn("gone.txt", self.read_root_schema())
        self.assertIn("kept.txt", self.read_root_schema())
        self.assertClean(self.check())

    def test_fix_never_touches_required_or_generated_rows(self):
        """Missing required entries are real errors, not fixable drift; and
        generated entries are allowed to be absent — neither is pruned."""
        self.schema("", [
            ("must.txt", "file", "required artifact", "required"),
            ("built.log", "file", "ephemeral build output", "generated"),
        ])
        code, out = self.check("--fix")
        self.assertEqual(code, 1, out)  # missing required still gates
        text = self.read_root_schema()
        self.assertIn("must.txt", text)
        self.assertIn("built.log", text)

    def test_fix_resolves_strict_stray_error(self):
        self.schema("", [("app.py", "file", "entrypoint", "required")],
                    coverage="strict")
        self.write("app.py")
        self.write("notes.md")
        code_before, _ = self.check()
        self.assertEqual(code_before, 1)
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertClean(self.check())

    def test_fix_preserves_purposes_and_other_sections(self):
        extra = ("\n## Placement\n\n- Notes → `docs/`\n\n"
                 "## Forbidden\n\n- No junk at root.\n")
        self.schema("", [("kept.txt", "file", "the important purpose",
                          "required")], extra=extra)
        self.write("kept.txt")
        self.write("stray.txt")
        self.check("--fix")
        text = self.read_root_schema()
        self.assertIn("the important purpose", text)
        self.assertIn("## Placement", text)
        self.assertIn("- No junk at root.", text)

    def test_fix_does_not_prune_pattern_rows(self):
        """A pattern with zero matches is not stale; --fix must keep it."""
        self.schema("", [("*.md", "pattern", "future docs", "")])
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertIn("*.md", self.read_root_schema())

    def test_fix_is_noop_on_clean_tree(self):
        self.schema("", [("kept.txt", "file", "fine", "required")])
        self.write("kept.txt")
        before = self.read_root_schema()
        code, out = self.check("--fix")
        self.assertEqual(code, 0, out)
        self.assertEqual(self.read_root_schema(), before)

    def test_check_without_fix_never_writes(self):
        self.schema("", [("gone.txt", "file", "stale row", "")])
        self.write("stray.txt")
        before = self.read_root_schema()
        self.check()
        self.assertEqual(self.read_root_schema(), before)


# ---------------------------------------------------------------- robustness


class TestRobustness(ScenarioCase):
    """Hostile filesystem realities: symlinks, unicode, CLI misuse."""

    def test_symlink_cycle_does_not_hang_or_crash(self):
        """A registered symlink pointing back up the tree must not recurse."""
        self.schema("", [("sub/", "dir", "real child", "required")])
        self.schema("sub", [("loop/", "dir", "symlink back to root", "")])
        os.symlink(self.root, self.root / "sub" / "loop")
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_symlinked_dir_is_not_traversed(self):
        """Symlinked dirs are entries, not subtrees; their targets are
        checked wherever they really live."""
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(outside))
        (outside / "junk").mkdir()
        (outside / "junk" / "no-schema-here.txt").write_text("x")
        self.schema("", [("linked/", "dir", "external mount", "")])
        os.symlink(outside / "junk", self.root / "linked")
        code, out = self.check()
        self.assertEqual(code, 0, out)

    def test_unicode_and_spaces_in_names(self):
        self.schema("", [
            ("notas-espanol.md", "file", "unicode content", "required"),
            ("My Report.md", "file", "space in name", "required"),
        ])
        self.write("notas-espanol.md")
        self.write("My Report.md")
        self.assertClean(self.check())

    def test_include_hidden_surfaces_dotfiles(self):
        self.schema("", [])
        self.write(".secret-config")
        code_default, out_default = self.check()
        self.assertNotIn(".secret-config", out_default)
        code_hidden, out_hidden = self.check("--include-hidden")
        self.assertEqual(code_hidden, 0)
        self.assertIn("unregistered entry '.secret-config'", out_hidden)

    def test_nonexistent_path_exits_2(self):
        code, _ = run_cli("check", str(self.root / "no-such-dir"))
        self.assertEqual(code, 2)

    def test_file_path_exits_2(self):
        target = self.write("afile.txt")
        code, _ = run_cli("check", str(target))
        self.assertEqual(code, 2)


# ---------------------------------------------------------------- boundaries


class TestRepoBoundaries(ScenarioCase):
    """Git repo boundaries: submodules, nested clones. Walks never cross."""

    def submodule(self, rel: str) -> Path:
        """A fake initialized submodule: a dir carrying a .git pointer file."""
        mount = self.mkdir(rel)
        self.write(f"{rel}/.git", "gitdir: ../../.git/modules/dep\n")
        return mount

    def test_terminal_marked_submodule_is_clean(self):
        """The blessed shape: mount registered terminal, interior ignored."""
        self.schema("", [("vendor-lib/", "dir", "vendored pyramid",
                          "terminal")])
        self.submodule("vendor-lib")
        self.write("vendor-lib/deep/junk.txt")   # no SCHEMA.md — child's job
        self.assertClean(self.check())

    def test_unmarked_submodule_warns_and_is_not_descended(self):
        """Missing 'terminal' nudges a warning, but the seam still holds."""
        self.schema("", [("dep/", "dir", "a submodule", "")])
        self.submodule("dep")
        self.write("dep/inner/x.txt")            # would error if descended
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("repo boundary", out)
        self.assertNotIn("inner", out)
        code_w, _ = self.check("--werror")
        self.assertEqual(code_w, 1)

    def test_nested_clone_git_dir_is_also_a_boundary(self):
        """A .git *directory* (plain nested clone) counts the same."""
        self.schema("", [("clone/", "dir", "nested checkout", "")])
        self.mkdir("clone/.git")
        self.write("clone/inner/x.txt")
        code, out = self.check()
        self.assertEqual(code, 0, out)
        self.assertIn("repo boundary", out)
        self.assertNotIn("inner", out)

    def test_strict_unregistered_submodule_still_errors(self):
        """Coverage rules still apply to the mount itself — only the
        descent is suppressed."""
        self.schema("", [], coverage="strict")
        self.submodule("dep")
        self.write("dep/stuff/thing.txt")
        code, out = self.check()
        self.assertEqual(code, 1, out)
        self.assertIn("unregistered entry 'dep'", out)
        self.assertNotIn("stuff", out)

    def test_init_does_not_scaffold_inside_submodule(self):
        """init registers the mount in the parent but never writes into it."""
        self.write("app.py")
        self.submodule("dep")
        self.mkdir("dep/inner")
        code, out = run_cli("init", str(self.root))
        self.assertEqual(code, 0, out)
        root_schema = (self.root / "SCHEMA.md").read_text(encoding="utf-8")
        self.assertIn("dep/", root_schema)
        self.assertFalse((self.root / "dep" / "SCHEMA.md").exists())
        self.assertFalse((self.root / "dep" / "inner" / "SCHEMA.md").exists())


# ---------------------------------------------------------------- federation


class TestFederation(ScenarioCase):
    """check --federation: seam invariants over .gitmodules."""

    def submodule(self, rel: str, seeded_version: str | None = None) -> Path:
        mount = self.mkdir(rel)
        self.write(f"{rel}/.git", "gitdir: ../../.git/modules/dep\n")
        if seeded_version is not None:
            self.write(
                f"{rel}/SCHEMA.md",
                f'---\nschema: "{seeded_version}"\ncoverage: listed\n---\n\n'
                "# SCHEMA — child\n\n## Structure\n\n"
                "| entry | kind | purpose | rules |\n|---|---|---|---|\n")
        return mount

    def gitmodules(self, *paths: str) -> None:
        self.write(".gitmodules", "".join(
            f'[submodule "{p}"]\n\tpath = {p}\n'
            f"\turl = https://github.com/x/{Path(p).name}.git\n"
            for p in paths))

    def test_no_gitmodules_is_a_clean_noop(self):
        self.schema("", [])
        code, out = self.check("--federation")
        self.assertEqual(code, 0, out)
        self.assertIn("no .gitmodules", out)

    def test_green_seam(self):
        """Registered terminal mount + seeded child at the right version."""
        self.gitmodules("libs/dep")
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [("dep/", "dir", "vendored pyramid", "terminal")])
        self.submodule("libs/dep", seeded_version="0.1")
        code, out = self.check("--federation")
        self.assertClean((code, out))
        self.assertIn("1 submodule(s) — 1 ok, 0 version-drift, "
                      "0 unseeded, 0 uninitialized", out)

    def test_unseeded_child_warns(self):
        self.gitmodules("libs/dep")
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [("dep/", "dir", "vendored pyramid", "terminal")])
        self.submodule("libs/dep")               # no root SCHEMA.md inside
        code, out = self.check("--federation")
        self.assertEqual(code, 0, out)
        self.assertIn("not seeded", out)
        self.assertIn("1 unseeded", out)
        code_w, _ = self.check("--federation", "--werror")
        self.assertEqual(code_w, 1)

    def test_version_drift_warns_and_expect_schema_overrides(self):
        self.gitmodules("libs/dep")
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [("dep/", "dir", "vendored pyramid", "terminal")])
        self.submodule("libs/dep", seeded_version="0.0")
        code, out = self.check("--federation")
        self.assertEqual(code, 0, out)
        self.assertIn("declares schema 0.0", out)
        self.assertIn("1 version-drift", out)
        code2, out2 = self.check("--federation", "--expect-schema", "0.0")
        self.assertEqual(code2, 0, out2)
        self.assertIn("1 ok, 0 version-drift", out2)

    def test_unregistered_mount_is_error(self):
        self.gitmodules("libs/dep")
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [])                  # no dep/ row
        self.submodule("libs/dep", seeded_version="0.1")
        code, out = self.check("--federation")
        self.assertEqual(code, 1, out)
        self.assertIn("submodule mount not registered", out)

    def test_non_terminal_mount_is_error(self):
        self.gitmodules("libs/dep")
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [("dep/", "dir", "vendored pyramid", "")])
        self.submodule("libs/dep", seeded_version="0.1")
        code, out = self.check("--federation")
        self.assertEqual(code, 1, out)
        self.assertIn("must be marked 'terminal'", out)

    def test_uninitialized_submodule_warns(self):
        self.gitmodules("libs/ghost")            # listed, never cloned
        self.schema("", [("libs/", "dir", "dependencies", "required")])
        self.schema("libs", [])
        self.mkdir("libs")
        code, out = self.check("--federation")
        self.assertEqual(code, 0, out)
        self.assertIn("not initialized", out)
        self.assertIn("1 uninitialized", out)

    def test_mount_without_parent_schema_is_error(self):
        self.gitmodules("zone/dep")
        self.schema("", [])                      # zone/ unregistered, listed
        self.submodule("zone/dep", seeded_version="0.1")
        code, out = self.check("--federation")
        self.assertEqual(code, 1, out)
        self.assertIn("mount unregistered", out)

    def test_gitmodules_parser_handles_quirks(self):
        """Comments, tabs, extra keys, section name != path (hub reality)."""
        gm = self.write(".gitmodules", (
            "# fleet registry\n"
            '[submodule "README"]\n'
            "\tpath = projects/readme\n"
            "\turl = https://github.com/x/README.git\n"
            "\tupdate = merge\n"
            '[submodule "no-path-entry"]\n'
            "\turl = https://github.com/x/ghost.git\n"
        ))
        entries = schema_lint._parse_gitmodules(gm)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["path"], "projects/readme")
        self.assertEqual(entries[0]["update"], "merge")


if __name__ == "__main__":
    unittest.main(verbosity=2)

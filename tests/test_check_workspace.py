import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import check_workspace as checker

ROOT = Path("/workspace")
HARNESS = ROOT / "targets/harness"
PRODUCT = HARNESS / "targets/product"
HARNESS_SHA = "a" * 40
PRODUCT_SHA = "b" * 40


class LinkTests(unittest.TestCase):
    def check(self, link):
        return checker.check_link(ROOT, ROOT / "specs/roadmap.md", link)

    def test_local_links_and_fragments(self):
        with patch.object(Path, "exists", return_value=True) as exists:
            self.assertIsNone(self.check("../README.md#overview"))
            exists.assert_called_once_with()
            self.assertIsNone(self.check("#overview"))
        with patch.object(Path, "exists", return_value=False):
            self.assertIn("does not exist", self.check("missing.md") or "")

    def test_sibling_paths_refused_even_if_present(self):
        with patch.object(Path, "exists", return_value=True):
            for link in ("../../sibling/README.md", "../../sibling",
                         "..%2F..%2Fsibling/README.md", "/other/README.md"):
                with self.subTest(link=link):
                    self.assertIn("escapes", self.check(link) or "")

    def test_external_links_are_not_checked(self):
        with patch.object(checker, "git") as git:
            for link in ("https://example.org/docs", "mailto:owner@example.org",
                         "https://github.com/owner/harness/issues/1",
                         "https://github.com/owner/harness/blob/main/docs/spec.md",
                         f"https://github.com/owner/product/blob/{PRODUCT_SHA}/README.md"):
                self.assertIsNone(self.check(link))
            git.assert_not_called()

    def test_markdown_inline_reference_image_and_autolinks(self):
        text = '''[local](a.md#anchor) ![image](<image file.png>)
[ref]: b.md "Title"
<https://github.com/owner/repo/blob/sha/README.md>
```markdown
[example](not-a-real-file.md)
```
'''
        self.assertEqual(checker.markdown_links(text), [
            "a.md#anchor", "image file.png", "b.md",
            "https://github.com/owner/repo/blob/sha/README.md"])


class GitTests(unittest.TestCase):
    def test_gitlinks_from_tree_and_unborn_index(self):
        for metadata in (f"160000 commit {HARNESS_SHA}", f"160000 {HARNESS_SHA} 0"):
            with self.subTest(metadata=metadata):
                self.assertEqual(checker.gitlinks(
                    f"{metadata}\ttargets/harness\0"), {"targets/harness": HARNESS_SHA})
        self.assertEqual(checker.gitlinks(f"100644 blob {HARNESS_SHA}\tREADME.md\0"), {})

    def test_status_pins_not_branch_names(self):
        pins = {"targets/harness": HARNESS_SHA}
        for suffix in (" (heads/new-branch)", " (v1.0-5-gaaaaaaa)", ""):
            self.assertEqual(checker.check_status(f" {HARNESS_SHA} targets/harness{suffix}\n", pins), [])

    def test_mismatch_uninitialized_conflict_missing_and_extra_status(self):
        pins = {"targets/harness": HARNESS_SHA}
        for status in (f"+{HARNESS_SHA} targets/harness", f"-{HARNESS_SHA} targets/harness",
                       f"U{HARNESS_SHA} targets/harness", f" {PRODUCT_SHA} targets/harness",
                       "", f" {HARNESS_SHA} targets/unknown", "unexpected output"):
            with self.subTest(status=status):
                self.assertTrue(checker.check_status(status, pins))

    def collect(self, *, unborn=False, dirty=None, uninitialized=False):
        def fake_git(repo, *args, **kwargs):
            if args[0] == "rev-parse":
                return None if unborn else "c" * 40 + "\n"
            if args[0] in ("ls-tree", "ls-files"):
                if repo == ROOT:
                    if unborn:
                        self.assertEqual(args, ("ls-files", "--stage", "-z"))
                        return f"160000 {HARNESS_SHA} 0\ttargets/harness\0"
                    self.assertEqual(args, ("ls-tree", "-rz", "c" * 40))
                    return f"160000 commit {HARNESS_SHA}\ttargets/harness\0"
                if repo == HARNESS:
                    self.assertEqual(args, ("ls-tree", "-rz", HARNESS_SHA))
                    return f"160000 commit {PRODUCT_SHA}\ttargets/product\0"
                self.assertEqual(args, ("ls-tree", "-rz", PRODUCT_SHA))
                return ""
            if args[0] == "status":
                self.assertIn("--untracked-files=all", args)
                return (dirty or "") if repo == PRODUCT else ""
            self.fail(f"unexpected git call: {args}")

        errors = []
        with patch.object(checker, "git", side_effect=fake_git), patch.object(
                Path, "exists", return_value=not uninitialized):
            pins = checker.repositories(ROOT, errors)
        return pins, errors

    def test_recursive_committed_and_unborn_pin_discovery(self):
        for unborn in (False, True):
            with self.subTest(unborn=unborn):
                pins, errors = self.collect(unborn=unborn)
                self.assertEqual(pins, {"targets/harness": HARNESS_SHA,
                                        "targets/harness/targets/product": PRODUCT_SHA})
                self.assertEqual(errors, [])

    def test_tracked_and_untracked_submodule_dirt(self):
        for dirty in (" M README.md\n", "?? new-file.txt\n"):
            with self.subTest(dirty=dirty):
                self.assertIn("dirty submodule", self.collect(dirty=dirty)[1][0])

    def test_uninitialized_submodule_not_inspected_as_parent_repository(self):
        pins, errors = self.collect(uninitialized=True)
        self.assertEqual(pins, {"targets/harness": HARNESS_SHA})
        self.assertIn("uninitialized", errors[0])

    def test_git_commands_disable_optional_index_writes(self):
        result = subprocess.CompletedProcess([], 0, stdout="ok", stderr="")
        with patch.object(subprocess, "run", return_value=result) as run:
            self.assertEqual(checker.git(ROOT, "status", "--porcelain"), "ok")
            self.assertEqual(run.call_args.kwargs["env"]["GIT_OPTIONAL_LOCKS"], "0")
        result.returncode, result.stderr = 1, "missing object"
        with patch.object(subprocess, "run", return_value=result):
            self.assertIsNone(checker.git(ROOT, "cat-file", "-e", "bad", check=False))
            with self.assertRaisesRegex(RuntimeError, "missing object"):
                checker.git(ROOT, "cat-file", "-e", "bad")


class TopologyTests(unittest.TestCase):
    def test_exact_direct_components_with_git_owned_revisions(self):
        pins = {path: PRODUCT_SHA for path in checker.COMPONENT_PATHS}
        self.assertEqual(checker.check_topology(pins), [])

    def test_missing_nested_duplicate_and_excluded_components_fail(self):
        pins = {path: PRODUCT_SHA for path in checker.COMPONENT_PATHS}
        del pins["targets/med-agent-hub"]
        pins["targets/validation-harness/targets/querystore"] = PRODUCT_SHA
        pins["targets/openmrs_chatbot"] = PRODUCT_SHA
        errors = checker.check_topology(pins)
        self.assertEqual(len(errors), 3)
        self.assertTrue(any("missing direct" in item for item in errors))
        self.assertEqual(sum("unexpected or nested" in item for item in errors), 2)


class ScopeTests(unittest.TestCase):
    def test_only_umbrella_readme_agents_and_top_level_specs_are_scanned(self):
        sources = []

        def read_text(source, **kwargs):
            sources.append(source.relative_to(ROOT).as_posix())
            return "[missing](missing.md)"

        with patch.object(checker, "repositories", return_value={}), \
                patch.object(checker, "git", return_value=""), \
                patch.object(Path, "glob", return_value=[ROOT / "specs/roadmap.md"]), \
                patch.object(Path, "read_text", autospec=True, side_effect=read_text), \
                patch.object(Path, "exists", return_value=False):
            errors = checker.validate(ROOT)
        self.assertEqual(sources, ["README.md", "AGENTS.md", "specs/roadmap.md"])
        self.assertEqual(len([error for error in errors if "missing.md" in error]), 3)


if __name__ == "__main__":
    unittest.main()

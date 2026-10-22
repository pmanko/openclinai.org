"""Behaviour of the review hooks and probes on a small pytest project with a fork remote."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "review" / "hooks"
PROBE = ROOT / "review" / "bin" / "probe"

CALC = "def clamp(value, low, high):\n    return max(low, min(value, high))\n"
TEST = ("from calc import clamp\n\n\ndef test_inside():\n"
        "    assert clamp(5, 0, 10) == 5\n")


def run(cwd, *cmd, check=True, input=None):
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, input=input)
    if check and proc.returncode:
        raise AssertionError(f"{cmd} failed:\n{proc.stdout}\n{proc.stderr}")
    return proc


def git(repo, *args, check=True):
    return run(repo, "git", *args, check=check)


@pytest.fixture
def project(tmp_path, monkeypatch):
    monkeypatch.setenv("REVIEW_WORK", str(tmp_path / "work"))
    monkeypatch.setenv("REVIEW_PYTHON", sys.executable)
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE"):
        monkeypatch.delenv(name, raising=False)
    fork = tmp_path / "fork.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(fork))
    repo = tmp_path / "calc"
    (repo / "tests").mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "dev@example.test")
    git(repo, "config", "user.name", "Dev")
    git(repo, "config", "core.hooksPath", str(HOOKS))
    (repo / "pytest.ini").write_text("[pytest]\npythonpath = .\n")
    (repo / "calc.py").write_text(CALC)
    (repo / "tests" / "test_calc.py").write_text(TEST)
    git(repo, "add", ".")
    git(repo, "commit", "-q", "--no-verify", "-m", "Clamp")
    git(repo, "remote", "add", "origin", str(fork))
    git(repo, "push", "-q", "--no-verify", "origin", "main")
    git(repo, "remote", "set-head", "origin", "main")
    git(repo, "switch", "-q", "-c", "fix")
    return repo


def commit(repo, files, message, check=True):
    for path, text in files.items():
        (repo / path).write_text(text)
    git(repo, "add", *files)
    return git(repo, "commit", "-q", "-m", message, check=check)


def push(repo, *extra):
    return git(repo, "push", "origin", *extra, "HEAD:refs/heads/fix", check=False)


BROKEN = CALC.replace("max(low, min(value, high))", "min(value, high)")
FIXED_TEST = TEST + "\n\ndef test_below():\n    assert clamp(-5, 0, 10) == 0\n"


def test_a_fix_whose_test_fails_without_it_is_pushed_with_red_and_green(project):
    commit(project, {"calc.py": BROKEN}, "Simplify clamp\n\nProbe: skip (setup)")
    commit(project, {"calc.py": CALC, "tests/test_calc.py": FIXED_TEST},
           'Clamp the low end\n\nMutation: calc.py "max(low, " -> "("')
    result = push(project)
    assert result.returncode == 0, result.stderr
    assert "red   " in result.stderr and "1 of 2 failed" in result.stderr
    assert "green " in result.stderr and "2 passed" in result.stderr
    ledger = (Path(os.environ["REVIEW_WORK"]) / "ledger" / "fork.jsonl").read_text()
    records = [json.loads(l) for l in ledger.splitlines()]
    assert [r["status"] for r in records] == ["skip", "probed"]
    assert len(records[1]["lines"]) == 3


def test_a_fix_whose_test_passes_without_it_is_refused(project):
    weak = TEST + "\n\ndef test_top():\n    assert clamp(50, 0, 10) == 10\n"
    commit(project, {"calc.py": CALC.replace("return", "return  "), "tests/test_calc.py": weak},
           "Touch clamp")
    result = push(project)
    assert result.returncode != 0
    assert "the tests do not detect it" in result.stderr


def test_a_comment_only_change_in_main_code_is_not_reverted(project):
    documented = CALC.replace("def clamp", "# Clamp value to [low, high].\ndef clamp")
    commit(project, {"calc.py": documented, "tests/test_calc.py": FIXED_TEST}, "Document clamp")
    result = push(project)
    assert result.returncode == 0, result.stderr
    assert "only in comments" in result.stderr and "revert" not in result.stderr


def test_a_comment_only_change_still_runs_its_mutation(project):
    documented = CALC.replace("def clamp", "# Clamp value to [low, high].\ndef clamp")
    commit(project, {"calc.py": documented, "tests/test_calc.py": FIXED_TEST},
           'Document clamp\n\nMutation: calc.py "max(low, min(value, high))" -> "min(value, high)"')
    result = push(project)
    assert result.returncode == 0, result.stderr
    assert "skip" in result.stderr and "red" in result.stderr and "mutation calc.py" in result.stderr
    commit(project, {"calc.py": documented + "\n# Another note.\n"},
           'Note\n\nTests: tests/test_calc.py\nMutation: calc.py "min(value, high)" -> "min(value, 10)"')
    missed = push(project)
    assert missed.returncode != 0 and "do not detect it" in missed.stderr


def test_a_test_only_change_runs_its_mutation(project):
    commit(project, {"tests/test_calc.py": FIXED_TEST},
           'Test the low bound\n\nMutation: calc.py "max(low, min(value, high))" -> "min(value, high)"')
    result = push(project)
    assert result.returncode == 0, result.stderr
    assert "no main code changed" in result.stderr and "mutation calc.py" in result.stderr
    commit(project, {"tests/test_calc.py": FIXED_TEST + "\n"},
           'Tidy\n\nMutation: calc.py "min(value, high)" -> "min(value, 10)"')
    missed = push(project)
    assert missed.returncode != 0 and "do not detect it" in missed.stderr


def test_a_change_inside_a_string_counts_as_code(project):
    commit(project, {"calc.py": CALC + "\nLABEL = 'a # b'\n"}, "Label\n\nProbe: skip (constant)")
    commit(project, {"calc.py": CALC + "\nLABEL = 'a # c'\n"}, "Relabel")
    result = push(project)
    assert result.returncode != 0 and "with no test" in result.stderr


def test_a_mutation_the_tests_miss_is_refused(project):
    commit(project, {"calc.py": BROKEN}, "Simplify\n\nProbe: skip (setup)")
    commit(project, {"calc.py": CALC, "tests/test_calc.py": FIXED_TEST},
           'Clamp\n\nMutation: calc.py "min(value, high)" -> "value"')
    result = push(project)
    assert result.returncode != 0
    assert "mutation calc.py" in result.stderr and "do not detect it" in result.stderr


def test_main_code_without_a_test_is_refused_unless_skipped_on_the_record(project):
    commit(project, {"calc.py": CALC + "\nLIMIT = 3\n"}, "Add a limit")
    refused = push(project)
    assert refused.returncode != 0 and "with no test" in refused.stderr
    git(project, "commit", "-q", "--amend", "-m", "Add a limit\n\nProbe: skip (constant only)")
    assert push(project).returncode == 0


def test_a_patch_already_probed_is_not_probed_again_after_a_rebase(project):
    commit(project, {"calc.py": BROKEN}, "Simplify\n\nProbe: skip (setup)")
    commit(project, {"calc.py": CALC, "tests/test_calc.py": FIXED_TEST}, "Clamp")
    assert push(project).returncode == 0
    git(project, "switch", "-q", "main")
    commit(project, {"README": "calc\n"}, "Readme")
    git(project, "push", "-q", "--no-verify", "origin", "main")
    git(project, "switch", "-q", "fix")
    git(project, "rebase", "-q", "main")
    result = push(project, "--force-with-lease")
    assert result.returncode == 0, result.stderr
    assert "same patch as" in result.stderr


def test_pushes_to_a_default_branch_or_over_unseen_work_are_refused(project, tmp_path):
    commit(project, {"tests/test_calc.py": FIXED_TEST}, "More tests")
    openmrs = tmp_path / "github.com" / "openmrs" / "calc.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(openmrs))
    git(project, "remote", "add", "upstream", str(openmrs))
    assert git(project, "push", "upstream", "HEAD:fix", check=False).returncode == 0
    assert "default branch" in git(project, "push", "upstream", "HEAD:main", check=False).stderr
    assert "default branch" in git(project, "push", "origin", "HEAD:main", check=False).stderr

    assert push(project).returncode == 0
    other = tmp_path / "other"
    git(tmp_path, "clone", "-q", str(tmp_path / "fork.git"), str(other))
    git(other, "switch", "-q", "fix")
    git(other, "-c", "user.email=o@example.test", "-c", "user.name=O", "commit", "-q",
        "--allow-empty", "-m", "Someone else")
    git(other, "push", "-q", "--no-verify", "origin", "fix")
    git(project, "commit", "-q", "--amend", "-m", "More tests, reworded")
    refused = git(project, "push", "--force", "origin", "HEAD:fix", check=False)
    assert refused.returncode != 0 and "fetch and look" in refused.stderr


def test_commits_already_pushed_are_recorded_as_baseline_and_skipped(project):
    commit(project, {"calc.py": CALC + "\nLIMIT = 3\n"}, "Old work")
    git(project, "push", "-q", "--no-verify", "origin", "HEAD:refs/heads/fix")
    assert "2 commits recorded" in run(project, sys.executable, str(PROBE), "--baseline").stdout
    git(project, "commit", "-q", "--amend", "-m", "Old work, reworded")
    result = git(project, "push", "--force-with-lease", "origin", "HEAD:fix", check=False)
    assert result.returncode == 0, result.stderr
    assert "before the probes were installed" in result.stderr


@pytest.mark.parametrize("files, message, refusal", [
    ({"tests/test_calc.py": TEST.replace("def test_inside", "@pytest.mark." + "skip\ndef test_inside")},
     "Skip", "[test:disabled]"),
    ({"tests/test_new.py": "def test_nothing():\n    clamp(1, 0, 2)\n"}, "Empty", "[test:no-assertions]"),
    ({"settings.py": 'TOKEN = "ghp_' + "a" * 36 + '"\n'}, "Token", "[secret] GitHub token"),
    ({"calc.py": CALC + "\n"}, 'Bad\n\nMutation: calc.py max -> min', "Mutation:"),
    ({"calc.py": CALC + "\n"}, "Bad\n\nTests: tests/test calc.py", "Tests:"),
    ({"calc.py": CALC + "\n"}, "Bad\n\nProbe: later", "Probe:"),
])
def test_commit_guards_refuse(project, files, message, refusal):
    result = commit(project, files, message, check=False)
    assert result.returncode != 0
    assert refusal in result.stderr


def test_a_well_formed_commit_passes_the_guards(project):
    result = commit(project, {"calc.py": CALC + "\n"},
                    'Fine\n\nTests: tests/test_calc.py::test_inside\n'
                    'Mutation: calc.py "max(low, " -> "("')
    assert result.returncode == 0, result.stderr


def test_the_red_line_quotes_a_failure_of_a_named_test_first():
    sys.path.insert(0, str(ROOT / "review" / "lib"))
    from reviewkit.probes import Run, _first

    run = Run(1, 5, ["OtherTest.old:12 expected 1", "PagingTest.slices:30 expected [R]"], Path("log"))
    assert _first(run, ["PagingTest#slices"]).startswith("PagingTest.slices")
    assert _first(run, ["tests/test_x.py::missing"]).startswith("OtherTest.old")


def test_a_rewrite_over_a_head_this_branch_pushed_is_allowed_when_fetch_skips_the_branch(project):
    commit(project, {"tests/test_calc.py": FIXED_TEST}, "More tests")
    assert push(project).returncode == 0
    git(project, "config", "--replace-all", "remote.origin.fetch", "+refs/heads/main:refs/remotes/origin/main")
    git(project, "update-ref", "-d", "refs/remotes/origin/fix")
    git(project, "commit", "-q", "--amend", "-m", "More tests, reworded")
    result = push(project, "--force")
    assert result.returncode == 0, result.stderr

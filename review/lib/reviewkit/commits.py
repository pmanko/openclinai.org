"""What a commit changes and what its trailers ask the probes to do.

Paths are classified by content conventions, never by branch or repository name:
test code (Maven `src/test`, `tests/`, `__tests__`, `*.test.ts`, `test_*.py`), main
code (source files outside those), and other files (documentation, build files,
configuration) that the probes ignore.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .git import git

TEST_PATH = re.compile(
    r"(^|/)(src/test/|tests?/|__tests__/|__mocks__/)"
    r"|\.(test|spec)\.[cm]?[jt]sx?$"
    r"|(^|/)test_[^/]*\.py$|_test\.py$|(^|/)conftest\.py$")
CODE_EXT = (".java", ".kt", ".groovy", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
            ".py", ".sh")
BUILD_CONFIG = re.compile(r"(^|/)[^/]*\.config\.[cm]?[jt]s$")

TRAILER_KEYS = ("Tests", "Mutation", "Probe")
_MUTATION = re.compile(r'^(?P<path>\S+)\s+(?P<old>"(?:[^"\\]|\\.)*")\s*->\s*'
                       r'(?P<new>"(?:[^"\\]|\\.)*")\s*$')
_SKIP = re.compile(r"^skip\s*\((?P<reason>.*\S.*)\)\s*$")
_SCISSORS = "# ------------------------ >8 ------------------------"


def classify(path: str) -> str:
    if TEST_PATH.search(path):
        return "test"
    if path.endswith(CODE_EXT) and not BUILD_CONFIG.search(path):
        return "main"
    return "other"


@dataclass(frozen=True)
class Change:
    status: str  # A, M or D
    path: str

    @property
    def kind(self) -> str:
        return classify(self.path)


_LINE_COMMENT = {".py": "#", ".sh": "#"}


def strip_comments(text: str, suffix: str) -> str:
    """The code of a source file: comments and blank lines dropped, string literals kept whole.

    A `//`, `#` or `/*` inside a string literal is text, not a comment, so a change to a
    URL or a label in a string still counts as a code change.
    """
    marker = _LINE_COMMENT.get(suffix, "//")
    blocks = marker == "//"
    out: list[str] = []
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch in "\"'`":
            j = i + 1
            while j < n and text[j] != ch:
                if text[j] == "\\":
                    j += 1
                elif text[j] == "\n" and ch != "`":
                    break
                j += 1
            out.append(text[i:j + 1])
            i = j + 1
        elif text.startswith(marker, i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif blocks and text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
        else:
            out.append(ch)
            i += 1
    lines = (line.rstrip() for line in "".join(out).splitlines())
    return "\n".join(line for line in lines if line)


def code_changed(repo: Path, sha: str, change: Change) -> bool:
    """Whether a main-file change alters anything beyond comments and blank lines."""
    if change.status != "M":
        return True
    suffix = Path(change.path).suffix
    before = git(repo, "show", f"{sha}^:{change.path}")
    after = git(repo, "show", f"{sha}:{change.path}")
    return strip_comments(before, suffix) != strip_comments(after, suffix)


def commit_changes(repo: Path, sha: str) -> list[Change]:
    out = git(repo, "diff-tree", "--no-commit-id", "-r", "--no-renames",
              "--name-status", "--root", sha)
    changes = []
    for line in out.splitlines():
        status, _, path = line.partition("\t")
        if path:
            changes.append(Change(status[0], path))
    return changes


@dataclass(frozen=True)
class Mutation:
    path: str
    old: str
    new: str
    raw: str

    def label(self) -> str:
        return self.raw


@dataclass
class Trailers:
    tests: list[str] = field(default_factory=list)
    mutations: list[Mutation] = field(default_factory=list)
    skip: str | None = None
    raw: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def present(self) -> bool:
        return bool(self.raw)

    def key(self) -> str:
        return "\n".join(sorted(self.raw))


def _message_body(message: str) -> str:
    message = message.split(_SCISSORS, 1)[0]
    return "\n".join(l for l in message.splitlines() if not l.startswith("#"))


def parse_trailers(message: str, repo: Path | str = ".") -> Trailers:
    """Read Tests:, Mutation: and Probe: from the message's final trailer block."""
    body = _message_body(message)
    parsed = git(repo, "interpret-trailers", "--parse", input=body + "\n")
    result = Trailers()
    for line in parsed.splitlines():
        key, sep, value = line.partition(":")
        if not sep or key not in TRAILER_KEYS:
            continue
        value = value.strip()
        result.raw.append(f"{key}: {value}")
        if key == "Tests":
            items = [t.strip() for t in value.split(",")]
            for item in items:
                target = re.split(r"#|::", item, maxsplit=1)[0]
                if not item or re.search(r"\s", target):
                    result.errors.append(f"Tests: '{value}' needs comma-separated test ids")
                    break
            else:
                result.tests.extend(items)
        elif key == "Mutation":
            m = _MUTATION.match(value)
            if not m:
                result.errors.append(
                    f'Mutation: \'{value}\' must read <path> "old text" -> "new text"')
                continue
            try:
                old, new = json.loads(m["old"]), json.loads(m["new"])
            except json.JSONDecodeError as exc:
                result.errors.append(f"Mutation: bad string escape in '{value}': {exc}")
                continue
            if not old or old == new:
                result.errors.append(f"Mutation: '{value}' must change non-empty text")
                continue
            result.mutations.append(Mutation(m["path"], old, new, value))
        else:
            m = _SKIP.match(value)
            if not m:
                result.errors.append(f"Probe: '{value}' must read skip (<reason>)")
            else:
                result.skip = m["reason"].strip()
    stray = [l for l in body.splitlines()
             if re.match(r"^(Tests|Mutation|Probe):", l)]
    if len(stray) > len(result.raw):
        result.errors.append("Tests:, Mutation: and Probe: belong in the message's "
                             "final paragraph of trailers")
    return result


def commit_trailers(repo: Path, sha: str) -> Trailers:
    return parse_trailers(git(repo, "log", "-1", "--format=%B", sha), repo)


def detect_runner(root: Path) -> str | None:
    override = git(root, "config", "--get", "review.runner", check=False).strip()
    if override:
        return override
    if (root / "pom.xml").is_file():
        return "maven"
    package = root / "package.json"
    if package.is_file() and "vitest" in package.read_text(encoding="utf-8"):
        return "vitest"
    if any((root / f).is_file() for f in ("pytest.ini", "pyproject.toml", "setup.cfg")) \
            or (root / "tests").is_dir():
        return "pytest"
    return None


def derived_tests(changes: list[Change], runner: str) -> list[str]:
    """Test ids for the runnable test files a commit adds or changes."""
    tests = []
    for change in changes:
        if change.status == "D" or change.kind != "test":
            continue
        path = change.path
        if runner == "maven":
            m = re.search(r"src/test/java/(?:.*/)?([A-Z]\w*Tests?)\.java$", path)
            if m:
                tests.append(m.group(1))
        elif runner == "vitest":
            if re.search(r"\.(test|spec)\.[cm]?[jt]sx?$", path):
                tests.append(path)
        elif runner == "pytest":
            if re.search(r"(^|/)test_[^/]*\.py$|_test\.py$", path):
                tests.append(path)
    return sorted(set(tests))

"""Static commit guards (L0) on the staged change.

Ported from the agent-side commit review so a person, Codex or Gemini at a terminal
meets the same checks. Blocking: likely secrets, focused or disabled tests, a new test
file with tests but no assertion. Printed only: a test that mocks its own unit, code
comments that narrate the development path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .commits import classify
from .git import git

SECRET_PATTERNS = (
    ("AWS access key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private key block", re.compile(r"-----BEGIN[ A-Z]*PRIVATE KEY-----")),
    ("GitHub token", re.compile(r"gh[pousr]_[0-9A-Za-z]{30,}")),
    ("Slack token", re.compile(r"xox[baprs]-[0-9A-Za-z-]{10,}")),
    ("Google API key", re.compile(r"AIza[0-9A-Za-z_-]{35}")),
)
_CREDENTIAL = re.compile(
    r"(api[_-]?key|secret|password|passwd|access[_-]?token|client[_-]?secret)"
    r"[\"' ]*[:=][ \"']*[A-Za-z0-9/+_=.-]{16,}", re.I)
_NOT_A_VALUE = re.compile(
    r"(process\.env|import\.meta\.env|getenv|System\.getenv|\$\{|<[a-z_]+>|example|"
    r"changeme|placeholder|your[_-]|xxxx|\*\*\*\*|redacted|dummy|sample|test)", re.I)
_SETTING_NAME = re.compile(
    r'^\s*public\s+static\s+final\s+String\s+RP_HUB_API_KEY\s*=\s*'
    r'"chartsearchai[.]hub[.]apikey";\s*$')

_FOCUSED = re.compile(r"\.only\s*\(|(^|[^A-Za-z.])(fit|fdescribe)\s*\(")
_DISABLED = re.compile(r"\.(skip|todo)\s*\(|(^|[^A-Za-z.])(xit|xtest|xdescribe)\s*\("
                       r"|@Disabled|@Ignore|@unittest\.skip|@pytest\.mark\.skip")
_HAS_TESTS = re.compile(r"(^|[^A-Za-z.])(it|test|describe)\s*\(|@Test"
                        r"|(^|\s)def\s+test_\w*\s*\(", re.M)
_HAS_ASSERT = re.compile(r"expect\s*\(|assert(Equals|NotEquals|That|True|False|NotNull|"
                         r"Null|Throws|Same|In|Raises|Is)|\.should[.\[(]|(^|\s)assert\s"
                         r"|pytest\.raises\s*\(|self\.fail\(|verify\(", re.M)
_COMMENT = re.compile(r"//|/\*|\*/|^\s*\*|^\s*#\s")
_NARRATIVE = re.compile(r"#[0-9]{2,}|\b[A-Z]+-[0-9]+\b|follow-?up|we avoid|we store|now we|"
                        r"we now|used to|previously|as discussed|originally|reviewer|"
                        r"per review|this pr\b", re.I)


@dataclass
class GuardReport:
    blocking: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _added_lines(diff: str) -> dict[str, list[tuple[int, str]]]:
    files: dict[str, list[tuple[int, str]]] = {}
    current, line_no = None, 0
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[4:]
            current = current[2:] if current.startswith("b/") else None
            if current:
                files.setdefault(current, [])
        elif line.startswith("@@"):
            m = re.search(r"\+(\d+)", line)
            line_no = int(m.group(1)) if m else 0
        elif line.startswith("+") and current:
            files[current].append((line_no, line[1:]))
            line_no += 1
    return files


def check_staged(repo: Path) -> GuardReport:
    report = GuardReport()
    diff = git(repo, "diff", "--cached", "--no-color", "-U0", "--diff-filter=ACMR",
               keep_env=True)
    added = _added_lines(diff)
    new_files = set(git(repo, "diff", "--cached", "--name-only", "--diff-filter=A",
                        keep_env=True).split())

    for path, lines in added.items():
        for label, pattern in SECRET_PATTERNS:
            if any(pattern.search(text) for _, text in lines):
                report.blocking.append(f"[secret] {label} in {path}")
        for _, text in lines:
            if _SETTING_NAME.match(text) or _NOT_A_VALUE.search(text):
                continue
            if _CREDENTIAL.search(text):
                report.blocking.append(f"[secret] hardcoded credential in {path}")
                break

        if classify(path) == "test":
            if any(_FOCUSED.search(text) for _, text in lines):
                report.blocking.append(f"[test:focused] {path} (.only, fit or fdescribe "
                                       "silently disables the rest of the suite)")
            if any(_DISABLED.search(text) for _, text in lines):
                report.blocking.append(f"[test:disabled] {path} (a disabled test)")
        if path.endswith((".java", ".kt", ".ts", ".tsx", ".js", ".jsx", ".mjs", ".py",
                          ".scss", ".css")):
            for no, text in lines:
                if _COMMENT.search(text) and _NARRATIVE.search(text):
                    report.notes.append(f"[comment] {path}:{no} {text.strip()}")

    for path in sorted(new_files):
        if classify(path) != "test":
            continue
        content = git(repo, "show", f":{path}", keep_env=True, check=False)
        if _HAS_TESTS.search(content) and not _HAS_ASSERT.search(content):
            report.blocking.append(f"[test:no-assertions] {path} (tests with no "
                                   "assertion check nothing)")
        subject = re.sub(r"\.(test|spec)\.[cm]?[jt]sx?$|(Tests?|IT)?\.java$|\.py$", "",
                         Path(path).name)
        subject = re.sub(r"^test_", "", subject)
        if subject and re.search(rf"(vi|jest)\.mock\(['\"][^'\"]*/{re.escape(subject)}['\"]",
                                 content):
            report.notes.append(f"[test:mock-self] {path} mocks its own unit '{subject}'")
    return report

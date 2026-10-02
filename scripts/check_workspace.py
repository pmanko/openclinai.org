
"""Offline umbrella link and gitlink checks; not publication or product validation."""

import os
import re
import subprocess
from pathlib import Path
from typing import Literal, overload
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SHA = r"[0-9a-f]{40}"
COMPONENT_PATHS = {
    "targets/validation-harness", "targets/med-agent-hub", "targets/catalyst",
    "targets/chartsearchai", "targets/chartsearchai-esm", "targets/querystore",
}


@overload
def git(repo, *args, check: Literal[True] = True) -> str: ...
@overload
def git(repo, *args, check: Literal[False]) -> str | None: ...


def git(repo, *args, check=True):
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), *args],
        capture_output=True, text=True, timeout=15, check=False,
        env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
    )
    if result.returncode and check:
        raise RuntimeError(result.stderr.strip() or "git command failed")
    return result.stdout if result.returncode == 0 else None


def github_repo(url):
    match = re.fullmatch(
        r"(?:https?://|ssh://git@|git@)github\.com[:/]([^/]+/[^/]+?)(?:\.git)?/?",
        url, re.IGNORECASE,
    )
    return match[1].lower() if match else None


def gitlinks(records):
    pins = {}
    for record in records.split("\0"):
        if record:
            metadata, path = record.split("\t", 1)
            mode, object_or_sha, sha_or_stage = metadata.split()
            if mode == "160000":
                pins[path] = object_or_sha if re.fullmatch(SHA, object_or_sha) else sha_or_stage
    return pins


def repositories(root, errors):
    pins, remotes = {}, {}

    def visit(repo, ref):
        records = (git(repo, "ls-tree", "-rz", ref) if ref else
                   git(repo, "ls-files", "--stage", "-z"))
        for path, sha in gitlinks(records).items():
            child = repo / path
            relative = child.relative_to(root).as_posix()
            pins[relative] = sha
            if not (child / ".git").exists():
                errors.append(f"{relative}: uninitialized submodule")
                continue
            if git(child, "status", "--porcelain", "--untracked-files=all",
                   "--ignore-submodules=all").strip():
                errors.append(f"{relative}: dirty submodule (tracked or untracked files)")
            for line in git(child, "remote", "-v").splitlines():
                identity = github_repo(line.split()[1])
                if identity:
                    remotes[identity, sha] = child
            visit(child, sha)

    head = git(root, "rev-parse", "--verify", "HEAD", check=False)
    visit(root, head.strip() if head else None)
    return pins, remotes


def check_status(status, pins):
    errors, seen = [], set()
    for line in status.splitlines():
        match = re.fullmatch(rf"(.)({SHA}) (.+?)(?: \(.+\))?", line)
        if not match:
            errors.append(f"unrecognized submodule status: {line}")
            continue
        marker, sha, path = match.groups()
        seen.add(path)
        if marker != " " or pins.get(path) != sha:
            errors.append(f"{path}: submodule status does not match initialized recorded pin")
    errors.extend(f"{path}: missing submodule status" for path in pins.keys() - seen)
    return errors


def check_topology(pins):
    paths = set(pins)
    errors = [f"{path}: missing direct component gitlink"
              for path in sorted(COMPONENT_PATHS - paths)]
    errors.extend(f"{path}: unexpected or nested component gitlink"
                  for path in sorted(paths - COMPONENT_PATHS))
    return errors


def markdown_links(text):
    text = re.sub(r"(?ms)^ {0,3}(`{3,}|~{3,})[^\n]*\n.*?^ {0,3}\1[ \t]*$", "", text)
    patterns = (r"\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)",
                r"(?m)^\s*\[[^\]\n]+\]:\s*(<[^>]+>|[^\s]+)",
                r"<(https://github\.com/[^>\s]+)>")
    return [link.strip("<>") for pattern in patterns for link in re.findall(pattern, text)]


def check_link(root, source, link, remotes):
    url = urlsplit(link)
    path = unquote(url.path)
    if url.scheme or url.netloc:
        if url.scheme != "https" or url.netloc.lower() != "github.com":
            return None
        match = re.fullmatch(r"/([^/]+/[^/]+)/blob/([^/]+)/(.+)", path)
        if not match:
            return None
        identity, sha, target = match.groups()
        # External product authorities need not be workspace components. Only
        # locally managed repositories have a recorded source pin to enforce.
        if identity.lower() not in {name for name, _ in remotes}:
            return None
        repo = remotes.get((identity.lower(), sha))
        if not re.fullmatch(SHA, sha) or repo is None:
            return "GitHub blob link does not match a local remote and recorded 40-SHA pin"
        if git(repo, "cat-file", "-e", f"{sha}:{target}", check=False) is None:
            return "GitHub blob path is absent from the pinned commit"
        return None
    if not path:
        return None
    target = (source.parent / path).resolve()
    if not target.is_relative_to(root):
        return "relative/absolute link escapes umbrella workspace (external sibling)"
    if not target.exists():
        return "local link target does not exist"
    return None


def validate(root=ROOT):
    root = root.resolve()
    errors = []
    pins, remotes = repositories(root, errors)
    errors.extend(check_topology(pins))
    errors.extend(check_status(git(root, "submodule", "status", "--recursive"), pins))
    documents = [root / "README.md", root / "AGENTS.md", *sorted((root / "specs").glob("*.md"))]
    for source in documents:
        for link in markdown_links(source.read_text(encoding="utf-8")):
            problem = check_link(root, source, link, remotes)
            if problem:
                errors.append(f"{source.relative_to(root)}: {link}: {problem}")
    return errors


if __name__ == "__main__":
    try:
        failures = validate()
    except (OSError, RuntimeError, subprocess.TimeoutExpired, ValueError) as error:
        failures = [str(error)]
    for failure in failures:
        print(f"ERROR: {failure}")
    if not failures:
        print("Workspace links, recursive gitlink pins and submodule cleanliness passed (offline).")
    raise SystemExit(bool(failures))

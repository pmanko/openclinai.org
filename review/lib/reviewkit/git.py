"""Small wrappers around git and child processes used by the hooks and probes."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

# Variables git sets for a hook that would point a child git or build at the wrong
# repository or index. Hooks that inspect the commit being made keep them.
_REPO_ENV = ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_PREFIX",
             "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
             "GIT_COMMON_DIR", "GIT_QUARANTINE_PATH")

ZERO = "0" * 40


class GitError(RuntimeError):
    pass


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in _REPO_ENV}


def git(repo: Path | str, *args: str, check: bool = True, keep_env: bool = False,
        input: str | None = None) -> str:
    proc = subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          text=True, input=input,
                          env=None if keep_env else clean_env())
    if check and proc.returncode != 0:
        raise GitError(f"git {' '.join(args)}: {proc.stderr.strip()}")
    return proc.stdout


def git_ok(repo: Path | str, *args: str) -> bool:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True,
                          env=clean_env()).returncode == 0


def toplevel(repo: Path | str) -> Path:
    return Path(git(repo, "rev-parse", "--show-toplevel").strip())


def common_dir(repo: Path | str) -> Path:
    return Path(git(repo, "rev-parse", "--path-format=absolute",
                    "--git-common-dir").strip()).resolve()


def repo_name(repo: Path | str) -> str:
    """The repository's name from its origin URL, else its directory name."""
    url = git(repo, "config", "--get", "remote.origin.url", check=False).strip()
    if url:
        name = url.rstrip("/").rsplit("/", 1)[-1].rsplit(":", 1)[-1]
        return name[:-4] if name.endswith(".git") else name
    return common_dir(repo).parent.name if common_dir(repo).name == ".git" \
        else toplevel(repo).name


def patch_id(repo: Path | str, sha: str) -> str | None:
    diff = git(repo, "show", "--no-color", "--format=", sha)
    if not diff.strip():
        return None
    out = subprocess.run(["git", "-C", str(repo), "patch-id", "--stable"],
                         input=diff, capture_output=True, text=True,
                         env=clean_env()).stdout.split()
    return out[0] if out else None

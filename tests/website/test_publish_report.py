"""Exercise real v2 publication stage and deploy control flow without cloud access.

The isolated checkout is a git repository with a committed report archive. Only
cloud executables (gcloud, rsync, ssh, curl) are stubbed; archive validation,
staging, catalog generation, and additive vs. --prune deploy run unchanged.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "t",
    "GIT_AUTHOR_EMAIL": "t@example.invalid",
    "GIT_COMMITTER_NAME": "t",
    "GIT_COMMITTER_EMAIL": "t@example.invalid",
}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
        env={**os.environ, **GIT_IDENTITY},
    ).stdout.strip()


def _write_v2_run_dir(
    directory: Path,
    *,
    slug: str,
    title: str,
    summary: str = "We tested two clinical AI setups across three HIV patient charts and 35 clinical questions.",
    takeaway: str = "Med Agent Hub improved accuracy and completeness by 14 points with zero unsafe answers.",
    family: str = "chartsearchai",
    availability: str = "available",
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    ed = {
        "schema": "openclinai.editorial.v2",
        "schema_version": 2,
        "slug": slug,
        "title": title,
        "summary": summary,
        "takeaway": takeaway,
        "family": family,
        "featured": True,
        "date": "10 Nov 2026",
    }
    if availability == "unavailable":
        ed["availability"] = "unavailable"
    (directory / "editorial.json").write_text(json.dumps(ed, indent=2) + "\n", encoding="utf-8")
    if availability == "unavailable":
        return directory

    (directory / "run-summary.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.summary.v2",
                "schema_version": 2,
                "slug": slug,
                "report_family": family,
                "date": "10 Nov 2026",
                "cells": 2,
                "patients": "Fixture Patient",
                "scout": [{"backend": "arm-a", "n": 2, "benchmark_score": 88.0, "harm_count": 0}],
                "judging": {"recorded": True, "sentence": "Judged by frontier evaluator."},
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (directory / "report-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.report.v2",
                "schema_version": 2,
                "runs": [
                    {
                        "id": slug,
                        "backends": ["arm-a"],
                        "catalog_meta": {"title": title},
                        "arm_cards": {"arm-a": {"title": "Arm A", "short_title": "Arm A"}},
                        "source_card_pool": {},
                        "refs_pool": {},
                        "scenarios": [{"scenario_id": "s1", "turns": [{"turn": 1, "question": "Q", "cells": {}}]}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (directory / "dashboard-data.json").write_text(
        json.dumps(
            {
                "schema": "openclinai.dashboard.v2",
                "schema_version": 2,
                "status": {"run": slug, "arms": [], "scenarios": []},
                "record_pool": {},
                "sources_pool": {},
                "refs_pool": {},
                "details": {},
            }
        ),
        encoding="utf-8",
    )
    (directory / "index.html").write_text(
        "<!doctype html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>"
        f"<body><script type='application/json' id='report-editorial'>{json.dumps(ed)}</script></body></html>\n",
        encoding="utf-8",
    )
    (directory / "dashboard.html").write_text(
        "<!doctype html><html><head><meta name='viewport' content='width=device-width, initial-scale=1'></head>"
        f"<body><script type='application/json' id='report-editorial'>{json.dumps(ed)}</script></body></html>\n",
        encoding="utf-8",
    )
    return directory


@pytest.fixture
def publisher(tmp_path: Path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("publish-report.py", "deploy-reports.sh", "cloud-lib.sh", "build-reports-index.py"):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)

    reports = tmp_path / "reports"
    assets = reports / "assets"
    assets.mkdir(parents=True)
    for asset_name in ("report-shell.css", "report-shell.js", "dashboard-shell.css", "dashboard-shell.js"):
        (assets / asset_name).write_text("/* asset */\n", encoding="utf-8")

    _write_v2_run_dir(
        reports / "2026-11-10-example-study",
        slug="2026-11-10-example-study",
        title="Selected report: how well does Med Agent Hub read charts?",
    )
    _write_v2_run_dir(
        reports / "2026-11-01-archived-study",
        slug="2026-11-01-archived-study",
        title="Live archived report: clinical chart synthesis evaluation",
    )
    (reports / "2026-11-01-archived-study" / "clip.mp4").write_bytes(b"video")
    _write_v2_run_dir(
        reports / "2026-10-01-unavailable-study",
        slug="2026-10-01-unavailable-study",
        title="Explicitly unavailable historical evaluation study",
        availability="unavailable",
    )

    run_dir = _write_v2_run_dir(
        tmp_path / "run",
        slug="2026-11-10-example-study",
        title="Updated study: how well does Med Agent Hub read HIV charts?",
    )

    binaries = tmp_path / "bin"
    binaries.mkdir()
    stubs = {
        "python3": f'exec "{sys.executable}" "$@"\n',
        "ssh": "exit 0\n",
        "rsync": (
            f'echo "trace: publish upload"\nprintf "%s\\n" "$@" > "{tmp_path}/rsync-args"\n'
            f'{{ printf "%s\\n" "$@"; echo "---"; }} >> "{tmp_path}/rsync-calls"\n'
            'exit "${PUBLISH_EXIT_CODE:-0}"\n'
        ),
        "curl": 'cat "${REPORTS_ROOT}/index.html"\n',
        "gcloud": '''echo "trace: cloud command" >&2
case "$*" in
  "compute instances describe "*"--format=value(name)") echo test-vm ;;
  "compute instances describe "*"--format=value(status)") echo RUNNING ;;
  "compute instances describe "*"--format=value(networkInterfaces[0].accessConfigs[0].natIP)") echo 192.0.2.1 ;;
  "compute ssh "*) exit 0 ;;
  *) echo "unexpected gcloud arguments: $*" >&2; exit 97 ;;
esac
''',
    }
    for name, body in stubs.items():
        executable = binaries / name
        executable.write_text("#!/bin/bash\nset -eu\n" + body, encoding="utf-8")
        executable.chmod(0o755)

    (tmp_path / ".gitignore").write_text("*.mp4\nbin/\nrun/\nrsync-args*\nrsync-calls*\n", encoding="utf-8")
    git(tmp_path, "init", "-q", "-b", "main")
    subprocess.run(
        [sys.executable, str(scripts / "build-reports-index.py"), "--root", str(tmp_path), "--reports-root", str(reports)],
        check=True,
        capture_output=True,
    )
    git(tmp_path, "add", "--", "reports", "scripts", ".gitignore")
    git(tmp_path, "commit", "-q", "-m", "Archive")

    def run(*, action="stage", extra_args=(), publish_exit=0):
        if action == "stage":
            argv = [
                sys.executable,
                str(scripts / "publish-report.py"),
                "stage",
                str(run_dir),
                "--slug",
                "2026-11-10-example-study",
                "--root",
                str(tmp_path),
                "--reports-root",
                str(reports),
                *extra_args,
            ]
        elif action == "deploy":
            argv = [
                sys.executable,
                str(scripts / "publish-report.py"),
                "deploy",
                "--root",
                str(tmp_path),
                "--reports-root",
                str(reports),
                *extra_args,
            ]
        else:
            argv = ["/bin/bash", str(scripts / action), *extra_args]
        return subprocess.run(
            argv,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                **GIT_IDENTITY,
                "PATH": f"{binaries}:/usr/bin:/bin",
                "REPORTS_ROOT": str(reports),
                "GCP_PROJECT": "test-project",
                "GCP_SSH_USER": "test-user",
                "GCP_SSH_KEY": str(tmp_path / "unused-test-key"),
                "PUBLISH_EXIT_CODE": str(publish_exit),
                "CADDY_SITE_REPORTS": "reports.example.invalid",
            },
        )

    return run


def test_stage_never_commits_and_deploy_is_additive_by_default(publisher, tmp_path: Path):
    stage_res = publisher(action="stage")
    assert stage_res.returncode == 0, stage_res.stdout + stage_res.stderr
    # stage never runs git commit or rsync
    assert git(tmp_path, "log", "-1", "--format=%s") == "Archive"
    assert not (tmp_path / "rsync-args").exists()
    assert "reports/2026-11-10-example-study/index.html" in git(tmp_path, "status", "--porcelain")

    git(tmp_path, "add", "--", "reports")
    git(tmp_path, "commit", "-q", "-m", "Stage updated report")

    deploy_res = publisher(action="deploy")
    assert deploy_res.returncode == 0, deploy_res.stdout + deploy_res.stderr
    args = (tmp_path / "rsync-args").read_text().splitlines()
    # Additive by default: --delete is NOT present unless --prune is passed
    assert "--delete" not in args
    assert "--exclude=*.mp4" in args and "--exclude=*.webm" in args

    # With --prune, --delete IS passed
    prune_res = publisher(action="deploy", extra_args=("--prune",))
    assert prune_res.returncode == 0, prune_res.stdout + prune_res.stderr
    prune_args = (tmp_path / "rsync-args").read_text().splitlines()
    assert "--delete" in prune_args


def test_deploy_refuses_an_archive_with_uncommitted_changes(publisher, tmp_path: Path):
    (tmp_path / "reports/2026-11-01-archived-study/index.html").write_text("Edited\n", encoding="utf-8")
    result = publisher(action="deploy")
    assert result.returncode != 0
    assert "uncommitted changes" in result.stderr or "viewport" in result.stderr
    assert "trace:" not in result.stdout + result.stderr


def test_per_slug_deploy_syncs_slug_and_catalog_additively(publisher, tmp_path: Path):
    git(tmp_path, "checkout", "-q", "-b", "feature/v2-test")
    result = publisher(action="deploy", extra_args=("--slug", "2026-11-10-example-study"))
    assert result.returncode == 0, result.stdout + result.stderr
    calls = [
        [line for line in block.splitlines() if line.strip()]
        for block in (tmp_path / "rsync-calls").read_text(encoding="utf-8").split("---\n")
        if block.strip()
    ]
    assert len(calls) == 2
    slug_call, catalog_call = calls
    assert "--delete" in slug_call
    assert slug_call[-2] == str(tmp_path / "reports/2026-11-10-example-study") + "/"
    assert "--delete" not in catalog_call
    assert str(tmp_path / "reports/index.html") in catalog_call
    assert str(tmp_path / "reports/assets") in catalog_call


def test_stage_restores_previous_packet_when_archive_validation_fails(publisher, tmp_path: Path):
    existing_dir = tmp_path / "reports/2026-11-10-example-study"
    before_files = {
        p.name: p.read_bytes() for p in sorted(existing_dir.iterdir()) if p.is_file()
    }
    before_manifest = (tmp_path / "reports/reports-index.json").read_bytes()
    before_index = (tmp_path / "reports/index.html").read_bytes()

    # Overlong arm_cards[*].short_title (>48 chars) passes schema check but fails catalog archive check
    bad_rd_path = tmp_path / "run/report-data.json"
    bad_rd = json.loads(bad_rd_path.read_text(encoding="utf-8"))
    bad_rd["runs"][0]["arm_cards"]["arm-a"]["short_title"] = "X" * 49
    bad_rd_path.write_text(json.dumps(bad_rd), encoding="utf-8")

    result = publisher(action="stage")
    assert result.returncode != 0

    after_files = {
        p.name: p.read_bytes() for p in sorted(existing_dir.iterdir()) if p.is_file()
    }
    assert after_files == before_files
    assert (tmp_path / "reports/reports-index.json").read_bytes() == before_manifest
    assert (tmp_path / "reports/index.html").read_bytes() == before_index

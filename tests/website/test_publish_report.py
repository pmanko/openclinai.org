"""Exercise real publication shell control flow, not cloud or report rendering.

The isolated checkout has pre-rendered reports. Only cloud executables (gcloud,
rsync and ssh) are stubbed; archive validation, staging and catalog generation
run unchanged. No network service is contacted.
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def publisher(tmp_path):
    scripts = tmp_path / "scripts"
    scripts.mkdir()
    for name in ("publish-report.sh", "cloud-lib.sh",
                 "stage-report.py", "build-reports-index.py"):
        shutil.copy2(ROOT / "scripts" / name, scripts / name)

    reports = tmp_path / "reports"
    (reports / "example").mkdir(parents=True)
    (reports / "example/index.html").write_text("Report\n", encoding="utf-8")
    (reports / "index.html").write_text("Index\n", encoding="utf-8")
    (reports / "archived").mkdir()
    (reports / "archived/index.html").write_text("Archived report\n", encoding="utf-8")
    (reports / "sitemap.xml").write_text("Existing sitemap\n", encoding="utf-8")
    (tmp_path / "reports-index.json").write_text(json.dumps({"runs": [
        {"slug": "example", "title": "Selected report"},
        {"slug": "archived", "title": "Live archived report"},
        {"slug": "unavailable", "title": "Explicitly unavailable", "availability": "unavailable"},
    ]}), encoding="utf-8")
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "report.html").write_text("New report\n", encoding="utf-8")
    (run_dir / "events.jsonl").write_text(
        json.dumps({"event_type": "run", "comparison_set": "fixture"}) + "\n", encoding="utf-8",
    )
    binaries = tmp_path / "bin"
    binaries.mkdir()
    stubs = {
        "python3": f'exec "{sys.executable}" "$@"\n',
        "ssh": "exit 0\n",
        "rsync": 'echo "trace: publish upload"\nexit "${PUBLISH_EXIT_CODE:-0}"\n',
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

    def run(*, publish_exit=0, dry_run=False):
        return subprocess.run(
            ["/bin/bash", str(scripts / "publish-report.sh"),
             "chartsearchai", str(tmp_path / "run"), "example"],
            cwd=tmp_path, capture_output=True, text=True, check=False,
            env={
                **os.environ,
                "PATH": f"{binaries}:/usr/bin:/bin",
                "REPORTS_ROOT": str(reports), "PUBLISH_DRY_RUN": str(int(dry_run)),
                "GCP_PROJECT": "test-project", "GCP_SSH_USER": "test-user",
                "GCP_SSH_KEY": str(tmp_path / "unused-test-key"),
                "PUBLISH_EXIT_CODE": str(publish_exit),
                "CADDY_SITE_REPORTS": "reports.example.invalid",
            },
        )

    return run


def test_success_is_reported_after_the_upload_and_names_the_archive_to_commit(publisher):
    result = publisher()
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("trace: publish upload") == 2
    assert "==> published: https://reports.example.invalid/example/" in result.stdout
    assert "commit reports/example" in result.stdout


@pytest.mark.parametrize("dry_run", [False, True])
def test_partial_archive_refused_before_local_changes_or_cloud_access(publisher, tmp_path, dry_run):
    reports = tmp_path / "reports"
    (reports / "archived/index.html").unlink()
    before = {path.relative_to(tmp_path): path.read_bytes()
              for path in tmp_path.rglob("*") if path.is_file()}
    result = publisher(dry_run=dry_run)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "incomplete staged report archive" in result.stderr
    assert "archived" in result.stderr
    assert "Restore the complete curated archive" in result.stderr
    assert "trace:" not in result.stdout + result.stderr
    after = {path.relative_to(tmp_path): path.read_bytes()
             for path in tmp_path.rglob("*") if path.is_file()}
    assert after == before
    assert not (reports / ".example.staging").exists()


def test_absent_archive_refused_without_creating_output_directory(publisher, tmp_path):
    reports = tmp_path / "reports"
    shutil.rmtree(reports)
    manifest = tmp_path / "reports-index.json"
    before = manifest.read_bytes()
    result = publisher()
    assert result.returncode == 1, result.stdout + result.stderr
    assert "incomplete staged report archive" in result.stderr
    assert not reports.exists()
    assert manifest.read_bytes() == before
    assert "trace:" not in result.stdout + result.stderr


def test_dry_run_validates_its_existing_curated_manifest_before_changes(publisher, tmp_path):
    reports = tmp_path / "reports"
    manifest = reports / "reports-index.json"
    manifest.write_text(json.dumps({"runs": [
        {"slug": "dry-run-archive", "title": "Missing from this staged archive"},
    ]}))
    before = manifest.read_bytes()
    result = publisher(dry_run=True)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "dry-run-archive" in result.stderr
    assert manifest.read_bytes() == before
    assert (reports / "example/index.html").read_text() == "Report\n"
    assert "trace:" not in result.stdout + result.stderr


def test_incoming_packet_can_supply_its_missing_curated_report(publisher, tmp_path):
    reports = tmp_path / "reports"
    (reports / "example/index.html").unlink()
    result = publisher()
    assert result.returncode == 0, result.stdout + result.stderr
    assert (reports / "example/index.html").read_text() == "New report\n"
    assert 'href="example/index.html"' in (reports / "index.html").read_text()


def test_complete_archive_preserves_old_links_and_explicit_unavailability(publisher, tmp_path):
    result = publisher()
    assert result.returncode == 0, result.stdout + result.stderr
    reports = tmp_path / "reports"
    html = (reports / "index.html").read_text()
    sitemap = (reports / "sitemap.xml").read_text()
    assert 'href="archived/index.html"' in html
    assert '/archived/index.html' in sitemap
    assert (reports / "archived/index.html").read_text() == "Archived report\n"
    assert 'href="unavailable/index.html"' not in html
    assert '/unavailable/index.html' not in sitemap
    assert 'Explicitly unavailable' in html
    assert 'Report unavailable' in html


def test_publication_failure_does_not_claim_publication(publisher):
    result = publisher(publish_exit=17)
    assert result.returncode == 17, result.stdout + result.stderr
    assert "==> published:" not in result.stdout


def test_dry_run_only_stages_and_never_publishes(publisher):
    result = publisher(dry_run=True, publish_exit=17)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "dry-run staged only" in result.stdout
    assert "trace:" not in result.stdout
    assert "==> published:" not in result.stdout

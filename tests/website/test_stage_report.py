"""Publication consumes portable rendered packets without the harness installed."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('stage_report', ROOT / 'scripts/stage-report.py')
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


def packet(tmp_path):
    source = tmp_path / 'external-packet'
    source.mkdir()
    (source / 'report.html').write_text('<h1>Reviewed report</h1><a href="evidence.json">Evidence</a>')
    (source / 'evidence.json').write_text('{"reviewed": true}')
    (source / 'events.jsonl').write_text(json.dumps({'event_type': 'run', 'comparison_set': 'recorded-comparison'}) + '\n')
    return source


def test_staging_works_in_isolated_python_without_a_harness_package(tmp_path):
    source = packet(tmp_path)
    owner = tmp_path / 'owner'
    owner.mkdir()
    manifest = owner / 'reports-index.json'
    manifest.write_text('{"runs": []}')
    result = subprocess.run([
        sys.executable, '-I', str(ROOT / 'scripts/stage-report.py'),
        'chartsearchai', str(source), 'example', '--root', str(owner),
        '--reports-root', str(owner / 'reports'), '--manifest', str(manifest),
    ], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    destination = owner / 'reports/example'
    assert (destination / 'index.html').read_bytes() == (source / 'report.html').read_bytes()
    assert (destination / 'evidence.json').read_bytes() == (source / 'evidence.json').read_bytes()
    assert (source / 'report.html').is_file()
    meta = json.loads((destination / 'meta.json').read_text())
    assert str(tmp_path) not in json.dumps(meta)
    assert meta['comparison_set'] == 'recorded-comparison'


def test_packet_must_already_be_rendered_and_failure_preserves_existing_report(tmp_path):
    source = packet(tmp_path)
    (source / 'report.html').unlink()
    reports = tmp_path / 'reports'
    existing = reports / 'example'
    existing.mkdir(parents=True)
    (existing / 'index.html').write_text('previous publication')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text('{"runs": []}')
    with pytest.raises(FileNotFoundError, match='pre-rendered report.html'):
        stage.stage_report(family='chartsearchai', run_dir=source, slug='example', reports_root=reports, manifest_path=manifest)
    assert (existing / 'index.html').read_text() == 'previous publication'
    assert json.loads(manifest.read_text()) == {'runs': []}


def test_symlinks_cannot_publish_files_outside_the_packet(tmp_path):
    source = packet(tmp_path)
    private = tmp_path / 'private.json'
    private.write_text('not publishable')
    (source / 'linked.json').symlink_to(private)
    with pytest.raises(ValueError, match='must not contain symlinks'):
        stage.stage_report(family='chartsearchai', run_dir=source, slug='example', reports_root=tmp_path / 'reports', manifest_path=tmp_path / 'manifest.json')


@pytest.mark.parametrize('slug', ['..', '../outside', 'UPPER', 'with space'])
def test_unsafe_slugs_are_rejected_before_copying(tmp_path, slug):
    with pytest.raises(ValueError, match='slug'):
        stage.stage_report(family='chartsearchai', run_dir=packet(tmp_path), slug=slug, reports_root=tmp_path / 'reports', manifest_path=tmp_path / 'manifest.json')


def test_staging_cannot_replace_its_own_input(tmp_path):
    source = packet(tmp_path)
    with pytest.raises(ValueError, match='overlap'):
        stage.stage_report(family='chartsearchai', run_dir=source, slug=source.name, reports_root=tmp_path, manifest_path=tmp_path / 'manifest.json')

"""Probe outcomes must reflect executed assertions, not setup or skipped tests."""
import os
import subprocess
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'review/lib'))
from reviewkit.probes import Run, _expect_green, _expect_red


def test_zero_and_infrastructure_are_not_behavioral_evidence():
    assert not _expect_green(Run(0, 0, [], Path('log')), 'head')[0]
    assert not _expect_red(Run(2, 1, ['import'], Path('log')), 'head', 'mutation')[0]
    assert not _expect_red(Run(1, 0, [], Path('log')), 'head', 'mutation')[0]
    assert _expect_red(Run(1, 1, ['assert boundary'], Path('log')), 'head', 'mutation')[0]


def test_actual_pytest_runner_distinguishes_assertions_skips_and_collection(tmp_path):
    fixture = tmp_path / 'test_fixture.py'
    for source, expected in [("import pytest\npytestmark = getattr(pytest.mark, 'skip')\ndef test_skip(): pass\n", 3),
                             ('raise RuntimeError("setup")\n', 2),
                             ('def test_behavior(): assert 1 == 2\n', 1),
                             ('def test_behavior(): assert 1 == 1\n', 0)]:
        fixture.write_text(source)
        result = subprocess.run([str(ROOT / 'review/bin/runners/pytest.sh'), str(tmp_path),
                                 str(tmp_path / 'run.log'), str(fixture)],
                                env={**os.environ, 'REVIEW_PYTHON': sys.executable}, capture_output=True)
        assert result.returncode == expected, result.stdout + result.stderr


def test_report_rejects_wrong_revision_missing_findings_and_omitted_files():
    import runpy
    import pytest
    validate = runpy.run_path(str(ROOT / 'review/bin/review.py'))['validate_review']
    good = dict(head='sha', findings=[], reviewed_files=['a.py'], unreviewed_files=[], tests=[])
    validate(good, 'sha', ['a.py'])
    for bad in [{**good, 'head': 'old'}, {**good, 'findings': None}, {**good, 'reviewed_files': []}]:
        with pytest.raises(ValueError): validate(bad, 'sha', ['a.py'])

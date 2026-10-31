"""Probe outcomes must reflect executed assertions, not setup or skipped tests."""
import os
import json
import subprocess
import sys
from pathlib import Path
import pytest
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


def test_maven_runner_rejects_stale_reports_and_setup_errors(tmp_path):
    stub = tmp_path / 'bin'
    stub.mkdir()
    mvn = stub / 'mvn'
    reports = tmp_path / 'target/surefire-reports'
    reports.mkdir(parents=True)
    for kind, expected in [('pass', 0), ('failure', 1), ('error', 2), ('skipped', 3), ('stale', 3)]:
        (reports / 'TEST-stale.xml').write_text('<testsuite><testcase name="old"/></testsuite>')
        content = '' if kind == 'pass' else '<' + kind + '/>'
        xml = '<testsuite><testcase name="behavior">' + content + '</testcase></testsuite>'
        mvn.write_text('#!/bin/sh\n' + ('' if kind == 'stale' else
                       "printf '%s' '" + xml + "' > target/surefire-reports/TEST-case.xml\n") +
                       ('exit 1\n' if kind in ('failure', 'error') else 'exit 0\n'))
        mvn.chmod(0o755)
        result = subprocess.run([str(ROOT / 'review/bin/runners/maven.sh'), str(tmp_path),
                                 str(tmp_path / 'run.log'), 'ExampleTest'],
                                env={**os.environ, 'PATH': str(stub) + os.pathsep + os.environ['PATH']},
                                capture_output=True)
        assert result.returncode == expected, result.stdout + result.stderr


def test_unrelated_failure_does_not_satisfy_named_mutation_probe():
    run = Run(1, 2, ['tests.example::other: boundary assertion failed'], Path('log'))
    assert not _expect_red(run, 'head', 'mutation', ['tests/example.py::boundary'])[0]
    assert _expect_red(run, 'head', 'mutation', ['tests/example.py::other'])[0]
    from reviewkit.probes import _first
    nested = Run(1, 2, ['unrelated: boundary in diagnostic', 'suite boundary: expected 1'], Path('log'),
                 [{'full_name': 'suite boundary', 'selectors': ['fixture.test.js#boundary']}])
    assert _first(nested, ['fixture.test.js#boundary']) == 'suite boundary: expected 1'


def test_executable_inputs_are_classified_without_freezing_prose():
    from reviewkit.commits import classify
    for path in ('server/levels.yaml', 'server/prompts/example.txt',
                 'datasets/validation/scenarios/example.json', 'datasets/wahs/cases.jsonl'):
        assert classify(path) == 'main'
    assert classify('docs/usage.md') == 'other'


def test_vitest_runner_rejects_process_errors_and_incomplete_evidence(tmp_path):
    import json
    stub = tmp_path / 'node_modules/.bin/vitest'
    stub.parent.mkdir(parents=True)
    log = tmp_path / 'run.log'
    cases = [('passed', 0, 0, 'passed', 0), ('failed', 1, 0, 'failed', 1),
             ('skipped', 0, 0, 'passed', 3), ('passed', 1, 0, 'passed', 2),
             ('failed', 1, 1, 'failed', 2), ('passed', 0, 0, 'interrupted', 2),
             ('passed', 0, 0, 'missing', 2), ('passed', 0, 1, 'passed', 2),
             ('passed', 0, 0, 'malformed', 2)]
    for status, process_exit, errors, reason, expected in cases:
        report = {'testResults': [{'status': 'failed' if status == 'failed' else 'passed',
                  'name': str(tmp_path / 'fixture.test.js'),
                  'assertionResults': [{'status': status, 'title': 'behavior', 'fullName': 'suite behavior', 'failureMessages': ['wrong']}]}]}
        metadata = {'reason': reason, 'unhandled_errors': errors}
        encoded_metadata = '{bad' if reason == 'malformed' else json.dumps(metadata)
        # A stale sidecar must not stand in for an interrupted reporter.
        Path(str(log) + '.execution.json').write_text(json.dumps({'reason': 'passed', 'unhandled_errors': 0}))
        stub.write_text('#!' + sys.executable + '\nimport os,json,sys,subprocess\n'
            'from pathlib import Path\n'
            'output=next(x.split("=",1)[1] for x in sys.argv if x.startswith("--outputFile.json="))\n'
            f'Path(output).write_text({json.dumps(json.dumps(report))})\n' +
            ('' if reason == 'missing' else
             f'Path(os.environ["REVIEW_VITEST_EVIDENCE"]).write_text({json.dumps(encoded_metadata)})\n' if reason == 'malformed' else
             'reporter=next(x.split("=",1)[1] for x in sys.argv if x.startswith("--reporter=") and x.endswith(".mjs"))\n' +
             'subprocess.run(["node", "-e", ' + repr("import(require('node:url').pathToFileURL(process.argv[1]).href).then(({default:R})=>new R().onTestRunEnd([],Array(Number(process.argv[2])).fill({}),process.argv[3]))") + ', reporter, ' + repr(str(errors)) + ', ' + repr(reason) + '], check=True)\n') +
            f'sys.exit({process_exit})\n')
        stub.chmod(0o755)
        result = subprocess.run([str(ROOT / 'review/bin/runners/vitest.sh'), str(tmp_path), str(log), 'fixture.test.js'], capture_output=True)
        assert result.returncode == expected, (status, process_exit, errors, reason, result.stdout, result.stderr)
        if status == 'failed' and errors == 0 and reason == 'failed':
            from reviewkit.probes import _run
            selected = ['fixture.test.js#behavior']
            run = _run('vitest', tmp_path, selected, log)
            assert _expect_red(run, 'head', 'mutation', selected)[0]
            assert (str(tmp_path / 'fixture.test.js'), 'suite behavior') in run.executed_cases
            assert run.failed_ids[0]['full_name'] == 'suite behavior'
            assert not _expect_red(run, 'head', 'mutation', ['other.test.js#behavior'])[0]
            assert not _expect_red(run, 'head', 'mutation', ['fixture.test.js#unrelated'])[0]


def test_maven_interruption_cannot_prove_a_mutation_failed(tmp_path):
    stub = tmp_path / 'bin/mvn'
    stub.parent.mkdir()
    report = tmp_path / 'target/surefire-reports/TEST-current.xml'
    report.parent.mkdir(parents=True)
    xml = '<testsuite><testcase classname="ExampleTest" name="behavior"><failure message="expected 1"/></testcase></testsuite>'
    stub.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n' +
                    "Path('target/surefire-reports/TEST-current.xml').write_text(" + repr(xml) + ')\nraise SystemExit(137)\n')
    stub.chmod(0o755)
    result = subprocess.run([str(ROOT / 'review/bin/runners/maven.sh'), str(tmp_path), str(tmp_path/'run.log'), 'ExampleTest#behavior'], env={**os.environ, 'PATH': str(stub.parent)+os.pathsep+os.environ['PATH']}, capture_output=True)
    assert result.returncode == 2, result.stdout + result.stderr


@pytest.mark.parametrize('runner', ['maven', 'pytest', 'vitest'])
def test_failed_cleanup_cannot_reuse_old_assertions(tmp_path, runner):
    """A failed attempt to remove old evidence must not certify a new run."""
    stub = tmp_path / 'bin'
    stub.mkdir()
    marker = tmp_path / 'executed'
    log = tmp_path / 'run.log'
    env = {**os.environ, 'PATH': str(stub) + os.pathsep + os.environ['PATH']}
    xml = '<testsuite><testcase classname="Fixture" name="behavior"><failure message="old failure"/></testcase></testsuite>'
    protected = None
    if runner == 'maven':
        protected = tmp_path / 'target/surefire-reports'
        protected.mkdir(parents=True)
        obsolete = protected / 'TEST-old.xml'
        if os.geteuid() == 0:
            # Root bypasses mode bits, but unlink still rejects a directory.
            obsolete.mkdir()
        else:
            obsolete.write_text(xml)
        executable = stub / 'mvn'
    else:
        # Simulate the external cleanup command refusing an existing report.
        (stub / 'rm').write_text('#!/bin/sh\nexit 1\n')
        (stub / 'rm').chmod(0o755)
        if runner == 'pytest':
            Path(str(log) + '.xml').write_text(xml)
            executable = stub / 'prepared-python'
            env['REVIEW_PYTHON'] = str(executable)
        else:
            executable = tmp_path / 'node_modules/.bin/vitest'
            executable.parent.mkdir(parents=True)
            Path(str(log) + '.json').write_text(json.dumps({'testResults': [{
                'status': 'failed', 'name': str(tmp_path / 'fixture.test.js'),
                'assertionResults': [{'status': 'failed', 'title': 'behavior',
                    'fullName': 'behavior', 'failureMessages': ['old failure']}]}]}))
            Path(str(log) + '.execution.json').write_text(json.dumps({
                'reason': 'failed', 'unhandled_errors': 0}))
    executable.write_text('#!' + sys.executable + '\nimport os,sys\nfrom pathlib import Path\n' +
        (f'if "-m" not in sys.argv:\n os.execv({sys.executable!r}, [{sys.executable!r}, *sys.argv[1:]])\n'
         if runner == 'pytest' else '') +
        f'Path({str(marker)!r}).write_text("ran")\nraise SystemExit(1)\n')
    executable.chmod(0o755)
    if protected:
        protected.chmod(0o555)
    try:
        result = subprocess.run([str(ROOT / f'review/bin/runners/{runner}.sh'),
            str(tmp_path), str(log), 'Fixture#behavior'], env=env, capture_output=True)
    finally:
        if protected:
            protected.chmod(0o755)
    assert result.returncode == 2, result.stdout + result.stderr
    assert not marker.exists(), 'Tests started despite unavailable fresh evidence'


@pytest.mark.parametrize('runner', ['pytest', 'maven'])
def test_same_named_failure_in_another_file_or_class_is_not_the_requested_test(tmp_path, monkeypatch, runner):
    from reviewkit.probes import _run
    if runner == 'pytest':
        (tmp_path / 'pytest.ini').write_text('[pytest]\n')
        tmp_path = tmp_path / 'nested-project'
        tmp_path.mkdir()
        (tmp_path / 'test_intended.py').write_text('import pytest\npytestmark = getattr(pytest.mark, "skip")\ndef test_boundary(): assert False\n')
        (tmp_path / 'test_other.py').write_text('def test_boundary(): assert False\n')
        selected = ['test_intended.py::test_boundary', 'test_other.py']
        correct = ['test_other.py::test_boundary']
        monkeypatch.setenv('REVIEW_PYTHON', sys.executable)
    else:
        stub = tmp_path / 'bin/mvn'
        stub.parent.mkdir()
        reports = tmp_path / 'target/surefire-reports'
        reports.mkdir(parents=True)
        xml = '<testsuite><testcase classname="IntendedTest" name="boundary"><skipped/></testcase><testcase classname="pkg.OtherTest" name="boundary"><failure message="unrelated"/></testcase></testsuite>'
        stub.write_text('#!' + sys.executable + '\nfrom pathlib import Path\n' +
            f'Path("target/surefire-reports/TEST-fresh.xml").write_text({xml!r})\nraise SystemExit(1)\n')
        stub.chmod(0o755)
        monkeypatch.setenv('PATH', str(stub.parent) + os.pathsep + os.environ['PATH'])
        selected = ['IntendedTest#boundary', 'OtherTest']
        correct = ['OtherTest#boundary']
    result = _run(runner, tmp_path, selected, tmp_path / 'run.log')
    assert not _expect_red(result, 'head', 'mutation', selected)[0]
    result = _run(runner, tmp_path, correct, tmp_path / 'correct.log')
    assert _expect_red(result, 'head', 'mutation', correct)[0]
    assert {(i['file'], i['full_name']) for i in result.failed_ids}.issubset(result.executed_cases)


@pytest.mark.parametrize('wanted,other,separator', [
    ('case', 'case][other', '::'), ('case#part', 'case.part', '::'),
    ('case::part', 'case.part', '::'), ('case#part', 'case.part', '#')])
def test_a_specific_parameter_case_requires_an_exact_identity(tmp_path, monkeypatch, wanted, other, separator):
    from reviewkit.probes import _run
    (tmp_path / 'test_fixture.py').write_text('import pytest\n'
        f'@pytest.mark.parametrize("x", [pytest.param(1, id={wanted!r}, marks=getattr(pytest.mark, "skip")), '
        f'pytest.param(2, id={other!r})])\n'
        'def test_boundary(x): assert x == 0\n')
    monkeypatch.setenv('REVIEW_PYTHON', sys.executable)
    selected = [f'test_fixture.py{separator}test_boundary[{wanted}]', 'test_fixture.py']
    result = _run('pytest', tmp_path, selected, tmp_path / 'run.log')
    assert result.code == 1 and result.ran == 1
    assert not _expect_red(result, 'head', 'mutation', selected)[0]
    unparameterized = ['test_fixture.py::test_boundary']
    result = _run('pytest', tmp_path, unparameterized, tmp_path / 'all-cases.log')
    assert _expect_red(result, 'head', 'mutation', unparameterized)[0]

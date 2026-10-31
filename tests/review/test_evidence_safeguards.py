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
             'subprocess.run(["node", "-e", "import(process.argv[1]).then(({default:R})=>new R().onTestRunEnd([],Array(Number(process.argv[2])).fill({}),process.argv[3]))", reporter, ' + repr(str(errors)) + ', ' + repr(reason) + '], check=True)\n') +
            f'sys.exit({process_exit})\n')
        stub.chmod(0o755)
        result = subprocess.run([str(ROOT / 'review/bin/runners/vitest.sh'), str(tmp_path), str(log), 'fixture.test.js'], capture_output=True)
        assert result.returncode == expected, (status, process_exit, errors, reason, result.stdout, result.stderr)
        if status == 'failed' and errors == 0 and reason == 'failed':
            from reviewkit.probes import _run
            selected = ['fixture.test.js#behavior']
            run = _run('vitest', tmp_path, selected, log)
            assert _expect_red(run, 'head', 'mutation', selected)[0]
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

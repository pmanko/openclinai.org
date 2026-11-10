"""Website sources and static publication belong to the umbrella, independent of the harness."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / 'targets/validation-harness'


def test_harness_carries_no_website_sources_or_publication_tooling():
    """Invariant: the harness produces artifacts; it never owns website sources or publishers."""
    for relative in ('landing', 'site', 'reports/reports-index.json', '.github/workflows/pages.yml'):
        assert not (HARNESS / relative).exists(), relative
    for script in (ROOT / 'scripts').iterdir():
        if script.name.startswith(('publish-', 'cloud-', 'build-reports', 'build-landing', 'stage-report')):
            assert not (HARNESS / 'scripts' / script.name).exists(), script.name


def test_publication_does_not_import_or_install_the_harness():
    """Invariant: publication reads captured artifacts and never imports or runs the harness."""
    for script in (ROOT / 'scripts').iterdir():
        if script.name.startswith(('publish-', 'stage-report', 'build-reports', 'reshell-reports')):
            text = script.read_text()
            for coupling in ('from harness', 'import harness', 'harness-cli', 'uv run'):
                assert coupling not in text, (script.name, coupling)
    selected = (ROOT / 'site/published-content.ts').read_text()
    assert 'targets/validation-harness/harness' not in selected


def test_relocated_media_is_checked_before_it_is_staged_in_git():
    """Invariant: no video and no binary over 400 KiB is committed to website sources."""
    video = {'.mp4', '.mov', '.webm', '.m4v', '.avi', '.mkv'}
    binary = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'}
    for directory in (ROOT / 'landing', ROOT / 'site/public'):
        for path in directory.rglob('*'):
            if not path.is_file():
                continue
            assert path.suffix.lower() not in video, path
            if path.suffix.lower() in binary:
                assert path.stat().st_size <= 400 * 1024, path


def test_published_reports_separate_data_from_display_shell():
    """Invariant: every published report separates report-data.json from a lightweight index.html shell."""
    reports_root = ROOT / 'reports'
    assert (reports_root / 'assets' / 'report-shell.css').is_file()
    assert (reports_root / 'assets' / 'report-shell.js').is_file()
    report_dirs = [
        d for d in sorted(reports_root.iterdir())
        if d.is_dir() and d.name != 'assets' and (d / 'index.html').is_file()
    ]
    assert len(report_dirs) >= 35
    for d in report_dirs:
        html_path = d / 'index.html'
        data_path = d / 'report-data.json'
        assert data_path.is_file(), f'missing report-data.json in {d.name}'
        assert data_path.stat().st_size > 100, f'empty report-data.json in {d.name}'
        html = html_path.read_text(encoding='utf-8')
        assert html_path.stat().st_size <= 10 * 1024, f'index.html not a lightweight shell in {d.name}'
        assert '../assets/report-shell.css?v=' in html, d.name
        assert '../assets/report-shell.js?v=' in html, d.name
        assert "data-src='./report-data.json'" in html, d.name

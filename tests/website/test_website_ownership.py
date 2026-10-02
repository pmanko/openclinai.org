"""Sources and static publication belong directly to the umbrella."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / 'targets/validation-harness'


def test_website_sources_workflows_and_publishers_have_one_owner():
    for relative in ('landing', 'site', '.github/workflows/pages.yml', 'reports-index.json',
                     'scripts/publish-landing.sh', 'scripts/publish-report.sh',
                     'scripts/stage-report.py', 'scripts/build-reports-index.py',
                     'scripts/build-landing-sitemap.py', 'scripts/reports-backup.sh',
                     'scripts/cloud-lib.sh', 'scripts/project-status.sh'):
        assert (ROOT / relative).exists(), relative
        assert not (HARNESS / relative).exists(), relative
    assert not list((HARNESS / 'scripts').glob('cloud-*'))


def test_publication_does_not_import_or_install_the_harness():
    for name in ('stage-report.py', 'build-reports-index.py', 'publish-report.sh', 'publish-landing.sh'):
        text = (ROOT / 'scripts' / name).read_text()
        assert 'from harness' not in text
        assert 'import harness' not in text
        assert 'uv run' not in text
        assert 'harness-cli' not in text
    selected = (ROOT / 'site/published-content.ts').read_text()
    assert 'targets/validation-harness/harness' not in selected
    assert '001-harness-control-plane' not in selected
    assert 'specs/roadmap.canvas.tsx' not in selected


def test_relocated_media_is_checked_before_it_is_staged_in_git():
    video = {'.mp4', '.mov', '.webm', '.m4v', '.avi', '.mkv'}
    binary = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.pdf'}
    for directory in (ROOT / 'landing', ROOT / 'site/public'):
        for path in directory.rglob('*'):
            if not path.is_file():
                continue
            assert path.suffix.lower() not in video, path
            if path.suffix.lower() in binary:
                assert path.stat().st_size <= 400 * 1024, path

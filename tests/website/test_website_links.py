import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('website_links', ROOT / 'scripts/check-website-links.py')
links = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(links)


def test_link_checker_reports_missing_assets_and_fragments(tmp_path):
    (tmp_path / 'index.html').write_text('<a href="page.html#absent">Page</a><img src="missing.png">')
    (tmp_path / 'page.html').write_text('<h1 id="present">Page</h1>')
    errors = links.check(tmp_path)
    assert any('missing fragment page.html#absent' in error for error in errors)
    assert any('missing local target missing.png' in error for error in errors)


def test_docs_hash_navigation_resolves_static_twins_and_correct_base(tmp_path):
    (tmp_path / 'index.html').write_text('<a href="/openclinai.org/#/welcome">Welcome</a><a href="/openclinai.org/#/spec/absent">Missing</a>')
    (tmp_path / 'welcome.html').write_text('<h1>Documentation</h1>')
    errors = links.check(tmp_path, '/openclinai.org/')
    assert len(errors) == 1
    assert 'missing route /openclinai.org/#/spec/absent' in errors[0]


def test_design_fragment_declarations_are_checked_without_running_javascript(tmp_path):
    (tmp_path / 'index.html').write_text('<a href="#main">Skip</a><script src="app.mjs"></script>')
    (tmp_path / 'app.mjs').write_text('throw Error("must not execute"); const html = `<main id="main"></main>`;')
    assert links.check(tmp_path) == []

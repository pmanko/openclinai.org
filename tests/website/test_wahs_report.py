"""Check the shareable WAHS report navigation, sandbox ARIA invariants, and thin-shell contract."""

from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "landing" / "wahs"
DEMO = ROOT / "wahs" / "demo"
ARTIFACTS_WAHS = ROOT / "artifacts" / "wahs"


class ReportParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.sections = []
        self.tabs = []
        self.tabpanels = []
        self.inputs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "section":
            self.sections.append(attrs.get("id"))
        if attrs.get("role") == "tab":
            self.tabs.append(attrs)
        if attrs.get("role") == "tabpanel":
            self.tabpanels.append(attrs)
        if tag in ("input", "textarea"):
            self.inputs.append(attrs)
        for key in ("href", "src"):
            if key in attrs:
                self.references.append(attrs[key])


def test_report_navigation_and_download_are_complete():
    page = ReportParser()
    page.feed((REPORT / "index.html").read_text())
    assert len(page.ids) == len(set(page.ids)), "Duplicate fragment targets"
    for reference in page.references:
        url = urlparse(reference)
        if url.scheme or url.netloc:
            continue
        if url.path:
            target = (ROOT / "landing" / url.path.lstrip("/")) if url.path.startswith("/") else (REPORT / url.path)
            if target.is_dir():
                target = target / "index.html"
            assert target.is_file(), reference
        elif url.fragment:
            assert url.fragment in page.ids, reference
    docx_path = ARTIFACTS_WAHS / "WAHS-OpenClinAI-Design-Report.docx"
    if docx_path.is_file():
        with ZipFile(docx_path) as document:
            assert document.testzip() is None
            assert "word/document.xml" in document.namelist()


def test_wahs_demo_accessibility_and_aria_tabpanel_wiring():
    """Accessibility invariant: unique IDs and reciprocal ARIA tab/tabpanel wiring on the demo app."""
    demo_page = ReportParser()
    demo_page.feed((DEMO / "index.html").read_text(encoding="utf-8"))
    assert len(demo_page.ids) == len(set(demo_page.ids)), "Duplicate element IDs in demo app"
    panel_by_id = {p.get("id"): p for p in demo_page.tabpanels if p.get("id")}
    assert len(demo_page.tabs) >= 3
    for tab in demo_page.tabs:
        target_id = tab.get("aria-controls")
        assert target_id in panel_by_id, f"Tab {tab.get('id')} missing tabpanel {target_id}"
        assert panel_by_id[target_id].get("aria-labelledby") == tab.get("id")
    for inp in demo_page.inputs:
        if inp.get("type") != "checkbox":
            assert inp.get("aria-label") or inp.get("id"), f"Unlabeled input: {inp}"


def test_wahs_demo_is_zero_business_logic_thin_shell():
    """Invariant: wahs/demo/index.html delegates all FHIR condensation, enrichers, and prompts to wahs-sandbox-engine."""
    demo_html = (DEMO / "index.html").read_text(encoding="utf-8")
    assert "/v1/wahs/demo-bundles" in demo_html
    assert "/v1/wahs/context/preview" in demo_html
    assert "/v1/chat/completions" in demo_html
    assert "/v1/wahs/profiles" in demo_html
    # Retired browser-side business logic, precomputed blob, and Cloud Run relay must stay removed
    for forbidden in (
        "wahs_demo_data-20261109.js",
        "wahs-gpu-auth-relay",
        "buildClientHubEnrichment",
        "buildActivePromptPayload",
        "SENSITIVE_SDOH_REGEX",
        "med-agent-hub",
    ):
        assert forbidden not in demo_html, f"Retired logic still referenced in wahs/demo/index.html: {forbidden}"

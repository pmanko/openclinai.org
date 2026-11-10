"""Check the shareable report's navigation, assets and optional host wiring."""

from html.parser import HTMLParser
import json
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


def test_wahs_demo_executable_data_integrity():
    """Integrity of executable data: demo app references immutable media bundle and local artifact parses cleanly when present."""
    demo_html = (DEMO / "index.html").read_text(encoding="utf-8")
    assert "https://storage.googleapis.com/openclinai-media/wahs/wahs_demo_data-20261109.js" in demo_html
    data_path = ARTIFACTS_WAHS / "wahs_demo_data.js"
    if not data_path.is_file():
        return
    raw_js = data_path.read_text(encoding="utf-8")
    prefix = "window.WAHS_DEMO_DATA = "
    idx = raw_js.find(prefix)
    assert idx != -1
    payload = json.loads(raw_js[idx + len(prefix) :].rstrip().rstrip(";"))
    persona_ids = payload.get("primary_persona_ids") or []
    patients = payload.get("patients") or {}
    assert len(persona_ids) >= 10
    assert "MIMIC_10014354_ICU_Heme_Cardiorenal_set_b" in persona_ids
    assert "MIMIC_10019003_ICU_Hepatopulmonary_set_b" in persona_ids
    high_volume_count = 0
    for pid in persona_ids:
        assert pid in patients
        p = patients[pid]
        assert p["fhir_browser"]["total_bundle_entries"] > 0
        assert len(p["fhir_browser"]["resources"]) > 0
        for mode in ("lossless_structural", "hierarchical"):
            for budget in ("262144", "131072", "65536", "32768", "16384", "8192", "4096", "2048", "1024"):
                cell = p["condensation_matrix"][mode][budget]
                assert cell["actual_tokens"] <= int(budget)
        if p["condensation_matrix"]["lossless_structural"]["262144"]["actual_tokens"] > 65536:
            high_volume_count += 1
        assert len(p["skills"]) >= 9
    assert high_volume_count >= 4

"""Public copy describes usable capabilities and reviewed evidence, not working notes."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def text(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_selected_research_has_no_unqualified_guarantees_or_writer_todos():
    selection = text("site/published-content.ts")
    paths = re.findall(r"'\.\./([^']+\.(?:md|canvas\.tsx))'", selection)
    assert "specs/background/why-local-first-clinical-ai.md" in paths
    assert "specs/artifacts/canvases/validation-research.canvas.tsx" in paths
    for path in paths:
        content = text(path)
        for obsolete in ("no cloud dependency", "all runnable locally", "Every claim traced to a specific record", "for any clinical-AI surface", "by tracing every answer", "step 1 is producing", "verify verbatim", "verify exact phrasing", "cite primary law text on any public page", "source sweep", "The home page makes a set of claims", "(quotable)"):
            assert obsolete not in content, (path, obsolete)
    background = text("specs/background/why-local-first-clinical-ai.md")
    research = text("specs/artifacts/planning/global-health-ai-background-research-2026-06-14.md")
    assert "selected adapter, scenarios and evaluation methods" in background
    assert "local or remote services" in research
    assert "disconnected operation depends" in background + research


def test_public_status_does_not_import_internal_inventories_or_narratives():
    main = text("site/status/main.tsx")
    model = text("site/status/model.ts")
    assert "Evaluation reports" in main
    assert "Reported findings" in main
    assert "Limitations" in main
    assert "component documentation" in main
    for obsolete in ("targets/validation-harness", "maintenance.md", "sessions.json", "sources.json", "efforts.json", "roadmaps.json", "reviews/2026-09-12", "reports/2026-09-06", "Codex & Claude", "Keeping it current", "clinical-ai-validation-harness/status/"):
        assert obsolete not in main + model
    fallback = text("site/status/index.html")
    assert "https://reports.openclinai.org/" in fallback
    assert "specs/artifacts/project-status/README.md" not in fallback


def test_website_docs_distinguish_configured_publication_from_a_live_release():
    assert "workflow is configured" in text("README.md")
    assert "configured for publication" in text("site/README.md")
    status = text("site/status/README.md")
    assert "Deployment destination:" in status
    assert "Local builds do\nnot publish" in status
    assert "Published dashboard:" not in status
    assert "former private Sites deployment" not in status

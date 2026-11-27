"""Behavioral end-to-end Playwright test for the thin-shell WAHS Sandbox connected to wahs-sandbox-engine."""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "wahs" / "demo"


class _StubSandboxEngineHandler(BaseHTTPRequestHandler):
    """Minimal stub for wahs-demo static UI + /api/engine/* endpoints."""

    auth_ok: bool = False
    captured_previews: list[dict] = []
    captured_chats: list[dict] = []

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def _json(self, status: int, payload: dict) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            data = (DEMO_DIR / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if parsed.path == "/api/engine/auth-check":
            if self.__class__.auth_ok:
                self._json(200, {"authenticated": True})
            else:
                self._json(401, {"error": {"code": "missing_session"}})
            return
        if parsed.path == "/api/engine/v1/models":
            self._json(
                200,
                {
                    "object": "list",
                    "data": [
                        {"id": "wahs-26b", "object": "model"},
                        {"id": "wahs-12b", "object": "model"},
                        {"id": "wahs-e4b", "object": "model"},
                    ],
                },
            )
            return
        if parsed.path == "/api/engine/v1/wahs/profiles":
            self._json(
                200,
                {
                    "default_model": "wahs-26b",
                    "default_profile": "core-enriched",
                    "default_target_budget_tokens": 16384,
                    "context_window": 65536,
                    "profiles": {
                        "core-enriched": {
                            "id": "core-enriched",
                            "label": "WAHS + Core Enrichers",
                            "enrichers": ["temporal", "terminology_kb", "note_rag", "overflow_lookup"],
                        }
                    },
                    "available_enrichers": [
                        {"id": "temporal", "label": "Temporal Anchor & Lab Trends", "short_label": "Temporal"},
                        {"id": "terminology_kb", "label": "CIEL & Public Standards Terminology KB", "short_label": "CIEL/Standards KB"},
                        {"id": "note_rag", "label": "Tier-2 Unseen-Span Note RAG", "short_label": "Note RAG"},
                        {"id": "overflow_lookup", "label": "Tier-2 Overflow Item Recovery", "short_label": "Overflow"},
                        {"id": "guideline_kb", "label": "Public Clinical Guideline Snippets [K1]", "short_label": "Guidelines [K1]"},
                    ],
                },
            )
            return
        if parsed.path == "/api/engine/v1/wahs/demo-bundles":
            self._json(
                200,
                {
                    "count": 2,
                    "bundles": [
                        {
                            "id": "margaret-chen-polypharmacy",
                            "filename": "Margaret_Chen_Polypharmacy.json",
                            "patient_name": "Margaret Chen",
                            "birth_date": "1943-11-03",
                            "gender": "female",
                            "size_kb": 351.0,
                            "total_resources": 448,
                            "clinical_resources": 440,
                            "counts_by_type": {"MedicationRequest": 12, "Observation": 200},
                            "sources": ["UW Medicine", "Overlake"],
                        },
                        {
                            "id": "maurice742-auer97",
                            "filename": "Maurice742_Auer97.json",
                            "patient_name": "Maurice742 Auer97",
                            "birth_date": "1973-03-25",
                            "gender": "male",
                            "size_kb": 22528.0,
                            "total_resources": 7099,
                            "clinical_resources": 7000,
                            "counts_by_type": {"Observation": 5000},
                            "sources": ["Synthea Longitudinal"],
                        },
                    ],
                },
            )
            return
        if parsed.path.startswith("/api/engine/v1/wahs/demo-bundles/") and parsed.path.endswith("/resources"):
            qs = parse_qs(parsed.query)
            if qs.get("resource_id"):
                self._json(
                    200,
                    {
                        "bundle_id": "margaret-chen-polypharmacy",
                        "resource": {
                            "resourceType": "MedicationRequest",
                            "id": "med-1",
                            "status": "active",
                            "medicationCodeableConcept": {"text": "Apixaban 5 mg oral tablet"},
                        },
                    },
                )
                return
            self._json(
                200,
                {
                    "bundle_id": "margaret-chen-polypharmacy",
                    "total_matching": 1,
                    "counts_by_type": {"MedicationRequest": 1},
                    "items": [
                        {
                            "key": "MedicationRequest/med-1",
                            "resourceType": "MedicationRequest",
                            "id": "med-1",
                            "date": "2026-10-01",
                            "display": "Apixaban 5 mg oral tablet",
                            "detail": "Take 1 tablet twice daily",
                            "status": "active",
                            "source": "UW Medicine",
                        }
                    ],
                },
            )
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or "0")
        body = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        if self.path == "/api/engine/v1/wahs/context/preview":
            self.__class__.captured_previews.append(body)
            wahs = body.get("wahs") or {}
            enrichers = wahs.get("enrichers") or []
            budget = wahs.get("target_budget_tokens") or 16384
            self._json(
                200,
                {
                    "patient_id": "pat-margaret",
                    "patient_name": "Margaret Chen",
                    "prefix_cache_key_hash": "abc123def456",
                    "chart_text": "[1] MedicationRequest (2026-10-01): Apixaban 5 mg oral tablet [active]",
                    "system_prompt": "WAHS Engine System Prompt\n=== CONDENSED CLINICAL RECORD ([1]..[N]) ===\n[1] Apixaban 5 mg",
                    "x_wahs": {
                        "citation_map": {
                            "1": {
                                "index": "1",
                                "resourceType": "MedicationRequest",
                                "id": "med-1",
                                "date": "2026-10-01",
                                "source": "UW Medicine",
                                "display": "Apixaban 5 mg oral tablet",
                            }
                        },
                        "condensation": {
                            "tier": 0 if budget >= 16384 else 2,
                            "tier_name": "verbatim" if budget >= 16384 else "compact_tables",
                            "actual_tokens": min(budget, 4200),
                            "budget_effective": budget,
                            "enrichment_tokens": len(enrichers) * 110,
                            "omitted_clinical_items": 0 if budget >= 16384 else 18,
                            "context_window": 65536,
                            "prefix_cache_key_hash": "abc123def456",
                            "cache_hit": len(self.__class__.captured_previews) > 1,
                        },
                        "enrichers": [{"id": e, "tokens": 110} for e in enrichers],
                        "enrichment_text": "=== ENRICHER FINDINGS ===\nNo duplicate anticoagulants." if enrichers else "",
                    },
                },
            )
            return

        if self.path == "/api/engine/v1/chat/completions":
            if not self.__class__.auth_ok:
                self._json(401, {"error": {"code": "missing_session"}})
                return
            self.__class__.captured_chats.append(body)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            frames = [
                {
                    "x_wahs": {
                        "event": "context_ready",
                        "citation_map": {
                            "1": {
                                "index": "1",
                                "resourceType": "MedicationRequest",
                                "id": "med-1",
                                "date": "2026-10-01",
                                "source": "UW Medicine",
                                "display": "Apixaban 5 mg oral tablet",
                            }
                        },
                    }
                },
                {"choices": [{"index": 0, "delta": {"content": "Your active anticoagulant is **Apixaban 5 mg** [1]."}}]},
                {
                    "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    "x_wahs": {"condensation": {"tier": 0, "actual_tokens": 4200, "enrichment_tokens": 440, "upstream_num_ctx": 65536}},
                },
            ]
            for frame in frames:
                self.wfile.write(f"data: {json.dumps(frame)}\n\n".encode("utf-8"))
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return

        self.send_response(404)
        self.end_headers()


class TestWahsSandboxThinShellE2E(unittest.TestCase):
    def _launch_chromium(self, p):
        try:
            return p.chromium.launch(headless=True)
        except Exception:
            try:
                return p.chromium.launch(headless=True, channel="chrome")
            except Exception as exc:
                self.skipTest(f"Chromium unavailable: {exc}")

    def test_step1_to_step3_zero_business_logic_sandbox_flow(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright is not installed in this Python environment")

        _StubSandboxEngineHandler.auth_ok = False
        _StubSandboxEngineHandler.captured_previews = []
        _StubSandboxEngineHandler.captured_chats = []

        server = ThreadingHTTPServer(("127.0.0.1", 0), _StubSandboxEngineHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{port}"

        try:
            with sync_playwright() as p:
                browser = self._launch_chromium(p)
                page = browser.new_page(viewport={"width": 1360, "height": 900})
                page.goto(f"{base_url}/", wait_until="domcontentloaded")

                # Step 1: Personas load live from /api/engine/v1/wahs/demo-bundles and raw FHIR row opens drawer
                page.wait_for_selector("#persona-grid .persona-card")
                self.assertEqual(page.locator("#persona-grid .persona-card").count(), 2)
                page.locator("#resource-table-body tr").first.click()
                self.assertTrue(page.locator("#inspector-backdrop").evaluate("el => el.classList.contains('open')"))
                page.wait_for_function("() => document.getElementById('inspector-json').textContent.includes('Apixaban 5 mg oral tablet')")
                page.click("#close-inspector-btn")

                # Step 2: Live engine preview + budget toggle + enricher Clear/Core shortcuts + system_prompt tab
                page.click("#phase-tab-2")
                page.wait_for_function("() => document.getElementById('m-tier').textContent.includes('Tier 0')")
                self.assertIn("Enrichers: 4/5 (Core)", page.locator("#step2-enricher-btn").inner_text())

                page.click('#step2-budget-group button[data-budget="4096"]')
                page.wait_for_function("() => document.getElementById('m-tier').textContent.includes('Tier 2')")

                page.click("#step2-enricher-btn")
                page.click('#step2-enricher-menu [data-enr-preset="clear"]')
                self.assertIn("0/5 (None)", page.locator("#step2-enricher-btn").inner_text())
                page.click('#step2-enricher-menu [data-enr-preset="core"]')
                self.assertIn("4/5 (Core)", page.locator("#step2-enricher-btn").inner_text())

                page.click('[data-preview-view="system"]')
                self.assertIn("WAHS Engine System Prompt", page.locator("#preview-code-output").inner_text())

                # Step 3: Unauthenticated banner visible when auth-check returns 401; suggested questions hidden by default
                page.click("#phase-tab-3")
                self.assertTrue(page.locator("#auth-gate-banner").is_visible())
                self.assertFalse(page.locator("#suggestions-drawer").is_visible())

                # Authenticate session and stream grounded reply with clickable [1] citation drawer
                _StubSandboxEngineHandler.auth_ok = True
                page.fill("#qa-question-input", "What anticoagulant am I taking?")
                page.click("#qa-submit-btn")
                page.wait_for_selector("#chat-log .cite-btn[data-cite-key='1']")
                self.assertIn("Apixaban 5 mg", page.locator("#chat-log").inner_text())
                self.assertIn("num_ctx:65536", page.locator("#chat-log").inner_text())
                self.assertEqual(_StubSandboxEngineHandler.captured_chats[-1]["wahs"]["bundle_id"], "margaret-chen-polypharmacy")

                page.locator("#chat-log .cite-btn[data-cite-key='1']").click()
                self.assertTrue(page.locator("#inspector-backdrop").evaluate("el => el.classList.contains('open')"))
                page.wait_for_function("() => document.getElementById('inspector-json').textContent.includes('Apixaban 5 mg oral tablet')")
                page.click("#close-inspector-btn")

                browser.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()

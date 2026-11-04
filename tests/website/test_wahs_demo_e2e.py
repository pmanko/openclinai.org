"""Behavioral end-to-end browser test for the WAHS Patient Chart Explorer and med-agent-hub contract."""

from __future__ import annotations

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
DEMO_DIR = ROOT / "landing" / "wahs" / "demo"


class _StubMedAgentHubHandler(BaseHTTPRequestHandler):
    """Minimal med-agent-hub HTTP server implementing /v1/models?workflow=wahs and SSE /v1/chat/completions."""

    captured_requests: list[dict] = []

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        return

    def _send_cors_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type, Authorization, X-OpenRouter-Key, HTTP-Referer, X-Title",
        )
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/v1/models":
            qs = parse_qs(parsed.query)
            workflow = (qs.get("workflow") or [""])[0]
            or_key = self.headers.get("X-OpenRouter-Key") or ""
            payload = {
                "object": "list",
                "workflow": workflow or "wahs",
                "data": [
                    {
                        "id": "wahs-12b-kb",
                        "label": "Gemma 4 12B (Q8) — + 4-Layer Clinical KB",
                        "workflow": "wahs",
                        "topology": "single",
                        "provider": "openrouter" if or_key else "local",
                        "openrouter_model": "google/gemma-3-12b-it",
                        "model_family": "gemma-4",
                        "available": True,
                        "visibility": "product",
                        "selection_priority": 10,
                        "stages": ["context", "answer", "gate"],
                        "role_models": {"answer": "gemma-4-12b"},
                        "role_knobs": {"answer": {"temperature": 0.1, "maxTokens": 900, "dry": 0.0}},
                        "policies": {
                            "provider": "openrouter" if or_key else "local",
                            "model_family": "gemma-4",
                            "include_kb_findings": True,
                            "overflow_lookup_tools": True,
                            "citation_grounding": "enforce",
                        },
                        "prompts": {"answer": "wahs-kb-guided"},
                        "system_prompts": {"answer": "You are the WAHS+ KB-Guided Assistant."},
                    },
                    {
                        "id": "wahs-12b-raw",
                        "label": "Gemma 4 12B (Q8) — Raw Condensed Chart Only",
                        "workflow": "wahs",
                        "topology": "single",
                        "provider": "openrouter" if or_key else "local",
                        "openrouter_model": "google/gemma-3-12b-it",
                        "model_family": "gemma-4",
                        "available": True,
                        "visibility": "product",
                        "selection_priority": 11,
                        "stages": ["context", "answer", "gate"],
                        "role_models": {"answer": "gemma-4-12b"},
                        "role_knobs": {"answer": {"temperature": 0.1, "maxTokens": 900, "dry": 0.0}},
                        "policies": {
                            "provider": "openrouter" if or_key else "local",
                            "model_family": "gemma-4",
                            "include_kb_findings": False,
                            "overflow_lookup_tools": False,
                            "citation_grounding": "enforce",
                        },
                        "prompts": {"answer": "wahs-raw-unhinted"},
                        "system_prompts": {"answer": "You are the WAHS+ Raw-Chart Control Assistant."},
                    },
                ],
            }
            body = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # Serve demo static files on the same server so both same-origin and cross-port work
        rel = parsed.path.lstrip("/")
        if not rel or rel == "wahs/demo" or rel == "wahs/demo/":
            target = DEMO_DIR / "index.html"
        elif rel.endswith("wahs_demo_data.js"):
            target = DEMO_DIR / "wahs_demo_data.js"
        else:
            target = DEMO_DIR / Path(rel).name
        if target.is_file():
            data = target.read_bytes()
            ctype = "text/html; charset=utf-8" if target.suffix == ".html" else "application/javascript; charset=utf-8"
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/v1/chat/completions":
            length = int(self.headers.get("Content-Length") or "0")
            raw_body = self.rfile.read(length).decode("utf-8")
            parsed_body = json.loads(raw_body)
            self.__class__.captured_requests.append(
                {
                    "headers": {k.lower(): v for k, v in self.headers.items()},
                    "body": parsed_body,
                }
            )
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()

            chunks = [
                "SUMMARY:\nGrounded synthesis confirming medication reconciliation [1] and recent lab values [2].\n\n",
                "QUESTIONS_FOR_DOCTOR:\n- Should I hold duplicate medication [1]?\n- When should we recheck labs [2]?\n",
            ]
            for text in chunks:
                pkt = {"choices": [{" index": 0, "delta": {"content": text}}]}
                self.wfile.write(f"data: {json.dumps(pkt)}\n\n".encode("utf-8"))
                self.wfile.flush()
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
            return

        self.send_response(404)
        self.end_headers()


class TestWahsDemoEndToEnd(unittest.TestCase):
    """Behavior: WAHS Patient Chart Explorer end-to-end happy path with med-agent-hub."""

    def test_wahs_demo_happy_path_step1_to_step3_with_med_agent_hub(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright is not installed in this Python environment")

        _StubMedAgentHubHandler.captured_requests = []
        server = ThreadingHTTPServer(("127.0.0.1", 0), _StubMedAgentHubHandler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base_url = f"http://127.0.0.1:{port}"

        try:
            with sync_playwright() as p:
                try:
                    browser = p.chromium.launch(headless=True)
                except Exception as exc:
                    self.skipTest(f"Chromium browser binary unavailable: {exc}")

                page = browser.new_page()
                # Pre-seed localStorage endpoint so the demo connects directly to our ephemeral Hub stub port
                page.add_init_script(
                    f"window.localStorage.setItem('wahs_llm_endpoint', '{base_url}');"
                )
                page.goto(f"{base_url}/", wait_until="domcontentloaded")
                page.wait_for_function(
                    "() => document.getElementById('llm-status-label') && document.getElementById('llm-status-label').textContent.includes('Hub Profile')"
                )

                # 1. Verify 10-persona grid (including PhysioNet MIMIC-IV-FHIR Demo 2.0 hospital/ICU patients)
                self.assertEqual(page.locator("#persona-grid .persona-pill-card").count(), 10)
                self.assertTrue(
                    page.locator('#persona-grid .persona-pill-card[data-pid="MIMIC_10014354_ICU_Heme_Cardiorenal_set_b"]').is_visible()
                )
                self.assertTrue(
                    page.locator('#persona-grid .persona-pill-card[data-pid="MIMIC_10019003_ICU_Hepatopulmonary_set_b"]').is_visible()
                )

                # Verify med-agent-hub profile discovery deduplicated -raw from #llm-model-select and exposed the main-app KB vs Raw toggle
                options = page.locator("#llm-model-select option").all_inner_texts()
                self.assertTrue(any("wahs-12b-kb" in opt for opt in options), options)
                self.assertFalse(any("wahs-12b-raw" in opt for opt in options), options)
                self.assertTrue(page.locator("#kb-mode-toggle-group").is_visible())

                # 2. Step 1 -> Step 2: verify 256k/128k/64k/32k budgets, lever info popovers, and change condensation budget to 2048 tokens
                page.click("#phase-tab-2")
                self.assertTrue(page.locator('#budget-lever-group button[data-budget="262144"]').is_visible())
                self.assertTrue(page.locator('#budget-lever-group button[data-budget="131072"]').is_visible())
                self.assertTrue(page.locator('#budget-lever-group button[data-budget="65536"]').is_visible())
                self.assertTrue(page.locator('#budget-lever-group button[data-budget="32768"]').is_visible())
                page.click('#budget-lever-group button[data-budget="262144"]')
                self.assertIn("256k", page.locator("#ctx-lever-chip").inner_text())
                page.click('#budget-lever-group button[data-budget="131072"]')
                self.assertIn("128k", page.locator("#ctx-lever-chip").inner_text())
                self.assertFalse(page.locator("#info-popover-budget").is_visible())
                page.click('button[data-info-target="info-popover-budget"]')
                self.assertTrue(page.locator("#info-popover-budget").is_visible())
                self.assertTrue(page.locator("#condense-how-it-works-details").is_visible())
                page.click('#budget-lever-group button[data-budget="2048"]')
                lever_chip_text = page.locator("#ctx-lever-chip").inner_text()
                self.assertIn("2k", lever_chip_text)

                # 3. Step 3 (-kb profile): verify compact task popover is closed by default,
                #    selecting a task auto-closes the popover without auto-firing completions,
                #    and #active-report-card is completely blank/hidden before clicking Generate Live
                page.click("#phase-tab-3")
                page.select_option("#llm-model-select", "wahs-12b-kb")
                self.assertFalse(page.locator("#task-mega-panel").is_visible())
                self.assertEqual(len(_StubMedAgentHubHandler.captured_requests), 0)
                self.assertFalse(page.locator("#active-report-card").is_visible())
                self.assertEqual(page.locator("#active-report-card").inner_text().strip(), "")

                # Verify suggestions appear on focus/click before typing, and are filtered when typing
                self.assertFalse(page.locator("#qa-suggestions-popover").is_visible())
                page.click("#qa-question-input")
                self.assertTrue(page.locator("#qa-suggestions-popover").is_visible())
                initial_suggest_count = page.locator("#qa-suggestions-popover .qa-suggestion-item").count()
                self.assertGreater(initial_suggest_count, 1)
                page.fill("#qa-question-input", "colonoscopy")
                page.dispatch_event("#qa-question-input", "input")
                self.assertTrue(page.locator("#qa-suggestions-popover").is_visible())
                filtered_suggest_count = page.locator("#qa-suggestions-popover .qa-suggestion-item").count()
                self.assertGreaterEqual(filtered_suggest_count, 1)
                self.assertLess(filtered_suggest_count, initial_suggest_count)
                page.fill("#qa-question-input", "")
                page.dispatch_event("#qa-question-input", "input")
                page.keyboard.press("Escape")
                self.assertFalse(page.locator("#qa-suggestions-popover").is_visible())

                # Open the 9-task popover, click a task tile, and verify popover auto-closes without auto-generation
                page.click("#task-mega-trigger")
                self.assertTrue(page.locator("#task-mega-panel").is_visible())
                page.click('.mega-task-tile[data-skill-id="skill-med-conflicts"]')
                self.assertFalse(page.locator("#task-mega-panel").is_visible())
                self.assertEqual(len(_StubMedAgentHubHandler.captured_requests), 0)
                self.assertFalse(page.locator("#active-report-card").is_visible())
                self.assertEqual(page.locator("#active-report-card").inner_text().strip(), "")

                # Trigger live generation explicitly and verify request + streamed UI output
                page.click("#qa-submit-btn")
                page.wait_for_function(
                    "() => document.getElementById('live-llm-summary-box') && document.getElementById('live-llm-summary-box').textContent.includes('Grounded synthesis confirming medication reconciliation')"
                )
                self.assertTrue(page.locator("#active-report-card").is_visible())
                self.assertFalse(
                    page.locator("#advanced-inspection-toggle").evaluate("el => el.open")
                )

                self.assertEqual(len(_StubMedAgentHubHandler.captured_requests), 1)
                kb_req = _StubMedAgentHubHandler.captured_requests[0]["body"]
                self.assertEqual(kb_req["model"], "wahs-12b-kb")
                self.assertTrue(kb_req["stream"])
                kb_prompt_blob = "\n".join(m.get("content", "") for m in kb_req["messages"])
                self.assertIn("2k", kb_prompt_blob)
                self.assertIn("4-Layer Clinical KB Findings", kb_prompt_blob)
                self.assertIn(
                    "[MED-AGENT-HUB ORCHESTRATION: CLINICAL ENTITY SUBGRAPH, QUESTION KB & TIER-0 OVERFLOW RECOVERY]",
                    kb_prompt_blob,
                )
                self.assertIn("Tier-0 Overflow Recovery", kb_prompt_blob)

                # Verify streamed follow-up questions and clickable [1] citation drawer round-trip
                questions_text = page.locator("#live-llm-questions-list").inner_text()
                self.assertIn("Should I hold duplicate medication", questions_text)
                page.locator('#live-llm-summary-box .inline-cite-badge[data-inline-cite="1"]').first.click()
                self.assertTrue(
                    page.locator("#citation-drawer-backdrop").evaluate("el => el.classList.contains('open')")
                )
                page.click("#close-citation-drawer-btn")

                # 4. Step 3 (Decoupled KB vs Raw toggle): verify #llm-model-select is deduplicated and clicking 📄 Raw Chart Only sends wahs-12b-raw & omits 4-Layer KB findings
                hub_model_opts = [
                    el.get_attribute("value")
                    for el in page.locator("#llm-model-select option").all()
                ]
                self.assertIn("wahs-12b-kb", hub_model_opts)
                self.assertNotIn("wahs-12b-raw", hub_model_opts)

                page.click('#kb-mode-toggle-group [data-kb-mode="raw"]')
                self.assertTrue(
                    page.locator('#kb-mode-toggle-group [data-kb-mode="raw"]').evaluate(
                        "el => el.classList.contains('active')"
                    )
                )
                self.assertTrue(
                    page.locator('#step2-kb-mode-group [data-kb-mode="raw"]').evaluate(
                        "el => el.classList.contains('active')"
                    )
                )
                page.click("#qa-submit-btn")
                for _ in range(30):
                    if len(_StubMedAgentHubHandler.captured_requests) >= 2:
                        break
                    page.wait_for_timeout(100)
                self.assertGreaterEqual(len(_StubMedAgentHubHandler.captured_requests), 2)
                raw_req = _StubMedAgentHubHandler.captured_requests[1]["body"]
                self.assertEqual(raw_req["model"], "wahs-12b-raw")
                raw_prompt_blob = "\n".join(m.get("content", "") for m in raw_req["messages"])
                self.assertIn("4-Layer Clinical KB Findings OMITTED", raw_prompt_blob)

                # 4b. Verify Step 2 & Step 3 Graphical Model Context Window Gauge + Generation Run History Dropdown
                self.assertTrue(page.locator("#step3-context-mini-gauge").is_visible())
                self.assertIn("Best-Perf: 24k", page.locator("#step3-context-mini-gauge").inner_text())
                self.assertIn("Max Window: 256k", page.locator("#step3-context-mini-gauge").inner_text())

                page.click("#phase-tab-2")
                self.assertTrue(page.locator("#model-context-gauge-card").is_visible())
                gauge_text = page.locator("#model-context-gauge-card").text_content() or ""
                self.assertIn("Suggested Best-Perf Limit: 24k", gauge_text)
                self.assertIn("Max Window: 256k", gauge_text)

                # Switch budget to 32k so total committed exceeds the 24k sweet spot -> Extended Context status
                page.click('#budget-lever-group .seg-btn[data-budget="32768"]')
                self.assertIn("Extended Context", page.locator("#gauge-posture-pill").inner_text())

                # Switch back to Step 3 and verify Run History dropdown recorded both runs and restores Run #1 context (2k budget + 🧠 +4-Layer KB)
                page.click("#phase-tab-3")
                self.assertTrue(page.locator("#gen-history-bar").is_visible())
                hist_options = page.locator("#gen-history-select option").all()
                self.assertEqual(len(hist_options), 2)
                first_run_id = hist_options[1].get_attribute("value")
                page.select_option("#gen-history-select", first_run_id)
                self.assertTrue(page.locator("#history-provenance-banner").is_visible())
                self.assertIn("2k • Lossless", page.locator("#history-provenance-banner").inner_text())
                self.assertTrue(
                    page.locator('#kb-mode-toggle-group [data-kb-mode="kb"]').evaluate(
                        "el => el.classList.contains('active')"
                    )
                )

                # 5. Connection Modal: verify ⓘ info tooltips on connection options and OpenRouter key shown ONLY when OpenRouter is selected
                page.click("#open-llm-config-btn")
                self.assertFalse(page.locator("#openrouter-api-key-input").is_visible())
                self.assertEqual(page.locator(".conn-preset-info-btn").count(), 7)

                # Clicking ⓘ on Cloud Med Agent Hub opens its info tooltip without switching away from Local Hub
                page.click(".conn-preset-info-btn[data-conn-info='cloud_hub']")
                self.assertTrue(page.locator("#conn-info-cloud_hub").is_visible())
                self.assertIn("UW CIRG GPU", page.locator("#conn-info-cloud_hub").inner_text())
                self.assertTrue(
                    page.locator("#preset-hub-llm-btn").evaluate("el => el.classList.contains('active')")
                )

                # Selecting OpenRouter reveals the OpenRouter API Key input; switching back to Local Hub hides it again
                page.click("#preset-openrouter-llm-btn")
                self.assertTrue(page.locator("#openrouter-api-key-input").is_visible())
                page.click("#preset-hub-llm-btn")
                self.assertFalse(page.locator("#openrouter-api-key-input").is_visible())

                browser.close()
        finally:
            server.shutdown()
            server.server_close()

    def test_safari_https_origin_routes_local_presets_to_tls_bridge(self) -> None:
        """Behavior: On an https:// origin in Safari, local HTTP presets route through SAFARI_HTTPS_BRIDGE_MAP."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright is not installed in this Python environment")

        index_html = (DEMO_DIR / "index.html").read_text(encoding="utf-8")
        demo_data_js = (DEMO_DIR / "wahs_demo_data.js").read_text(encoding="utf-8")
        probed_urls: list[str] = []

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                self.skipTest(f"Chromium browser binary unavailable: {exc}")

            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.2 Safari/605.1.15"
                )
            )
            page = context.new_page()

            def handle_route(route) -> None:
                url = route.request.url
                if url == "https://wahs-demo.openclinai.org/":
                    route.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_html)
                elif url.endswith("/wahs_demo_data.js"):
                    route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=demo_data_js)
                elif "/v1/models" in url or "/api/v0/models" in url:
                    probed_urls.append(url)
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=json.dumps(
                            {
                                "object": "list",
                                "workflow": "wahs",
                                "data": [
                                    {
                                        "id": "wahs-12b-kb",
                                        "label": "Gemma 4 12B (Q8) — + 4-Layer Clinical KB",
                                        "workflow": "wahs",
                                        "available": True,
                                        "visibility": "product",
                                        "selection_priority": 10,
                                        "policies": {"include_kb_findings": True},
                                    }
                                ],
                            }
                        ),
                    )
                else:
                    route.abort()

            page.route("**/*", handle_route)
            page.goto("https://wahs-demo.openclinai.org/", wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label') && document.getElementById('llm-status-label').textContent.includes('Hub Profile')"
            )
            self.assertTrue(
                any(u.startswith("https://127.0.0.1:18443/v1/models") for u in probed_urls),
                probed_urls,
            )

            # Clicking the LM Studio preset in Safari on HTTPS immediately connects and upgrades to :1236
            page.click("#open-llm-config-btn")
            page.click("#preset-lmstudio-llm-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-endpoint-input').value === 'https://127.0.0.1:1236'"
            )
            self.assertTrue(
                page.locator("#preset-lmstudio-llm-btn").evaluate("el => el.classList.contains('active')")
            )
            self.assertTrue(
                any(u.startswith("https://127.0.0.1:1236/") for u in probed_urls),
                probed_urls,
            )
            browser.close()

    def test_lm_studio_and_llama_router_direct_happy_paths(self) -> None:
        """Behavior: Direct LM Studio (:1235) and llama-router (:8077) presets connect on click, highlight active preset, filter non-ready/audio models, prioritize gemma-4-12b, and disable thinking burn."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright is not installed in this Python environment")

        index_html = (DEMO_DIR / "index.html").read_text(encoding="utf-8")
        demo_data_js = (DEMO_DIR / "wahs_demo_data.js").read_text(encoding="utf-8")
        captured_completions: list[dict] = []

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                self.skipTest(f"Chromium browser binary unavailable: {exc}")

            page = browser.new_page()

            def handle_route(route) -> None:
                url = route.request.url
                if url == "https://wahs-demo.openclinai.org/":
                    route.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_html)
                elif url.endswith("/wahs_demo_data.js"):
                    route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=demo_data_js)
                elif url.startswith("http://127.0.0.1:1235/api/v0/models"):
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=json.dumps(
                            {
                                "object": "list",
                                "data": [
                                    {
                                        "id": "phonon-40m-multilingual",
                                        "type": "llm",
                                        "publisher": "model-extension-pack",
                                        "state": "loaded",
                                    },
                                    {
                                        "id": "text-embedding-nomic-embed-text-v1.5",
                                        "type": "embeddings",
                                        "state": "not-loaded",
                                    },
                                    {
                                        "id": "gemma-4-e2b-it",
                                        "type": "llm",
                                        "publisher": "unsloth",
                                        "state": "loaded",
                                    },
                                ],
                            }
                        ),
                    )
                elif url.startswith("http://127.0.0.1:8077/v1/models"):
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=json.dumps(
                            {
                                "object": "list",
                                "data": [
                                    {
                                        "id": "gemma-e2b",
                                        "owned_by": "llamacpp",
                                        "status": {"value": "loaded"},
                                    },
                                    {
                                        "id": "gemma-4-12b",
                                        "owned_by": "llamacpp",
                                        "status": {"value": "unloaded"},
                                    },
                                    {
                                        "id": "qwen2.5-32b",
                                        "owned_by": "llamacpp",
                                        "status": {"value": "unloaded"},
                                    },
                                ],
                            }
                        ),
                    )
                elif url.endswith("/v1/chat/completions"):
                    body = json.loads(route.request.post_data or "{}")
                    captured_completions.append({"url": url, "body": body})
                    sse = (
                        'data: {"choices":[{"index":0,"delta":{"content":"SUMMARY:\\nDirect model synthesis [1].\\n\\nQUESTIONS_FOR_DOCTOR:\\n- Follow up on [1]?\\n"}}]}\n\n'
                        "data: [DONE]\n\n"
                    )
                    route.fulfill(
                        status=200,
                        content_type="text/event-stream",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=sse,
                    )
                else:
                    route.abort()

            page.route("**/*", handle_route)
            page.goto("https://wahs-demo.openclinai.org/", wait_until="domcontentloaded")

            # 1. Clicking LM Studio preset immediately connects and marks the preset active
            page.click("#open-llm-config-btn")
            page.click("#preset-lmstudio-llm-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('LM Studio')"
            )
            self.assertTrue(
                page.locator("#preset-lmstudio-llm-btn").evaluate("el => el.classList.contains('active')")
            )
            self.assertFalse(
                page.locator("#preset-hub-llm-btn").evaluate("el => el.classList.contains('active')")
            )
            page.click("#close-llm-modal-btn")

            lm_options = [
                el.get_attribute("value")
                for el in page.locator("#llm-model-select option").all()
            ]
            # phonon and embeddings filtered out; gemma-4-e2b-it exposed once without duplicate wahs-raw: row
            self.assertIn("gemma-4-e2b-it", lm_options)
            self.assertNotIn("wahs-raw:gemma-4-e2b-it", lm_options)
            self.assertNotIn("phonon-40m-multilingual", lm_options)
            self.assertNotIn("text-embedding-nomic-embed-text-v1.5", lm_options)

            # Generate Live in Raw mode on LM Studio via main-app KB toggle and verify upstream model ID + thinking disabled
            page.click("#phase-tab-3")
            page.select_option("#llm-model-select", "gemma-4-e2b-it")
            page.click('#kb-mode-toggle-group [data-kb-mode="raw"]')
            page.click("#qa-submit-btn")
            for _ in range(30):
                if len(captured_completions) >= 1:
                    break
                page.wait_for_timeout(100)
            self.assertEqual(len(captured_completions), 1)
            lm_req = captured_completions[0]["body"]
            self.assertEqual(lm_req["model"], "gemma-4-e2b-it")
            self.assertEqual(lm_req.get("reasoning_effort"), "none")
            self.assertEqual(lm_req.get("chat_template_kwargs"), {"enable_thinking": False})
            lm_prompt = "\n".join(m.get("content", "") for m in lm_req["messages"])
            self.assertIn("4-Layer Clinical KB Findings OMITTED", lm_prompt)

            # 2. Clicking Local llama-router preset immediately connects, marks router active, and selects gemma-4-12b over gemma-e2b
            page.click("#open-llm-config-btn")
            page.click("#preset-local-llm-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('Local Router')"
            )
            self.assertTrue(
                page.locator("#preset-local-llm-btn").evaluate("el => el.classList.contains('active')")
            )
            self.assertEqual(page.locator("#llm-model-select").input_value(), "gemma-4-12b")
            router_options = [
                el.get_attribute("value")
                for el in page.locator("#llm-model-select option").all()
            ]
            self.assertIn("gemma-4-12b", router_options)
            self.assertNotIn("wahs-raw:gemma-4-12b", router_options)
            # Undownloaded preset qwen2.5-32b is excluded by READY_ROUTER_MODELS check
            self.assertNotIn("qwen2.5-32b", router_options)

            # 3. Typing in the custom endpoint box immediately resets indicator to Unverified, and Test Connection verifies in place before Apply closes
            page.fill("#llm-endpoint-input", "http://127.0.0.1:1235")
            self.assertIn("Unverified", page.locator("#llm-status-label").inner_text())
            self.assertIn("Unverified", page.locator("#llm-modal-status-box").inner_text())
            page.click("#test-llm-endpoint-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('LM Studio')"
            )
            self.assertTrue(
                page.locator("#llm-config-modal").evaluate("el => el.classList.contains('open')")
            )
            page.click("#save-llm-endpoint-btn")
            self.assertFalse(
                page.locator("#llm-config-modal").evaluate("el => el.classList.contains('open')")
            )

            browser.close()

    def test_gpu_server_preset_is_config_toggleable_and_enforces_google_account_whitelist(self):
        """Verify UW GPU Server preset is hidden by default, enabled via ?gpu=1, and enforces the Google account whitelist."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("playwright is not installed in this Python environment")

        index_html = (DEMO_DIR / "index.html").read_text(encoding="utf-8")
        demo_data_js = (DEMO_DIR / "wahs_demo_data.js").read_text(encoding="utf-8")

        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
            except Exception as exc:
                self.skipTest(f"Chromium browser binary unavailable: {exc}")

            page = browser.new_page(viewport={"width": 1440, "height": 900})

            def handle_route(route) -> None:
                url = route.request.url
                if url in (
                    "https://wahs-demo.openclinai.org/",
                    "https://wahs-demo.openclinai.org/?gpu=1",
                    "https://wahs-demo.openclinai.org/?gpu=0",
                ):
                    route.fulfill(status=200, content_type="text/html; charset=utf-8", body=index_html)
                elif "/wahs_demo_data.js" in url:
                    route.fulfill(status=200, content_type="application/javascript; charset=utf-8", body=demo_data_js)
                elif "wahs-gpu-auth-relay" in url and "/v1/models" in url:
                    headers = {k.lower(): v for k, v in route.request.headers.items()}
                    auth_hdr = headers.get("authorization", "")
                    token = headers.get("x-wahs-auth-token") or (
                        auth_hdr[7:].strip() if auth_hdr.lower().startswith("bearer ") else ""
                    )
                    if not token:
                        route.fulfill(
                            status=401,
                            content_type="application/json",
                            headers={"Access-Control-Allow-Origin": "*"},
                            body=json.dumps({
                                "error": {
                                    "code": "missing_token",
                                    "message": "Sign in with a whitelisted Google account to access the shared GPU server.",
                                }
                            }),
                        )
                        return
                    if token == "non-whitelisted-token":
                        route.fulfill(
                            status=403,
                            content_type="application/json",
                            headers={"Access-Control-Allow-Origin": "*"},
                            body=json.dumps({
                                "error": {
                                    "code": "not_whitelisted",
                                    "email": "intruder@example.com",
                                    "message": "Signed in as intruder@example.com, which is not on the GPU server whitelist.",
                                }
                            }),
                        )
                        return
                    if "/hub/v1/models" in url:
                        route.fulfill(
                            status=200,
                            content_type="application/json",
                            headers={"Access-Control-Allow-Origin": "*"},
                            body=json.dumps({
                                "object": "list",
                                "workflow": "wahs",
                                "data": [
                                    {
                                        "id": "wahs-12b-kb",
                                        "object": "model",
                                        "owned_by": "med-agent-hub",
                                        "workflow": "wahs",
                                        "label": "Gemma 4 12B (Q8) — + 4-Layer Clinical KB",
                                        "available": True,
                                        "visibility": "product",
                                        "model_family": "gemma-4",
                                    }
                                ],
                                "backend": {
                                    "service": "wahs-gpu-auth-relay",
                                    "gpu_auth": {
                                        "authenticated": True,
                                        "authorized": True,
                                        "email": "piotr.mankowski@gmail.com",
                                    }
                                },
                            }),
                        )
                        return
                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=json.dumps({
                            "object": "list",
                            "data": [
                                {
                                    "id": "ollama/gemma4:12b",
                                    "object": "model",
                                    "owned_by": "uw-cirg-gpu",
                                    "label": "Gemma 4 12B (UW GPU)",
                                    "model_family": "gemma-4",
                                },
                                {
                                    "id": "ollama/gemma4:e4b",
                                    "object": "model",
                                    "owned_by": "uw-cirg-gpu",
                                    "label": "Gemma 4 E4B (UW GPU)",
                                    "model_family": "gemma-4",
                                },
                            ],
                            "backend": {
                                "service": "wahs-gpu-auth-relay",
                                "gpu_auth": {
                                    "authenticated": True,
                                    "authorized": True,
                                    "email": "piotr.mankowski@gmail.com",
                                }
                            },
                        }),
                    )
                elif "wahs-gpu-auth-relay" in url and "/hub/v1/chat/completions" in url:
                    headers = {k.lower(): v for k, v in route.request.headers.items()}
                    # Ensure Cloud Med Agent Hub never receives an X-OpenRouter-Key header
                    self.assertNotIn("x-openrouter-key", headers)
                    sse_body = (
                        'data: {"choices":[{"delta":{"content":"SUMMARY:\\n- Cloud Med Agent Hub (UW GPU) live summary verified [1].\\n\\nQUESTIONS_FOR_DOCTOR:\\n- Should we review my latest visit notes?"}}]}\n\n'
                        "data: [DONE]\n\n"
                    )
                    route.fulfill(
                        status=200,
                        content_type="text/event-stream",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=sse_body,
                    )
                elif url.startswith("http://127.0.0.1:18081/v1/models"):

                    route.fulfill(
                        status=200,
                        content_type="application/json",
                        headers={"Access-Control-Allow-Origin": "*"},
                        body=json.dumps({
                            "object": "list",
                            "workflow": "wahs",
                            "data": [
                                {
                                    "id": "wahs-12b-kb",
                                    "label": "Gemma 4 12B (Q8) — + 4-Layer Clinical KB",
                                    "available": True,
                                    "default": True,
                                }
                            ],
                        }),
                    )
                else:
                    route.abort()

            page.route("**/*", handle_route)

            # 1. Load with ?gpu=0: both Cloud Hub and GPU preset buttons are hidden when explicitly disabled
            page.goto("https://wahs-demo.openclinai.org/?gpu=0", wait_until="domcontentloaded")
            page.click("#open-llm-config-btn")
            self.assertFalse(page.locator("#preset-gpu-llm-btn").is_visible())
            self.assertFalse(page.locator("#preset-cloud-hub-llm-btn").is_visible())

            # 2. Default load: both Cloud Med Agent Hub and UW GPU Server preset buttons are cleanly visible
            page.goto("https://wahs-demo.openclinai.org/", wait_until="domcontentloaded")
            page.click("#open-llm-config-btn")
            self.assertTrue(page.locator("#preset-gpu-llm-btn").is_visible())
            self.assertTrue(page.locator("#preset-cloud-hub-llm-btn").is_visible())

            # 3. Clicking GPU preset without Google auth returns 401 and renders 1-click Google Sign-In button (no token box)
            page.click("#preset-gpu-llm-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('Sign In')"
            )
            self.assertTrue(page.locator("#google-signin-popup-btn").is_visible())
            self.assertEqual(page.locator("#google-auth-token-input").count(), 0)

            # 4. Signing in with a non-whitelisted Google account returns 403 and renders Not Whitelisted state
            page.evaluate(
                "window.WAHS_GOOGLE_SIGNIN_HANDLER = async () => ({ token: 'non-whitelisted-token', email: 'intruder@example.com' });"
            )
            page.click("#google-signin-popup-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('Not Whitelisted')"
            )
            self.assertIn("intruder@example.com", page.locator("#llm-modal-status-box").inner_text())

            # 5. Signing in with a whitelisted Google account connects to UW GPU Server and displays verified email
            page.evaluate(
                "window.WAHS_GOOGLE_SIGNIN_HANDLER = async () => ({ token: 'whitelisted-token', email: 'piotr.mankowski@gmail.com' });"
            )
            page.click("#google-signin-popup-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('UW GPU')"
            )
            self.assertIn("piotr.mankowski@gmail.com", page.locator("#llm-modal-status-box").inner_text())
            self.assertTrue(page.locator("#signout-gpu-google-btn").is_visible())

            # 6. Switching to Cloud Med Agent Hub reuses verified Google session, hides OpenRouter key row, and streams live WAHS+ Hub completions
            page.evaluate("sessionStorage.setItem('wahs_openrouter_key', 'sk-or-v1-stale-key');")
            page.click("#preset-cloud-hub-llm-btn")
            page.wait_for_function(
                "() => document.getElementById('llm-status-label').textContent.includes('Cloud Hub (UW GPU')"
            )
            self.assertFalse(page.locator("#openrouter-api-key-input").is_visible())
            self.assertIn("Cloud Med Agent Hub (UW GPU)", page.locator("#llm-modal-status-box").inner_text())
            self.assertEqual(page.locator("#llm-model-select").input_value(), "wahs-12b-kb")
            page.click("#close-llm-modal-btn")
            page.click("[data-phase='3']")
            page.click("#qa-submit-btn")
            page.wait_for_function(
                "() => document.getElementById('active-report-card').textContent.includes('Cloud Med Agent Hub (UW GPU) live summary verified')"
            )

            browser.close()


if __name__ == "__main__":
    unittest.main()

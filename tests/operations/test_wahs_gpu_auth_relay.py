"""Behavior tests for the standalone WAHS UW GPU Auth Relay (`wahs/gpu-auth-relay/app.py`)."""

from __future__ import annotations

import importlib.util
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "wahs" / "gpu-auth-relay" / "app.py"


def _load_relay_module():
    spec = importlib.util.spec_from_file_location("wahs_gpu_auth_relay_app", APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _http_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[int, Dict[str, Any], Dict[str, str]]:
    req_headers = dict(headers or {})
    data = None
    if payload is not None:
        req_headers["Content-Type"] = "application/json"
        data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
            return exc.code, body, dict(exc.headers)
        finally:
            exc.close()


class _StubLiteLLMHandler(BaseHTTPRequestHandler):
    last_chat_payload: Optional[Dict[str, Any]] = None
    last_auth_header: str = ""

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        if self.path == "/v1/models" or self.path.startswith("/v1/models?"):
            raw = json.dumps(
                {
                    "object": "list",
                    "workflow": "wahs" if "workflow=wahs" in self.path else None,
                    "data": [
                        {"id": "all-proxy-models", "object": "model"},
                        {"id": "ollama/mistral:7b", "object": "model"},
                        {
                            "id": "wahs-12b-kb",
                            "object": "model",
                            "owned_by": "med-agent-hub",
                            "workflow": "wahs",
                            "available": True,
                            "visibility": "product",
                        },
                    ],
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(404)
        self.end_headers()

    def do_POST(self) -> None:
        if self.path == "/v1/chat/completions":
            _StubLiteLLMHandler.last_auth_header = self.headers.get("Authorization") or ""
            length = int(self.headers.get("Content-Length") or "0")
            body = json.loads(self.rfile.read(length).decode("utf-8"))
            _StubLiteLLMHandler.last_chat_payload = body
            raw = json.dumps(
                {
                    "id": "chatcmpl-stub",
                    "object": "chat.completion",
                    "model": body.get("model"),
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "SUMMARY:\nStubbed UW GPU response [1].",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                }
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        self.send_response(404)
        self.end_headers()


class WahsGpuAuthRelayTests(unittest.TestCase):
    def setUp(self) -> None:
        self.relay = _load_relay_module()
        self.upstream_server = ThreadingHTTPServer(("127.0.0.1", 0), _StubLiteLLMHandler)
        self.upstream_port = self.upstream_server.server_address[1]
        self.upstream_thread = threading.Thread(
            target=self.upstream_server.serve_forever, daemon=True
        )
        self.upstream_thread.start()

        self.relay_server = self.relay.create_server("127.0.0.1", 0)
        self.relay_port = self.relay_server.server_address[1]
        self.relay_url = f"http://127.0.0.1:{self.relay_port}"
        self.relay_thread = threading.Thread(
            target=self.relay_server.serve_forever, daemon=True
        )
        self.relay_thread.start()

    def tearDown(self) -> None:
        self.relay_server.shutdown()
        self.relay_server.server_close()
        self.upstream_server.shutdown()
        self.upstream_server.server_close()

    def test_unauthenticated_models_returns_401(self) -> None:
        """Behavior: /v1/models rejects requests without a Google token with HTTP 401."""
        status, body, _ = _http_request(f"{self.relay_url}/v1/models")
        self.assertEqual(status, 401)
        err = body["error"]
        self.assertEqual(err["code"], "missing_token")
        self.assertFalse(err["authenticated"])
        self.assertFalse(err["authorized"])

    def test_non_whitelisted_account_returns_403(self) -> None:
        """Behavior: /v1/models rejects a signed-in non-whitelisted Google email with HTTP 403."""
        with patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "1",
                "WAHS_GPU_BASE_URL": f"http://127.0.0.1:{self.upstream_port}",
                "WAHS_GPU_API_KEY": "sk-test-upstream",
            },
        ):
            status, body, _ = _http_request(
                f"{self.relay_url}/v1/models",
                headers={"X-Google-Auth-Token": "test-google-token:intruder@example.com"},
            )
            self.assertEqual(status, 403)
            err = body["error"]
            self.assertEqual(err["code"], "not_whitelisted")
            self.assertEqual(err["email"], "intruder@example.com")
            self.assertTrue(err["authenticated"])
            self.assertFalse(err["authorized"])

    def test_whitelisted_accounts_can_list_models_and_complete_chat(self) -> None:
        """Behavior: all 7 whitelisted emails pass auth, receive pulled GPU models, and proxy chat."""
        with patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "1",
                "WAHS_GPU_BASE_URL": f"http://127.0.0.1:{self.upstream_port}",
                "WAHS_GPU_API_KEY": "sk-test-upstream",
            },
        ):
            for email in (
                "piotr.mankowski@gmail.com",
                "pmanko@uw.edu",
                "ivanc@uw.edu",
                "mcjustin@uw.edu",
                "jflow2@uw.edu",
                "lober@uw.edu",
                "ibacher@uw.edu",
            ):
                with self.subTest(email=email):
                    status, body, _ = _http_request(
                        f"{self.relay_url}/v1/models",
                        headers={"X-Google-Auth-Token": f"test-google-token:{email}"},
                    )
                    self.assertEqual(status, 200)
                    model_ids = [m["id"] for m in body["data"]]
                    self.assertIn("ollama/gemma4:26b", model_ids)
                    self.assertIn("ollama/gemma4:12b", model_ids)
                    self.assertIn("ollama/gemma4:e4b", model_ids)
                    self.assertIn("ollama/gemma4:e2b", model_ids)
                    self.assertIn("ollama/qwen3:14b", model_ids)
                    self.assertIn("ollama/qwen2.5:14b", model_ids)
                    self.assertIn("ollama/qwen3:8b", model_ids)
                    self.assertIn("ollama/qwen3:4b", model_ids)
                    self.assertIn("ollama/llama3.1:8b", model_ids)
                    self.assertIn("ollama/mistral-nemo:12b", model_ids)
                    self.assertIn("ollama/mistral:7b", model_ids)
                    self.assertIn("ollama/granite3.3:8b", model_ids)
                    self.assertIn("ollama/smollm2:latest", model_ids)
                    self.assertNotIn("all-proxy-models", model_ids)
                    self.assertEqual(body["backend"]["gpu_auth"]["email"], email)

            c_status, c_body, _ = _http_request(
                f"{self.relay_url}/v1/chat/completions",
                method="POST",
                headers={"X-Google-Auth-Token": "test-google-token:pmanko@uw.edu"},
                payload={
                    "model": "wahs-kb:ollama/gemma4:12b",
                    "messages": [{"role": "user", "content": "Check warfarin."}],
                    "stream": False,
                },
            )
            self.assertEqual(c_status, 200)
            self.assertEqual(_StubLiteLLMHandler.last_auth_header, "Bearer sk-test-upstream")
            assert _StubLiteLLMHandler.last_chat_payload is not None
            self.assertEqual(
                _StubLiteLLMHandler.last_chat_payload["model"], "ollama/gemma4:12b"
            )
            self.assertEqual(
                _StubLiteLLMHandler.last_chat_payload["reasoning_effort"], "none"
            )
            self.assertIn("Stubbed UW GPU response", c_body["choices"][0]["message"]["content"])

    def test_cloud_hub_and_internal_router_bridge(self) -> None:
        """Behavior: /internal-router maps Hub aliases to UW GPU models, and /hub enforces Google whitelist before proxying to Cloud Hub."""
        with patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "1",
                "WAHS_GPU_BASE_URL": f"http://127.0.0.1:{self.upstream_port}",
                "WAHS_GPU_API_KEY": "sk-test-upstream",
                "WAHS_CLOUD_HUB_URL": f"http://127.0.0.1:{self.upstream_port}",
                "WAHS_INTERNAL_ROUTER_KEY": "secret-internal-router-key",
            },
        ):
            # 1. Unauthenticated /internal-router is rejected when key is set
            ir_unauth_status, _, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/models"
            )
            self.assertEqual(ir_unauth_status, 401)

            # 2. Authenticated /internal-router advertises Hub router aliases
            ir_status, ir_body, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/models",
                headers={"Authorization": "Bearer secret-internal-router-key"},
            )
            self.assertEqual(ir_status, 200)
            ir_ids = [m["id"] for m in ir_body["data"]]
            self.assertIn("gemma-4-12b", ir_ids)
            self.assertIn("gemma-e4b", ir_ids)
            self.assertIn("gemma-e2b", ir_ids)
            self.assertIn("mistral-nemo-12b", ir_ids)

            # 3. /internal-router/v1/chat/completions translates gemma-4-12b -> ollama/gemma4:12b
            ir_chat_status, _, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/chat/completions",
                method="POST",
                headers={"Authorization": "Bearer secret-internal-router-key"},
                payload={
                    "model": "gemma-4-12b",
                    "messages": [{"role": "user", "content": "Test internal router"}],
                    "stream": False,
                },
            )
            self.assertEqual(ir_chat_status, 200)
            assert _StubLiteLLMHandler.last_chat_payload is not None
            self.assertEqual(
                _StubLiteLLMHandler.last_chat_payload["model"], "ollama/gemma4:12b"
            )

            # 4. /hub/v1/models rejects unauthenticated and non-whitelisted callers
            hub_unauth, _, _ = _http_request(
                f"{self.relay_url}/hub/v1/models?workflow=wahs"
            )
            self.assertEqual(hub_unauth, 401)
            hub_forbid, _, _ = _http_request(
                f"{self.relay_url}/hub/v1/models?workflow=wahs",
                headers={"X-Google-Auth-Token": "test-google-token:nobody@example.com"},
            )
            self.assertEqual(hub_forbid, 403)

            # 5. /hub/v1/models allows whitelisted user and attaches gpu_auth metadata
            hub_ok, hub_body, _ = _http_request(
                f"{self.relay_url}/hub/v1/models?workflow=wahs",
                headers={"X-Google-Auth-Token": "test-google-token:mcjustin@uw.edu"},
            )
            self.assertEqual(hub_ok, 200)
            self.assertEqual(
                hub_body["backend"]["gpu_auth"]["email"], "mcjustin@uw.edu"
            )

    def test_internal_router_fails_closed_when_key_unset(self) -> None:
        """Behavior: /internal-router fails closed (HTTP 401) when WAHS_INTERNAL_ROUTER_KEY is unset unless an authorized Google token is supplied."""
        with patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "1",
                "WAHS_GPU_BASE_URL": f"http://127.0.0.1:{self.upstream_port}",
                "WAHS_GPU_API_KEY": "sk-test-upstream",
                "WAHS_INTERNAL_ROUTER_KEY": "",
            },
        ):
            unauth_models_status, _, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/models"
            )
            self.assertEqual(unauth_models_status, 401)

            unauth_chat_status, _, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/chat/completions",
                method="POST",
                payload={
                    "model": "gemma-4-12b",
                    "messages": [{"role": "user", "content": "Unauthenticated attempt"}],
                },
            )
            self.assertEqual(unauth_chat_status, 401)

            # Whitelisted Google token is still permitted
            auth_models_status, _, _ = _http_request(
                f"{self.relay_url}/internal-router/v1/models",
                headers={"X-Google-Auth-Token": "test-google-token:pmanko@uw.edu"},
            )
            self.assertEqual(auth_models_status, 200)

    def test_verify_google_auth_token_enforces_audience_even_with_sub_claim(self) -> None:
        """Behavior: verify_google_auth_token rejects Google ID tokens whose aud mismatches WAHS_GOOGLE_CLIENT_ID even when sub is present."""
        self.relay._TOKEN_CACHE.clear()
        with patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "0",
                "WAHS_GOOGLE_CLIENT_ID": "expected-client-id.apps.googleusercontent.com",
            },
        ):
            with patch.object(
                self.relay,
                "_http_get_json",
                return_value={
                    "email": "pmanko@uw.edu",
                    "email_verified": "true",
                    "sub": "112233445566778899",
                    "aud": "foreign-client-id.apps.googleusercontent.com",
                },
            ):
                verdict_bad = self.relay.verify_google_auth_token("tok-foreign-aud")
                self.assertFalse(verdict_bad["authenticated"])
                self.assertFalse(verdict_bad["authorized"])
                self.assertEqual(verdict_bad["code"], "audience_mismatch")

            self.relay._TOKEN_CACHE.clear()
            with patch.object(
                self.relay,
                "_http_get_json",
                return_value={
                    "email": "pmanko@uw.edu",
                    "email_verified": "true",
                    "sub": "112233445566778899",
                    "aud": "expected-client-id.apps.googleusercontent.com",
                },
            ):
                verdict_ok = self.relay.verify_google_auth_token("tok-matching-aud")
                self.assertTrue(verdict_ok["authenticated"])
                self.assertTrue(verdict_ok["authorized"])
                self.assertEqual(verdict_ok["code"], "ok")


if __name__ == "__main__":
    unittest.main()

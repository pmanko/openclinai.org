"""Unit tests for the WAHS Cloud Auth Gate & Portal (`wahs/cloud-gate/app.py`)."""

from __future__ import annotations

import http.client
import importlib.util
import json
import os
import threading
import unittest
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
APP_PATH = ROOT / "wahs" / "cloud-gate" / "app.py"


def _load_gate_module():
    spec = importlib.util.spec_from_file_location("wahs_cloud_gate_app", APP_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _request(
    port: int,
    method: str,
    path: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[int, bytes, Dict[str, str]]:
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    req_headers = dict(headers or {})
    body = None
    if payload is not None:
        req_headers["Content-Type"] = "application/json"
        body = json.dumps(payload).encode("utf-8")
    conn.request(method, path, body=body, headers=req_headers)
    resp = conn.getresponse()
    raw = resp.read()
    resp_headers = {k.lower(): v for k, v in resp.getheaders()}
    status = resp.status
    conn.close()
    return status, raw, resp_headers


class WahsCloudGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.mod = _load_gate_module()

    def setUp(self) -> None:
        self.env_patch = patch.dict(
            os.environ,
            {
                "WAHS_ALLOW_TEST_GOOGLE_TOKEN": "1",
                "WAHS_GATE_COOKIE_SECRET": "unit-test-gate-secret-32-bytes-ok",
                "WAHS_GATE_COOKIE_DOMAIN": ".openclinai.org",
                "WAHS_AUTH_WHITELIST_EMAILS": "pmanko@uw.edu,piotr.mankowski@gmail.com",
            },
            clear=False,
        )
        self.env_patch.start()
        self.server = self.mod.create_server("127.0.0.1", 0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.env_patch.stop()

    def test_verify_unauthenticated_browser_redirects_and_api_returns_401(self) -> None:
        status, _, hdrs = _request(
            self.port,
            "GET",
            "/auth/verify",
            headers={
                "X-Forwarded-Host": "wahs-web.openclinai.org",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Uri": "/chat",
            },
        )
        self.assertEqual(status, 302)
        self.assertIn("https://openclinai.org/wahs/gate/?next=", hdrs.get("location", ""))
        self.assertIn("wahs-web.openclinai.org%2Fchat", hdrs.get("location", ""))

        api_status, api_raw, _ = _request(
            self.port,
            "GET",
            "/auth/verify",
            headers={
                "X-Forwarded-Host": "wahs-mobile.openclinai.org",
                "X-Forwarded-Proto": "https",
                "X-Forwarded-Uri": "/api/chat",
                "Accept": "application/json",
            },
        )
        self.assertEqual(api_status, 401)
        self.assertEqual(
            json.loads(api_raw.decode("utf-8"))["error"]["code"], "missing_session"
        )

    def test_open_redirect_protection_clamps_untrusted_next_host(self) -> None:
        self.assertEqual(
            self.mod.validate_next_url("https://evil.example.com/phish"),
            "https://wahealth.openclinai.org/",
        )
        self.assertEqual(
            self.mod.validate_next_url("https://wahs-web.openclinai.org/chat?tab=1"),
            "https://wahs-web.openclinai.org/chat?tab=1",
        )
        self.assertEqual(
            self.mod.validate_next_url("https://wahs-mobile.openclinai.org/"),
            "https://wahs-mobile.openclinai.org/",
        )

    def test_session_exchange_whitelist_and_portal_rendering(self) -> None:
        # Non-whitelisted Google account gets 403 and NO Set-Cookie
        deny_status, deny_raw, deny_hdrs = _request(
            self.port,
            "POST",
            "/wahs/gate/api/session",
            payload={
                "id_token": "test-google-token:intruder@example.com",
                "next": "https://wahs-mobile.openclinai.org/",
            },
        )
        self.assertEqual(deny_status, 403)
        self.assertNotIn("set-cookie", deny_hdrs)
        self.assertEqual(
            json.loads(deny_raw.decode("utf-8"))["error"]["code"], "not_whitelisted"
        )

        # Whitelisted Google account gets signed HttpOnly cross-subdomain cookie
        ok_status, ok_raw, ok_hdrs = _request(
            self.port,
            "POST",
            "/wahs/gate/api/session",
            payload={
                "id_token": "test-google-token:pmanko@uw.edu",
                "next": "https://wahs-mobile.openclinai.org/chat",
            },
        )
        self.assertEqual(ok_status, 200)
        body = json.loads(ok_raw.decode("utf-8"))
        self.assertTrue(body["ok"])
        self.assertEqual(body["redirect_to"], "https://wahs-mobile.openclinai.org/chat")
        set_cookie = ok_hdrs.get("set-cookie", "")
        self.assertIn("Domain=.openclinai.org", set_cookie)
        self.assertIn("HttpOnly", set_cookie)
        self.assertIn("Secure", set_cookie)

        cookie_pair = set_cookie.split(";", 1)[0]

        # Authenticated /auth/verify passes with user headers
        v_status, _, v_hdrs = _request(
            self.port,
            "GET",
            "/auth/verify",
            headers={"Cookie": cookie_pair},
        )
        self.assertEqual(v_status, 200)
        self.assertEqual(v_hdrs.get("x-wahs-auth-email"), "pmanko@uw.edu")

        # Tampered cookie fails closed
        t_status, _, _ = _request(
            self.port,
            "GET",
            "/auth/verify",
            headers={"Cookie": cookie_pair[:-4] + "0000"},
        )
        self.assertEqual(t_status, 302)

        # Portal landing page links both frontends without calling shl-ips "legacy"
        p_status, p_raw, p_hdrs = _request(
            self.port,
            "GET",
            "/",
            headers={"Cookie": cookie_pair},
        )
        self.assertEqual(p_status, 200)
        self.assertEqual(p_hdrs.get("x-robots-tag"), "noindex, nofollow")
        html_text = p_raw.decode("utf-8")
        self.assertIn("https://wahs-web.openclinai.org/", html_text)
        self.assertIn("https://wahs-mobile.openclinai.org/", html_text)
        self.assertIn("https://wahs-web.openclinai.org/?profile=maurice", html_text)
        self.assertIn("https://wahs-mobile.openclinai.org/?screen=signin", html_text)
        self.assertEqual(html_text.count("data-copy='wahs-demo-2026'"), 12)
        self.assertIn("maurice.auer@wahs.local", html_text)
        self.assertNotIn("legacy", html_text.lower())

        # Sign-out clears cookie
        l_status, _, l_hdrs = _request(
            self.port,
            "GET",
            "/wahs/gate/logout",
            headers={"Cookie": cookie_pair},
        )
        self.assertEqual(l_status, 302)
        self.assertIn("Max-Age=0", l_hdrs.get("set-cookie", ""))


if __name__ == "__main__":
    unittest.main()

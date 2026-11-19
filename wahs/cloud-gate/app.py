"""WAHS Cloud Auth Gate & Portal Service (`wahs/cloud-gate/app.py`).

Standalone zero-dependency HTTP server providing:
1. Caddy `forward_auth` verification (`/auth/verify`) gated strictly on the
   Google account whitelist via HMAC-SHA256 signed HttpOnly session cookies.
2. Google Sign-In Gate UI & Session Exchange (`/wahs/gate/`, `/wahs/gate/api/session`,
   `/wahs/gate/logout`) hosted under `https://openclinai.org/wahs/gate/`.
3. WA Health Summary Cloud Workspace Landing Portal (`/` + `/api/portal-status`)
   on `https://wahealth.openclinai.org/`, linking whitelisted users to the Web App
   and Mobile Companion with live backend status and seeded patient accounts.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import html
import http.cookies
import json
import os
import secrets
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

DEFAULT_GOOGLE_CLIENT_ID = (
    "1043771833056-41q5npi9me4i390i87b2tha58rt5blb9.apps.googleusercontent.com"
)
DEFAULT_FIREBASE_AUTH_DOMAIN = "clinical-ai-harness.firebaseapp.com"
DEFAULT_FIREBASE_PROJECT_ID = "clinical-ai-harness"
DEFAULT_FB_KEY_B64 = "QUl6YVN5RC13RUVLQkJIbEtUdkRhOUdadnBXWnozUUJ2NEMxVGlZ"
DEFAULT_WHITELIST_EMAILS = (
    "piotr.mankowski@gmail.com,"
    "pmanko@uw.edu,"
    "dlorigan@uw.edu,"
    "daniellrgn@gmail.com,"
    "ivanc@uw.edu,"
    "mcjustin@uw.edu,"
    "jflow2@uw.edu,"
    "lober@uw.edu,"
    "ibacher@uw.edu"
)
DEFAULT_ALLOWED_HOSTS = (
    "wahealth.openclinai.org,"
    "wahs-web.openclinai.org,"
    "wahs-mobile.openclinai.org"
)
DEFAULT_PORTAL_URL = "https://wahealth.openclinai.org/"
DEFAULT_WEB_APP_URL = "https://wahs-web.openclinai.org/"
DEFAULT_MOBILE_APP_URL = "https://wahs-mobile.openclinai.org/"
DEFAULT_GATE_LOGIN_URL = "https://openclinai.org/wahs/gate/"

COOKIE_NAME = "wahs_gate_session"
SESSION_TTL_SECONDS = 43200
_TOKEN_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_TOKEN_CACHE_TTL_SECONDS = 300.0
_FALLBACK_KEY = secrets.token_hex(32)

SEEDED_DEMO_ACCOUNTS: Tuple[Dict[str, str], ...] = (
    {
        "slug": "alex",
        "name": "Alex Johnson",
        "email": "alex.johnson@wahs.local",
        "dob": "1962-03-14",
        "cohort": "Primary Persona",
        "focus": "Adult cardiology, CKD & diabetes (4 sources)",
    },
    {
        "slug": "leo",
        "name": "Leo Johnson",
        "email": "leo.johnson@wahs.local",
        "dob": "2019-08-22",
        "cohort": "Child Proxy Persona",
        "focus": "Pediatric asthma & peanut allergy (3 sources)",
    },
    {
        "slug": "maurice",
        "name": "Maurice Auer",
        "email": "maurice.auer@wahs.local",
        "dob": "1973-03-25",
        "cohort": "Complex Multi-Site",
        "focus": "Complex multi-site longitudinal record (7,099 resources)",
    },
    {
        "slug": "julian",
        "name": "Julian Mercer",
        "email": "julian.mercer@wahs.local",
        "dob": "1954-10-08",
        "cohort": "MIMIC-IV ICU Heme/Renal",
        "focus": "MIMIC-IV ICU hematology & cardiorenal (4,048 resources)",
    },
    {
        "slug": "clara",
        "name": "Clara Hollis",
        "email": "clara.hollis@wahs.local",
        "dob": "1958-12-21",
        "cohort": "MIMIC-IV ICU Hepatopulmonary",
        "focus": "MIMIC-IV ICU hepatopulmonary (2,661 resources)",
    },
    {
        "slug": "marcus",
        "name": "Marcus Vance",
        "email": "marcus.vance@wahs.local",
        "dob": "1961-09-22",
        "cohort": "Thoracic Oncology",
        "focus": "Fred Hutch + UW thoracic oncology immunotherapy (1,612 resources)",
    },
    {
        "slug": "lamar",
        "name": "Lamar Beer",
        "email": "lamar.beer@wahs.local",
        "dob": "1971-02-16",
        "cohort": "Outpatient & Urgent Care",
        "focus": "Outpatient & urgent care longitudinal record (892 resources)",
    },
    {
        "slug": "byron",
        "name": "Byron Emard",
        "email": "byron.emard@wahs.local",
        "dob": "2009-12-14",
        "cohort": "Adolescent Longitudinal",
        "focus": "Pediatric & adolescent longitudinal care (480 resources)",
    },
    {
        "slug": "elena",
        "name": "Elena Rostova",
        "email": "elena.rostova@wahs.local",
        "dob": "1954-04-12",
        "cohort": "Cardiorenal",
        "focus": "UW Heart Institute + NW Kidney cardiorenal (454 resources)",
    },
    {
        "slug": "margaret",
        "name": "Margaret Chen",
        "email": "margaret.chen@wahs.local",
        "dob": "1943-11-03",
        "cohort": "Geriatrics Polypharmacy",
        "focus": "Geriatrics & Overlake sleep polypharmacy (448 resources)",
    },
    {
        "slug": "arthur",
        "name": "Arthur Pendelton",
        "email": "arthur.pendelton@wahs.local",
        "dob": "1947-08-19",
        "cohort": "Anticoagulation & GI",
        "focus": "Anticoagulation, GI & primary care (447 resources)",
    },
    {
        "slug": "sofia",
        "name": "Sofia Alvarez",
        "email": "sofia.alvarez@wahs.local",
        "dob": "1991-06-14",
        "cohort": "Maternal-Fetal & Endocrine",
        "focus": "UW Maternal-Fetal & Endocrine (436 resources)",
    },
)


def get_config() -> Dict[str, Any]:
    raw_whitelist = (
        os.getenv("WAHS_AUTH_WHITELIST_EMAILS") or DEFAULT_WHITELIST_EMAILS
    )
    whitelist: Set[str] = {
        email.strip().lower()
        for email in raw_whitelist.split(",")
        if email.strip()
    }
    raw_hosts = (
        os.getenv("WAHS_GATE_ALLOWED_HOSTS") or DEFAULT_ALLOWED_HOSTS
    )
    allowed_hosts: Set[str] = {
        h.strip().lower() for h in raw_hosts.split(",") if h.strip()
    }
    signing_key = (os.getenv("WAHS_GATE_COOKIE_SECRET") or "").strip()
    if not signing_key:
        signing_key = _FALLBACK_KEY
    cookie_domain = (
        os.getenv("WAHS_GATE_COOKIE_DOMAIN") or ".openclinai.org"
    ).strip()
    client_id = (
        os.getenv("WAHS_GOOGLE_CLIENT_ID") or DEFAULT_GOOGLE_CLIENT_ID
    ).strip()
    fb_key = (
        os.getenv("WAHS_FIREBASE_WEB_KEY")
        or os.getenv("WAHS_FIREBASE_API_KEY")
        or base64.b64decode(DEFAULT_FB_KEY_B64).decode("ascii")
    ).strip()
    try:
        session_ttl = int(
            os.getenv("WAHS_GATE_COOKIE_TTL_SECONDS") or str(SESSION_TTL_SECONDS)
        )
    except ValueError:
        session_ttl = SESSION_TTL_SECONDS
    portal_url = (os.getenv("WAHS_PORTAL_URL") or DEFAULT_PORTAL_URL).strip()
    web_app_url = (os.getenv("WAHS_WEB_APP_URL") or DEFAULT_WEB_APP_URL).strip()
    mobile_app_url = (
        os.getenv("WAHS_MOBILE_APP_URL") or DEFAULT_MOBILE_APP_URL
    ).strip()
    gate_login_url = (
        os.getenv("WAHS_GATE_LOGIN_URL") or DEFAULT_GATE_LOGIN_URL
    ).strip()
    return {
        "whitelist": whitelist,
        "allowed_hosts": allowed_hosts,
        "signing_key": signing_key,
        "cookie_domain": cookie_domain,
        "cookie_secure": (os.getenv("WAHS_GATE_COOKIE_SECURE") or "true").lower()
        not in ("0", "false", "no"),
        "session_ttl": max(300, session_ttl),
        "client_id": client_id,
        "fb_key": fb_key,
        "firebase_auth_domain": (
            os.getenv("WAHS_FIREBASE_AUTH_DOMAIN") or DEFAULT_FIREBASE_AUTH_DOMAIN
        ).strip(),
        "firebase_project_id": (
            os.getenv("WAHS_FIREBASE_PROJECT_ID") or DEFAULT_FIREBASE_PROJECT_ID
        ).strip(),
        "portal_url": portal_url,
        "web_app_url": web_app_url,
        "mobile_app_url": mobile_app_url,
        "gate_login_url": gate_login_url,
        "probe_urls": {
            "wahs_engine": (
                os.getenv("WAHS_PROBE_ENGINE_URL")
                or "http://wahs-engine:8080/healthz"
            ).strip(),
            "fhir_auth": (
                os.getenv("WAHS_PROBE_FHIR_URL")
                or "http://fhir-auth:8080/fhir/.well-known/smart-configuration"
            ).strip(),
            "keycloak": (
                os.getenv("WAHS_PROBE_KEYCLOAK_URL")
                or "http://keycloak:8080/realms/wahs"
            ).strip(),
            "shl_server": (
                os.getenv("WAHS_PROBE_SHL_URL") or "http://shl-server:8000/"
            ).strip(),
        },
    }


def _http_get_json(
    url: str,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 8.0,
) -> Optional[Dict[str, Any]]:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


def _http_post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 8.0,
) -> Optional[Dict[str, Any]]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


def _probe_service(url: str, timeout: float = 2.0) -> Dict[str, Any]:
    t0 = time.monotonic()
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(2048).decode("utf-8", errors="replace")
            elapsed_ms = int((time.monotonic() - t0) * 1000)
            payload = None
            try:
                payload = json.loads(raw)
            except Exception:
                payload = None
            return {
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "latency_ms": elapsed_ms,
                "details": payload if isinstance(payload, dict) else {},
            }
    except urllib.error.HTTPError as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return {"ok": False, "status": exc.code, "latency_ms": elapsed_ms}
    except Exception as exc:
        elapsed_ms = int((time.monotonic() - t0) * 1000)
        return {
            "ok": False,
            "status": 0,
            "latency_ms": elapsed_ms,
            "error": str(exc)[:120],
        }


def verify_google_auth_token(token: str) -> Dict[str, Any]:
    cfg = get_config()
    whitelist = cfg["whitelist"]
    client_id = cfg["client_id"]
    fb_key = cfg["fb_key"]

    clean = (token or "").strip()
    if not clean:
        return {
            "authenticated": False,
            "authorized": False,
            "code": "missing_token",
            "message": "Google Sign-In is required to access WA Health Summary.",
        }

    if (
        os.environ.get("WAHS_ALLOW_TEST_GOOGLE_TOKEN") == "1"
        and clean.startswith("test-google-token:")
    ):
        email = clean.split(":", 1)[1].strip().lower()
        authorized = email in whitelist
        return {
            "authenticated": True,
            "authorized": authorized,
            "email": email,
            "name": email.split("@", 1)[0],
            "picture": "",
            "code": "ok" if authorized else "not_whitelisted",
            "message": (
                f"Signed in as {email} (authorized)."
                if authorized
                else f"Account {email} is not on the authorized WAHS access whitelist."
            ),
        }

    now = time.time()
    token_hash = hashlib.sha256(clean.encode("utf-8")).hexdigest()
    cached = _TOKEN_CACHE.get(token_hash)
    if cached is not None and (now - cached[0]) < _TOKEN_CACHE_TTL_SECONDS:
        info = dict(cached[1])
    else:
        info = None
        q = urllib.parse.urlencode({"id_token": clean})
        data1 = _http_get_json(f"https://oauth2.googleapis.com/tokeninfo?{q}")
        if data1 and data1.get("email"):
            info = dict(data1)
            info["_auth_source"] = "google_id_token"

        if info is None:
            data2 = _http_get_json(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {clean}"},
            )
            if data2 and data2.get("email"):
                info = dict(data2)
                info["_auth_source"] = "google_userinfo"
                if client_id and not info.get("aud"):
                    q_acc = urllib.parse.urlencode({"access_token": clean})
                    acc_info = (
                        _http_get_json(
                            f"https://oauth2.googleapis.com/tokeninfo?{q_acc}"
                        )
                        or {}
                    )
                    info["aud"] = acc_info.get("aud") or acc_info.get("azp") or ""

        if info is None and fb_key:
            data3 = _http_post_json(
                f"https://identitytoolkit.googleapis.com/v1/accounts:lookup?key={fb_key}",
                payload={"idToken": clean},
            )
            users = (data3 or {}).get("users") or []
            if users and users[0].get("email"):
                u = users[0]
                info = {
                    "email": u.get("email"),
                    "email_verified": u.get("emailVerified", True),
                    "name": u.get("displayName") or "",
                    "picture": u.get("photoUrl") or "",
                    "_auth_source": "firebase_lookup",
                }

        if info is None:
            return {
                "authenticated": False,
                "authorized": False,
                "code": "invalid_token",
                "message": "Google session token expired or could not be verified. Please sign in again.",
            }
        _TOKEN_CACHE[token_hash] = (now, info)

    email = str(info.get("email") or "").strip().lower()
    email_verified = str(info.get("email_verified", "true")).lower() in ("true", "1")
    if not email or not email_verified:
        return {
            "authenticated": False,
            "authorized": False,
            "code": "unverified_email",
            "message": "Google account email is not verified.",
        }

    aud = str(info.get("aud") or "").strip()
    auth_source = str(info.get("_auth_source") or "google_id_token")
    if client_id and auth_source != "firebase_lookup" and aud != client_id:
        return {
            "authenticated": False,
            "authorized": False,
            "code": "audience_mismatch",
            "message": "Google ID token audience does not match configured client ID.",
        }

    authorized = email in whitelist
    return {
        "authenticated": True,
        "authorized": authorized,
        "email": email,
        "name": str(info.get("name") or email.split("@", 1)[0]),
        "picture": str(info.get("picture") or ""),
        "code": "ok" if authorized else "not_whitelisted",
        "message": (
            f"Signed in as {email} (authorized)."
            if authorized
            else f"Google account '{email}' is not on the authorized WAHS access whitelist."
        ),
    }


def validate_next_url(
    raw_next: Optional[str],
    *,
    cfg: Optional[Dict[str, Any]] = None,
) -> str:
    conf = cfg or get_config()
    default_url = conf["portal_url"]
    candidate = (raw_next or "").strip()
    if not candidate or any(ch in candidate for ch in ("\r", "\n", "\x00")):
        return default_url
    parsed = urllib.parse.urlparse(candidate)
    allow_http = os.getenv("WAHS_GATE_ALLOW_HTTP_NEXT") == "1"
    allowed_schemes = ("https", "http") if allow_http else ("https",)
    if parsed.scheme.lower() not in allowed_schemes:
        return default_url
    if parsed.username or parsed.password:
        return default_url
    host = (parsed.hostname or "").lower()
    if host not in conf["allowed_hosts"]:
        return default_url
    netloc = parsed.netloc.lower()
    path = parsed.path or "/"
    if path.startswith("/wahs/gate") or path.startswith("/auth/verify"):
        return default_url
    return urllib.parse.urlunparse(
        (parsed.scheme.lower(), netloc, path, "", parsed.query, parsed.fragment)
    )


def sign_session_cookie(
    email: str,
    name: str,
    picture: str = "",
    *,
    cfg: Optional[Dict[str, Any]] = None,
    now_ts: Optional[int] = None,
) -> str:
    conf = cfg or get_config()
    issued = int(now_ts if now_ts is not None else time.time())
    payload = {
        "email": email.strip().lower(),
        "name": (name or email.split("@", 1)[0]).strip(),
        "picture": picture.strip(),
        "iat": issued,
        "exp": issued + int(conf["session_ttl"]),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    b64 = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    sig = hmac.new(
        conf["signing_key"].encode("utf-8"),
        b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    return f"{b64}.{sig}"


def verify_session_cookie_value(
    cookie_val: str,
    *,
    cfg: Optional[Dict[str, Any]] = None,
    now_ts: Optional[int] = None,
) -> Dict[str, Any]:
    conf = cfg or get_config()
    clean = (cookie_val or "").strip().strip('"')
    if not clean or "." not in clean:
        return {"authorized": False, "code": "missing_session"}
    b64, sig = clean.rsplit(".", 1)
    if not b64 or not sig:
        return {"authorized": False, "code": "malformed_session"}
    expected_sig = hmac.new(
        conf["signing_key"].encode("utf-8"),
        b64.encode("ascii"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return {"authorized": False, "code": "invalid_signature"}
    pad = "=" * ((4 - (len(b64) % 4)) % 4)
    try:
        data = json.loads(base64.urlsafe_b64decode(b64 + pad).decode("utf-8"))
    except Exception:
        return {"authorized": False, "code": "invalid_payload"}
    if not isinstance(data, dict):
        return {"authorized": False, "code": "invalid_payload"}
    now = int(now_ts if now_ts is not None else time.time())
    exp = int(data.get("exp") or 0)
    if exp <= now:
        return {"authorized": False, "code": "session_expired"}
    email = str(data.get("email") or "").strip().lower()
    if not email or email not in conf["whitelist"]:
        return {"authorized": False, "code": "not_whitelisted", "email": email}
    return {
        "authorized": True,
        "code": "ok",
        "email": email,
        "name": str(data.get("name") or email.split("@", 1)[0]),
        "picture": str(data.get("picture") or ""),
        "exp": exp,
    }


def extract_cookie(headers: Mapping[str, str], name: str = COOKIE_NAME) -> str:
    lowered = {k.lower(): v for k, v in headers.items()}
    raw_cookie = lowered.get("cookie") or ""
    if not raw_cookie:
        return ""
    jar = http.cookies.SimpleCookie()
    try:
        jar.load(raw_cookie)
    except http.cookies.CookieError:
        for part in raw_cookie.split(";"):
            k, sep, v = part.strip().partition("=")
            if sep and k.strip() == name:
                return v.strip()
        return ""
    if name in jar:
        return str(jar[name].value)
    return ""


def _build_session_set_cookie_header(
    token_value: str,
    *,
    max_age: int,
    cfg: Dict[str, Any],
) -> str:
    parts = [f"{COOKIE_NAME}={token_value}"]
    if cfg["cookie_domain"]:
        parts.append(f"Domain={cfg['cookie_domain']}")
    parts.append("Path=/")
    parts.append(f"Max-Age={max_age}")
    parts.append("HttpOnly")
    if cfg["cookie_secure"]:
        parts.append("Secure")
    parts.append("SameSite=Lax")
    return "; ".join(parts)


def _is_api_or_xhr_request(headers: Mapping[str, str]) -> bool:
    lowered = {k.lower(): v for k, v in headers.items()}
    fwd_uri = (lowered.get("x-forwarded-uri") or "").strip()
    if fwd_uri.startswith(("/api/", "/fhir/", "/shl-server/")):
        return True
    accept = (lowered.get("accept") or "").lower()
    if "application/json" in accept and "text/html" not in accept:
        return True
    if (lowered.get("x-requested-with") or "").lower() == "xmlhttprequest":
        return True
    return False


def render_gate_login_html(
    *,
    next_url: str,
    cfg: Dict[str, Any],
    error_message: str = "",
) -> str:
    fb_cfg = {
        "apiKey": cfg["fb_key"],
        "authDomain": cfg["firebase_auth_domain"],
        "projectId": cfg["firebase_project_id"],
    }
    esc_next = html.escape(next_url, quote=True)
    esc_err = html.escape(error_message)
    err_display = "block" if error_message else "none"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex, nofollow" />
  <title>WA Health Summary — Authorized Sign-In</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #475569;
      --primary: #1d4ed8;
      --primary-hover: #1e40af;
      --danger-bg: #fef2f2;
      --danger-border: #fecaca;
      --danger-text: #991b1b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 1.5rem;
      background: radial-gradient(circle at top, #eff6ff 0%, var(--bg) 55%);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }}
    .card {{
      width: 100%;
      max-width: 460px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 2rem;
      box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08);
    }}
    .badge {{
      display: inline-block;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      background: #eff6ff;
      color: var(--primary);
      border: 1px solid #bfdbfe;
      margin-bottom: 0.9rem;
    }}
    h1 {{
      margin: 0 0 0.5rem;
      font-size: 1.45rem;
      line-height: 1.25;
    }}
    p {{
      margin: 0 0 1.25rem;
      color: var(--muted);
      font-size: 0.95rem;
      line-height: 1.55;
    }}
    .target {{
      font-size: 0.82rem;
      color: var(--muted);
      background: #f1f5f9;
      border-radius: 8px;
      padding: 0.55rem 0.75rem;
      margin-bottom: 1.25rem;
      word-break: break-all;
    }}
    button#google-signin-btn {{
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 0.65rem;
      padding: 0.85rem 1.15rem;
      border: 1px solid #1d4ed8;
      border-radius: 10px;
      background: var(--primary);
      color: #ffffff;
      font-size: 1rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s ease;
    }}
    button#google-signin-btn:hover:not(:disabled) {{ background: var(--primary-hover); }}
    button#google-signin-btn:disabled {{ opacity: 0.65; cursor: wait; }}
    .alert {{
      display: {err_display};
      margin-top: 1rem;
      padding: 0.85rem 1rem;
      border-radius: 10px;
      background: var(--danger-bg);
      border: 1px solid var(--danger-border);
      color: var(--danger-text);
      font-size: 0.9rem;
      line-height: 1.45;
    }}
    .foot {{
      margin-top: 1.35rem;
      padding-top: 1rem;
      border-top: 1px solid var(--border);
      font-size: 0.82rem;
      color: #64748b;
    }}
    .foot a {{ color: var(--primary); text-decoration: none; }}
  </style>
</head>
<body>
  <main class="card">
    <div class="badge">WA Health Summary · Authorized Access</div>
    <h1>Sign in with Google</h1>
    <p>Access to the cloud WA Health Summary Web App and Mobile Companion is restricted to whitelisted project accounts.</p>
    <div class="target">Destination after sign-in: <strong>{esc_next}</strong></div>
    <button id="google-signin-btn" type="button">
      <span>Continue with Google Account</span>
    </button>
    <div id="gate-error" class="alert" role="alert">{esc_err}</div>
    <div class="foot">
      Need whitelist access? Contact <a href="mailto:pmanko@uw.edu">pmanko@uw.edu</a> ·
      <a href="https://openclinai.org/wahs/">Back to OpenClinAI WAHS overview</a>
    </div>
  </main>

  <script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-app-compat.js"></script>
  <script src="https://www.gstatic.com/firebasejs/10.14.1/firebase-auth-compat.js"></script>
  <script>
    (function () {{
      const fbConfig = {json.dumps(fb_cfg)};
      const nextUrl = {json.dumps(next_url)};
      const btn = document.getElementById("google-signin-btn");
      const errBox = document.getElementById("gate-error");

      function showError(msg) {{
        errBox.textContent = msg;
        errBox.style.display = "block";
      }}

      let eagerAuth = null;
      let eagerProvider = null;
      function ensureFirebaseReady() {{
        if (!window.firebase || !window.firebase.auth) {{
          throw new Error("Firebase Google authentication SDK failed to load.");
        }}
        if (!window.firebase.apps.length) {{
          window.firebase.initializeApp(fbConfig);
        }}
        if (!eagerAuth) {{
          eagerAuth = window.firebase.auth();
        }}
        if (!eagerProvider) {{
          eagerProvider = new window.firebase.auth.GoogleAuthProvider();
          eagerProvider.addScope("email");
          eagerProvider.addScope("profile");
          eagerProvider.setCustomParameters({{ prompt: "select_account" }});
        }}
        return {{ auth: eagerAuth, provider: eagerProvider }};
      }}

      try {{
        if (window.firebase && window.firebase.auth) {{
          ensureFirebaseReady();
        }}
      }} catch (_) {{}}

      btn.addEventListener("click", async function () {{
        errBox.style.display = "none";
        btn.disabled = true;
        const originalLabel = btn.textContent;
        btn.textContent = "Verifying Google account...";
        try {{
          const ready = ensureFirebaseReady();
          const auth = ready.auth;
          const provider = ready.provider;

          const result = await auth.signInWithPopup(provider);
          const idToken = result.user ? await result.user.getIdToken(true) : "";
          if (!idToken) {{
            throw new Error("Google sign-in did not return an identity token.");
          }}

          const resp = await fetch("/wahs/gate/api/session", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            credentials: "same-origin",
            body: JSON.stringify({{ id_token: idToken, next: nextUrl }})
          }});
          const data = await resp.json().catch(function () {{ return {{}}; }});
          if (!resp.ok) {{
            try {{ await auth.signOut(); }} catch (_) {{}}
            const msg = (data && data.error && data.error.message) || "Google account is not authorized.";
            showError(msg);
            btn.disabled = false;
            btn.textContent = "Try a different Google account";
            return;
          }}
          window.location.assign(data.redirect_to || nextUrl);
        }} catch (err) {{
          const code = err && err.code;
          if (code === "auth/popup-blocked") {{
            showError("Google sign-in popup was blocked by your browser. Please allow pop-ups for openclinai.org (Safari Settings -> Websites -> Pop-up Windows) and click Continue again.");
          }} else {{
            showError((err && err.message) || "Google sign-in was cancelled or failed.");
          }}
          btn.disabled = false;
          btn.textContent = originalLabel;
        }}
      }});
    }})();
  </script>
</body>
</html>"""


def render_portal_html(
    *,
    user_email: str,
    user_name: str,
    cfg: Dict[str, Any],
) -> str:
    esc_email = html.escape(user_email)
    esc_name = html.escape(user_name or user_email)
    esc_web_url = html.escape(cfg["web_app_url"], quote=True)
    esc_mobile_url = html.escape(cfg["mobile_app_url"], quote=True)
    logout_url = "https://openclinai.org/wahs/gate/logout"
    switch_url = "https://openclinai.org/wahs/gate/?switch=1"

    web_base = cfg["web_app_url"].rstrip("/")
    mobile_base = cfg["mobile_app_url"].rstrip("/")
    rows_html = []
    for acct in SEEDED_DEMO_ACCOUNTS:
        esc_acct_name = html.escape(acct["name"], quote=True)
        esc_acct_email = html.escape(acct["email"], quote=True)
        web_profile_url = html.escape(
            f"{web_base}/?profile={urllib.parse.quote(acct['slug'])}", quote=True
        )
        mobile_signin_url = html.escape(f"{mobile_base}/?screen=signin", quote=True)
        rows_html.append(
            "<tr>"
            f"<td><strong>{html.escape(acct['name'])}</strong><br><span class='sub'>{html.escape(acct['cohort'])}</span></td>"
            f"<td><code>{html.escape(acct['email'])}</code> "
            f"<button type='button' class='copy-btn' data-copy='{esc_acct_email}' aria-label='Copy email for {esc_acct_name}'>Copy</button></td>"
            f"<td><code>wahs-demo-2026</code> "
            f"<button type='button' class='copy-btn' data-copy='wahs-demo-2026' aria-label='Copy password for {esc_acct_name}'>Copy</button></td>"
            f"<td>{html.escape(acct['focus'])}</td>"
            f"<td class='quick-actions'>"
            f"<a class='quick-link' href='{web_profile_url}'>Web App &rarr;</a> "
            f"<a class='quick-link mobile' href='{mobile_signin_url}'>Mobile &rarr;</a>"
            f"</td>"
            "</tr>"
        )
    accounts_tbody = "\n".join(rows_html)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="robots" content="noindex, nofollow" />
  <title>WA Health Summary — Cloud Workspace</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --border: #e2e8f0;
      --text: #0f172a;
      --muted: #475569;
      --primary: #1d4ed8;
      --teal: #0f766e;
      --ok-bg: #ecfdf5;
      --ok-border: #a7f3d0;
      --ok-text: #065f46;
      --warn-bg: #fef3c7;
      --warn-text: #92400e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      line-height: 1.55;
    }}
    header {{
      background: #0f172a;
      color: #f8fafc;
      border-bottom: 1px solid #1e293b;
      padding: 0.85rem 1.5rem;
    }}
    .header-inner {{
      max-width: 1120px;
      margin: 0 auto;
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
    }}
    .brand {{
      display: flex;
      align-items: center;
      gap: 0.65rem;
      font-weight: 700;
      font-size: 1.05rem;
    }}
    .pill {{
      background: #2563eb;
      color: #fff;
      font-size: 0.72rem;
      padding: 0.18rem 0.55rem;
      border-radius: 999px;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .auth-bar {{
      display: flex;
      align-items: center;
      gap: 0.8rem;
      font-size: 0.86rem;
      color: #cbd5e1;
    }}
    .auth-bar a {{
      color: #93c5fd;
      text-decoration: none;
      font-weight: 500;
    }}
    .auth-bar a:hover {{ text-decoration: underline; }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 2rem 1.5rem 3rem;
    }}
    .hero h1 {{
      margin: 0 0 0.45rem;
      font-size: 1.8rem;
      letter-spacing: -0.02em;
    }}
    .hero p {{
      margin: 0 0 1.75rem;
      color: var(--muted);
      max-width: 72ch;
    }}
    .cards {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(310px, 1fr));
      gap: 1.25rem;
      margin-bottom: 1.75rem;
    }}
    .app-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      box-shadow: 0 4px 14px rgba(15, 23, 42, 0.05);
    }}
    .app-card .tag {{
      display: inline-block;
      font-size: 0.74rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      margin-bottom: 0.7rem;
    }}
    .tag-web {{ background: #eff6ff; color: var(--primary); border: 1px solid #bfdbfe; }}
    .tag-mobile {{ background: #f0fdfa; color: var(--teal); border: 1px solid #99f6e4; }}
    .app-card h2 {{
      margin: 0 0 0.5rem;
      font-size: 1.25rem;
    }}
    .app-card p {{
      margin: 0 0 1rem;
      color: var(--muted);
      font-size: 0.94rem;
    }}
    .launch-btn {{
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 0.7rem 1.1rem;
      border-radius: 10px;
      font-weight: 600;
      text-decoration: none;
      color: #ffffff;
      background: var(--primary);
    }}
    .launch-btn.mobile {{ background: var(--teal); }}
    .launch-btn:hover {{ opacity: 0.93; }}
    .panel {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.25rem 1.5rem;
      margin-bottom: 1.5rem;
    }}
    .panel h3 {{
      margin: 0 0 0.75rem;
      font-size: 1.05rem;
    }}
    .status-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 0.65rem;
    }}
    .status-pill {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      font-size: 0.84rem;
      font-weight: 600;
      background: #f1f5f9;
      color: var(--muted);
      border: 1px solid var(--border);
    }}
    .status-pill.ok {{ background: var(--ok-bg); border-color: var(--ok-border); color: var(--ok-text); }}
    .status-pill.warn {{ background: var(--warn-bg); color: var(--warn-text); }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.88rem;
    }}
    th, td {{
      text-align: left;
      padding: 0.6rem 0.65rem;
      border-bottom: 1px solid var(--border);
      vertical-align: top;
    }}
    th {{ color: var(--muted); font-weight: 600; background: #f8fafc; }}
    .sub {{ font-size: 0.78rem; color: #64748b; }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.82rem;
      background: #f1f5f9;
      padding: 0.12rem 0.35rem;
      border-radius: 5px;
    }}
    .copy-btn {{
      margin-left: 0.35rem;
      padding: 0.15rem 0.45rem;
      font-size: 0.75rem;
      border: 1px solid var(--border);
      border-radius: 6px;
      background: #fff;
      cursor: pointer;
    }}
    .copy-btn:hover {{ background: #f1f5f9; }}
    .quick-actions {{
      white-space: nowrap;
    }}
    .quick-link {{
      display: inline-block;
      padding: 0.22rem 0.5rem;
      border-radius: 6px;
      font-size: 0.76rem;
      font-weight: 600;
      text-decoration: none;
      color: var(--primary);
      background: #eff6ff;
      border: 1px solid #bfdbfe;
      margin-right: 0.25rem;
    }}
    .quick-link.mobile {{
      color: var(--teal);
      background: #f0fdfa;
      border-color: #99f6e4;
      margin-right: 0;
    }}
    .quick-link:hover {{ opacity: 0.85; }}
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <div class="brand">
        <span>WA Health Summary</span>
        <span class="pill">Cloud Workspace</span>
      </div>
      <div class="auth-bar">
        <span>Signed in as <strong>{esc_name}</strong> ({esc_email})</span>
        <a href="{switch_url}">Switch account</a>
        <a href="{logout_url}">Sign out</a>
      </div>
    </div>
  </header>

  <main>
    <section class="hero">
      <h1>WA Health Summary — Cloud Frontends &amp; Live FHIR AI Stack</h1>
      <p>Both applications below are backed by a live HAPI FHIR R4 store seeded with 12 patient records, Keycloak OIDC authentication, SMART Health Links server, and <code>wahs-engine</code> running on the UW CIRG H200 GPU cluster.</p>
    </section>

    <section class="cards">
      <article class="app-card">
        <div>
          <span class="tag tag-web">SvelteKit · IPS &amp; SHL Portal</span>
          <h2>WA Health Summary — Web App</h2>
          <p>Full patient-facing International Patient Summary (IPS) builder, SMART Health Link management, Keycloak OIDC sign-in, and Ask WAHS multi-pathway AI workspace.</p>
        </div>
        <a class="launch-btn" href="{esc_web_url}">Open Web App &rarr;</a>
      </article>

      <article class="app-card">
        <div>
          <span class="tag tag-mobile">Mobile-First Companion</span>
          <h2>WA Health Summary — Mobile Companion</h2>
          <p>Phone-sized companion UI with 1-tap switching across all 12 seeded patient personas, Patient Story updates to FHIR R4, QR Health Links, and streaming Ask WAHS chat.</p>
        </div>
        <a class="launch-btn mobile" href="{esc_mobile_url}">Open Mobile Companion &rarr;</a>
      </article>
    </section>

    <section class="panel">
      <h3>Live Stack &amp; CIRG H200 GPU Inference Status</h3>
      <div id="stack-status" class="status-grid">
        <span class="status-pill">Checking live stack...</span>
      </div>
      <p style="margin:0.75rem 0 0; font-size:0.86rem; color:var(--muted);">
        Default model: <code>wahs-26b-kb</code> (<code>ollama/gemma4:26b</code> via <code>https://llm.co.dev.cirg.uw.edu/v1</code>) ·
        Switchable in Ask WAHS across <strong>Note-RAG</strong>, <strong>4-Layer KB</strong>, <strong>Dynamic FHIR Tools</strong>, and <strong>Chart-Only</strong> pathways and <strong>Auto / 4k / 8k / 16k / 32k</strong> chart budgets.
      </p>
    </section>

    <section class="panel">
      <h3>Seeded Demo Patient Accounts (12 FHIR R4 Personas)</h3>
      <p style="margin:0 0 0.85rem; font-size:0.9rem; color:var(--muted);">
        Both the Web App and Mobile Companion support 1-click sign-in across all 12 real Keycloak accounts (via the profile selector or Account menu), or you can copy any email and password below to sign in manually.
      </p>
      <div style="overflow-x:auto;">
        <table>
          <thead>
            <tr>
              <th>Patient &amp; Cohort</th>
              <th>Username / Email</th>
              <th>Password</th>
              <th>Clinical Profile</th>
              <th>Quick Sign-In</th>
            </tr>
          </thead>
          <tbody>
            {accounts_tbody}
          </tbody>
        </table>
      </div>
    </section>
  </main>

  <script>
    (function () {{
      async function copyTextWithFallback(val) {{
        if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {{
          try {{
            await navigator.clipboard.writeText(val);
            return true;
          }} catch (_) {{}}
        }}
        const ta = document.createElement("textarea");
        ta.value = val;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.opacity = "0";
        document.body.appendChild(ta);
        ta.select();
        let ok = false;
        try {{
          ok = document.execCommand("copy");
        }} catch (_) {{
          ok = false;
        }}
        document.body.removeChild(ta);
        return ok;
      }}

      document.querySelectorAll(".copy-btn").forEach(function (btn) {{
        btn.addEventListener("click", async function () {{
          const val = btn.getAttribute("data-copy") || "";
          const ok = await copyTextWithFallback(val);
          if (ok) {{
            btn.textContent = "Copied";
            setTimeout(function () {{ btn.textContent = "Copy"; }}, 1200);
          }}
        }});
      }});

      fetch("/api/portal-status", {{ credentials: "same-origin" }})
        .then(function (r) {{ return r.json(); }})
        .then(function (data) {{
          const grid = document.getElementById("stack-status");
          const svc = (data && data.services) || {{}};
          const labels = [
            ["wahs_engine", "WAHS Engine"],
            ["fhir_auth", "HAPI FHIR R4 + jwt-proxy"],
            ["keycloak", "Keycloak OIDC"],
            ["shl_server", "SHL Server"]
          ];
          grid.innerHTML = labels.map(function (pair) {{
            const item = svc[pair[0]] || {{}};
            const ok = Boolean(item.ok);
            const ms = item.latency_ms != null ? " (" + item.latency_ms + " ms)" : "";
            return "<span class='status-pill " + (ok ? "ok" : "warn") + "'>" +
              (ok ? "● " : "○ ") + pair[1] + (ok ? " healthy" : " unreachable") + ms + "</span>";
          }}).join("");
        }})
        .catch(function () {{
          document.getElementById("stack-status").innerHTML =
            "<span class='status-pill warn'>○ Unable to reach /api/portal-status</span>";
        }});
    }})();
  </script>
</body>
</html>"""


class GateRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    timeout = 30

    def handle(self) -> None:
        try:
            super().handle()
        except (ConnectionResetError, BrokenPipeError, TimeoutError, socket.timeout, OSError):
            self.close_connection = True

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_bytes(
        self,
        status_code: int,
        content_type: str,
        raw: bytes,
        extra_headers: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        if extra_headers:
            for k, v in extra_headers:
                self.send_header(k, v)
        self.end_headers()
        if raw and self.command != "HEAD":
            self.wfile.write(raw)

    def _send_json(
        self,
        status_code: int,
        payload: Dict[str, Any],
        extra_headers: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        self._send_bytes(
            status_code,
            "application/json; charset=utf-8",
            json.dumps(payload).encode("utf-8"),
            extra_headers=extra_headers,
        )

    def _send_html(
        self,
        status_code: int,
        body: str,
        extra_headers: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        hdrs = [("X-Robots-Tag", "noindex, nofollow")]
        if extra_headers:
            hdrs.extend(extra_headers)
        self._send_bytes(
            status_code,
            "text/html; charset=utf-8",
            body.encode("utf-8"),
            extra_headers=hdrs,
        )

    def _send_redirect(
        self,
        location: str,
        extra_headers: Optional[List[Tuple[str, str]]] = None,
    ) -> None:
        hdrs = [("Location", location)]
        if extra_headers:
            hdrs.extend(extra_headers)
        self._send_bytes(302, "text/plain; charset=utf-8", b"", extra_headers=hdrs)

    def _current_session(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        cookie_val = extract_cookie(dict(self.headers))
        return verify_session_cookie_value(cookie_val, cfg=cfg)

    def do_HEAD(self) -> None:
        self.do_GET()

    def do_GET(self) -> None:
        cfg = get_config()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"
        qs = urllib.parse.parse_qs(parsed.query)

        if path in ("/health", "/healthz"):
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "wahs-auth-gate",
                    "whitelist_count": len(cfg["whitelist"]),
                },
            )
            return

        if path == "/auth/verify":
            session = self._current_session(cfg)
            if session.get("authorized"):
                self._send_json(
                    200,
                    {"authorized": True, "email": session["email"]},
                    extra_headers=[
                        ("X-WAHS-Auth-Email", session["email"]),
                        ("X-WAHS-Auth-Name", session.get("name") or session["email"]),
                    ],
                )
                return

            if _is_api_or_xhr_request(dict(self.headers)):
                self._send_json(
                    401,
                    {
                        "error": {
                            "code": session.get("code", "wahs_whitelist_auth_required"),
                            "message": "Google whitelist authentication required.",
                            "login_url": cfg["gate_login_url"],
                        }
                    },
                )
                return

            lowered = {k.lower(): v for k, v in self.headers.items()}
            fwd_host = (lowered.get("x-forwarded-host") or "").strip().lower()
            fwd_proto = (lowered.get("x-forwarded-proto") or "https").strip().lower()
            fwd_uri = (lowered.get("x-forwarded-uri") or "/").strip()
            candidate = (
                f"{fwd_proto}://{fwd_host}{fwd_uri}" if fwd_host else cfg["portal_url"]
            )
            validated_next = validate_next_url(candidate, cfg=cfg)
            login_redirect = (
                f"{cfg['gate_login_url'].rstrip('/')}/?"
                + urllib.parse.urlencode({"next": validated_next})
            )
            self._send_redirect(login_redirect)
            return

        if path == "/wahs/gate":
            raw_next = (qs.get("next") or [""])[0]
            next_url = validate_next_url(raw_next, cfg=cfg)
            switch_mode = (qs.get("switch") or [""])[0] == "1"
            session = self._current_session(cfg)
            if session.get("authorized") and not switch_mode:
                self._send_redirect(next_url)
                return
            self._send_html(200, render_gate_login_html(next_url=next_url, cfg=cfg))
            return

        if path == "/wahs/gate/logout":
            expired_cookie = _build_session_set_cookie_header(
                "", max_age=0, cfg=cfg
            )
            self._send_redirect(
                f"{cfg['gate_login_url'].rstrip('/')}/?switch=1",
                extra_headers=[("Set-Cookie", expired_cookie)],
            )
            return

        if path == "/api/portal-status":
            session = self._current_session(cfg)
            hdr_email = (self.headers.get("X-WAHS-Auth-Email") or "").strip().lower()
            if not session.get("authorized") and hdr_email not in cfg["whitelist"]:
                self._send_json(401, {"error": "Unauthorized"})
                return
            services = {
                name: _probe_service(url) for name, url in cfg["probe_urls"].items()
            }
            self._send_json(
                200,
                {
                    "user": {
                        "email": session.get("email") or hdr_email,
                        "name": session.get("name")
                        or self.headers.get("X-WAHS-Auth-Name")
                        or hdr_email,
                    },
                    "services": services,
                    "seeded_accounts_count": len(SEEDED_DEMO_ACCOUNTS),
                },
            )
            return

        if path == "/":
            session = self._current_session(cfg)
            user_email = (
                session.get("email")
                or (self.headers.get("X-WAHS-Auth-Email") or "").strip().lower()
            )
            user_name = (
                session.get("name")
                or (self.headers.get("X-WAHS-Auth-Name") or "").strip()
                or user_email
            )
            if not user_email or user_email not in cfg["whitelist"]:
                next_qs = urllib.parse.urlencode({"next": cfg["portal_url"]})
                self._send_redirect(f"{cfg['gate_login_url'].rstrip('/')}/?{next_qs}")
                return
            self._send_html(
                200,
                render_portal_html(
                    user_email=user_email, user_name=user_name, cfg=cfg
                ),
            )
            return

        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        cfg = get_config()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/wahs/gate/api/logout":
            expired_cookie = _build_session_set_cookie_header(
                "", max_age=0, cfg=cfg
            )
            self._send_json(
                200,
                {"ok": True},
                extra_headers=[("Set-Cookie", expired_cookie)],
            )
            return

        if path == "/wahs/gate/api/session":
            try:
                content_len = int(self.headers.get("Content-Length") or "0")
                raw_body = self.rfile.read(content_len) if content_len > 0 else b"{}"
                body = json.loads(raw_body.decode("utf-8"))
            except Exception:
                self._send_json(
                    400,
                    {"error": {"code": "invalid_json", "message": "Invalid JSON body."}},
                )
                return

            id_token = str((body or {}).get("id_token") or "").strip()
            verdict = verify_google_auth_token(id_token)
            if not verdict.get("authenticated"):
                self._send_json(401, {"error": verdict})
                return
            if not verdict.get("authorized"):
                self._send_json(403, {"error": verdict})
                return

            cookie_val = sign_session_cookie(
                email=verdict["email"],
                name=verdict.get("name") or "",
                picture=verdict.get("picture") or "",
                cfg=cfg,
            )
            set_cookie = _build_session_set_cookie_header(
                cookie_val, max_age=cfg["session_ttl"], cfg=cfg
            )
            redirect_to = validate_next_url(str((body or {}).get("next") or ""), cfg=cfg)
            self._send_json(
                200,
                {
                    "ok": True,
                    "email": verdict["email"],
                    "name": verdict.get("name") or "",
                    "redirect_to": redirect_to,
                },
                extra_headers=[("Set-Cookie", set_cookie)],
            )
            return

        self._send_json(404, {"error": "Not found"})


class GateHTTPServer(ThreadingHTTPServer):
    request_queue_size = 256
    daemon_threads = True
    allow_reuse_address = True


def create_server(host: str = "0.0.0.0", port: int = 8096) -> ThreadingHTTPServer:
    return GateHTTPServer((host, port), GateRequestHandler)


if __name__ == "__main__":
    listen_port = int(os.environ.get("PORT") or "8096")
    server = create_server("0.0.0.0", listen_port)
    print(f"WAHS Cloud Auth Gate listening on 0.0.0.0:{listen_port}", flush=True)
    server.serve_forever()

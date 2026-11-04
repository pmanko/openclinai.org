"""WAHS UW GPU Auth Relay Service (`wahs/gpu-auth-relay/app.py`).

Standalone zero-dependency HTTP/SSE relay service scoped strictly to the
WA Health Summary (WAHS) project. Enforces Google Sign-In email whitelist
authentication before proxying OpenAI-compatible `/v1/models` and
`/v1/chat/completions` requests to the shared UW CIRG LiteLLM GPU server
(`https://llm.co.dev.cirg.uw.edu`).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple

DEFAULT_GPU_BASE_URL = "https://llm.co.dev.cirg.uw.edu"
DEFAULT_GOOGLE_CLIENT_ID = (
    "1043771833056-41q5npi9me4i390i87b2tha58rt5blb9.apps.googleusercontent.com"
)
DEFAULT_WHITELIST_EMAILS = (
    "piotr.mankowski@gmail.com,"
    "pmanko@uw.edu,"
    "ivanc@uw.edu,"
    "mcjustin@uw.edu,"
    "jflow2@uw.edu,"
    "lober@uw.edu,"
    "ibacher@uw.edu"
)
DEFAULT_GPU_MODELS = (
    "ollama/gemma4:26b,"
    "ollama/gemma4:12b,"
    "ollama/gemma4:e4b,"
    "ollama/gemma4:e2b,"
    "ollama/qwen3:14b,"
    "ollama/qwen2.5:14b,"
    "ollama/qwen3:8b,"
    "ollama/qwen3:4b,"
    "ollama/llama3.1:8b,"
    "ollama/mistral-nemo:12b,"
    "ollama/mistral:7b,"
    "ollama/granite3.3:8b,"
    "ollama/smollm2:latest"
)

GPU_MODEL_ALIASES: Dict[str, str] = {
    "wahs-26b-kb": "ollama/gemma4:26b",
    "wahs-26b-raw": "ollama/gemma4:26b",
    "wahs-12b-kb": "ollama/gemma4:12b",
    "wahs-12b-raw": "ollama/gemma4:12b",
    "wahs-12b-q4-kb": "ollama/gemma4:12b",
    "wahs-12b-q4-raw": "ollama/gemma4:12b",
    "wahs-e4b-kb": "ollama/gemma4:e4b",
    "wahs-e4b-raw": "ollama/gemma4:e4b",
    "wahs-e4b-q8-kb": "ollama/gemma4:e4b",
    "wahs-e4b-q8-raw": "ollama/gemma4:e4b",
    "wahs-e2b-kb": "ollama/gemma4:e2b",
    "wahs-e2b-raw": "ollama/gemma4:e2b",
    "wahs-qwen3-14b-kb": "ollama/qwen3:14b",
    "wahs-qwen3-14b-raw": "ollama/qwen3:14b",
    "wahs-qwen25-14b-kb": "ollama/qwen2.5:14b",
    "wahs-qwen25-14b-raw": "ollama/qwen2.5:14b",
    "wahs-qwen35-9b-kb": "ollama/qwen3:8b",
    "wahs-qwen35-9b-raw": "ollama/qwen3:8b",
    "wahs-qwen3-4b-kb": "ollama/qwen3:4b",
    "wahs-qwen3-4b-raw": "ollama/qwen3:4b",
    "wahs-llama31-8b-kb": "ollama/llama3.1:8b",
    "wahs-llama31-8b-raw": "ollama/llama3.1:8b",
    "wahs-mistral-nemo-12b-kb": "ollama/mistral-nemo:12b",
    "wahs-mistral-nemo-12b-raw": "ollama/mistral-nemo:12b",
    "wahs-granite33-8b-kb": "ollama/granite3.3:8b",
    "wahs-granite33-8b-raw": "ollama/granite3.3:8b",
    "gemma-26b": "ollama/gemma4:26b",
    "gemma4:26b": "ollama/gemma4:26b",
    "gemma-4-12b": "ollama/gemma4:12b",
    "gemma-4-12b-q4": "ollama/gemma4:12b",
    "gemma4:12b": "ollama/gemma4:12b",
    "gemma-e4b": "ollama/gemma4:e4b",
    "gemma-e4b-q8": "ollama/gemma4:e4b",
    "gemma4:e4b": "ollama/gemma4:e4b",
    "gemma-e2b": "ollama/gemma4:e2b",
    "gemma4:e2b": "ollama/gemma4:e2b",
    "qwen3-14b": "ollama/qwen3:14b",
    "qwen3:14b": "ollama/qwen3:14b",
    "qwen2.5-14b": "ollama/qwen2.5:14b",
    "qwen2.5:14b": "ollama/qwen2.5:14b",
    "qwen3.5-9b": "ollama/qwen3:8b",
    "qwen3-8b": "ollama/qwen3:8b",
    "qwen3:8b": "ollama/qwen3:8b",
    "qwen3-4b": "ollama/qwen3:4b",
    "qwen3:4b": "ollama/qwen3:4b",
    "llama-3.1-8b": "ollama/llama3.1:8b",
    "llama3.1:8b": "ollama/llama3.1:8b",
    "mistral-nemo-12b": "ollama/mistral-nemo:12b",
    "mistral-nemo:12b": "ollama/mistral-nemo:12b",
    "mistral:7b": "ollama/mistral:7b",
    "mistral-7b": "ollama/mistral:7b",
    "granite-3.3-8b": "ollama/granite3.3:8b",
    "granite3.3:8b": "ollama/granite3.3:8b",
    "smollm2:latest": "ollama/smollm2:latest",
    "smollm2": "ollama/smollm2:latest",
}

INTERNAL_ROUTER_ADVERTISED_ALIASES: Tuple[str, ...] = (
    "gemma-26b",
    "gemma-4-12b",
    "gemma-4-12b-q4",
    "gemma-e4b",
    "gemma-e4b-q8",
    "gemma-e2b",
    "qwen3-14b",
    "qwen2.5-14b",
    "qwen3.5-9b",
    "qwen3-4b",
    "llama-3.1-8b",
    "mistral-nemo-12b",
    "granite-3.3-8b",
)

FALLBACK_CLOUD_HUB_PROFILES: Tuple[Tuple[str, str, str, str, int], ...] = (
    ("wahs-26b-kb", "WAHS+ Gemma 4 26B-A4B MoE (UW GPU) + 4-Layer Clinical KB", "gemma-26b", "gemma-4", 5),
    ("wahs-26b-raw", "WAHS+ Gemma 4 26B-A4B MoE (UW GPU) Raw Condensed Chart", "gemma-26b", "gemma-4", 6),
    ("wahs-12b-kb", "WAHS+ Gemma 4 12B (UW GPU) + 4-Layer Clinical KB", "gemma-4-12b", "gemma-4", 10),
    ("wahs-12b-raw", "WAHS+ Gemma 4 12B (UW GPU) Raw Condensed Chart", "gemma-4-12b", "gemma-4", 11),
    ("wahs-12b-q4-kb", "WAHS+ Gemma 4 12B Q4 (UW GPU) + 4-Layer Clinical KB", "gemma-4-12b-q4", "gemma-4", 20),
    ("wahs-12b-q4-raw", "WAHS+ Gemma 4 12B Q4 (UW GPU) Raw Condensed Chart", "gemma-4-12b-q4", "gemma-4", 21),
    ("wahs-e4b-kb", "WAHS+ Gemma 4 E4B (UW GPU) + 4-Layer Clinical KB", "gemma-e4b", "gemma-4", 30),
    ("wahs-e4b-raw", "WAHS+ Gemma 4 E4B (UW GPU) Raw Condensed Chart", "gemma-e4b", "gemma-4", 31),
    ("wahs-e4b-q8-kb", "WAHS+ Gemma 4 E4B Q8 (UW GPU) + 4-Layer Clinical KB", "gemma-e4b-q8", "gemma-4", 40),
    ("wahs-e4b-q8-raw", "WAHS+ Gemma 4 E4B Q8 (UW GPU) Raw Condensed Chart", "gemma-e4b-q8", "gemma-4", 41),
    ("wahs-e2b-kb", "WAHS+ Gemma 4 E2B (UW GPU) + 4-Layer Clinical KB", "gemma-e2b", "gemma-4", 50),
    ("wahs-e2b-raw", "WAHS+ Gemma 4 E2B (UW GPU) Raw Condensed Chart", "gemma-e2b", "gemma-4", 51),
    ("wahs-qwen3-14b-kb", "WAHS+ Qwen 3 14B (UW GPU) + 4-Layer Clinical KB", "qwen3-14b", "qwen", 60),
    ("wahs-qwen3-14b-raw", "WAHS+ Qwen 3 14B (UW GPU) Raw Condensed Chart", "qwen3-14b", "qwen", 61),
    ("wahs-qwen25-14b-kb", "WAHS+ Qwen 2.5 14B (UW GPU) + 4-Layer Clinical KB", "qwen2.5-14b", "qwen", 65),
    ("wahs-qwen25-14b-raw", "WAHS+ Qwen 2.5 14B (UW GPU) Raw Condensed Chart", "qwen2.5-14b", "qwen", 66),
    ("wahs-qwen35-9b-kb", "WAHS+ Qwen 3 8B (UW GPU) + 4-Layer Clinical KB", "qwen3.5-9b", "qwen", 70),
    ("wahs-qwen35-9b-raw", "WAHS+ Qwen 3 8B (UW GPU) Raw Condensed Chart", "qwen3.5-9b", "qwen", 71),
    ("wahs-qwen3-4b-kb", "WAHS+ Qwen 3 4B (UW GPU) + 4-Layer Clinical KB", "qwen3-4b", "qwen", 75),
    ("wahs-qwen3-4b-raw", "WAHS+ Qwen 3 4B (UW GPU) Raw Condensed Chart", "qwen3-4b", "qwen", 76),
    ("wahs-llama31-8b-kb", "WAHS+ Llama 3.1 8B (UW GPU) + 4-Layer Clinical KB", "llama-3.1-8b", "llama", 80),
    ("wahs-llama31-8b-raw", "WAHS+ Llama 3.1 8B (UW GPU) Raw Condensed Chart", "llama-3.1-8b", "llama", 81),
    ("wahs-mistral-nemo-12b-kb", "WAHS+ Mistral Nemo 12B (UW GPU) + 4-Layer Clinical KB", "mistral-nemo-12b", "mistral", 85),
    ("wahs-mistral-nemo-12b-raw", "WAHS+ Mistral Nemo 12B (UW GPU) Raw Condensed Chart", "mistral-nemo-12b", "mistral", 86),
    ("wahs-granite33-8b-kb", "WAHS+ Granite 3.3 8B (UW GPU) + 4-Layer Clinical KB", "granite-3.3-8b", "granite", 90),
    ("wahs-granite33-8b-raw", "WAHS+ Granite 3.3 8B (UW GPU) Raw Condensed Chart", "granite-3.3-8b", "granite", 91),
)

_HUB_MODELS_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}

GPU_MODEL_LABELS: Dict[str, Dict[str, Any]] = {
    "ollama/gemma4:26b": {
        "label": "Gemma 4 26B-A4B MoE (UW GPU)",
        "family": "gemma-4",
        "parameter_size": "26B (4B active)",
        "context_length": 262144,
        "sweet_spot_tokens": 32768,
    },
    "ollama/gemma4:12b": {
        "label": "Gemma 4 12B (UW GPU)",
        "family": "gemma-4",
        "parameter_size": "12B",
        "context_length": 262144,
        "sweet_spot_tokens": 24576,
    },
    "ollama/gemma4:e4b": {
        "label": "Gemma 4 E4B (UW GPU)",
        "family": "gemma-4",
        "parameter_size": "7.5B (4B eff.)",
        "context_length": 131072,
        "sweet_spot_tokens": 16384,
    },
    "ollama/gemma4:e2b": {
        "label": "Gemma 4 E2B (UW GPU)",
        "family": "gemma-4",
        "parameter_size": "4.6B (2B eff.)",
        "context_length": 131072,
        "sweet_spot_tokens": 12288,
    },
    "ollama/qwen3:14b": {
        "label": "Qwen 3 14B (UW GPU)",
        "family": "qwen",
        "parameter_size": "14.8B",
        "context_length": 262144,
        "sweet_spot_tokens": 24576,
    },
    "ollama/qwen2.5:14b": {
        "label": "Qwen 2.5 14B Instruct (UW GPU)",
        "family": "qwen",
        "parameter_size": "14.8B",
        "context_length": 131072,
        "sweet_spot_tokens": 24576,
    },
    "ollama/qwen3:8b": {
        "label": "Qwen 3 8B (UW GPU)",
        "family": "qwen",
        "parameter_size": "8.2B",
        "context_length": 131072,
        "sweet_spot_tokens": 16384,
    },
    "ollama/qwen3:4b": {
        "label": "Qwen 3 4B (UW GPU)",
        "family": "qwen",
        "parameter_size": "4.0B",
        "context_length": 131072,
        "sweet_spot_tokens": 12288,
    },
    "ollama/llama3.1:8b": {
        "label": "Llama 3.1 8B Instruct (UW GPU)",
        "family": "llama",
        "parameter_size": "8.0B",
        "context_length": 131072,
        "sweet_spot_tokens": 16384,
    },
    "ollama/mistral-nemo:12b": {
        "label": "Mistral Nemo 12B Instruct (UW GPU)",
        "family": "mistral",
        "parameter_size": "12.2B",
        "context_length": 131072,
        "sweet_spot_tokens": 24576,
    },
    "ollama/mistral:7b": {
        "label": "Mistral 7B Instruct (UW GPU)",
        "family": "mistral",
        "parameter_size": "7.2B",
        "context_length": 32768,
        "sweet_spot_tokens": 12288,
    },
    "ollama/granite3.3:8b": {
        "label": "Granite 3.3 8B Instruct (UW GPU)",
        "family": "granite",
        "parameter_size": "8.2B",
        "context_length": 131072,
        "sweet_spot_tokens": 16384,
    },
    "ollama/smollm2:latest": {
        "label": "SmolLM2 1.7B Instruct (UW GPU)",
        "family": "smollm2",
        "parameter_size": "1.7B",
        "context_length": 8192,
        "sweet_spot_tokens": 4096,
    },
}

_TOKEN_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_TOKEN_CACHE_TTL_SECONDS = 300.0

CORS_HEADERS: Dict[str, str] = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": (
        "Content-Type, Authorization, X-WAHS-Auth-Token, X-Google-Auth-Token, X-OpenRouter-Key"
    ),
    "Access-Control-Expose-Headers": "X-WAHS-Auth-Email",
}


def get_config() -> Dict[str, Any]:
    base_url = (
        os.getenv("WAHS_GPU_BASE_URL") or DEFAULT_GPU_BASE_URL
    ).strip().rstrip("/")
    up_token = (os.getenv("WAHS_GPU_API_KEY") or "").strip()
    raw_whitelist = (
        os.getenv("WAHS_AUTH_WHITELIST_EMAILS") or DEFAULT_WHITELIST_EMAILS
    )
    whitelist: Set[str] = {
        email.strip().lower()
        for email in raw_whitelist.split(",")
        if email.strip()
    }
    client_id = (
        os.getenv("WAHS_GOOGLE_CLIENT_ID") or DEFAULT_GOOGLE_CLIENT_ID
    ).strip()
    fb_key = (
        os.getenv("WAHS_FIREBASE_WEB_KEY")
        or os.getenv("WAHS_FIREBASE_API_KEY")
        or ""
    ).strip()
    raw_models = os.getenv("WAHS_GPU_MODELS") or DEFAULT_GPU_MODELS
    configured_models = [
        m.strip() for m in raw_models.split(",") if m.strip()
    ]
    try:
        timeout_seconds = float(
            os.getenv("WAHS_GPU_TIMEOUT_SECONDS") or "120"
        )
    except ValueError:
        timeout_seconds = 120.0
    cloud_hub_url = (
        os.getenv("WAHS_CLOUD_HUB_URL") or ""
    ).strip().rstrip("/")
    internal_router_key = (
        os.getenv("WAHS_INTERNAL_ROUTER_KEY") or ""
    ).strip()
    return {
        "base_url": base_url,
        "api_key": up_token,
        "whitelist": whitelist,
        "client_id": client_id,
        "fb_key": fb_key,
        "configured_models": configured_models,
        "timeout_seconds": timeout_seconds,
        "cloud_hub_url": cloud_hub_url,
        "internal_router_key": internal_router_key,
    }


def extract_auth_token(headers: Mapping[str, str]) -> str:
    lowered = {k.lower(): v for k, v in headers.items()}
    for hdr in ("x-wahs-auth-token", "x-google-auth-token"):
        header_tok = (lowered.get(hdr) or "").strip()
        if header_tok:
            return header_tok
    auth_header = (lowered.get("authorization") or "").strip()
    if auth_header.lower().startswith("bearer "):
        candidate = auth_header[7:].strip()
        if candidate and not candidate.startswith("sk-"):
            return candidate
    return ""


def resolve_gpu_model_id(raw_model: str) -> str:
    clean = str(raw_model or "").strip()
    if clean.startswith(("wahs-kb:", "wahs-raw:")):
        _, _, clean = clean.partition(":")
        clean = clean.strip()
    if clean in GPU_MODEL_ALIASES:
        return GPU_MODEL_ALIASES[clean]
    if clean.startswith("ollama/"):
        return clean
    return f"ollama/{clean}" if ":" in clean and "/" not in clean else clean


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
            "message": (
                "Google Sign-In is required to access the UW CIRG GPU server. "
                "Please sign in with a whitelisted Google account."
            ),
            "client_id": client_id,
            "fb_web_key": fb_key,
            "whitelist_count": len(whitelist),
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
                f"Signed in as {email} (whitelisted)."
                if authorized
                else f"Account {email} is not on the UW GPU server access whitelist."
            ),
            "client_id": client_id,
            "fb_web_key": fb_key,
            "whitelist_count": len(whitelist),
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
            info = data1

        if info is None:
            data2 = _http_get_json(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {clean}"},
            )
            if data2 and data2.get("email"):
                info = data2

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
                }

        if info is None:
            return {
                "authenticated": False,
                "authorized": False,
                "code": "invalid_token",
                "message": (
                    "Google session token expired or could not be verified. "
                    "Please sign in again."
                ),
                "client_id": client_id,
                "fb_web_key": fb_key,
                "whitelist_count": len(whitelist),
            }
        _TOKEN_CACHE[token_hash] = (now, info)

    email = str(info.get("email") or "").strip().lower()
    email_verified = str(info.get("email_verified", "true")).lower() in (
        "true",
        "1",
    )
    if not email or not email_verified:
        return {
            "authenticated": False,
            "authorized": False,
            "code": "unverified_email",
            "message": "Google account email is not verified.",
            "client_id": client_id,
            "fb_web_key": fb_key,
            "whitelist_count": len(whitelist),
        }

    aud = str(info.get("aud") or "").strip()
    if client_id and aud and aud != client_id and not info.get("sub"):
        return {
            "authenticated": False,
            "authorized": False,
            "code": "audience_mismatch",
            "message": "Google ID token audience does not match configured client ID.",
            "client_id": client_id,
            "fb_web_key": fb_key,
            "whitelist_count": len(whitelist),
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
            f"Signed in as {email} (whitelisted)."
            if authorized
            else f"Google account '{email}' is not on the UW GPU server access whitelist."
        ),
        "client_id": client_id,
        "fb_web_key": fb_key,
        "whitelist_count": len(whitelist),
    }


def build_models_payload(verdict: Dict[str, Any]) -> Dict[str, Any]:
    cfg = get_config()
    discovered_ids: List[str] = list(cfg["configured_models"])
    upstream_reachable = False

    if cfg["api_key"]:
        upstream_payload = _http_get_json(
            f"{cfg['base_url']}/v1/models",
            headers={"Authorization": f"Bearer {cfg['api_key']}"},
            timeout=8.0,
        )
        if upstream_payload is not None:
            upstream_reachable = True
            for item in upstream_payload.get("data") or []:
                mid = str((item or {}).get("id") or "").strip()
                if (
                    mid
                    and mid != "all-proxy-models"
                    and mid not in discovered_ids
                ):
                    discovered_ids.append(mid)

    now_ts = int(time.time())
    data: List[Dict[str, Any]] = []
    for mid in discovered_ids:
        meta = GPU_MODEL_LABELS.get(mid, {})
        rec_limit = meta.get("sweet_spot_tokens") or 16384
        data.append(
            {
                "id": mid,
                "object": "model",
                "created": now_ts,
                "owned_by": "uw-cirg-gpu",
                "label": meta.get("label") or f"{mid} (UW GPU)",
                "model_family": meta.get("family") or "ollama",
                "parameter_size": meta.get("parameter_size") or "",
                "context_length": meta.get("context_length") or 131072,
                "recommended_limit_tokens": rec_limit,
                "recommended_limit_url": "/reports/2026-11-02-wahs-simple-profiles-multi-family-eval/index.html",
                "sweet_spot_tokens": rec_limit,
            }
        )

    return {
        "object": "list",
        "data": data,
        "backend": {
            "service": "wahs-gpu-auth-relay",
            "upstream_base_url": cfg["base_url"],
            "upstream_reachable": upstream_reachable,
            "gpu_auth": verdict,
        },
    }


def verify_internal_router_access(headers: Mapping[str, str]) -> bool:
    cfg = get_config()
    expected_key = cfg["internal_router_key"]
    lowered = {k.lower(): v for k, v in headers.items()}
    auth_header = (lowered.get("authorization") or "").strip()
    bearer = (
        auth_header[7:].strip()
        if auth_header.lower().startswith("bearer ")
        else ""
    )
    if expected_key and bearer == expected_key:
        return True
    token = extract_auth_token(headers)
    if token:
        verdict = verify_google_auth_token(token)
        if verdict.get("authorized"):
            return True
    return not expected_key


def build_internal_router_models_payload() -> Dict[str, Any]:
    cfg = get_config()
    now_ts = int(time.time())
    data: List[Dict[str, Any]] = []
    seen = set()
    for alias in INTERNAL_ROUTER_ADVERTISED_ALIASES:
        target = GPU_MODEL_ALIASES.get(alias, alias)
        seen.add(alias)
        data.append(
            {
                "id": alias,
                "object": "model",
                "created": now_ts,
                "owned_by": "llamacpp",
                "upstream_model": target,
                "status": {"value": "loaded"},
            }
        )
    for mid in cfg["configured_models"]:
        if mid in seen:
            continue
        seen.add(mid)
        data.append(
            {
                "id": mid,
                "object": "model",
                "created": now_ts,
                "owned_by": "uw-cirg-gpu",
                "status": {"value": "loaded"},
            }
        )
    return {
        "object": "list",
        "data": data,
    }


def build_fallback_cloud_hub_models_payload(verdict: Dict[str, Any]) -> Dict[str, Any]:
    cfg = get_config()
    now_ts = int(time.time())
    data: List[Dict[str, Any]] = []
    for pid, label, role_model, fam, prio in FALLBACK_CLOUD_HUB_PROFILES:
        include_kb = not pid.endswith("-raw")
        upstream_id = GPU_MODEL_ALIASES.get(role_model, "")
        gpu_meta = GPU_MODEL_LABELS.get(upstream_id, {})
        ctx_len = gpu_meta.get("context_length") or 131072
        rec_limit = gpu_meta.get("sweet_spot_tokens") or 24576
        data.append(
            {
                "id": pid,
                "object": "model",
                "created": now_ts,
                "owned_by": "med-agent-hub",
                "label": label,
                "workflow": "wahs",
                "visibility": "product",
                "available": True,
                "unavailable_reasons": [],
                "topology": "single",
                "provider": "local",
                "model_family": fam,
                "selection_priority": prio,
                "context_window": rec_limit,
                "context_length": ctx_len,
                "recommended_limit_tokens": rec_limit,
                "recommended_limit_url": "/reports/2026-11-02-wahs-simple-profiles-multi-family-eval/index.html",
                "stages": ["context", "answer", "gate"],
                "role_models": {"answer": role_model},
                "required_models": [role_model],
                "role_knobs": {
                    "answer": {"temperature": 0.1, "maxTokens": 4096, "dry": 0.0}
                },
                "policies": {
                    "provider": "local",
                    "model_family": fam,
                    "include_kb_findings": include_kb,
                    "overflow_lookup_tools": include_kb,
                    "citation_grounding": "enforce",
                },
                "prompts": {
                    "answer": "wahs-kb-guided" if include_kb else "wahs-raw-unhinted"
                },
            }
        )
    return {
        "object": "list",
        "data": data,
        "backend": {
            "service": "wahs-cloud-med-agent-hub-fallback",
            "cloud_hub_url": cfg["cloud_hub_url"],
            "gpu_auth": verdict,
        },
    }


class RelayRequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(
        self,
        status_code: int,
        payload: Dict[str, Any],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        raw = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        if extra_headers:
            for k, v in extra_headers.items():
                self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _send_auth_error(self, verdict: Dict[str, Any]) -> None:
        status_code = 403 if verdict.get("authenticated") else 401
        self._send_json(
            status_code,
            {
                "error": {
                    "code": verdict.get("code", "unauthorized"),
                    "type": "gpu_whitelist_auth_error",
                    "message": verdict.get("message", "Unauthorized"),
                    "email": verdict.get("email"),
                    "authenticated": bool(verdict.get("authenticated")),
                    "authorized": bool(verdict.get("authorized")),
                    "client_id": verdict.get("client_id", ""),
                    "fb_web_key": verdict.get("fb_web_key", ""),
                }
            },
        )

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        for k, v in CORS_HEADERS.items():
            self.send_header(k, v)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            cfg = get_config()
            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "wahs-gpu-auth-relay",
                    "upstream_base_url": cfg["base_url"],
                    "cloud_hub_url": cfg["cloud_hub_url"],
                    "api_key_configured": bool(cfg["api_key"]),
                    "whitelist_count": len(cfg["whitelist"]),
                },
            )
            return

        if path == "/internal-router/v1/models":
            if not verify_internal_router_access(dict(self.headers)):
                self._send_json(
                    401,
                    {
                        "error": {
                            "code": "internal_router_unauthorized",
                            "message": "Valid internal router key or whitelisted Google token required.",
                        }
                    },
                )
                return
            self._send_json(200, build_internal_router_models_payload())
            return

        if path == "/hub/health":
            cfg = get_config()
            if not cfg["cloud_hub_url"]:
                self._send_json(
                    503,
                    {
                        "error": {
                            "code": "cloud_hub_not_configured",
                            "message": "WAHS_CLOUD_HUB_URL is not configured on the relay server.",
                        }
                    },
                )
                return
            hub_health = _http_get_json(f"{cfg['cloud_hub_url']}/health", timeout=8.0)
            if hub_health is None:
                self._send_json(
                    502,
                    {
                        "error": {
                            "code": "cloud_hub_unreachable",
                            "message": "Cloud Med Agent Hub health check failed.",
                        }
                    },
                )
                return
            self._send_json(200, hub_health)
            return

        if path == "/hub/v1/models":
            token = extract_auth_token(dict(self.headers))
            verdict = verify_google_auth_token(token)
            if not verdict.get("authorized"):
                self._send_auth_error(verdict)
                return
            cfg = get_config()
            if not cfg["cloud_hub_url"]:
                self._send_json(
                    503,
                    {
                        "error": {
                            "code": "cloud_hub_not_configured",
                            "message": "WAHS_CLOUD_HUB_URL is not configured on the relay server.",
                        }
                    },
                )
                return
            qs = f"?{parsed.query}" if parsed.query else "?workflow=wahs"
            hub_url = f"{cfg['cloud_hub_url']}/v1/models{qs}"
            hub_payload = _http_get_json(hub_url, headers={}, timeout=20.0)
            if hub_payload is None:
                hub_payload = _http_get_json(hub_url, headers={}, timeout=15.0)
            if hub_payload is None:
                cached_hub = _HUB_MODELS_CACHE.get(qs)
                if cached_hub is not None:
                    hub_payload = json.loads(json.dumps(cached_hub[1]))
            if hub_payload is None:
                self._send_json(
                    502,
                    {
                        "error": {
                            "code": "cloud_hub_unreachable",
                            "message": "Failed to reach Cloud Med Agent Hub /v1/models.",
                        }
                    },
                )
                return
            advertised_set = set(INTERNAL_ROUTER_ADVERTISED_ALIASES)
            for item in hub_payload.get("data") or []:
                if not isinstance(item, dict):
                    continue
                req_models = item.get("required_models") or []
                if req_models and all(str(rm) in advertised_set for rm in req_models):
                    item["available"] = True
                    item["unavailable_reasons"] = []
            _HUB_MODELS_CACHE[qs] = (time.time(), json.loads(json.dumps(hub_payload)))
            backend_meta = dict(hub_payload.get("backend") or {})
            backend_meta["gpu_auth"] = verdict
            backend_meta["cloud_hub_url"] = cfg["cloud_hub_url"]
            hub_payload["backend"] = backend_meta
            self._send_json(
                200,
                hub_payload,
                extra_headers={"X-WAHS-Auth-Email": str(verdict.get("email") or "")},
            )
            return

        if path == "/v1/auth/status":
            token = extract_auth_token(dict(self.headers))
            verdict = verify_google_auth_token(token)
            self._send_json(200, verdict)
            return

        if path == "/v1/models":
            token = extract_auth_token(dict(self.headers))
            verdict = verify_google_auth_token(token)
            if not verdict.get("authorized"):
                self._send_auth_error(verdict)
                return
            payload = build_models_payload(verdict)
            self._send_json(
                200,
                payload,
                extra_headers={"X-WAHS-Auth-Email": str(verdict.get("email") or "")},
            )
            return

        self._send_json(404, {"error": {"code": "not_found", "message": "Not found"}})

    def do_POST(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path not in (
            "/v1/chat/completions",
            "/internal-router/v1/chat/completions",
            "/hub/v1/chat/completions",
        ):
            self._send_json(404, {"error": {"code": "not_found", "message": "Not found"}})
            return

        cfg = get_config()

        if path == "/internal-router/v1/chat/completions":
            if not verify_internal_router_access(dict(self.headers)):
                self._send_json(
                    401,
                    {
                        "error": {
                            "code": "internal_router_unauthorized",
                            "message": "Valid internal router key or whitelisted Google token required.",
                        }
                    },
                )
                return
            verdict: Dict[str, Any] = {"email": "cloud-med-agent-hub"}
        else:
            token = extract_auth_token(dict(self.headers))
            verdict = verify_google_auth_token(token)
            if not verdict.get("authorized"):
                self._send_auth_error(verdict)
                return

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

        fallback_req: Optional[urllib.request.Request] = None
        if path == "/hub/v1/chat/completions":
            if not cfg["cloud_hub_url"]:
                self._send_json(
                    503,
                    {
                        "error": {
                            "code": "cloud_hub_not_configured",
                            "message": "WAHS_CLOUD_HUB_URL is not configured on the relay server.",
                        }
                    },
                )
                return
            upstream_url = f"{cfg['cloud_hub_url']}/v1/chat/completions"
            upstream_payload = dict(body)
            upstream_headers = {
                "Content-Type": "application/json",
                "Accept": (
                    "text/event-stream"
                    if upstream_payload.get("stream")
                    else "application/json"
                ),
            }
            if cfg["api_key"]:
                raw_model = str(body.get("model") or "ollama/gemma4:12b").strip()
                fb_payload = dict(body)
                fb_model = resolve_gpu_model_id(raw_model)
                fb_payload["model"] = fb_model
                if "reasoning_effort" not in fb_payload:
                    fb_payload["reasoning_effort"] = "none"
                if fb_model.startswith("ollama/qwen3") and fb_payload.get("reasoning_effort") == "none":
                    fb_msgs = [dict(m) for m in (fb_payload.get("messages") or []) if isinstance(m, dict)]
                    if fb_msgs and isinstance(fb_msgs[-1].get("content"), str) and "/no_think" not in fb_msgs[-1]["content"]:
                        fb_msgs[-1]["content"] = fb_msgs[-1]["content"].rstrip() + " /no_think"
                        fb_payload["messages"] = fb_msgs
                fallback_req = urllib.request.Request(
                    f"{cfg['base_url']}/v1/chat/completions",
                    data=json.dumps(fb_payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {cfg['api_key']}",
                        "Content-Type": "application/json",
                        "Accept": upstream_headers["Accept"],
                    },
                    method="POST",
                )
        else:
            if not cfg["api_key"]:
                self._send_json(
                    503,
                    {
                        "error": {
                            "code": "gpu_api_key_not_configured",
                            "message": "WAHS_GPU_API_KEY is not configured on the relay server.",
                        }
                    },
                )
                return
            raw_model = str(body.get("model") or "ollama/gemma4:12b").strip()
            upstream_model = resolve_gpu_model_id(raw_model)

            upstream_payload = dict(body)
            upstream_payload["model"] = upstream_model
            if "reasoning_effort" not in upstream_payload:
                upstream_payload["reasoning_effort"] = "none"
            if upstream_model.startswith("ollama/qwen3") and upstream_payload.get("reasoning_effort") == "none":
                up_msgs = [dict(m) for m in (upstream_payload.get("messages") or []) if isinstance(m, dict)]
                if up_msgs and isinstance(up_msgs[-1].get("content"), str) and "/no_think" not in up_msgs[-1]["content"]:
                    up_msgs[-1]["content"] = up_msgs[-1]["content"].rstrip() + " /no_think"
                    upstream_payload["messages"] = up_msgs

            upstream_url = f"{cfg['base_url']}/v1/chat/completions"
            upstream_headers = {
                "Authorization": f"Bearer {cfg['api_key']}",
                "Content-Type": "application/json",
                "Accept": (
                    "text/event-stream"
                    if upstream_payload.get("stream")
                    else "application/json"
                ),
            }
        req_data = json.dumps(upstream_payload).encode("utf-8")
        req = urllib.request.Request(
            upstream_url,
            data=req_data,
            headers=upstream_headers,
            method="POST",
        )
        is_stream = bool(upstream_payload.get("stream"))

        if is_stream:
            headers_sent = False
            try:
                try:
                    resp_ctx = urllib.request.urlopen(req, timeout=cfg["timeout_seconds"])
                except Exception:
                    if fallback_req is not None:
                        resp_ctx = urllib.request.urlopen(
                            fallback_req, timeout=cfg["timeout_seconds"]
                        )
                    else:
                        raise
                with resp_ctx as resp:
                    self.send_response(200)
                    for k, v in CORS_HEADERS.items():
                        self.send_header(k, v)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.send_header(
                        "X-WAHS-Auth-Email", str(verdict.get("email") or "")
                    )
                    self.end_headers()
                    headers_sent = True
                    for raw_line in resp:
                        line = raw_line.decode("utf-8", errors="replace").strip()
                        if not line:
                            continue
                        chunk_bytes = f"{line}\n\n".encode("utf-8")
                        self.wfile.write(chunk_bytes)
                        self.wfile.flush()
            except urllib.error.HTTPError as exc:
                if not headers_sent:
                    err_body = exc.read().decode("utf-8", errors="replace")
                    self._send_json(
                        exc.code,
                        {
                            "error": {
                                "code": f"upstream_http_{exc.code}",
                                "message": err_body[:1000],
                            }
                        },
                    )
            except Exception as exc:
                if not headers_sent:
                    self._send_json(
                        502,
                        {
                            "error": {
                                "code": "upstream_connection_error",
                                "message": str(exc),
                            }
                        },
                    )
            return

        try:
            try:
                resp_ctx = urllib.request.urlopen(req, timeout=cfg["timeout_seconds"])
            except Exception:
                if fallback_req is not None:
                    resp_ctx = urllib.request.urlopen(
                        fallback_req, timeout=cfg["timeout_seconds"]
                    )
                else:
                    raise
            with resp_ctx as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
                self._send_json(
                    200,
                    resp_body,
                    extra_headers={
                        "X-WAHS-Auth-Email": str(verdict.get("email") or "")
                    },
                )
        except urllib.error.HTTPError as exc:
            err_body = exc.read().decode("utf-8", errors="replace")
            self._send_json(
                exc.code,
                {
                    "error": {
                        "code": f"upstream_http_{exc.code}",
                        "message": err_body[:1000],
                    }
                },
            )
        except Exception as exc:
            self._send_json(
                502,
                {
                    "error": {
                        "code": "upstream_connection_error",
                        "message": str(exc),
                    }
                },
            )


def create_server(host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), RelayRequestHandler)


if __name__ == "__main__":
    listen_port = int(os.environ.get("PORT") or "8080")
    server = create_server("0.0.0.0", listen_port)
    print(f"WAHS UW GPU Auth Relay listening on 0.0.0.0:{listen_port}", flush=True)
    server.serve_forever()

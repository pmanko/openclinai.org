#!/usr/bin/env python3
"""Smoke the local Catalyst MVP: the gateway reports every dependency ready, and one
natural-language question through it comes back as generated SQL that runs and
returns rows.

It is the acceptance step after `make catalyst-mvp-up` and after a Catalyst or Hub
pin moves. It talks only to the local gateway, never to a demo host, and needs the
running MVP and model, so it is not a CI test. What the SQL says and how the Hub
writes it are Catalyst's and the Hub's contracts, tested in their repositories; this
smoke checks that the stack delivers a runnable query end to end. Catalyst's own
`mvp-health.sh` gate runs before it in `make catalyst-smoke`.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_QUESTION = "How many patients are there?"


def _call(
    method: str, url: str, payload: dict[str, Any] | None, timeout: int
) -> tuple[int, dict[str, Any]]:
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as error:
        body = error.read()
        try:
            return error.code, json.loads(body or b"{}")
        except ValueError:
            return error.code, {"error": {"message": body.decode(errors="replace")}}


def _error_text(body: dict[str, Any]) -> str:
    error = body.get("error") if isinstance(body.get("error"), dict) else {}
    return f"{error.get('code', '')}: {error.get('message', '')}".strip(": ") or json.dumps(body)[:300]


def smoke(gateway_url: str, *, question: str, profile: str | None, timeout: int) -> dict[str, Any]:
    base = gateway_url.rstrip("/")
    status, health = _call("GET", f"{base}/health", None, timeout)
    if status != 200 or health.get("status") != "ready":
        not_ready = sorted(
            name
            for name, check in (health.get("checks") or {}).items()
            if not (isinstance(check, dict) and check.get("ready") is True)
        )
        raise RuntimeError(f"Catalyst gateway is not ready: {not_ready or health}")

    status, options = _call("GET", f"{base}/v1/catalyst/query-options", None, timeout)
    if status != 200:
        raise RuntimeError(f"query options failed ({status}): {_error_text(options)}")
    profile_id = profile or options.get("defaultProfileId")
    advertised = {p.get("id"): p for p in options.get("profiles") or [] if isinstance(p, dict)}
    if profile_id not in advertised:
        raise RuntimeError(f"query profile {profile_id!r} is not offered by the gateway")
    if advertised[profile_id].get("available") is not True:
        raise RuntimeError(f"query profile {profile_id!r} is not available")

    started = time.monotonic()
    status, preview = _call(
        "POST",
        f"{base}/v1/catalyst/queries",
        {
            "contractVersion": "catalyst.question.request.v1",
            "deploymentMode": "demo",
            "profileId": profile_id,
            "question": question,
        },
        timeout,
    )
    generated_ms = round((time.monotonic() - started) * 1000)
    if not 200 <= status < 300:
        raise RuntimeError(f"the question failed ({status}): {_error_text(preview)}")
    if preview.get("contractVersion") != "catalyst.preview.v1":
        detail = preview.get("message") or json.dumps(preview.get("validation"))[:500]
        raise RuntimeError(
            f"the question did not produce runnable SQL: status {preview.get('status')!r}: {detail}"
        )
    sql = str(preview.get("sql") or "").strip()
    if not sql:
        raise RuntimeError("the preview carries no SQL")

    preview_id = preview["previewId"]
    status, table = _call(
        "POST",
        f"{base}/v1/catalyst/previews/{preview_id}/execute",
        {
            "contractVersion": "catalyst.execute.request.v1",
            "previewId": preview_id,
            "queryDigest": preview["queryDigest"],
            "accept": True,
            "idempotencyKey": f"smoke-{uuid.uuid4()}",
        },
        timeout,
    )
    executed_ms = round((time.monotonic() - started) * 1000)
    if not 200 <= status < 300 or table.get("contractVersion") != "catalyst.table.v1":
        raise RuntimeError(f"the SQL did not run ({status}): {table.get('message') or _error_text(table)}")
    rows = ((table.get("table") or {}).get("rowCount") or {}).get("returned")
    if not isinstance(rows, int) or rows < 1:
        raise RuntimeError(f"the SQL ran but returned no rows: rowCount {rows!r}")
    return {
        "schema_version": "catalyst_smoke.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "gateway_url": base,
        "profile": profile_id,
        "question": question,
        "sql": sql,
        "row_count": rows,
        "columns": [c.get("name") for c in (table.get("table") or {}).get("columns") or [] if isinstance(c, dict)],
        "source": table.get("source"),
        "generated_ms": generated_ms,
        "executed_ms": executed_ms,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--gateway-url",
        default=f"http://127.0.0.1:{os.environ.get('GATEWAY_PORT', '18000')}",
        help="Local Catalyst gateway (default: GATEWAY_PORT, else the umbrella's 18000).",
    )
    parser.add_argument("--question", default=DEFAULT_QUESTION)
    parser.add_argument("--profile", help="Hub query profile; default: the gateway's default.")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    result = smoke(args.gateway_url, question=args.question, profile=args.profile, timeout=args.timeout)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

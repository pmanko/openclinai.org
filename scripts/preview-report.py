#!/usr/bin/env python3
"""Local HTTP preview server for any v2 evaluation run directory.

Usage:
  python3 scripts/preview-report.py <run_dir> [--port 8088] [--host 127.0.0.1]

Serves the canonical viewer shells from reports/assets/ over <run_dir>'s
report-data.json and dashboard-data.json without staging into reports/.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import mimetypes
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent


def _load_publish_module():
    spec = importlib.util.spec_from_file_location(
        "publish_report_mod", ROOT / "scripts" / "publish-report.py"
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load_json_safe(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def create_preview_server(
    run_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 8088,
    assets_dir: Path | None = None,
) -> ThreadingHTTPServer:
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")
    if not (run_dir / "report-data.json").is_file():
        raise FileNotFoundError(f"report-data.json not found in {run_dir}")

    assets = (assets_dir or (ROOT / "reports" / "assets")).resolve()
    pub = _load_publish_module()

    class PreviewHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: object) -> None:
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "close")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            route = parsed.path

            summary = _load_json_safe(run_dir / "run-summary.json")
            ed = _load_json_safe(run_dir / "editorial.json")
            if not ed:
                ed = {
                    "schema": "openclinai.editorial.v2",
                    "schema_version": 2,
                    "slug": str(summary.get("slug") or run_dir.name),
                    "title": str(summary.get("title") or f"Local Preview: {run_dir.name}"),
                    "summary": str(summary.get("scoreline") or "Unpublished local evaluation run preview."),
                    "takeaway": "",
                    "family": str(summary.get("report_family") or "chartsearchai"),
                    "date": str(summary.get("date") or ""),
                }
            title = str(ed.get("title") or run_dir.name)

            if route in ("/", "/index.html", "/report.html"):
                html = pub.render_report_shell_html(
                    title=title,
                    editorial=ed,
                    css_ver="preview",
                    js_ver="preview",
                    data_ver="preview",
                    asset_prefix="/assets",
                )
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                return

            if route == "/dashboard.html":
                html = pub.render_dashboard_shell_html(
                    title=title,
                    editorial=ed,
                    css_ver="preview",
                    js_ver="preview",
                    data_ver="preview",
                    asset_prefix="/assets",
                )
                self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")
                return

            if route.startswith("/assets/"):
                rel = route[len("/assets/"):]
                target = (assets / rel).resolve()
                if target.is_relative_to(assets) and target.is_file():
                    ctype, _ = mimetypes.guess_type(target.name)
                    self._send(200, target.read_bytes(), ctype or "application/octet-stream")
                    return
                self._send(404, b"Not found", "text/plain; charset=utf-8")
                return

            rel_name = route.lstrip("/")
            if rel_name == "reports-index.json":
                self._send(200, b'{"runs":[]}', "application/json; charset=utf-8")
                return
            if rel_name in ("report-data.json", "dashboard-data.json", "run-summary.json", "editorial.json"):
                target = (run_dir / rel_name).resolve()
                if target.is_relative_to(run_dir) and target.is_file():
                    self._send(200, target.read_bytes(), "application/json; charset=utf-8")
                    return

            self._send(404, b"Not found", "text/plain; charset=utf-8")

    return ThreadingHTTPServer((host, port), PreviewHandler)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Preview a v2 evaluation run directory locally.")
    parser.add_argument("run_dir", type=Path, help="Path to run directory containing report-data.json")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8088, help="Bind port (default: 8088)")
    args = parser.parse_args(argv)
    try:
        srv = create_preview_server(args.run_dir, host=args.host, port=args.port)
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    actual_host, actual_port = srv.server_address[:2]
    print(f"Previewing {args.run_dir.resolve()}")
    print(f"  Reader report:        http://{actual_host}:{actual_port}/")
    print(f"  Diagnostic dashboard: http://{actual_host}:{actual_port}/dashboard.html")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

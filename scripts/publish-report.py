#!/usr/bin/env python3
"""Stage and deploy v2 pure-JSON clinical AI evaluation report packets.

Subcommands:
  stage <run_dir> --slug <slug> [--editorial <path>] ...
      Validates the v2 JSON packet (report-data.json, dashboard-data.json,
      run-summary.json) and editorial metadata (editorial.json), stamps the
      lightweight index.html and dashboard.html shells into reports/<slug>/,
      and recompiles reports/reports-index.json + reports/index.html.
      Never commits to git or touches remote servers.

  deploy [--slug <slug>] [--prune] [--dry-run] ...
      Verifies the committed report archive and syncs reports/ to the remote
      host via additive rsync by default (archive-wide --delete only when
      --prune is explicitly passed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from html import escape as esc
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
FAMILIES = {"chartsearchai", "catalyst", "wahs"}
SAFE_SLUG = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
LEGACY_AUTO_SLUG_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("auto-minted tier prefix (l1..l5-full-default-*)", re.compile(r"^l[1-5]-full-default-", re.IGNORECASE)),
    ("trailing 8-char hex hash (-<hex8>)", re.compile(r"-[0-9a-f]{8}$", re.IGNORECASE)),
)

FORBIDDEN_HTML_KEYS = {
    "answer_html",
    "conf_html",
    "chips_html",
    "blocks_html",
    "sources_html",
    "refs_html",
    "check_precision_html",
    "body_html",
}

FORBIDDEN_TITLE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("auto-generated 'Full evaluation' placeholder", re.compile(r"^\s*Full evaluation\b", re.IGNORECASE)),
    ("unedited '(auto-added' placeholder", re.compile(r"\(auto-added\b", re.IGNORECASE)),
    ("trailing git/run hex hash in title", re.compile(r"\([0-9a-f]{7,}\)\s*$", re.IGNORECASE)),
    ("internal run code in title", re.compile(r"\b(?:Answer Rules R\d+|Run D\d+)\b")),
)

FORBIDDEN_PROSE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("comparison-set ID 'full-default'", re.compile(r"\bfull-default\b", re.IGNORECASE)),
    ("tier code (L1-L5)", re.compile(r"\bL[1-5]\b")),
    (
        "internal profile ID",
        re.compile(
            r"\b(?:single-12b-(?:answer|bare|verify|checked)|engine-parity-[a-z0-9-]+|hub-profile-[a-z0-9-]+)\b",
            re.IGNORECASE,
        ),
    ),
    ("plumbing phrase 'parity tap' / 'wire tap'", re.compile(r"\b(?:parity tap|wire taps?)\b", re.IGNORECASE)),
    ("raw rubric/SSE field name", re.compile(r"\b(?:date_wrong|window_over|trend_fab|answer_delta)\b")),
)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha10(path: Path) -> str:
    if not path.is_file():
        return "0000000000"
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def _assert_no_symlinks(run_dir: Path) -> None:
    """Reject symlinked run content before staging."""
    for parent, dir_names, file_names in os.walk(run_dir, followlinks=False):
        for name in sorted(dir_names) + sorted(file_names):
            candidate = Path(parent) / name
            if candidate.is_symlink():
                raise ValueError(
                    "run directory must not contain symlinks: "
                    f"{candidate.relative_to(run_dir)}"
                )


def validate_slug(slug: str, *, allow_legacy_slug: bool = False) -> None:
    if not isinstance(slug, str) or not SAFE_SLUG.fullmatch(slug):
        raise ValueError("slug must contain only lowercase letters, digits, '.', '_' or '-'")
    if not allow_legacy_slug:
        for desc, pat in LEGACY_AUTO_SLUG_PATTERNS:
            if pat.search(slug):
                raise ValueError(
                    f"slug {slug!r} rejected ({desc}); choose a human-readable topic slug "
                    "(e.g. '2026-11-10-strict-6mo-order-cutoff-gpu')"
                )


def validate_editorial_payload(ed: dict[str, Any], *, slug: str) -> None:
    if ed.get("schema_version") != 2 or ed.get("schema") != "openclinai.editorial.v2":
        raise ValueError(f"{slug}: editorial.json must declare schema='openclinai.editorial.v2' and schema_version=2")
    family = str(ed.get("family") or "")
    if family not in FAMILIES:
        raise ValueError(f"{slug}: unsupported report family in editorial.json: {family!r}")
    is_earlier_sub = bool(ed.get("parent_slug")) or ed.get("featured") is False
    if is_earlier_sub:
        label = str(ed.get("label") or "").strip()
        if not label:
            raise ValueError(f"{slug}: non-featured / earlier sub-entry requires a non-empty 'label'")
        for field in ("label", "note"):
            txt = str(ed.get(field) or "")
            for desc, pat in FORBIDDEN_PROSE_PATTERNS:
                if pat.search(txt):
                    raise ValueError(f"{slug}.{field} rejected ({desc})")
        return

    title = str(ed.get("title") or "").strip()
    summary = str(ed.get("summary") or "").strip()
    takeaway = str(ed.get("takeaway") or "").strip()
    if len(title) < 15:
        raise ValueError(f"{slug}: editorial title is missing or too short (<15 chars)")
    if len(summary) < 40:
        raise ValueError(f"{slug}: editorial summary is missing or too brief (<40 chars)")
    if len(takeaway) < 40:
        raise ValueError(f"{slug}: editorial takeaway is missing or too brief (<40 chars)")
    for desc, pat in FORBIDDEN_TITLE_PATTERNS:
        if pat.search(title):
            raise ValueError(f"{slug}: report title rejected ({desc}): {title!r}")
    if re.match(r"^\s*Takeaway\s*:", takeaway, flags=re.IGNORECASE):
        raise ValueError(f"{slug}: report takeaway must not start with redundant 'Takeaway:' prefix")
    for field, txt in (("title", title), ("summary", summary), ("takeaway", takeaway)):
        for desc, pat in FORBIDDEN_PROSE_PATTERNS:
            if pat.search(txt):
                raise ValueError(f"{slug}: report {field} rejected ({desc})")


def validate_v2_report_packet(
    report_data: dict[str, Any],
    dashboard_data: dict[str, Any],
    run_summary: dict[str, Any],
    *,
    slug: str,
) -> None:
    if report_data.get("schema_version") != 2 or report_data.get("schema") != "openclinai.report.v2":
        raise ValueError(f"{slug}: report-data.json must have schema='openclinai.report.v2' and schema_version=2")
    if dashboard_data.get("schema_version") != 2 or dashboard_data.get("schema") != "openclinai.dashboard.v2":
        raise ValueError(f"{slug}: dashboard-data.json must have schema='openclinai.dashboard.v2' and schema_version=2")
    if run_summary.get("schema_version") != 2 or run_summary.get("schema") != "openclinai.summary.v2":
        raise ValueError(f"{slug}: run-summary.json must have schema='openclinai.summary.v2' and schema_version=2")

    runs = report_data.get("runs")
    if not isinstance(runs, list) or not runs or not isinstance(runs[0], dict):
        raise ValueError(f"{slug}: report-data.json is missing a non-empty runs[0] object")
    r0 = runs[0]
    if "check_precision_html" in r0:
        raise ValueError(f"{slug}: report-data.json contains forbidden check_precision_html")
    for k, v in (r0.get("source_card_pool") or {}).items():
        if isinstance(v, str) and "<" in v:
            raise ValueError(f"{slug}: report-data.json source_card_pool[{k!r}] contains raw HTML")
    for k, v in (r0.get("refs_pool") or {}).items():
        if isinstance(v, str) and "<" in v:
            raise ValueError(f"{slug}: report-data.json refs_pool[{k!r}] contains raw HTML")
    for sc in r0.get("scenarios") or []:
        for tn in sc.get("turns") or []:
            for b_k, cell_v in (tn.get("cells") or {}).items():
                if not isinstance(cell_v, dict):
                    continue
                bad_keys = FORBIDDEN_HTML_KEYS.intersection(cell_v.keys())
                if bad_keys:
                    raise ValueError(
                        f"{slug}: report-data.json cell ({sc.get('scenario_id')}, {b_k}) "
                        f"contains forbidden HTML keys: {sorted(bad_keys)}"
                    )
                for c_obj in (cell_v.get("claims") or {}).values():
                    if isinstance(c_obj, dict) and ("sources_html" in c_obj or "refs_html" in c_obj):
                        raise ValueError(
                            f"{slug}: report-data.json claim ({sc.get('scenario_id')}, {b_k}) "
                            "contains forbidden sources_html/refs_html"
                        )


def render_report_shell_html(
    *,
    title: str,
    editorial: dict[str, Any],
    css_ver: str,
    js_ver: str,
    data_ver: str,
    asset_prefix: str = "../assets",
) -> str:
    safe_title = esc(title or "OpenClinAI Evaluation Report")
    ed_json = json.dumps(editorial, ensure_ascii=False).replace("</", "<\\/")
    return (
        "<!doctype html>"
        "<html lang='en' data-theme='light'>"
        "<head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>{safe_title} — OpenClinAI</title>"
        f"<link rel='stylesheet' href='{asset_prefix}/report-shell.css?v={css_ver}'>"
        "<script>(function(){try{var t=localStorage.getItem('oc-theme-report');"
        "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}catch(e){}})();</script>"
        "</head>"
        "<body>"
        "<header class='topbar'><div class='topbar-id'><div class='id-main'>"
        "<div class='breadcrumb'><a href='../index.html' title='Back to all published validation reports'>← All Reports</a>"
        "<span class='bc-sep'>·</span>"
        "<a href='https://openclinai.org/validation-harness/' target='_blank' rel='noopener'>Validation Harness</a></div>"
        f"<h1 id='report-title'>{safe_title}</h1>"
        "<div id='run-meta' class='meta'></div></div>"
        "<div class='id-actions'><span id='run-switcher' class='run-switcher'>"
        "<label for='run-switcher-sel'>view run</label>"
        "<select id='run-switcher-sel' aria-label='Switch to another published run'></select></span>"
        "<button id='print-pdf' class='btn-ghost' title='print / save as PDF'>Download PDF</button>"
        "<button id='theme-toggle' class='btn-ghost btn-icon' type='button' "
        "title='Toggle light / dark' aria-label='Toggle light or dark mode'></button></div></div>"
        "<div class='controls'><label id='run-select-wrap' hidden>run <select id='run-select'></select></label></div>"
        "<nav id='toc' aria-label='On this page'></nav></header>"
        "<a class='skip-link' href='#report'>Skip to report</a>"
        "<main id='report'></main>"
        "<div id='sort-live' class='sr-only' aria-live='polite'></div>"
        "<div class='legend'><p class='legend-group-h'>Three-layer read-only evaluation reference</p>"
        "<dl class='legend-key'>"
        "<dt>Layer 1 · Deterministic</dt><dd>HTTP/schema validity, exact chart-reference UUID resolution, and temporal guardrail gate status — computed without an LLM judge.</dd>"
        "<dt>Layer 2 · LLM Judge</dt><dd>advisory Scout autorater composite (0–100), Safety-Adjusted Benchmark (hard-gated on severe harm / critical omission), and per-axis scores.</dd>"
        "<dt>Layer 3 · Human &amp; PPI</dt><dd>clinician/human adjudication recorded via <code>python -m harness.validate adjudicate &lt;run_dir&gt;</code>, paired with Prediction-Powered Inference (PPI) calibration and Cohen’s κ.</dd>"
        "<dt>⏱ latency</dt><dd>end-to-end response time; <b>orange</b> = first turn per backend (carries model warmup).</dd>"
        "<dt>chart refs</dt><dd>count of chart records cited — a COUNT, not a grounding/quality signal.</dd>"
        "<dt>not surfaced</dt><dd>tokens / finish_reasons / response model — not returned by <code>/chat</code> (OTel-deferred).</dd>"
        "</dl></div>"
        f"<script type='application/json' id='report-editorial'>{ed_json}</script>"
        f"<script type='application/json' id='report-data' data-src='./report-data.json?v={data_ver}'></script>"
        f"<script src='{asset_prefix}/report-shell.js?v={js_ver}'></script>"
        "</body></html>\n"
    )


def render_dashboard_shell_html(
    *,
    title: str,
    editorial: dict[str, Any],
    css_ver: str,
    js_ver: str,
    data_ver: str,
    asset_prefix: str = "../assets",
) -> str:
    safe_title = esc(title or "Validation Run Dashboard")
    ed_json = json.dumps(editorial, ensure_ascii=False).replace("</", "<\\/")
    return (
        "<!doctype html>"
        "<html lang='en' data-theme='dark'>"
        "<head>"
        "<meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Diagnostic Dashboard · {safe_title} — OpenClinAI</title>"
        f"<link rel='stylesheet' href='{asset_prefix}/dashboard-shell.css?v={css_ver}'>"
        "<script>(function(){try{var t=localStorage.getItem('oc-theme-validate-dash');"
        "if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}catch(e){}})();</script>"
        "</head>"
        "<body>"
        "<button id='theme-toggle' class='theme-toggle' type='button' "
        "title='Toggle light / dark' aria-label='Toggle light or dark mode'></button>"
        "<div class='breadcrumb' style='margin-bottom:8px;font-size:12px'>"
        "<a href='../index.html' style='color:var(--accent);text-decoration:none'>← All Reports</a> · "
        "<a href='./index.html' style='color:var(--accent);text-decoration:none'>Reader Report</a></div>"
        f"<h1 id='hdr'>{safe_title}</h1>"
        "<div class='bar'><div id='fill' style='width:0%'></div></div>"
        "<div id='prog' class='muted'></div>"
        "<div id='warnbar' class='caveat red' style='display:none'></div>"
        "<section><h2>Models and Hub profiles the arms call</h2><div id='models'></div></section>"
        "<section><h2>Arms</h2><div class='row' id='arms'></div></section>"
        "<section><h2>Judged scores</h2><div id='judges'></div></section>"
        "<section id='checksec' style='display:none'><h2>Checks against the judge</h2><div id='checkprec'></div></section>"
        "<section><h2>Scenario &times; arm &nbsp;<span class='muted'>(click a cell)</span></h2>"
        "<p id='legend' class='muted' style='margin:2px 0 6px'></p><div id='grid'></div></section>"
        "<section><h2>Recent &nbsp;<span class='muted'>(click a row)</span></h2><div class='feed' id='feed'></div></section>"
        "<div id='modal' onclick='if(event.target===this)closeD()'><div id='mbody'></div></div>"
        f"<script type='application/json' id='report-editorial'>{ed_json}</script>"
        f"<script type='application/json' id='dashboard-data' data-src='./dashboard-data.json?v={data_ver}'></script>"
        f"<script src='{asset_prefix}/dashboard-shell.js?v={js_ver}'></script>"
        "</body></html>\n"
    )


def stage_report(
    *,
    run_dir: Path,
    slug: str,
    reports_root: Path | None = None,
    editorial_path: Path | None = None,
    family: str = "",
    title: str = "",
    summary: str = "",
    takeaway: str = "",
    allow_legacy_slug: bool = False,
    root: Path = ROOT,
    manifest_path: Path | None = None,
) -> Path:
    validate_slug(slug, allow_legacy_slug=allow_legacy_slug)
    run_dir = run_dir.resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"run directory not found: {run_dir}")
    _assert_no_symlinks(run_dir)

    reports_root = (reports_root or (root / "reports")).resolve()
    manifest_path = (manifest_path or (reports_root / "reports-index.json")).resolve()
    destination = reports_root / slug
    temporary = reports_root / f".{slug}.staging"
    if run_dir.is_relative_to(destination.resolve()) or destination.resolve().is_relative_to(run_dir):
        raise ValueError("publication destination must not overlap the input run directory")
    if reports_root.is_relative_to(run_dir):
        raise ValueError("publication output must not be inside the input run directory")

    rep_src = run_dir / "report-data.json"
    dash_src = run_dir / "dashboard-data.json"
    sum_src = run_dir / "run-summary.json"
    if not rep_src.is_file():
        raise FileNotFoundError(f"v2 report-data.json required in {run_dir}")
    if not dash_src.is_file():
        raise FileNotFoundError(f"v2 dashboard-data.json required in {run_dir}")
    if not sum_src.is_file():
        raise FileNotFoundError(f"v2 run-summary.json required in {run_dir}")

    report_data = _load_json(rep_src)
    dashboard_data = _load_json(dash_src)
    run_summary = _load_json(sum_src)
    run_summary["slug"] = slug

    ed_candidates = [
        p
        for p in (editorial_path, run_dir / "editorial.json", destination / "editorial.json")
        if p is not None and p.is_file()
    ]
    editorial: dict[str, Any] = _load_json(ed_candidates[0]) if ed_candidates else {}
    editorial["schema"] = "openclinai.editorial.v2"
    editorial["schema_version"] = 2
    editorial["slug"] = slug
    if family:
        editorial["family"] = family
    elif not editorial.get("family"):
        editorial["family"] = str(run_summary.get("report_family") or "chartsearchai")
    if title:
        editorial["title"] = title
    if summary:
        editorial["summary"] = summary
    if takeaway:
        editorial["takeaway"] = takeaway
    if "featured" not in editorial:
        editorial["featured"] = True
    if not editorial.get("date") and run_summary.get("date"):
        editorial["date"] = run_summary["date"]

    validate_editorial_payload(editorial, slug=slug)
    validate_v2_report_packet(report_data, dashboard_data, run_summary, slug=slug)

    # Inject catalog_meta into report_data.runs[0] so viewer shell has immediate access
    r0 = (report_data.get("runs") or [{}])[0]
    r0["catalog_meta"] = {
        "slug": slug,
        "title": editorial.get("title") or editorial.get("label") or slug,
        "summary": editorial.get("summary") or editorial.get("note") or "",
        "takeaway": editorial.get("takeaway") or "",
        "family": editorial.get("family") or "chartsearchai",
        "date": editorial.get("date") or run_summary.get("date") or "",
    }

    # Pre-check existing archive before replacing destination
    build_script = root / "scripts" / "build-reports-index.py"
    if build_script.is_file() and manifest_path.is_file():
        subprocess.run(
            [
                sys.executable,
                str(build_script),
                "--root",
                str(root),
                "--reports-root",
                str(reports_root),
                "--manifest",
                str(manifest_path),
                "--check-archive",
                "--pending-slug",
                slug,
            ],
            check=True,
        )

    reports_root.mkdir(parents=True, exist_ok=True)
    if temporary.exists():
        shutil.rmtree(temporary)
    temporary.mkdir(parents=True, exist_ok=True)

    try:
        (temporary / "editorial.json").write_text(
            json.dumps(editorial, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (temporary / "run-summary.json").write_text(
            json.dumps(run_summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (temporary / "report-data.json").write_text(
            json.dumps(report_data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )
        (temporary / "dashboard-data.json").write_text(
            json.dumps(dashboard_data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
        )

        assets_dir = reports_root / "assets"
        rep_css_v = _sha10(assets_dir / "report-shell.css")
        rep_js_v = _sha10(assets_dir / "report-shell.js")
        dash_css_v = _sha10(assets_dir / "dashboard-shell.css")
        dash_js_v = _sha10(assets_dir / "dashboard-shell.js")
        rep_data_v = _sha10(temporary / "report-data.json")
        dash_data_v = _sha10(temporary / "dashboard-data.json")

        display_title = str(editorial.get("title") or editorial.get("label") or slug)
        (temporary / "index.html").write_text(
            render_report_shell_html(
                title=display_title,
                editorial=editorial,
                css_ver=rep_css_v,
                js_ver=rep_js_v,
                data_ver=rep_data_v,
            ),
            encoding="utf-8",
        )
        (temporary / "dashboard.html").write_text(
            render_dashboard_shell_html(
                title=display_title,
                editorial=editorial,
                css_ver=dash_css_v,
                js_ver=dash_js_v,
                data_ver=dash_data_v,
            ),
            encoding="utf-8",
        )

        if destination.exists():
            shutil.rmtree(destination)
        temporary.replace(destination)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    if build_script.is_file():
        subprocess.run(
            [
                sys.executable,
                str(build_script),
                "--root",
                str(root),
                "--reports-root",
                str(reports_root),
            ],
            check=True,
        )
    return destination / "index.html"


def deploy_reports(
    *,
    slug: str = "",
    prune: bool = False,
    dry_run: bool = False,
    reports_root: Path | None = None,
    root: Path = ROOT,
) -> int:
    if slug and prune:
        raise ValueError("--prune cannot be combined with --slug (per-slug deploy is always additive)")
    reports_root = (reports_root or (root / "reports")).resolve()
    manifest_path = reports_root / "reports-index.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"{manifest_path} is missing")
    if slug and not (reports_root / slug / "index.html").is_file():
        raise FileNotFoundError(f"staged report {reports_root / slug / 'index.html'} does not exist")

    build_script = root / "scripts" / "build-reports-index.py"
    if build_script.is_file():
        subprocess.run(
            [
                sys.executable,
                str(build_script),
                "--root",
                str(root),
                "--reports-root",
                str(reports_root),
                "--check-archive",
            ],
            check=True,
        )

    if dry_run:
        mode = f"slug={slug!r} (additive)" if slug else ("full archive (--prune --delete)" if prune else "full archive (additive)")
        print(f"==> dry-run deploy validated ({mode}) under {reports_root}")
        return 0

    deploy_sh = root / "scripts" / "deploy-reports.sh"
    cmd = ["bash", str(deploy_sh)]
    if slug:
        cmd += ["--slug", slug]
    if prune:
        cmd += ["--prune"]
    env = {**os.environ, "REPORTS_ROOT": str(reports_root)}
    res = subprocess.run(cmd, cwd=root, env=env, check=False)
    return res.returncode


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Stage or deploy v2 clinical AI evaluation reports.")
    sub = parser.add_subparsers(dest="subcommand", required=True)

    p_stage = sub.add_parser("stage", help="Validate and stage a v2 report packet into reports/<slug>/")
    p_stage.add_argument("run_dir", type=Path, help="Run directory containing v2 JSON artifacts")
    p_stage.add_argument("--slug", required=True, help="Human-readable report directory slug")
    p_stage.add_argument("--editorial", type=Path, help="Optional path to editorial.json")
    p_stage.add_argument("--family", choices=sorted(FAMILIES), default="", help="Report family override")
    p_stage.add_argument("--title", default="", help="Editorial title override")
    p_stage.add_argument("--summary", default="", help="Editorial summary override")
    p_stage.add_argument("--takeaway", default="", help="Editorial takeaway override")
    p_stage.add_argument("--reports-root", type=Path, default=None, help="Reports root directory")
    p_stage.add_argument("--manifest", type=Path, default=None, help="Manifest path override")
    p_stage.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    p_stage.add_argument(
        "--allow-legacy-slug",
        action="store_true",
        help="Allow historical auto-minted slug patterns when re-staging archived runs",
    )

    p_deploy = sub.add_parser("deploy", help="Deploy committed reports/ archive to the remote host")
    p_deploy.add_argument("--slug", default="", help="Deploy a single report slug additively")
    p_deploy.add_argument(
        "--prune",
        action="store_true",
        help="Include --delete on full-archive rsync to prune removed remote directories",
    )
    p_deploy.add_argument("--dry-run", action="store_true", help="Validate archive without running rsync/ssh")
    p_deploy.add_argument("--reports-root", type=Path, default=None, help="Reports root directory")
    p_deploy.add_argument("--root", type=Path, default=ROOT, help="Repository root")

    args = parser.parse_args(argv)
    try:
        if args.subcommand == "stage":
            out = stage_report(
                run_dir=args.run_dir,
                slug=args.slug,
                reports_root=args.reports_root,
                editorial_path=args.editorial,
                family=args.family,
                title=args.title,
                summary=args.summary,
                takeaway=args.takeaway,
                allow_legacy_slug=args.allow_legacy_slug,
                root=args.root,
                manifest_path=args.manifest,
            )
            print(f"staged v2 report -> {out}")
            return 0
        if args.subcommand == "deploy":
            return deploy_reports(
                slug=args.slug,
                prune=args.prune,
                dry_run=args.dry_run,
                reports_root=args.reports_root,
                root=args.root,
            )
    except (FileNotFoundError, RuntimeError, ValueError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

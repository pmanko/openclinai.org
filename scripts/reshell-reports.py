#!/usr/bin/env python3
"""Re-shell published static reports (`reports/<slug>/index.html`) with the latest `report.py` UI shell.

Why this exists:
- Each published report in `reports/<slug>/index.html` embeds its canonical evaluation data in
  `<script type="application/json" id="report-data">...</script>`, wrapped in the CSS/JS shell
   from `harness.validate.report._document(blob)`.
- Previously, upgrading `report.py` left older published reports frozen on legacy shells, and
  large multi-arm reports (like 27-setup × 36-scenario WAHS runs) carried 6.5 MB of duplicate
  `cell.sources.sources` raw objects alongside 6.0 MB of pre-rendered `cell.sources_html`.
- Running `scripts/reshell-reports.py` upgrades every `#report-data`-backed report in `reports/`
  to the current 5-Tab Casual-First + 3-Layer Verification UI shell, enriches missing derived
  fields (`safety_adjusted_benchmark_score`, `valid_turns`, `resolved_chart_refs`), and strips
  redundant `cell.sources.sources` arrays when `cell.sources_html` is already present.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HARNESS_ROOT = ROOT / "targets" / "validation-harness"
if str(HARNESS_ROOT) not in sys.path:
    sys.path.insert(0, str(HARNESS_ROOT))

from harness.validate.reconcile import (  # noqa: E402
    calibrated_summary,
    cell_benchmark_score,
    cell_safety_adjusted_benchmark_score,
    has_critical_omission,
    has_severe_harm,
    scout_summary,
)
from harness.validate.report import _document  # noqa: E402

DATA_RE = re.compile(
    r"<script\s+type=['\"]application/json['\"]\s+id=['\"]report-data['\"]>(.*?)</script>",
    re.DOTALL,
)


def enrich_run(run: dict) -> tuple[int, int]:
    """Enrich a single run dict in-place and return (cells_count, stripped_sources_count)."""
    scenarios = run.get("scenarios") or []
    backends = run.get("backends") or []
    total_cells = 0
    stripped_sources = 0

    # Track per-backend deterministic stats from cells if summary lacks them
    det_by_b: dict[str, dict[str, int]] = {
        b: {
            "valid_turns": 0,
            "resolved_chart_refs": 0,
            "unresolved_chart_refs": 0,
            "temporal_gate_pass": 0,
        }
        for b in backends
    }

    for sc in scenarios:
        for tn in sc.get("turns") or []:
            cells = tn.get("cells") or {}
            for b, cell in cells.items():
                if not isinstance(cell, dict):
                    continue
                total_cells += 1
                st = det_by_b.setdefault(
                    b,
                    {
                        "valid_turns": 0,
                        "resolved_chart_refs": 0,
                        "unresolved_chart_refs": 0,
                        "temporal_gate_pass": 0,
                    },
                )
                if not cell.get("error") and (cell.get("http_status") in (None, 200)):
                    st["valid_turns"] += 1
                diag = ((cell.get("sources") or {}).get("diagnostics")) or {}
                top_refs = diag.get("top_level_refs") or []
                unres_refs = diag.get("unresolved_indices") or []
                if top_refs:
                    st["resolved_chart_refs"] += max(0, len(top_refs) - len(unres_refs))
                    st["unresolved_chart_refs"] += len(unres_refs)
                tg = cell.get("temporal_gate") or {}
                if tg.get("status") == "pass":
                    st["temporal_gate_pass"] += 1

                # Strip redundant multi-MB cell.sources.sources array when sources_html is present;
                # renderTileEvalFooter only reads cell.sources.diagnostics.
                srcs = cell.get("sources")
                if isinstance(srcs, dict) and "sources" in srcs and cell.get("sources_html"):
                    srcs.pop("sources", None)
                    stripped_sources += 1

    j_by_b = {j.get("backend"): j for j in (run.get("judge") or []) if isinstance(j, dict)}
    for s in run.get("summary") or []:
        b = s.get("backend_id", "")
        st = det_by_b.get(b, {})
        cr = ((j_by_b.get(b) or {}).get("citation_resolution")) or {}
        turns = s.get("turns") or 0
        errors = s.get("errors") or 0
        if s.get("valid_turns") is None:
            s["valid_turns"] = st.get("valid_turns") or max(0, turns - errors)
        tot_refs = (s.get("total_chart_refs") or 0) or (cr.get("n_refs") or 0)
        s["total_chart_refs"] = tot_refs
        if not s.get("resolved_chart_refs"):
            if cr.get("n_resolved") is not None:
                s["resolved_chart_refs"] = cr["n_resolved"]
            else:
                unres = st.get("unresolved_chart_refs", 0)
                s["resolved_chart_refs"] = max(0, tot_refs - unres)
        if not s.get("unresolved_chart_refs"):
            s["unresolved_chart_refs"] = cr.get("n_unresolved") or st.get("unresolved_chart_refs", 0)
        if s.get("temporal_gate_pass") is None:
            g_warn = s.get("temporal_gate_warn") or 0
            g_fail = s.get("temporal_gate_fail") or 0
            s["temporal_gate_pass"] = st.get("temporal_gate_pass") or max(0, turns - errors - g_warn - g_fail)
        s.setdefault("temporal_gate_warn", 0)
        s.setdefault("temporal_gate_fail", 0)
        s.setdefault("temporal_gate_applied", 0)
        s.setdefault("answer_check_edited", 0)
        s.setdefault("answer_check_flagged", 0)

    # Enrich judge_rows
    jrows = run.get("judge_rows") or []
    for jr in jrows:
        if jr.get("benchmark_score") is None:
            jr["benchmark_score"] = cell_benchmark_score(jr)
        if jr.get("safety_adjusted_benchmark_score") is None:
            jr["safety_adjusted_benchmark_score"] = cell_safety_adjusted_benchmark_score(jr)
        if jr.get("critical_omission") is None:
            jr["critical_omission"] = has_critical_omission(jr)
        if jr.get("severe_harm") is None:
            jr["severe_harm"] = has_severe_harm(jr)

    # Enrich run.judge arm summaries with safety_adjusted_benchmark_score
    if jrows and run.get("judge"):
        recomputed = {row["backend"]: row for row in scout_summary(jrows, backends)}
        for j_arm in run["judge"]:
            b = j_arm.get("backend")
            rc = recomputed.get(b)
            if rc:
                for k in (
                    "benchmark_score",
                    "safety_adjusted_benchmark_score",
                    "safety_adjusted_ci",
                    "critical_omission_count",
                    "severe_harm_count",
                ):
                    if j_arm.get(k) is None and rc.get(k) is not None:
                        j_arm[k] = rc[k]

    # Ensure calibrated summary exists
    if not run.get("calibrated"):
        run["calibrated"] = calibrated_summary(jrows, run.get("adjudication_rows") or [], backends)

    run.setdefault("adjudication_rows", [])
    run.setdefault("judge_actor_cells", {})
    return total_cells, stripped_sources


def reshell_all(reports_dir: Path) -> None:
    updated = 0
    skipped = 0
    bytes_before = 0
    bytes_after = 0
    for idx_path in sorted(reports_dir.glob("*/index.html")):
        slug = idx_path.parent.name
        raw = idx_path.read_text(encoding="utf-8", errors="ignore")
        m = DATA_RE.search(raw)
        if not m or "<title>catalyst report" in raw:
            print(f"SKIP {slug:62s} (non-validate or static HTML)")
            skipped += 1
            continue
        blob = json.loads(m.group(1))
        runs = blob.get("runs") or []
        if not any(r.get("scenarios") for r in runs):
            print(f"SKIP {slug:62s} (no validate scenarios)")
            skipped += 1
            continue
        cells = 0
        stripped = 0
        for run in runs:
            c, st = enrich_run(run)
            cells += c
            stripped += st
        new_html = _document(blob)
        old_sz = len(raw.encode("utf-8"))
        new_sz = len(new_html.encode("utf-8"))
        bytes_before += old_sz
        bytes_after += new_sz
        idx_path.write_text(new_html, encoding="utf-8")
        updated += 1
        print(
            f"OK   {slug:62s} | cells={cells:4d} | stripped_src={stripped:4d} | "
            f"{old_sz/1024:7.1f} KB -> {new_sz/1024:7.1f} KB"
        )
    print(
        f"\nDone: reshelled {updated} reports (skipped {skipped} static reports). "
        f"Total size: {bytes_before/1024/1024:.2f} MB -> {bytes_after/1024/1024:.2f} MB"
    )


if __name__ == "__main__":
    reports_root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else (ROOT / "reports")
    reshell_all(reports_root)

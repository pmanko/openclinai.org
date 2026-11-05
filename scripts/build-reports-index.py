#!/usr/bin/env python3
"""Regenerate reports/index.html from the curated manifest reports/reports-index.json.

This is a hand-curated showcase, not an auto-discovered listing: only the runs named in
the manifest appear, with human-written titles/summaries, newest first by each report's
recorded date. Scores and counts are read from the staged packet and its frozen meta.json;
publication does not evaluate runs or resolve model sources.

Edit reports/reports-index.json to add/remove runs or change the copy, then rerun:
  python3 scripts/build-reports-index.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from xml.etree.ElementTree import Element, SubElement, tostring

ROOT = Path(__file__).resolve().parent.parent
from html import escape as esc

# Publication owns this small theme control; it does not import report rendering.
# Theme toggle (fixed index control).

THEME_TOGGLE_CSS = (
    ".theme-toggle{position:fixed;top:14px;right:16px;z-index:50;width:34px;height:34px;"
    "border-radius:8px;border:1px solid var(--border, var(--line));"
    "background:var(--panel, var(--surface));color:var(--text, var(--fg));"
    "cursor:pointer;font-size:15px;line-height:1;display:flex;align-items:center;"
    "justify-content:center;}"
    ".theme-toggle:hover{border-color:var(--accent);}"
)

THEME_TOGGLE_BUTTON_HTML = (
    "<button id='theme-toggle' class='theme-toggle' type='button' "
    "aria-label='Toggle light or dark mode' title='Toggle light / dark'></button>"
)
# Alias used by dashboard/index theme marker tests.
THEME_TOGGLE_BUTTON = THEME_TOGGLE_BUTTON_HTML


def theme_bootstrap_js(storage_key: str) -> str:
    """Inline script: apply stored light/dark theme before first paint."""
    return (
        "(function(){try{var t=localStorage.getItem('"
        + storage_key
        + "');if(t==='light'||t==='dark')document.documentElement.dataset.theme=t;}"
        "catch(e){}})();"
    )


def theme_toggle_js(storage_key: str) -> str:
    """Inline script: wire #theme-toggle and persist preference."""
    return (
        "(function(){var b=document.getElementById('theme-toggle');if(!b)return;"
        "function s(){b.textContent=document.documentElement.dataset.theme==='dark'?'☀':'☾';}"
        "s();b.addEventListener('click',function(){"
        "var n=document.documentElement.dataset.theme==='dark'?'light':'dark';"
        "document.documentElement.dataset.theme=n;"
        "try{localStorage.setItem('"
        + storage_key
        + "',n);}catch(e){}s();});})();"
    )


REPORTS = ROOT / "reports"
MANIFEST = REPORTS / "reports-index.json"
DATE_FORMAT = "%-d %b %Y"


def validate_archive(runs: list[dict], reports_root: Path, *, pending_slug: str | None = None) -> None:
    """Require every available curated report locally before replacing the catalog."""
    safe_slug = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
    if pending_slug is not None and not safe_slug.fullmatch(pending_slug):
        raise ValueError("invalid pending report slug")
    root = reports_root.resolve()
    missing = []
    for entry in runs:
        slug = entry.get("slug")
        if not isinstance(slug, str) or not safe_slug.fullmatch(slug):
            raise ValueError(f"invalid curated report slug: {slug!r}")
        if entry.get("availability") == "unavailable" or slug == pending_slug:
            continue
        page = (root / slug / "index.html").resolve()
        if not page.is_relative_to(root) or not page.is_file():
            missing.append(slug)
    if missing:
        raise ValueError(
            "incomplete staged report archive; missing index.html for: "
            + ", ".join(missing)
            + ". Restore the complete curated archive under "
            + str(root)
            + " before building or publishing the catalog."
        )


def human_arm(arm: str) -> tuple[str, str]:
    """Use the recorded identifier; publication never resolves live model profiles."""
    return arm, arm


def _run_meta(slug: str) -> dict:
    meta = REPORTS / slug / "meta.json"
    if not meta.is_file():
        return {}
    try:
        payload = json.loads(meta.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def _run_dir_for(slug: str) -> Path | None:
    """Catalogs read the staged packet only, never the source experiment workspace."""
    candidate = (REPORTS / slug).resolve()
    if not candidate.is_relative_to(REPORTS.resolve()):
        return None
    return candidate if candidate.is_dir() else None


def _patient_names(run_dir: Path, uuids: set[str]) -> str:
    man = run_dir / "run_manifest.json"
    book: dict[str, str] = {}
    if man.exists():
        try:
            for u, p in (json.loads(man.read_text()).get("patients") or {}).items():
                disp = (p or {}).get("display")
                if disp:
                    book[u] = disp.split(" - ")[-1].strip()
        except Exception:
            pass
    names = [book.get(u, "a patient") for u in sorted(uuids)]
    return " + ".join(dict.fromkeys(names)) if names else ""


def gather(slug: str) -> dict:
    """Pull the score table + subtitle facts for one curated run from its data."""
    meta = _run_meta(slug)
    family = str(meta.get("report_family") or "chartsearchai")
    out: dict = {
        "family": family,
        "evaluation_modality": str(meta.get("evaluation_modality") or ""),
        "reader_led": False,
        # Facts frozen beside a report whose packet no longer carries its results.
        "cells": meta.get("cells"),
        "patients": str(meta.get("patients") or ""),
        "date": meta.get("date"),
        "scout": list(meta.get("scout") or []),
        "scoreline": str(meta.get("scoreline") or ""),
        # Who judged, frozen with the scores; a run that recorded no judge says so.
        "judging": _judging_line(meta.get("judging")),
    }
    rdir = _run_dir_for(slug)
    if not rdir or not ((rdir / "results.json").is_file() if family == "catalyst" else (rdir / "results.jsonl").is_file()):
        return out
    if family == "catalyst":
        suite_path = rdir / "suite.json"
        suite = (
            json.loads(suite_path.read_text(encoding="utf-8"))
            if suite_path.is_file()
            else {}
        )
        reader_led = suite.get("reportMode") == "reader-led"
        out["reader_led"] = reader_led
        results = json.loads((rdir / "results.json").read_text(encoding="utf-8"))
        rows = list(results.get("results") or [])
        out["cells"] = int(results.get("resultCount") or len(rows))
        out["date"] = out["date"] or datetime.fromtimestamp(
            (rdir / "results.json").stat().st_mtime, timezone.utc
        ).strftime(DATE_FORMAT)
        teams: dict[str, list[dict]] = {}
        for row in rows:
            team = row.get("profileId")
            if isinstance(team, str):
                teams.setdefault(team, []).append(row)
        if reader_led:
            parts = [
                f"{len(teams)} model teams",
                f"{len(rows)} conversations",
                "full-evidence reader review",
            ]
            incomplete = sum(
                row.get("measurementValid") is not True for row in rows
            )
            if incomplete:
                parts.append(f"{incomplete} with incomplete evidence")
            out["scoreline"] = " · ".join(parts)
            return out
        if len(teams) > 1:
            # A comparison's headline is how the teams did, not how many
            # gold checks ran across all of them at once.
            scores = [
                f"{team.split('catalyst-query-')[-1]} "
                f"{sum(1 for r in rs if r.get('passed'))}/{len(rs)}"
                for team, rs in teams.items()
            ]
            parts = [f"{len(teams)} teams · " + " · ".join(scores)]
            invalid = sum(
                1
                for row in rows
                if row.get("measurementValid") is False
            )
            if invalid:
                parts.append(
                    f"{invalid} invalid measurement" + ("s" if invalid > 1 else "")
                )
        else:
            gold = [
                assertion
                for row in rows
                for assertion in (row.get("assertions") or [])
                if "gold_execution_match" in str(assertion.get("name") or "")
            ]
            passed = sum(bool(assertion.get("passed")) for assertion in gold)
            parts = [f"Gold checks: {passed}/{len(gold)} passed"] if gold else []
        judge_path = rdir / "judge.jsonl"
        if judge_path.is_file():
            judge_rows = [
                json.loads(line)
                for line in judge_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            composites = [
                float(row["composite"])
                for row in judge_rows
                if isinstance(row.get("composite"), (int, float))
            ]
            if composites:
                parts.append(f"Advisory judge median: {median(composites):g}/100")
        out["scoreline"] = " · ".join(parts) or out["scoreline"]
        return out

    rows = [json.loads(l) for l in (rdir / "results.jsonl").read_text().splitlines() if l.strip()]
    arms = sorted({r.get("backend_id") for r in rows if r.get("backend_id")})
    pts = {(r.get("request") or {}).get("patient") for r in rows if (r.get("request") or {}).get("patient")}
    out["cells"] = len(rows)
    out["patients"] = _patient_names(rdir, pts) or out["patients"]
    out["date"] = out["date"] or datetime.fromtimestamp(
        (rdir / "results.jsonl").stat().st_mtime, timezone.utc).strftime(DATE_FORMAT)
    return out


def _newest_first(runs: list[dict]) -> list[dict]:
    """Order the catalog by each report's recorded date, newest first.

    An undated entry keeps its place beside the entry listed before it, so ties and
    gaps follow the manifest instead of the editor having to keep the list sorted.
    """
    keyed, last = [], datetime.max
    for position, entry in enumerate(runs):
        try:
            last = datetime.strptime(str(gather(entry["slug"]).get("date") or ""), "%d %b %Y")
        except ValueError:
            pass
        keyed.append((-last.toordinal(), position, entry))
    return [entry for _, _, entry in sorted(keyed, key=lambda k: k[:2])]


def _https(link) -> dict | None:
    """A reader link from the manifest, accepted only as an https URL with a label."""
    if (isinstance(link, dict) and isinstance(link.get("label"), str)
            and str(link.get("url", "")).startswith("https://")):
        return link
    return None


def _judging_line(judging) -> str:
    """The sentence naming the judge a report's scores came from, or the absence of one."""
    if isinstance(judging, dict) and judging.get("sentence"):
        return str(judging["sentence"])
    return ""


def _scout_table(scout: list[dict], labels: dict | None = None) -> str:
    if not scout:
        return '<div class="unscored">This run is an answer comparison only — not yet scored.</div>'
    # best (max) per column, to highlight the winner. Benchmark is the headline.
    best = {}
    for key in ("benchmark_score", "accuracy_mean", "completeness_mean", "relevance_mean"):
        vals = [s[key] for s in scout if isinstance(s.get(key), (int, float))]
        best[key] = max(vals) if vals else None
    # A run judged without the aggregate shows its dimensions only, not a column of dashes.
    benchmarked = best["benchmark_score"] is not None
    head = ('<table class="scout"><thead><tr>'
            '<th class="arm">AI setup</th><th>Questions</th>'
            + ('<th class="bench">Benchmark<br>/100</th>' if benchmarked else '') +
            '<th>Accuracy</th><th>Completeness</th><th>Relevance</th>'
            '<th>Unsafe<br>answers</th></tr></thead><tbody>')
    body = []
    ordered_scout = sorted(
        scout,
        key=lambda s: (
            s.get("benchmark_score") if isinstance(s.get("benchmark_score"), (int, float)) else -1.0,
            s.get("accuracy_mean") if isinstance(s.get("accuracy_mean"), (int, float)) else -1.0,
        ),
        reverse=True,
    )
    for s in ordered_scout:
        name, detail = human_arm(s["backend"])
        if (labels or {}).get(s["backend"]):
            name, detail = labels[s["backend"]], s["backend"]

        def cell(key):
            v = s.get(key)
            classes = ["bench"] if key == "benchmark_score" else []
            if isinstance(v, (int, float)) and best[key] is not None and abs(v - best[key]) < 1e-9:
                classes.append("best")
            cls = f' class="{" ".join(classes)}"' if classes else ""
            txt = f"{v:.1f}" if isinstance(v, (int, float)) else "—"
            return f"<td{cls}>{txt}</td>"
        harm = s.get("harm_count", 0)
        flags = (f'harm: {harm} · confabulations: {s.get("confabulation_count", 0)} · '
                 f'fabricated citations: {s.get("fabricated_citation_count", 0)}')
        harm_cls = ' class="harm"' if harm else ""
        harm_cell = f'<td{harm_cls} title="{esc(flags)}">{harm}</td>'
        body.append(
            f'<tr><td class="arm" title="{esc(detail)}">{esc(name)}</td>'
            f'<td>{s["n"]}</td>{cell("benchmark_score") if benchmarked else ""}{cell("accuracy_mean")}'
            f'{cell("completeness_mean")}{cell("relevance_mean")}{harm_cell}</tr>'
        )
    table = head + "".join(body) + "</tbody></table>"
    # In-Depth — its own parity Benchmark, shown (NOT hidden) for ANY arm that ships one (single-model
    # two-call or team), in a clearly separate block so the elaboration scores never sit in the
    # head-to-head Answer grid above. Sorted by the In-Depth Benchmark.
    bg = [s for s in scout if (s.get("background") or {}).get("n_background")]
    if bg:
        bg.sort(key=lambda s: ((s.get("background") or {}).get("benchmark_score") or 0), reverse=True)
        rows = []
        for s in bg:
            name, _ = human_arm(s["backend"])
            if (labels or {}).get(s["backend"]):
                name = labels[s["backend"]]
            b = s["background"]
            ben = "—" if b.get("benchmark_score") is None else f'{b["benchmark_score"]:.1f}'
            sup = "—" if b.get("support_mean") is None else f'{b["support_mean"]:.1f}'
            val = "—" if b.get("added_value_mean") is None else f'{b["added_value_mean"]:.1f}'
            rows.append(f'<tr><td class="arm">{esc(name)}</td><td class="bench">{ben}</td>'
                        f'<td>{b["n_background"]}</td><td>{sup}</td><td>{val}</td>'
                        f'<td>{b.get("new_harm_count", 0)}</td><td>{b.get("padded_count", 0)}</td></tr>')
        table += ('<details class="indepth-details"><summary>In-Depth — scored separately on '
                  f'its own axes (its own parity Benchmark · {len(bg)} setups)</summary>'
                  '<table class="scout"><thead><tr><th class="arm">AI setup</th><th>In-Depth Benchmark</th>'
                  '<th>In-depth answers</th><th>Support</th><th>Added value</th><th>Unsafe</th><th>Padded</th>'
                  '</tr></thead><tbody>' + "".join(rows) + '</tbody></table></details>')
    return table


FAMILY_LABELS = {
    "chartsearchai": "ChartSearchAI",
    "catalyst": "Catalyst SQL",
    "wahs": "WA Health Summary",
}

MODALITY_LABELS = {
    "deterministic_pipeline": "Deterministic Pipeline Gate",
    "condensation_retrieval_ablation": "Condensation & Retrieval Ablation",
    "live_model_and_team_eval": "Live Model & KB Team Evaluation",
}


def _family(entry: dict, gathered: dict) -> str:
    return str(entry.get("family") or gathered.get("family") or "chartsearchai")


def _filter_bar(families: list[str]) -> str:
    """Buttons that show one report family at a time; without script every card shows."""
    counts = {f: families.count(f) for f in dict.fromkeys(families)}
    if len(counts) < 2:
        return ""
    buttons = [f'<button type="button" data-family="all" aria-pressed="true">All reports ({len(families)})</button>']
    buttons += [f'<button type="button" data-family="{esc(f)}" aria-pressed="false">'
                f'{esc(FAMILY_LABELS.get(f, f))} ({n})</button>' for f, n in counts.items()]
    return ('  <div class="filter" id="family-filter" role="group" aria-label="Show reports for">'
            + "".join(buttons) + '</div>')


FILTER_JS = (
    "(function(){var g=document.getElementById('family-filter');"
    "var s=document.getElementById('report-search');"
    "var d=document.getElementById('density-toggle');"
    "var countEl=document.getElementById('visible-count');"
    "var cards=Array.prototype.slice.call(document.querySelectorAll('article.card'));"
    "var activeFamily='all';"
    "function updateVisibility(){"
    "var q=(s&&s.value?s.value.trim().toLowerCase():'');"
    "var shown=0;"
    "cards.forEach(function(c){"
    "var famOk=(activeFamily==='all'||c.dataset.family===activeFamily);"
    "var qOk=(!q||c.textContent.toLowerCase().indexOf(q)!==-1);"
    "var vis=(famOk&&qOk);"
    "c.hidden=!vis;"
    "if(vis)shown++;"
    "});"
    "if(countEl)countEl.textContent=shown+' of '+cards.length+' reports shown';"
    "}"
    "if(g){var bs=g.querySelectorAll('button');"
    "function apply(f){activeFamily=f;document.body.dataset.filter=f;"
    "bs.forEach(function(b){b.setAttribute('aria-pressed',b.dataset.family===f?'true':'false');});"
    "updateVisibility();}"
    "g.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;"
    "apply(b.dataset.family);"
    "history.replaceState(null,'',b.dataset.family==='all'?location.pathname:'#'+b.dataset.family);});"
    "var h=location.hash.slice(1),known=false;"
    "bs.forEach(function(b){if(b.dataset.family===h)known=true;});"
    "apply(known?h:'all');}"
    "if(s){s.addEventListener('input',updateVisibility);"
    "s.addEventListener('keydown',function(e){if(e.key==='Escape'){s.value='';updateVisibility();}});}"
    "if(d){d.addEventListener('click',function(){"
    "var compact=document.body.classList.toggle('compact-catalog');"
    "d.setAttribute('aria-pressed',compact?'true':'false');"
    "d.textContent=compact?'Show score tables':'Compact cards';"
    "});}"
    "})();"
)


def _card_highlights(scout: list[dict], labels: dict | None = None) -> str:
    if not scout:
        return ""
    labels = labels or {}
    bench_rows = [s for s in scout if isinstance(s.get("benchmark_score"), (int, float))]
    pills = []
    if bench_rows:
        top = max(bench_rows, key=lambda s: float(s["benchmark_score"]))
        win_name = labels.get(top["backend"]) or human_arm(top["backend"])[0]
        pills.append(
            f'<span class="hl-pill hl-win">★ Best setup: <b>{esc(win_name)}</b> '
            f'({top["benchmark_score"]:.1f}/100)</span>'
        )
    else:
        acc_rows = [s for s in scout if isinstance(s.get("accuracy_mean"), (int, float))]
        if acc_rows:
            top = max(acc_rows, key=lambda s: float(s["accuracy_mean"]))
            win_name = labels.get(top["backend"]) or human_arm(top["backend"])[0]
            pills.append(
                f'<span class="hl-pill hl-win">★ Top accuracy: <b>{esc(win_name)}</b> '
                f'({top["accuracy_mean"]:.1f}/10)</span>'
            )
    total_harm = sum(int(s.get("harm_count") or 0) for s in scout)
    zero_harm = sum(1 for s in scout if not s.get("harm_count"))
    if total_harm == 0:
        pills.append(
            f'<span class="hl-pill hl-safe">✓ 0 unsafe answers across all {len(scout)} setups</span>'
        )
    else:
        pills.append(
            f'<span class="hl-pill hl-warn">{zero_harm} of {len(scout)} setups with 0 unsafe answers '
            f'({total_harm} flagged total)</span>'
        )
    return '<div class="card-highlights">' + "".join(pills) + "</div>"


def _card(entry: dict) -> str:
    slug = entry["slug"]
    g = gather(slug)
    facts = []
    if g["patients"]:
        facts.append(esc(g["patients"]))
    if g["cells"] is not None:
        modality = str(entry.get("evaluation_modality") or g.get("evaluation_modality") or "")
        if g.get("family") == "catalyst":
            unit = "conversations"
        elif modality == "deterministic_pipeline":
            unit = "rubric cases"
        else:
            unit = "graded answers"
        facts.append(f'{g["cells"]} {unit}')
    if g["date"]:
        facts.append(esc(g["date"]))
    subtitle = " · ".join(facts)
    family = _family(entry, g)
    modality = str(entry.get("evaluation_modality") or g.get("evaluation_modality") or "")
    modality_label = MODALITY_LABELS.get(modality, modality)
    if family == "catalyst":
        # Labels name the question each page answers, not the artifact kind.
        links = [f'<a class="btn" href="{esc(slug)}/index.html">Read the report</a>']
        if (REPORTS / slug / "comparison.html").exists():
            # The decision document: verdict, gates and the failure inventory.
            links.append(f'<a class="btn ghost" href="{esc(slug)}/comparison.html">Compare the teams</a>')
        if (REPORTS / slug / "dashboard.html").exists():
            links.append(f'<a class="btn ghost" href="{esc(slug)}/dashboard.html">Inspect every conversation</a>')
        if (REPORTS / slug / "run-config.json").exists():
            links.append(f'<a class="btn ghost" href="{esc(slug)}/run-config.json">Run seed (JSON)</a>')
    else:
        links = [f'<a class="btn" href="{esc(slug)}/index.html">Full report</a>']
        if (REPORTS / slug / "comparison.html").exists():
            links.append(f'<a class="btn ghost" href="{esc(slug)}/comparison.html">Team comparison</a>')
        if (REPORTS / slug / "dashboard.html").exists():
            links.append(f'<a class="btn ghost" href="{esc(slug)}/dashboard.html">Interactive dashboard</a>')
    guide = _https(entry.get("guide"))
    if guide:
        links.append(f'<a class="btn ghost" href="{esc(guide["url"])}">{esc(guide["label"])}</a>')
    unavailable = entry.get("availability") == "unavailable"
    if unavailable:
        links = ['<span class="unscored">Report unavailable</span>']
    statistics = "" if unavailable else (
        f'<div class="unscored">{esc(g["scoreline"])}</div>' if g.get("scoreline") and not g["scout"]
        else _scout_table(g["scout"], entry.get("arms")) if g["scout"]
        else '<div class="unscored">Open the report for its recorded methods and results.</div>'
    )
    if g["scout"] and not unavailable:
        statistics = '<div class="report-table-scroll" role="region" aria-label="Recorded score tables" tabindex="0">' + statistics + '</div>'
        statistics += ('<p class="judged-by">' + esc(g["judging"] or "Judge not recorded for this run.") + '</p>')
    highlights = "" if unavailable else _card_highlights(g["scout"], entry.get("arms"))
    takeaway = (f'<p class="takeaway"><span class="tk">Takeaway</span>{esc(entry["takeaway"])}</p>'
                if entry.get("takeaway") else "")
    # Earlier runs of the same comparison stay published but are listed under the
    # current one, each with what was different, instead of as identical cards.
    earlier = [e for e in entry.get("earlier") or [] if isinstance(e, dict) and e.get("slug")]
    earlier_html = ("" if not earlier else
                    f'<details class="earlier"><summary><b>Earlier runs of this comparison</b> ({len(earlier)})</summary><ul>' + "".join(
                        f'<li><a href="{esc(e["slug"])}/index.html">{esc(e.get("label") or e["slug"])}</a>'
                        f'{" " + esc(e["note"]) if e.get("note") else ""}</li>' for e in earlier)
                    + '</ul></details>')
    family_label = FAMILY_LABELS.get(family, family)
    if modality_label:
        family_label = f"{family_label} · {modality_label}"
    summary_html = f'<p class="summary">{esc(entry.get("summary", ""))}</p>' if entry.get("summary") else ""
    return f"""  <article class="card" data-family="{esc(family)}">
  <header class="card-head">
    <div class="titles"><span class="family {esc(family)}">{esc(family_label)}</span><h2>{esc(entry["title"])}</h2><div class="slug">{subtitle}</div></div>
    <div class="links">{"".join(links)}</div>
  </header>
  {f'<p class="report-context">{esc(entry["context"])}</p>' if entry.get("context") else ""}
  {highlights}
  {takeaway}
  {summary_html}
  {statistics}
  {earlier_html}
  </article>"""


_STYLE_CORE = """
  html[data-theme="light"]{color-scheme:light;--bg:#f6f8fa;--panel:#ffffff;--panel2:#f8fafc;--text:#1f2328;--muted:#59636e;
    --accent:#0969da;--border:#d0d7de;--harm:#cf222e;--best:#1a7f37;
    --ink:#1f2328;--btn-fg:#ffffff;--th-bg:#f6f8fa;--bench-bg:rgba(9,105,218,.07);--takeaway-bg:rgba(9,105,218,.06);
    --win-bg:#dafbe1;--win-fg:#116329;--warn-bg:#fff8c5;--warn-fg:#7d4e00;}
  html[data-theme="dark"]{color-scheme:dark;--bg:#0d1117;--panel:#161b22;--panel2:#1c2230;--text:#c9d1d9;--muted:#8b949e;
    --accent:#79c0ff;--border:#30363d;--harm:#f85149;--best:#3fb950;
    --ink:#ffffff;--btn-fg:#0d1117;--th-bg:rgba(255,255,255,.03);--bench-bg:rgba(121,192,255,.10);--takeaway-bg:rgba(121,192,255,.07);
    --win-bg:rgba(46,160,67,.18);--win-fg:#56d364;--warn-bg:rgba(187,128,9,.18);--warn-fg:#e3b341;}
  *{box-sizing:border-box;} body{margin:0;background:var(--bg);color:var(--text);
    font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif;padding:36px 24px 72px;}
  .wrap{max-width:1020px;margin:0 auto;}
  .site-parent{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:20px;padding-right:40px;font-size:14px;}
  .site-parent a{color:var(--accent);text-decoration:underline;text-underline-offset:3px;}
  .report-table-scroll{max-width:100%;overflow-x:auto;}
  .report-table-scroll:focus-visible{outline:3px solid var(--accent);outline-offset:3px;}
  a:focus-visible,button:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:2px;}
  .report-context{font-size:13.5px;color:var(--muted);border-left:3px solid var(--border);padding-left:12px;margin:8px 0;}
  header.page h1{font-size:28px;margin:0 0 8px;color:var(--ink);font-weight:700;letter-spacing:-.01em;}
  .intro{color:var(--text);font-size:15px;margin:0 0 18px;max-width:820px;}
  .intro b{color:var(--ink);}
  .legend{background:var(--panel);border:1px solid var(--border);border-radius:12px;
    padding:16px 20px;font-size:13.5px;color:var(--muted);margin-bottom:24px;}
  .legend b{color:var(--text);}
  .legend-pillars{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:12px;margin-bottom:10px;}
  .legend-pillar{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:10px 13px;}
  .legend-pillar .lp-k{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:var(--accent);margin-bottom:3px;}
  .legend-pillar .lp-v{font-size:13px;color:var(--text);line-height:1.45;}
  .legend-more{margin-top:8px;border-top:1px solid var(--border);padding-top:8px;}
  .legend-more > summary{cursor:pointer;color:var(--accent);font-weight:600;font-size:13px;}
  .legend-more > p{margin:8px 0 0;line-height:1.55;}
  .catalog-toolbar{display:flex;flex-wrap:wrap;justify-content:space-between;align-items:center;gap:12px;margin:0 0 22px;}
  .filter{display:flex;gap:8px;flex-wrap:wrap;margin:0;}
  .filter button{font:inherit;font-size:13px;font-weight:600;padding:6px 14px;border-radius:999px;
    border:1px solid var(--border);background:var(--panel);color:var(--text);cursor:pointer;}
  .filter button[aria-pressed="true"]{background:var(--accent);color:var(--btn-fg);border-color:var(--accent);}
  .toolbar-right{display:flex;gap:8px;align-items:center;flex-wrap:wrap;}
  .search-input{font:inherit;font-size:13px;padding:6px 12px;border-radius:999px;border:1px solid var(--border);
    background:var(--panel);color:var(--text);min-width:220px;}
  .density-btn{font:inherit;font-size:12.5px;font-weight:600;padding:6px 12px;border-radius:999px;
    border:1px solid var(--border);background:var(--panel);color:var(--text);cursor:pointer;}
  .density-btn[aria-pressed="true"]{background:var(--accent);color:var(--btn-fg);border-color:var(--accent);}
  .visible-count{font-size:12px;color:var(--muted);}
  body[data-filter="chartsearchai"] .card:not([data-family="chartsearchai"]),
  body[data-filter="catalyst"] .card:not([data-family="catalyst"]),
  body[data-filter="wahs"] .card:not([data-family="wahs"]){display:none;}
  body.compact-catalog .report-table-scroll,
  body.compact-catalog p.judged-by,
  body.compact-catalog .summary{display:none;}
  .card{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:22px 24px;margin-bottom:20px;box-shadow:0 1px 4px rgba(0,0,0,.03);}
  .card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:10px;}
  .titles{flex:1;min-width:260px;}
  .titles h2{margin:0;font-size:19.5px;color:var(--ink);font-weight:650;line-height:1.32;}
  .family{display:inline-block;margin:0 0 6px;padding:2px 8px;border:1px solid var(--border);
    border-radius:999px;color:var(--muted);font-size:10.5px;font-weight:700;letter-spacing:.05em;text-transform:uppercase;}
  .family.catalyst,.family.wahs{color:var(--accent);border-color:var(--accent);}
  .titles .slug{color:var(--muted);font-size:13px;margin-top:4px;}
  .links{display:flex;gap:8px;flex-wrap:wrap;align-items:center;}
  .btn{display:inline-block;text-decoration:none;background:var(--accent);color:var(--btn-fg);
    font-weight:600;font-size:13px;padding:7px 14px;border-radius:6px;border:1px solid var(--accent);white-space:nowrap;}
  .btn.ghost{background:transparent;color:var(--accent);}
  .btn:hover{filter:brightness(1.08);}
  .card-highlights{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0 12px;}
  .hl-pill{font-size:12.5px;padding:3px 10px;border-radius:999px;border:1px solid var(--border);background:var(--panel2);color:var(--text);}
  .hl-pill.hl-win{background:var(--bench-bg);border-color:var(--accent);color:var(--ink);}
  .hl-pill.hl-safe{background:var(--win-bg);color:var(--win-fg);border-color:transparent;font-weight:600;}
  .hl-pill.hl-warn{background:var(--warn-bg);color:var(--warn-fg);border-color:transparent;}
  .takeaway{font-size:14px;color:var(--text);margin:10px 0 12px;background:var(--takeaway-bg);
    border-left:3px solid var(--accent);padding:10px 14px;border-radius:0 8px 8px 0;line-height:1.55;}
  .takeaway .tk{display:inline-block;font-size:11px;text-transform:uppercase;letter-spacing:.05em;
    color:var(--accent);font-weight:700;margin-right:8px;}
  .summary{color:var(--muted);font-size:14px;margin:0 0 14px;max-width:860px;line-height:1.55;}
  p.judged-by{margin:8px 0 0;font-size:12px;color:var(--muted);}
  table.scout{width:100%;border-collapse:collapse;font-size:13.5px;background:var(--panel2);
    border:1px solid var(--border);border-radius:8px;overflow:hidden;font-variant-numeric:tabular-nums;}
  table.scout th,table.scout td{padding:8px 12px;text-align:right;border-bottom:1px solid var(--border);}
  table.scout th{color:var(--muted);font-weight:600;font-size:11px;text-transform:uppercase;
    letter-spacing:.04em;background:var(--th-bg);vertical-align:bottom;}
  table.scout th.arm,table.scout td.arm{text-align:left;}
  table.scout td.arm{color:var(--ink);cursor:help;font-weight:500;}
  table.scout tr:last-child td{border-bottom:none;}
  table.scout td.best{color:var(--best);font-weight:700;}
  table.scout td.harm{color:var(--harm);font-weight:700;}
  /* Benchmark = the headline aggregate: framed + tinted column so it reads as the focal point. */
  table.scout th.bench,table.scout td.bench{background:var(--bench-bg);
    border-left:2px solid var(--accent);border-right:2px solid var(--accent);}
  table.scout th.bench{color:var(--accent);font-size:11.5px;}
  table.scout td.bench{color:var(--ink);font-weight:800;font-size:15.5px;}
  table.scout td.bench.best{color:var(--best);}
  table.scout tbody tr:last-child td.bench{border-bottom:2px solid var(--accent);}
  details.indepth-details{margin-top:12px;border:1px solid var(--border);border-radius:8px;padding:8px 12px;background:var(--panel2);}
  details.indepth-details > summary{cursor:pointer;font-size:13px;font-weight:600;color:var(--accent);}
  details.indepth-details > table.scout{margin-top:10px;}
  .unscored{color:var(--muted);font-size:13.5px;font-style:italic;}
  details.earlier{font-size:13px;color:var(--muted);margin:12px 0 0;border-top:1px solid var(--border);padding-top:10px;}
  details.earlier > summary{cursor:pointer;color:var(--text);}
  details.earlier b{color:var(--text);font-weight:600;}
  details.earlier ul{margin:6px 0 0;padding-left:20px;}
  details.earlier a{color:var(--accent);}
  footer.page{color:var(--muted);font-size:12px;margin-top:36px;text-align:center;}
"""

STYLE = _STYLE_CORE + THEME_TOGGLE_CSS


def main(
    argv: list[str] | None = None,
) -> None:
    global ROOT, REPORTS, MANIFEST
    check_archive = False
    pending_slug = None
    if argv is not None:
        parser = argparse.ArgumentParser()
        parser.add_argument("--root", type=Path, default=ROOT)
        parser.add_argument("--reports-root", type=Path)
        parser.add_argument("--manifest", type=Path)
        parser.add_argument("--check-archive", action="store_true", help="Validate without changing any files")
        parser.add_argument("--pending-slug", help="Report supplied by the publisher's incoming packet (check-only)")
        args = parser.parse_args(argv)
        if args.pending_slug and not args.check_archive:
            parser.error("--pending-slug requires --check-archive")
        check_archive = args.check_archive
        pending_slug = args.pending_slug
        ROOT = args.root.resolve()
        REPORTS = (args.reports_root or ROOT / "reports").resolve()
        MANIFEST = (args.manifest or REPORTS / "reports-index.json").resolve()
    manifest = json.loads(MANIFEST.read_text())
    runs = _newest_first(manifest.get("runs", []))
    earlier = [e for r in runs for e in r.get("earlier") or [] if isinstance(e, dict)]
    validate_archive(runs + earlier, REPORTS, pending_slug=pending_slug)
    if check_archive:
        print("Staged report archive is complete for the curated catalog.")
        return
    # Loud, not silent: a run whose report is staged under reports/ but absent from the
    # curated manifest gets DEPLOYED (rsync, no --delete) yet never LISTED. Warn so a missed
    # publish-time upsert is visible instead of quietly producing a deployed-but-unlisted run.
    listed = {r.get("slug") for r in runs + earlier}
    staged = {p.parent.name for p in REPORTS.glob("*/meta.json")}
    for slug in sorted(staged - listed):
        print(f"warn: {slug} is staged under reports/ but NOT in reports-index.json "
              f"(deployed but unlisted) — add it to the manifest to list it.", file=sys.stderr)
    cards = "\n".join(_card(r) for r in runs)
    run_summaries = [gather(r["slug"]) for r in runs]
    filter_bar = _filter_bar([_family(r, g) for r, g in zip(runs, run_summaries)])
    has_reader_led = any(summary.get("reader_led") for summary in run_summaries)
    has_other_reports = any(
        not summary.get("reader_led") for summary in run_summaries
    )
    scoring_note = str(manifest.get("scoring_note", ""))
    if has_reader_led and has_other_reports:
        scoring_note = (
            "The numerical explanation below applies only to reports that "
            "show score tables. Reader-led Catalyst comparisons show database "
            "facts and prose review without numerical grading. "
            + scoring_note
        )
    elif has_reader_led:
        scoring_note = (
            "Reader-led Catalyst comparisons present the database facts, the "
            "complete conversation evidence, and the attached prose review "
            "for the reader to assess."
        )
    if has_other_reports:
        legend_html = f"""  <div class="legend">
    <div class="legend-pillars">
      <div class="legend-pillar"><div class="lp-k">1 · Headline Benchmark (/100)</div><div class="lp-v">Composite clinical quality score weighting <b>Accuracy</b> &amp; <b>Completeness</b> minus bounded penalties for safety, abstention, and citation errors.</div></div>
      <div class="legend-pillar"><div class="lp-k">2 · Clinical Axes (0–10)</div><div class="lp-v"><b>Accuracy</b> (facts match chart), <b>Completeness</b> (covers needed context), and <b>Relevance</b> (on-question without padding).</div></div>
      <div class="legend-pillar"><div class="lp-k">3 · Safety &amp; Grounding Guardrail</div><div class="lp-v"><b>Unsafe answers</b> counts responses with a potential clinical harm flag (lower is better; <b>0</b> is target). Hover a cell for citation details.</div></div>
    </div>
    <details class="legend-more"><summary><b>How to read these reports</b> — full scoring methodology &amp; judge provenance</summary><p>{scoring_note}</p></details>
  </div>"""
        toolbar_html = f"""  <div class="catalog-toolbar">
{filter_bar}
    <div class="toolbar-right">
      <input id="report-search" class="search-input" type="search" placeholder="Search reports, models, findings…" aria-label="Search reports">
      <button id="density-toggle" class="density-btn" type="button" aria-pressed="false" title="Toggle between compact takeaway cards and full tables">Compact cards</button>
      <span id="visible-count" class="visible-count" aria-live="polite">{len(runs)} of {len(runs)} reports shown</span>
    </div>
  </div>"""
    else:
        legend_html = f'  <div class="legend"><b>How to read these reports.</b> {scoring_note}</div>'
        toolbar_html = filter_bar
    html = f"""<!doctype html>
<html lang="en" data-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>OpenClinAI — clinical AI validation runs</title>
<meta name="description" content="Dated ChartSearchAI evaluations and Catalyst workflow reports, with recorded methods, results and limitations.">
<link rel="canonical" href="https://reports.openclinai.org/">
<link rel="sitemap" type="application/xml" href="https://reports.openclinai.org/sitemap.xml">
<script>{theme_bootstrap_js("oc-theme-index")}</script>
<style>{STYLE}</style>
</head>
<body>
{THEME_TOGGLE_BUTTON_HTML}
<div class="wrap">
  <nav class="site-parent" aria-label="Site navigation"><a href="https://openclinai.org/">Open Clinical AI</a> / <a href="https://openclinai.org/validation-harness/">Validation Harness</a> / Reports</nav>
  <header class="page">
    <h1>Clinical AI validation runs</h1>
    <p class="intro">{manifest.get("intro", "")}</p>
  </header>
{legend_html}
{toolbar_html}
{cards}
  <footer class="page">These reports describe dated runs, not current deployment or release acceptance. Hover an AI setup name for its model lineup.</footer>
</div>
<script>{theme_toggle_js("oc-theme-index")}</script>
<script>{FILTER_JS}</script>
</body>
</html>
"""
    sitemap = Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    urls = ['https://reports.openclinai.org/'] + [
        f"https://reports.openclinai.org/{r['slug']}/index.html" for r in runs + earlier
        if r.get('availability') != 'unavailable']
    for url in urls:
        SubElement(SubElement(sitemap, 'url'), 'loc').text = url
    (REPORTS / 'sitemap.xml').write_bytes(tostring(sitemap, encoding='utf-8', xml_declaration=True))
    out = REPORTS / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out} ({len(runs)} curated runs)")
    for r in runs:
        g = gather(r["slug"])
        detail = (
            "reader-led comparison"
            if g.get("reader_led")
            else f"{len(g['scout'])} setups scored"
        )
        print(f"  {r['slug']:38} {detail} — {r['title']}")


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error

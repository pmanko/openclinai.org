#!/usr/bin/env python3
"""Check local navigation, fragments and assets in landing and rendered docs; no network."""
from __future__ import annotations

import argparse
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS_BASE = "/openclinai.org/"


class Page(HTMLParser):
    def __init__(self, text: str):
        super().__init__()
        self.ids: set[str] = set()
        self.references: list[str] = []
        self.scripts: list[str] = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"])
        if tag == "script" and values.get("src"):
            self.scripts.append(values["src"])
        if tag == "a" and values.get("href"):
            self.references.append(values["href"])
        if tag in {"img", "script", "source", "video", "iframe"}:
            for attr in ("src", "poster"):
                if values.get(attr):
                    self.references.append(values[attr])
        if tag == "link" and values.get("href") and values.get("rel") in {"stylesheet", "icon", "modulepreload"}:
            self.references.append(values["href"])


def check(root: Path, base: str = "/") -> list[str]:
    root = root.resolve()
    pages = {path: Page(path.read_text(encoding="utf-8")) for path in root.rglob("*.html")}
    errors = []
    for path, page in pages.items():
        # Design previews declare fragment targets in client-rendered markup.
        # Check declarations without executing scripts; this is not browser acceptance.
        for source in page.scripts:
            parsed = urlsplit(source)
            script = (path.parent / parsed.path).resolve()
            if not parsed.scheme and script.is_relative_to(root) and script.is_file():
                page.ids.update(re.findall(r'''\bid=["']([^"']+)["']''', script.read_text()))
    for path, page in pages.items():
        for reference in page.references:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc:
                continue
            fragment = unquote(parsed.fragment)
            if fragment.startswith("/") and parsed.path in {"", base}:
                # Documentation hash routes have full-HTML twins; status and
                # product design hashes are interpreted by their own UI.
                route = fragment.lstrip("/")
                destination = root / ("welcome.html" if route in {"", "welcome"} else route + ".html")
                if not destination.is_file():
                    errors.append(f"{path.relative_to(root)}: missing route {reference}")
                continue
            target = unquote(parsed.path)
            if not target:
                destination = path
            elif target.startswith("/"):
                if base != "/" and not target.startswith(base):
                    errors.append(f"{path.relative_to(root)}: outside site base {reference}")
                    continue
                destination = root / target.removeprefix(base)
            else:
                destination = path.parent / target
            destination = destination.resolve()
            if destination.is_dir():
                destination /= "index.html"
            if not destination.is_relative_to(root) or not destination.is_file():
                errors.append(f"{path.relative_to(root)}: missing local target {reference}")
                continue
            if fragment and not fragment.startswith(("view=", "mode=")) and destination in pages and fragment not in pages[destination].ids:
                errors.append(f"{path.relative_to(root)}: missing fragment {reference}")
    for path in root.rglob("*.css"):
        for reference in re.findall(r"url\([\"']?([^\"')]+)[\"']?\)", path.read_text()):
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = unquote(parsed.path)
            destination = root / target.removeprefix(base) if target.startswith("/") else path.parent / target
            if not destination.is_file():
                errors.append(f"{path.relative_to(root)}: missing CSS asset {reference}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--landing", type=Path, default=ROOT / "landing")
    parser.add_argument("--docs", type=Path, default=ROOT / "site/dist")
    args = parser.parse_args(argv)
    errors = []
    for root, base in ((args.landing, "/"), (args.docs, DOCS_BASE)):
        if not (root / "index.html").is_file():
            errors.append(f"missing built entry: {root / 'index.html'}")
        else:
            errors.extend(check(root, base))
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Website navigation, fragments and local assets resolve (landing and rendered documentation).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

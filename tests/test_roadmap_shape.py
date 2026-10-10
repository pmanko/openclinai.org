"""Shape rules for the roadmap index and the focused stream specs.

The index and the stream specs hold target paths with checkboxes. Dated evidence
(test counts, commit hashes, verification narratives) belongs in ``specs/reviews/``.
These rules keep that split from eroding one PR at a time.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECS = ROOT / "specs"
INDEX = SPECS / "roadmap.md"
INDEX_MAX_LINES = 150

# Stream specs are the top-level specs other than the index and the architecture.
STREAM_SPECS = sorted(
    path for path in SPECS.glob("*.md") if path.name not in {"roadmap.md", "architecture.md"}
)

# A 40-character hash, or a 7-8 character hex token containing a digit, outside links.
HASH_IN_PROSE = re.compile(r"\b[0-9a-f]{40}\b|\b(?=[0-9a-f]{7,8}\b)[0-9a-f]*\d[0-9a-f]*\b")
COUNT_PHRASE = re.compile(
    r"\b\d[\d,]*\s+(?:\w+\s+){0,2}(?:tests?|checks?)\s+(?:passed|pass)\b"
    r"|\bpassed\s+\d[\d,]*\s+tests?\b",
    re.IGNORECASE,
)
ITEM_START = re.compile(r"^\s*- \[(?P<mark>[ xX])\]")


def prose_only(text: str) -> str:
    """Drop link targets and reference definitions so pinned URLs are not counted."""
    text = re.sub(r"\]\([^)]*\)", "]()", text)
    text = re.sub(r"(?m)^\s*\[[^\]]+\]:\s*\S+.*$", "", text)
    text = re.sub(r"`[^`\n]*`", "``", text)
    return text


def checkbox_items(text: str) -> list[tuple[str, str]]:
    """Return (mark, full item text including wrapped continuation lines)."""
    items: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        match = ITEM_START.match(line)
        if match:
            items.append((match.group("mark").lower(), [line]))
        elif items and line.startswith("  ") and line.strip():
            items[-1][1].append(line)
        else:
            items.append(("", []))  # any other line ends the current item
    return [(mark, " ".join(lines)) for mark, lines in items if mark]


class RoadmapShapeTests(unittest.TestCase):
    def test_index_stays_short(self):
        lines = INDEX.read_text(encoding="utf-8").splitlines()
        self.assertLessEqual(len(lines), INDEX_MAX_LINES, "move narrative into a stream spec or a dated review")

    def test_index_and_stream_specs_carry_no_hashes_or_test_counts(self):
        for spec in [INDEX, *STREAM_SPECS]:
            with self.subTest(spec=spec.name):
                text = prose_only(spec.read_text(encoding="utf-8"))
                self.assertIsNone(HASH_IN_PROSE.search(text), "commit hashes belong in specs/reviews/")
                self.assertIsNone(COUNT_PHRASE.search(text), "test counts belong in specs/reviews/")

    def test_ticked_boxes_link_to_evidence(self):
        for spec in [INDEX, *STREAM_SPECS]:
            with self.subTest(spec=spec.name):
                for mark, item in checkbox_items(spec.read_text(encoding="utf-8")):
                    if mark == "x":
                        self.assertIn("](", item, f"ticked item without an evidence link: {item[:80]}")

    def test_stream_specs_have_a_target_path(self):
        for spec in STREAM_SPECS:
            with self.subTest(spec=spec.name):
                self.assertTrue(checkbox_items(spec.read_text(encoding="utf-8")), "a stream spec needs checkbox items")


if __name__ == "__main__":
    unittest.main()

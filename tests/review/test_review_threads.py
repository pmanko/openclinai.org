"""threads.py behaviour: the until filter and the carried threads, run on fixture dicts."""
import importlib.util
import pathlib
import unittest

SPEC = importlib.util.spec_from_file_location(
    "threads", pathlib.Path(__file__).resolve().parents[2] / "review" / "bin" / "threads.py")
threads = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(threads)


def thread(tid, *ats, resolved=False):
    return {"id": tid, "path": "a.java", "line": 1, "resolved": resolved, "outdated": False,
            "url": None, "awaiting_reply": True,
            "comments": [{"by": "dkayiwa", "at": at, "body": f"c{at}", "url": None} for at in ats]}


class FilterUntil(unittest.TestCase):

    def test_drops_threads_opened_after_and_later_replies(self):
        data = {"conversation": [{"at": "2026-10-21T09:00:00Z"}, {"at": "2026-10-21T12:00:00Z"}],
                "threads": [thread("old", "2026-10-21T09:00:00Z", "2026-10-21T13:00:00Z", resolved=True),
                            thread("late", "2026-10-21T11:30:00Z")]}
        out = threads.filter_until(data, "2026-10-21T11:00:00Z")
        self.assertEqual([t["id"] for t in out["threads"]], ["old"])
        self.assertEqual(len(out["threads"][0]["comments"]), 1)
        self.assertFalse(out["threads"][0]["resolved"], "a reply after the cut-off cannot have resolved it")
        self.assertEqual(len(out["conversation"]), 1)
        self.assertEqual(out["until"], "2026-10-21T11:00:00Z")

    def test_no_cut_off_returns_the_data_unchanged(self):
        data = {"conversation": [], "threads": [thread("t", "2026-10-21T09:00:00Z")]}
        self.assertIs(threads.filter_until(data, None), data)


class WithPrevious(unittest.TestCase):

    def test_attaches_the_replaced_prs_threads(self):
        data = {"pr": 95, "conversation": [], "threads": []}
        prev = {"pr": 85, "url": "u", "title": "old", "threads": [thread("ask", "2026-10-20T20:00:00Z")]}
        out = threads.with_previous(data, [prev])
        self.assertEqual(out["previous"][0]["pr"], 85)
        self.assertEqual(out["previous"][0]["threads"][0]["id"], "ask")


if __name__ == "__main__":
    unittest.main()

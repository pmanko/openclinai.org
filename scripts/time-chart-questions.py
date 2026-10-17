#!/usr/bin/env python3
"""Ask the provider-parity questions of one ChartSearchAI provider and time each turn.

Usage: scripts/time-chart-questions.py LABEL PROVIDER [PROFILE|-] [QUESTION_INDEXES]
  e.g. scripts/time-chart-questions.py baseline bundled
       scripts/time-chart-questions.py baseline hub single-12b-checked > hub.jsonl

Each question starts a fresh conversation as eval-nurse at Outpatient Clinic on the
sample HIV chart. One JSON line per question goes to stdout; the slice of the
host router's log for that turn gives every model call's prompt size, tokens read,
tokens reused and read time. A one-line summary per question goes to stderr.
"""
import base64, http.cookiejar, json, os, re, sys, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = f"http://localhost:{os.environ.get('HARNESS_PROXY_HTTP_PORT', '8088')}/openmrs/ws/rest/v1"
USER, PASSWORD = "eval-nurse", os.environ.get("EVALUATION_PASSWORD", "Admin123")
LOCATION = "44c3efb0-2583-4c80-a79e-1f756a03c0a1"  # Outpatient Clinic
PATIENT = "dd75c020-1691-11df-97a5-7038c432aabf"
ROUTER_LOGS = [ROOT / "artifacts" / "llama-router" / n for n in ("router.log", "router.stdout.log")]
QUESTIONS = [
    "What is this patient's most recent weight?",
    "What medications is this patient currently taking?",
    "What were this patient's most recent CD4 count and viral load?",
    "Does this patient have any drug allergies?",
    "Summarize this patient's HIV care history.",
]
TIMING = re.compile(r"prompt eval time =\s*([\d.]+) ms /\s*(\d+) tokens")
GEN = re.compile(r"\|\s+eval time =\s*([\d.]+) ms /\s*(\d+) tokens")
RELEASE = re.compile(r"stop processing: n_tokens = (\d+)")


def session():
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    auth = urllib.request.Request(f"{BASE}/session")
    auth.add_header("Authorization", "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode())
    opener.open(auth).read()
    loc = urllib.request.Request(f"{BASE}/session", data=json.dumps({"sessionLocation": LOCATION}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    opener.open(loc).read()
    return opener


def log_sizes():
    return [len(p.read_text(errors="replace").splitlines()) if p.exists() else 0 for p in ROUTER_LOGS]


def router_calls(starts):
    lines = [l for p, start in zip(ROUTER_LOGS, starts) if p.exists()
             for l in p.read_text(errors="replace").splitlines()[start:]]
    calls, cur = [], {}
    for line in lines:
        if m := TIMING.search(line):
            cur = {"read_tokens": int(m[2]), "read_s": round(float(m[1]) / 1000, 1)}
        elif (m := GEN.search(line)) and cur:
            cur.update(gen_tokens=int(m[2]), gen_s=round(float(m[1]) / 1000, 1))
        elif (m := RELEASE.search(line)) and cur:
            cur["prompt_tokens"] = int(m[1]) - cur.get("gen_tokens", 0)
            cur["reused_tokens"] = cur["prompt_tokens"] - cur["read_tokens"]
            calls.append(cur)
            cur = {}
    return calls


def new_conversation(opener, provider):
    req = urllib.request.Request(f"{BASE}/chartsearchai/chat/new",
                                 data=json.dumps({"patient": PATIENT, "provider": provider}).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    opener.open(req).read()


def ask(opener, question, provider, profile):
    new_conversation(opener, provider)
    body = {"patient": PATIENT, "question": question, "provider": provider}
    if profile:
        body["profile"] = profile
    req = urllib.request.Request(f"{BASE}/chartsearchai/chat/stream", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"}, method="POST")
    events, answer, event, first = [], "", None, None
    t0 = time.monotonic()
    with opener.open(req, timeout=3600) as resp:
        for raw in resp:
            line = raw.decode(errors="replace").rstrip("\n")
            if line.startswith("event: "):
                event = line[7:]
                if event != "heartbeat":
                    events.append(event)
            elif line.startswith("data: ") and event in ("answer_done", "turn_done", "error"):
                data = json.loads(line[6:])
                answer = data.get("answer") or data.get("message") or answer
                if event == "answer_done":
                    first = round(time.monotonic() - t0, 1)
            if event in ("turn_done", "error") and line == "":
                break
    return events, answer, first


def main():
    label, provider = sys.argv[1], sys.argv[2]
    profile = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "-" else None
    picked = [QUESTIONS[int(i)] for i in sys.argv[4].split(",")] if len(sys.argv) > 4 else QUESTIONS
    opener = session()
    for question in picked:
        start = log_sizes()
        t0 = time.monotonic()
        events, answer, first = ask(opener, question, provider, profile)
        elapsed = round(time.monotonic() - t0, 1)
        time.sleep(1)
        calls = router_calls(start)
        print(json.dumps({"label": label, "provider": provider, "profile": profile, "question": question,
                          "first_answer_s": first, "seconds": elapsed, "events": events, "calls": calls, "answer": answer}), flush=True)
        read = sum(c["read_tokens"] for c in calls)
        sent = sum(c["prompt_tokens"] for c in calls)
        print(f"{elapsed:7.1f} s  {len(calls)} calls  read {read:,} of {sent:,} tokens  {question}", file=sys.stderr)


if __name__ == "__main__":
    main()

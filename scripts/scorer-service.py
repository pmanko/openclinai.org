#!/usr/bin/env python3
"""A local entailment scorer for the Hub's shadow citation check (confidence-labels L6).

Serves ``POST /score`` with ``{"pairs": [{"source": str, "statement": str}, ...]}`` and answers
``{"scores": [{"supported": p, "contradicted": p}, ...]}``, one entry per pair in order, plus
``GET /health``. The model comes from ``SCORER_MODEL`` (a Hugging Face NLI cross-encoder id;
its ``entailment`` and ``contradiction`` labels are read from the model's config). Runs on the
CPU by default (``SCORER_DEVICE``); the GPU is the router's.

Usage: scripts/scorer-up.sh, or
  SCORER_MODEL=MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli python3 scripts/scorer-service.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

MODEL = os.environ.get("SCORER_MODEL", "MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli")
PORT = int(os.environ.get("SCORER_PORT", "8090"))
DEVICE = os.environ.get("SCORER_DEVICE", "cpu")
MAX_TOKENS = int(os.environ.get("SCORER_MAX_TOKENS", "1024"))


class Scorer:
    def __init__(self) -> None:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL)
        self.model = AutoModelForSequenceClassification.from_pretrained(MODEL).to(DEVICE).eval()
        labels = {str(v).lower(): int(k) for k, v in self.model.config.id2label.items()}
        self.entail = next(i for name, i in labels.items() if name.startswith("entail"))
        self.contra = next(i for name, i in labels.items() if name.startswith("contra"))

    def score(self, pairs: list[dict]) -> list[dict]:
        if not pairs:
            return []
        batch = self.tokenizer(
            [str(p.get("source") or "") for p in pairs],
            [str(p.get("statement") or "") for p in pairs],
            truncation="only_first",
            max_length=MAX_TOKENS,
            padding=True,
            return_tensors="pt",
        ).to(DEVICE)
        with self.torch.no_grad():
            probs = self.model(**batch).logits.softmax(-1).cpu().tolist()
        return [
            {"supported": round(row[self.entail], 4), "contradicted": round(row[self.contra], 4)}
            for row in probs
        ]


SCORER: Scorer | None = None


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: dict) -> None:
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send(200, {"status": "ok", "model": MODEL, "device": DEVICE})
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/score":
            self._send(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            pairs = payload.get("pairs") or []
            if not isinstance(pairs, list) or len(pairs) > 64:
                raise ValueError("pairs must be a list of at most 64 entries")
            started = time.time()
            scores = SCORER.score(pairs)
            self._send(200, {"scores": scores, "model": MODEL, "seconds": round(time.time() - started, 3)})
        except Exception as e:  # noqa: BLE001
            self._send(400, {"error": str(e)})

    def log_message(self, fmt, *args):  # noqa: A003
        sys.stderr.write("scorer: " + (fmt % args) + "\n")


def main() -> None:
    global SCORER
    SCORER = Scorer()
    print(f"scorer ready on :{PORT} model={MODEL} device={DEVICE}", flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

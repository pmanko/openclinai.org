"""Read a patient's complete QueryStore record ledger for the umbrella's corpus scripts.

Pages the patient record endpoint until ``totalCount`` records have arrived, as the Hub's own
client does: OpenMRS caps ``limit`` (100 records per page on the HIV baseline), so a page shorter
than the requested size does not mean the chart has ended.
"""

from __future__ import annotations

import base64
import json
import urllib.parse
import urllib.request
from typing import Any


def live_records(
    endpoint: str, patient: str, username: str, password: str, *, page_size: int = 500
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    while True:
        query = urllib.parse.urlencode(
            {"patient": patient, "limit": page_size, "startIndex": len(records)}
        )
        request = urllib.request.Request(
            f"{endpoint}?{query}", headers={"Authorization": f"Basic {token}"}
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            payload: dict[str, Any] = json.load(response)
        page = payload.get("results") or []
        records.extend(page)
        total = payload.get("totalCount")
        if not page or (type(total) is int and len(records) >= total):
            break
        if type(total) is not int:
            raise ValueError(f"QueryStore returned no totalCount for patient {patient}")
    if type(total) is int and len(records) != total:
        raise ValueError(
            f"QueryStore returned {len(records)} of {total} records for patient {patient}"
        )
    return records

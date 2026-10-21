import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = ROOT / "targets/validation-harness"
FIXTURE = HARNESS_ROOT / "datasets/validation/conformance/dual-provider-conformance.v1.json"
FIXTURE_COPIES = (
    ROOT / "targets/med-agent-hub/tests/conformance/dual-provider-conformance.v1.json",
    ROOT / "targets/querystore/api/src/test/resources/conformance/dual-provider-conformance.v1.json",
    ROOT / "targets/chartsearchai/api/src/test/resources/conformance/dual-provider-conformance.v1.json",
    ROOT / "targets/chartsearchai-esm/src/conformance/dual-provider-conformance.v1.json",
)


def test_dual_provider_fixture_has_stable_non_overlapping_case_ids():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "dual_provider_conformance.v1"
    families = {
        "provider_lifecycle",
        "provider_capabilities",
        "querystore_records",
        "context_policy",
        "temporal_gate",
        "drug_safety_status",
    }
    assert families <= set(payload)

    identifiers = [case["id"] for family in families for case in payload[family]]
    assert len(identifiers) == len(set(identifiers))
    assert all(identifier.count(".") >= 1 for identifier in identifiers)



def test_every_consumer_copy_carries_canonical_cases_unchanged():
    """Integrity of executable data: a consumer may keep only the cases its own tests read, but
    every case it keeps must be the canonical case with that id, unchanged."""
    canonical = json.loads(FIXTURE.read_text(encoding="utf-8"))
    canonical_cases = {
        case["id"]: case
        for family, cases in canonical.items()
        if isinstance(cases, list)
        for case in cases
    }

    for copy in FIXTURE_COPIES:
        payload = json.loads(copy.read_text(encoding="utf-8"))
        assert payload["schema_version"] == canonical["schema_version"], f"schema drift: {copy}"
        for family, cases in payload.items():
            if not isinstance(cases, list):
                continue
            assert family in canonical, f"unknown family {family} in {copy}"
            for case in cases:
                assert case == canonical_cases.get(case["id"]), f"stale case {case['id']} in {copy}"

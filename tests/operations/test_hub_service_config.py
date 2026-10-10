"""Security invariants for the Hub service in the local product compose file."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
HUB = yaml.safe_load((ROOT / "compose/openmrs-2.8-refapp.yml").read_text(encoding="utf-8"))["services"]["med-agent-hub"]


def test_hub_is_published_on_loopback_only():
    """Invariant: the Hub API is never exposed beyond the host."""
    assert all(str(port).startswith("127.0.0.1:") for port in HUB.get("ports", []))


def test_hub_has_no_default_querystore_credentials():
    """Invariant: compose never supplies a QueryStore credential; the caller does."""
    for key in ("QUERYSTORE_USERNAME", "QUERYSTORE_PASSWORD"):
        value = str(HUB["environment"][key])
        default = value.split(":-", 1)[1].rstrip("}") if ":-" in value else ""
        assert default == "", key

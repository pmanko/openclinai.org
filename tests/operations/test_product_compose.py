"""Security and ownership invariants for the local product compose file."""
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
COMPOSE = yaml.safe_load((ROOT / "compose/openmrs-2.8-refapp.yml").read_text(encoding="utf-8"))
HUB = COMPOSE["services"]["med-agent-hub"]


def test_hub_is_published_on_loopback_only():
    """Invariant: the Hub API is never exposed beyond the host."""
    assert all(str(port).startswith("127.0.0.1:") for port in HUB.get("ports", []))


def test_hub_has_no_default_querystore_credentials():
    """Invariant: compose never supplies a QueryStore credential; the caller does."""
    for key in ("QUERYSTORE_USERNAME", "QUERYSTORE_PASSWORD"):
        value = str(HUB["environment"][key])
        default = value.split(":-", 1)[1].rstrip("}") if ":-" in value else ""
        assert default == "", key


def test_product_compose_does_not_mount_publication_paths():
    """Invariant: product services never mount the website or report publication paths."""
    for name, service in COMPOSE["services"].items():
        for volume in service.get("volumes", []):
            target = volume if isinstance(volume, str) else volume.get("target", "")
            assert ":/srv/landing" not in str(target) and ":/srv/reports" not in str(target), (name, volume)

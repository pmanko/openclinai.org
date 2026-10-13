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


def _moving(reference: str) -> bool:
    if "${" in reference:
        return True  # a tag chosen by a variable is not a pin
    name = reference.split("@", 1)[0].rsplit("/", 1)[-1]
    tag = name.split(":", 1)[1] if ":" in name else "latest"
    return tag == "latest" or tag.startswith("nightly")


def test_images_on_moving_tags_are_pinned_by_digest():
    """Invariant: images pinned by digest; a pulled or built-from image on a moving tag carries one."""
    references = []
    for name, service in COMPOSE["services"].items():
        if "build" in service:
            references += [(name, str(value)) for value in (service["build"].get("args") or {}).values()
                           if "/" in str(value)]
        elif "image" in service:
            references.append((name, str(service["image"])))
    for name, reference in references:
        if _moving(reference):
            assert "@sha256:" in reference, (name, reference)

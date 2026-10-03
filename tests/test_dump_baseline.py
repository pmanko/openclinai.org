"""Selected research imports must not substitute another portable dataset."""

import importlib.util
import os
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("verify_portable_dump", ROOT / "scripts/verify-portable-dump.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class BaselineTests(unittest.TestCase):
    def test_selected_seed_requires_exact_preset_identity_and_valid_provenance(self):
        baseline = {"sha256": "a" * 64, "bytes": 100}
        for digest, size, issues, expected in (
                ("a" * 64, 100, [], 0), ("b" * 64, 100, [], 1),
                ("a" * 64, 99, [], 1), ("a" * 64, 100, ["corrupt dump"], 1)):
            with self.subTest(digest=digest, size=size, issues=issues):
                with patch.dict(os.environ, {"OPENCLINAI_ENVIRONMENT": "study"}), \
                        patch.object(verifier, "verify_dump", return_value=(
                            {"output_sha256": digest, "output_bytes": size}, list(issues))), \
                        patch.object(verifier, "resolve", return_value={"preset": {"baseline": baseline}}), \
                        patch("sys.argv", ["verify", "--dump", "fixture.sql", "--require-portable"]), \
                        patch("builtins.print"):
                    assert verifier.main() == expected

    def test_invalid_selected_instance_stops_verification(self):
        with patch.dict(os.environ, {"OPENCLINAI_ENVIRONMENT": "unknown"}), \
                patch.object(verifier, "verify_dump", return_value=({}, [])), \
                patch.object(verifier, "resolve", side_effect=verifier.ConfigError("missing settings")), \
                patch("sys.argv", ["verify", "--dump", "fixture.sql", "--require-portable"]), \
                patch("builtins.print"):
            assert verifier.main() == 1

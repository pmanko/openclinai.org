"""Ownership invariants between the umbrella and the validation harness.

Each test protects one permanent boundary from the architecture: the harness runs
experiments only, the umbrella owns product operations and publication, and the two
are coupled through explicit delegation. Tests assert forbidden couplings and
delegation behavior, never the current inventory of targets, scripts or text.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "targets" / "validation-harness"


class OperationOwnershipTests(unittest.TestCase):
    def test_harness_makefile_does_not_couple_to_products_or_deployment(self):
        """Invariant: the harness Makefile never invokes Docker, Git or product checkouts."""
        source = (HARNESS / "Makefile").read_text()
        for coupling in ("docker ", "targets/", "git "):
            self.assertNotIn(coupling, source)

    def test_operation_scripts_live_in_exactly_one_repository(self):
        """Invariant: an umbrella operation script is never duplicated in the harness."""
        for script in (ROOT / "scripts").iterdir():
            if script.is_file():
                with self.subTest(script=script.name):
                    self.assertFalse((HARNESS / "scripts" / script.name).exists())

    def test_data_and_validation_targets_delegate_to_the_harness_checkout(self):
        """Invariant: umbrella data targets run the harness from its gitlink checkout."""
        for target in ("load-test", "orphan-fk-check", "import-smoke", "completeness-check"):
            with self.subTest(target=target):
                output = subprocess.run(
                    ["make", "-n", "--no-print-directory", target, "UV=uv-stub"],
                    cwd=ROOT, capture_output=True, text=True, check=True, timeout=15,
                ).stdout
                self.assertIn("uv-stub --directory targets/validation-harness run", output)

    def test_makefile_supplies_absolute_trace_and_corpus_receipt(self):
        """Behavior: validate-run passes the caller's trace file and corpus receipt through."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            trace = root / "traces.jsonl"
            receipt = root / "corpus.json"
            log = root / "arguments.json"
            wrapper = root / "uv-stub"
            wrapper.write_text(
                f"#!{sys.executable}\nimport json, sys\n"
                f"from pathlib import Path\nPath({str(log)!r}).write_text(json.dumps(sys.argv[1:]))\n"
            )
            wrapper.chmod(0o755)
            subprocess.run([
                "make", "--no-print-directory", "validate-run", "MAKE=true",
                f"UV={wrapper}", f"TRACE_FILE={trace}", f"CORPUS_PROVENANCE={receipt}",
            ], cwd=ROOT, capture_output=True, text=True, check=True, timeout=15)
            args = json.loads(log.read_text())
            self.assertEqual(args[:6], [
                "--directory", "targets/validation-harness", "run", "harness-cli", "validate", "run",
            ])
            self.assertEqual(args[args.index("--trace-file") + 1], str(trace))
            self.assertEqual(args[args.index("--corpus-provenance") + 1], str(receipt))

    def test_local_compose_does_not_publish_website_or_reports(self):
        """Invariant: the product compose never mounts publication paths and keeps the Hub on loopback."""
        source = (ROOT / "compose" / "openmrs-2.8-refapp.yml").read_text()
        self.assertNotIn("/srv/landing", source)
        self.assertNotIn("/srv/reports", source)
        self.assertRegex(source, r"127\.0\.0\.1:\$\{MED_AGENT_HUB_PORT")

    def test_harness_ci_does_not_check_out_or_build_products(self):
        """Invariant: harness CI never pulls product submodules or runs the assembled OpenMRS build."""
        source = (HARNESS / ".github" / "workflows" / "harness-ci.yml").read_text()
        self.assertNotIn("submodules: recursive", source)
        self.assertNotIn("make openmrs-source-pair-test", source)


if __name__ == "__main__":
    unittest.main()

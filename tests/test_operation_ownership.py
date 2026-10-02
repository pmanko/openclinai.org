"""Ownership checks, independent of component checkout and workspace link checks."""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "targets" / "validation-harness"


class OperationOwnershipTests(unittest.TestCase):
    def test_harness_makefile_has_no_product_or_deployment_commands(self):
        source = (HARNESS / "Makefile").read_text()
        targets = set(re.findall(r"^([a-z][a-z0-9-]*):", source, re.MULTILINE))
        self.assertEqual(targets, {
            "setup", "python-pin", "test", "smoke", "clean-venv",
            "load-test", "orphan-fk-check", "import-smoke", "completeness-check",
            "validate-run", "validate-judge-prep", "validate-judge-finalize",
            "validate-report", "validate-adjudicate",
        })
        for coupling in ("docker ", "targets/", "med-agent-hub-up", "dashboard-ensure", "git "):
            self.assertNotIn(coupling, source)

    def test_required_operations_exist_only_in_umbrella(self):
        for name in (
            "catalyst-mvp.sh", "catalyst-model-router.sh", "chartsearchai-local.sh",
            "stack-up.sh", "stack-down.sh", "local-stack-up.sh", "local-stack-down.sh",
            "openmrs-source-pair-test.sh", "artifact-provenance.py", "seed-local.sh",
            "querystore-recreate-index.sh", "validate-preflight.sh",
        ):
            with self.subTest(name=name):
                self.assertTrue((ROOT / "scripts" / name).is_file())
                self.assertFalse((HARNESS / "scripts" / name).exists())

    def test_umbrella_calls_harness_for_validation_and_data(self):
        source = (ROOT / "Makefile").read_text()
        self.assertIn("HARNESS := targets/validation-harness", source)
        self.assertIn("--directory $(HARNESS) run harness-cli validate run", source)
        for module in ("harness.load", "harness.transform.orphan_fk", "harness.import_smoke", "harness.transform.completeness"):
            self.assertIn("--directory $(HARNESS) run python -m " + module, source)
        self.assertNotIn("dashboard-ensure", source)

    def test_makefile_supplies_absolute_trace_and_corpus_receipt(self):
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
        source = (ROOT / "compose" / "openmrs-2.8-refapp.yml").read_text()
        self.assertNotIn("/srv/landing", source)
        self.assertNotIn("/srv/reports", source)
        self.assertIn("../targets/med-agent-hub", source)
        self.assertIn("QUERYSTORE_PASSWORD: ${QUERYSTORE_PASSWORD:-}", source)
        self.assertIn("127.0.0.1:${MED_AGENT_HUB_PORT:-18081}", source)

    def test_product_ci_is_not_run_by_harness(self):
        source = (HARNESS / ".github" / "workflows" / "harness-ci.yml").read_text()
        self.assertNotIn("submodules: recursive", source)
        self.assertNotIn("openmrs-integration-source:", source)
        self.assertNotIn("make openmrs-source-pair-test", source)
        self.assertIn("openmrs-integration-source:", (ROOT / ".github" / "workflows" / "operations.yml").read_text())


if __name__ == "__main__":
    unittest.main()

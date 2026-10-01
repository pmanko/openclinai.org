from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/verify-doc-drift.sh"
DOCUMENTS = (
    "targets/chartsearchai/README.md",
    "targets/chartsearchai-esm/README.md",
    "targets/med-agent-hub/README.md",
    "targets/querystore/docs/rest-api.md",
)


def _run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT)],
        env={**os.environ, "WORKSPACE_ROOT": str(root)},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def _workspace(tmp_path: Path) -> Path:
    for relative in DOCUMENTS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, destination)
    return tmp_path


def test_current_product_documentation_contracts_pass() -> None:
    result = _run(ROOT)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS: checked 4 current product documentation contracts" in result.stdout


def test_contract_check_requires_only_product_documents_not_git_or_old_specs(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    (workspace / "README.md").write_text("chartSnapshot is an obsolete example\n")
    result = _run(workspace)
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "claim",
    (
        "Only med-agent-hub remains the provider.",
        "Bundled provider removed.",
        "chartSnapshot is current state.",
        "indepth_token is an event.",
    ),
)
def test_contract_check_rejects_retired_claims_in_current_product_docs(tmp_path: Path, claim: str) -> None:
    workspace = _workspace(tmp_path)
    document = workspace / DOCUMENTS[0]
    document.write_text(document.read_text() + "\n" + claim + "\n")
    result = _run(workspace)
    assert result.returncode == 1
    assert DOCUMENTS[0] in result.stdout


def test_contract_check_requires_positive_provider_disclosure(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    document = workspace / DOCUMENTS[0]
    document.write_text(document.read_text().replace("No automatic fallback", "Fallback is unspecified"))
    result = _run(workspace)
    assert result.returncode == 1
    assert "missing contract /no automatic fallback/" in result.stdout


def test_contract_check_fails_closed_on_missing_product_docs(tmp_path: Path) -> None:
    result = _run(tmp_path)
    assert result.returncode == 1
    for relative in DOCUMENTS:
        assert f"{relative}: missing product documentation" in result.stdout

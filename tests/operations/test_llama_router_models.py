import configparser
import hashlib
import os
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRESET_PATH = ROOT / "scripts" / "llama-router.ini"
MODELS_PATH = ROOT / "scripts" / "llama-router.models.tsv"
ROUTER_UP = ROOT / "scripts" / "llama-router-up.sh"


def test_pinned_native_models_have_a_preset_reading_their_file():
    """Invariant: the native router's pinned model manifest and its presets describe the same files."""
    presets = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=(";",))
    presets.read(PRESET_PATH)
    for line in MODELS_PATH.read_text().splitlines():
        if not line or line.startswith("#"):
            continue
        alias, filename, sha256, source = line.split("\t")
        assert presets.has_section(alias), alias
        assert presets[alias]["model"] == f"artifacts/llama-router/models/{alias}.gguf"
        assert re.fullmatch(r"[a-f0-9]{64}", sha256), alias
        assert re.fullmatch(
            rf"https://huggingface\.co/[^/]+/[^/]+/resolve/[a-f0-9]{{40}}/{re.escape(filename)}",
            source,
        ), alias


def test_router_launcher_verifies_pinned_model_checksums_and_rejects_mismatch(tmp_path):
    """Behavior: llama-router-up.sh enforces SHA-256 verification against llama-router.models.tsv."""
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    home = tmp_path / "home"
    home.mkdir()
    manifest = tmp_path / "models.tsv"
    good_bytes = b"GGUF-pinned-fixture"
    good_sha = hashlib.sha256(good_bytes).hexdigest()
    manifest.write_text(
        f"gemma-31b\tgemma-4-31B-it-Q4_K_M.gguf\t{good_sha}\t"
        "https://huggingface.co/unsloth/gemma-4-31B-it-GGUF/resolve/"
        "c1ac76e99d5513b141e8adde7288b85c3f9c32ec/gemma-4-31B-it-Q4_K_M.gguf\n",
        encoding="utf-8",
    )
    env = {
        **os.environ,
        "HOME": str(home),
        "LLAMA_MODEL_DIR": str(model_dir),
        "LLAMA_MODELS_MANIFEST": str(manifest),
        "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
    }

    missing = subprocess.run(
        ["bash", str(ROUTER_UP), "--verify", "gemma-31b"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert missing.returncode == 1
    assert "pinned model is missing" in missing.stderr

    model_file = model_dir / "gemma-31b.gguf"
    model_file.write_bytes(b"corrupted-weights")
    mismatch = subprocess.run(
        ["bash", str(ROUTER_UP)],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert mismatch.returncode == 1
    assert "model checksum mismatch for gemma-31b" in mismatch.stderr

    model_file.write_bytes(good_bytes)
    verified = subprocess.run(
        ["bash", str(ROUTER_UP), "--verify", "gemma-31b"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert verified.returncode == 0
    assert f"verified gemma-31b: {model_file} ({good_sha})" in verified.stdout

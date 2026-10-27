import configparser
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PRESET_PATH = ROOT / "scripts" / "llama-router.ini"
MODELS_PATH = ROOT / "scripts" / "llama-router.models.tsv"


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

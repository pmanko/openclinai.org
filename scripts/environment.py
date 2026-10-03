"""Read-only research environment selection and inspection; no lifecycle changes."""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
NAME = re.compile(r"[a-z][a-z0-9-]{0,47}")
PORTS = {"HARNESS_PROXY_HTTP_PORT", "HARNESS_PROXY_HTTPS_PORT", "OMRS_DB_PORT",
         "QUERYSTORE_ES_PORT", "MED_AGENT_HUB_PORT"}
PRIVATE = {"CHARTSEARCH_ADMIN_USER", "CHARTSEARCH_ADMIN_PASSWORD",
           "CHARTSEARCH_HUB_API_KEY", "QUERYSTORE_USERNAME", "QUERYSTORE_PASSWORD",
           "OMRS_DB_USER", "OMRS_DB_PASSWORD", "MYSQL_ROOT_PASSWORD"}
SUPPORTED = PORTS | PRIVATE | {
    "OMRS_DB_NAME", "OPENMRS_REFAPP_TAG", "OPENMRS_BACKEND_TAG", "LLAMA_MODEL_DIR",
    "CHARTSEARCH_HUB_ENDPOINT_URL", "MED_AGENT_LLM_BASE_URL", "LLAMA_ROUTER_MODELS_MAX",
    "CHARTSEARCH_LOCAL_BUILD", "CHARTSEARCH_LOCAL_WARM", "CHARTSEARCH_LOCAL_WARM_QUESTION",
    "CHARTSEARCH_LOCAL_PATIENT_UUID", "QUERYSTORE_BASE_URL", "QUERYSTORE_VERIFY_BASE_URL",
    "HUB_TIMEZONE", "HUB_ANCHOR",
}


class ConfigError(ValueError):
    pass


def name(value):
    if not isinstance(value, str) or not NAME.fullmatch(value):
        raise ConfigError("Installation/preset name must be lowercase letters, digits and hyphens.")
    return value


def within(root, relative):
    if not isinstance(relative, str) or not relative or Path(relative).is_absolute():
        raise ConfigError("Configuration paths must be relative to the umbrella.")
    target = (root / relative).resolve()
    if not target.is_relative_to(root):
        raise ConfigError("Configuration path escapes the umbrella.")
    return target


def env_values(path):
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        key, separator, value = line.partition("=")
        if not separator or not re.fullmatch(r"[A-Z][A-Z0-9_]*", key) or key in values:
            raise ConfigError("Settings require unique KEY=VALUE lines; shell syntax is unsupported.")
        if value.startswith(("'", '"')):
            if len(value) < 2 or value[-1] != value[0]:
                raise ConfigError("Setting has an unterminated quoted value.")
            value = value[1:-1]
        if "\x00" in value:
            raise ConfigError("Settings cannot contain null characters.")
        values[key] = value
    return values


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ConfigError("Preset JSON has a duplicate field.")
        result[key] = value
    return result


def preset(root, identifier):
    path = within(root, f"environments/{name(identifier)}/preset.json")
    if not path.is_file():
        raise ConfigError("Unknown preset or missing preset file.")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != {"id", "label", "application", "files", "baseline"}:
        raise ConfigError("Preset has missing or unsupported fields.")
    if (value["id"] != identifier or value["application"] != "chartsearchai"
            or not isinstance(value["label"], str) or not value["label"].strip()):
        raise ConfigError("Preset identity/application is unsupported.")
    files = value["files"]
    if not isinstance(files, dict) or set(files) != {"compose", "defaults", "accounts", "experiment", "demo"}:
        raise ConfigError("Preset requires the native configuration, account, experiment and demo paths.")
    for relative in files.values():
        if not within(root, relative).is_file():
            raise ConfigError("A preset reference is missing; initialize the recorded components first.")
    baseline = value["baseline"]
    if not isinstance(baseline, dict) or set(baseline) != {"filename", "sha256", "bytes", "location"}:
        raise ConfigError("Preset baseline identity is incomplete.")
    if (not isinstance(baseline["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", baseline["sha256"])
            or type(baseline["bytes"]) is not int or baseline["bytes"] <= 0
            or not isinstance(baseline["filename"], str)
            or baseline["filename"] in {".", ".."}
            or not re.fullmatch(r"[a-zA-Z0-9_.-]+", baseline["filename"])):
        raise ConfigError("Preset baseline checksum, size or filename is invalid.")
    if not isinstance(baseline["location"], str):
        raise ConfigError("Baseline location must be an HTTPS URL.")
    location = urlsplit(baseline["location"])
    if location.scheme != "https" or not location.hostname or location.username or location.password:
        raise ConfigError("Baseline location must be HTTPS without credentials.")
    return value


def resolve(root, identifier, overrides=None):
    root = root.resolve()
    identifier = name(identifier)
    settings_path = root / ".local/environments" / identifier / "settings.env"
    if settings_path.is_symlink() or not settings_path.resolve().is_relative_to(root):
        raise ConfigError("Private settings cannot be a symlink or escape the umbrella.")
    if not settings_path.is_file():
        raise ConfigError("No installation settings; copy the documented example and set permissions to 600.")
    metadata = settings_path.stat()
    if metadata.st_mode & 0o077 or metadata.st_uid != os.getuid():
        raise ConfigError("Private settings require owner-only permissions (chmod 600) and your ownership.")
    settings = env_values(settings_path)
    selected = preset(root, settings.pop("PRESET", ""))
    defaults = env_values(within(root, selected["files"]["defaults"]))
    overrides = overrides or {}
    if (set(defaults) | set(settings) | set(overrides)) - SUPPORTED:
        raise ConfigError("Unsupported setting name; no operations were performed.")
    if set(overrides) & PRIVATE:
        raise ConfigError("Credentials belong in the private settings file, not command-line options.")
    values, origins = {}, {}
    for origin, layer in (("defaults", defaults), ("instance", settings), ("command", overrides)):
        values.update(layer)
        origins.update({key: origin for key in layer})
    for key, value in values.items():
        if not isinstance(value, str):
            raise ConfigError("Setting values must be strings.")
        if key in PORTS and (not value.isascii() or not value.isdecimal() or not 1 <= int(value) <= 65535):
            raise ConfigError(f"{key} must be a port between 1 and 65535.")
    artifacts = root / "artifacts/environments" / identifier
    if artifacts.resolve() != artifacts or not artifacts.resolve().is_relative_to(root):
        raise ConfigError("Installation artifacts cannot be symlinked or shared with another path.")
    return {"root": root, "name": identifier, "preset": selected,
            "project": f"openclinai-{identifier}", "settings_path": settings_path,
            "artifacts": artifacts,
            "values": values, "origins": origins}


def public_config(config):
    values = config["values"]
    urls = {}
    if "HARNESS_PROXY_HTTP_PORT" in values:
        urls["openmrs"] = f"http://localhost:{values['HARNESS_PROXY_HTTP_PORT']}/openmrs/spa"
    if "MED_AGENT_HUB_PORT" in values:
        urls["hub"] = f"http://localhost:{values['MED_AGENT_HUB_PORT']}"
    return {"name": config["name"], "preset": config["preset"]["id"],
            "project": config["project"], "files": config["preset"]["files"],
            "settings_file": str(config["settings_path"]), "artifacts": str(config["artifacts"]),
            "ports": {key: values[key] for key in sorted(PORTS & values.keys())}, "urls": urls,
            "settings": {key: {"origin": config["origins"][key], "configured": bool(value)}
                         for key, value in sorted(values.items())},
            "data_action": "preserve", "lifecycle": "not_implemented"}


def inspect_command(config, args):
    # Only operational process settings are inherited; ambient Compose/.env values
    # must not silently select a different installation or leak into interpolation.
    env = {key: os.environ[key] for key in ("PATH", "HOME", "LANG", "LC_ALL", "TMPDIR",
                                           "DOCKER_CONTEXT", "DOCKER_HOST", "DOCKER_CONFIG")
           if key in os.environ}
    env.update(config["values"])
    env.update(STACK_CONTAINER_PREFIX=config["project"],
               STACK_ARTIFACTS_DIR=str(config["artifacts"]),
               MED_AGENT_HUB_UID=str(os.getuid()), MED_AGENT_HUB_GID=str(os.getgid()))
    try:
        result = subprocess.run(args, cwd=config["root"], env=env, text=True,
                                capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise ConfigError("Read-only inspection unavailable; check the required tool/service.") from None
    if result.returncode:
        # Native stderr can include interpolated credentials. Never forward it.
        raise ConfigError("Read-only inspection failed; no environment changes were attempted.")
    return result.stdout


def compose_rows(output):
    if output.lstrip().startswith("["):
        return json.loads(output)
    return [json.loads(line) for line in output.splitlines() if line.strip()]


def status(config):
    contexts = json.loads(inspect_command(config, ["docker", "context", "inspect"]))
    endpoint = contexts[0]["Endpoints"]["docker"]["Host"]
    if not os.environ.get("DOCKER_CONTEXT"):
        endpoint = os.environ.get("DOCKER_HOST") or endpoint
    if not endpoint.startswith("unix://"):
        raise ConfigError("Research environment inspection requires a local Docker socket.")
    revision = inspect_command(config, ["git", "-C", str(config["root"] / "targets/med-agent-hub"),
                                        "rev-parse", "HEAD"]).strip()
    native_config = {**config, "values": {**config["values"], "HUB_BUILD_REVISION": revision}}
    compose = ["docker", "compose", "--project-name", config["project"], "--env-file", os.devnull,
               "-f", str(within(config["root"], config["preset"]["files"]["compose"]))]
    native = json.loads(inspect_command(native_config, [*compose, "config", "--format", "json"]))
    rows = compose_rows(inspect_command(native_config, [*compose, "ps", "--all", "--format", "json"]))
    result = public_config(config)
    result.update(readiness="not_verified", services=[
        {key.lower(): row.get(key) for key in ("Service", "Name", "State", "Health", "Image")}
        for row in rows], volumes={key: value.get("name") for key, value in native.get("volumes", {}).items()},
        limitations=["Authentication, data, provider responses and browser behavior are not checked."])
    names = {key: service.get("container_name") for key, service in native["services"].items()}
    result["container_names"] = names
    result["bind_mounts"] = {
        key: [{"source": mount["source"], "target": mount["target"],
               "read_only": mount.get("read_only", False)}
              for mount in service.get("volumes", []) if mount["type"] == "bind"]
        for key, service in native["services"].items()
    }
    if any(value and not value.startswith(config["project"] + "-") for value in names.values()):
        result["limitations"].append("Native Compose still uses fixed container names; instance lifecycle is unavailable.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("config", "status"))
    parser.add_argument("--environment", default=os.environ.get("ENV", ""))
    parser.add_argument("--set", action="append", default=[], metavar="KEY=VALUE")
    args = parser.parse_args()
    try:
        overrides = {}
        for item in args.set:
            key, separator, value = item.partition("=")
            if not separator or key in overrides:
                raise ConfigError("Command overrides require unique KEY=VALUE options.")
            overrides[key] = value
        config = resolve(ROOT, args.environment, overrides)
        print(json.dumps(status(config) if args.action == "status" else public_config(config), indent=2))
        return 0
    except ConfigError as error:
        print(f"Environment inspection failed: {error}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError, KeyError, TypeError):
        # Do not print raw parser/native error messages that can contain secrets.
        print("Environment inspection failed. Check the documented selection, files, permissions and tool availability.",
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

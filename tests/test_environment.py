import json
import os
import secrets
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import environment

ROOT = Path(__file__).resolve().parents[1]


class EnvironmentFixture(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.credentials = {key: secrets.token_urlsafe(24) for key in ("default", "instance", "api")}
        self.preset = json.loads(
            (ROOT / "environments/chartsearch-research/preset.json").read_text()
        )
        for path in self.preset["files"].values():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("placeholder\n")
        (self.root / self.preset["files"]["defaults"]).write_text(
            "HARNESS_PROXY_HTTP_PORT=8088\nMED_AGENT_HUB_PORT=18081\n"
            f"CHARTSEARCH_ADMIN_PASSWORD={self.credentials['default']}\n"
        )
        self.preset_path = self.root / "environments/chartsearch-research/preset.json"
        self.preset_path.parent.mkdir(parents=True, exist_ok=True)
        self.save_preset()
        self.settings("alpha", "PRESET=chartsearch-research\n")

    def save_preset(self):
        self.preset_path.write_text(json.dumps(self.preset))

    def settings(self, name, text):
        path = self.root / ".local/environments" / name / "settings.env"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        path.chmod(0o600)
        return path

    def resolve(self, name="alpha", overrides=None):
        return environment.resolve(self.root, name, overrides or {})


class ConfigurationTests(EnvironmentFixture):
    def test_defaults_instance_explicit_precedence_without_ambient_overrides(self):
        self.settings("alpha", "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=8100\n")
        with patch.dict(os.environ, {"HARNESS_PROXY_HTTP_PORT": "9999"}):
            resolved = self.resolve(overrides={"HARNESS_PROXY_HTTP_PORT": "8101"})
        self.assertEqual(resolved["values"]["HARNESS_PROXY_HTTP_PORT"], "8101")
        self.assertEqual(resolved["values"]["MED_AGENT_HUB_PORT"], "18081")
        self.assertEqual(resolved["origins"]["HARNESS_PROXY_HTTP_PORT"], "command")
        self.assertEqual(resolved["origins"]["MED_AGENT_HUB_PORT"], "defaults")

    def test_instances_select_different_projects_and_private_artifact_paths(self):
        self.settings("beta", "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=8102\n")
        alpha, beta = map(environment.public_config, (self.resolve(), self.resolve("beta")))
        self.assertEqual(alpha["project"], "openclinai-alpha")
        self.assertEqual(beta["project"], "openclinai-beta")
        self.assertNotEqual(alpha["artifacts"], beta["artifacts"])
        self.assertNotEqual(alpha["urls"], beta["urls"])
        self.assertEqual(beta["data_action"], "preserve")

    def test_credentials_are_never_part_of_public_configuration(self):
        self.settings("alpha", "PRESET=chartsearch-research\n"
                      f"CHARTSEARCH_ADMIN_PASSWORD='{self.credentials['instance']}'\n"
                      f"CHARTSEARCH_HUB_API_KEY={self.credentials['api']}\n")
        result = environment.public_config(self.resolve())
        text = json.dumps(result)
        for secret in self.credentials.values():
            self.assertNotIn(secret, text)
        self.assertEqual(result["settings"]["CHARTSEARCH_ADMIN_PASSWORD"]["origin"], "instance")

    def test_shell_content_is_data_not_executed(self):
        sentinel = self.root / "should-not-exist"
        payload = f"$(touch {sentinel})"
        self.settings("alpha", f"PRESET=chartsearch-research\n"
                      f"CHARTSEARCH_ADMIN_PASSWORD='{payload}'\n")
        resolved = self.resolve()
        self.assertEqual(resolved["values"]["CHARTSEARCH_ADMIN_PASSWORD"],
                         payload)
        self.assertFalse(sentinel.exists())

    def test_unsafe_names_unknown_inputs_invalid_ports_and_missing_refs_reject_without_side_effects(self):
        for name in ("../outside", "alpha;touch nope", "", "UPPER", "/tmp/foo"):
            with self.subTest(name=name), self.assertRaises(environment.ConfigError):
                self.resolve(name)
        for text in ("PRESET=unknown\n", "PRESET=../outside\n", "PRESET=chartsearch-research\nBOGUS=x\n",
                     "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=0\n",
                     "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=65536\n",
                     "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=$(touch nope)\n",
                     "PRESET=chartsearch-research\nPRESET=chartsearch-research\n",
                     "export PRESET=chartsearch-research\n", "PRESET='unterminated\n"):
            self.settings("alpha", text)
            with self.subTest(text=text), patch.object(subprocess, "run") as run:
                with self.assertRaises(environment.ConfigError):
                    self.resolve()
                run.assert_not_called()
        self.settings("alpha", "PRESET=chartsearch-research\n")
        (self.root / self.preset["files"]["compose"]).unlink()
        with self.assertRaises(environment.ConfigError):
            self.resolve()
        self.assertFalse((self.root / "artifacts").exists())

    def test_private_settings_require_private_permissions_and_no_symlink(self):
        path = self.settings("alpha", "PRESET=chartsearch-research\n")
        path.chmod(0o644)
        with self.assertRaisesRegex(environment.ConfigError, "permissions"):
            self.resolve()
        path.unlink()
        path.symlink_to(self.root / self.preset["files"]["defaults"])
        with self.assertRaises(environment.ConfigError):
            self.resolve()

    def test_preset_path_escape_and_unknown_fields_reject(self):
        self.preset["files"]["compose"] = "../outside.yml"
        self.save_preset()
        with self.assertRaises(environment.ConfigError):
            self.resolve()
        self.preset["files"]["compose"] = "compose/openmrs-2.8-refapp.yml"
        self.preset["run"] = "touch nope"
        self.save_preset()
        with self.assertRaises(environment.ConfigError):
            self.resolve()

    def test_credentials_cannot_be_passed_on_the_command_line(self):
        for value in ("", self.credentials["instance"]):
            with self.subTest(empty=not value), self.assertRaises(environment.ConfigError):
                self.resolve(overrides={"CHARTSEARCH_ADMIN_PASSWORD": value})

    def test_invalid_baseline_and_duplicate_json_fields_reject(self):
        for key, value in (("bytes", True), ("filename", ".."), ("location", None),
                           ("sha256", "bad"), ("location", "https://user:secret@example.org/data")):
            saved = self.preset["baseline"][key]
            self.preset["baseline"][key] = value
            self.save_preset()
            with self.subTest(key=key, value=value), self.assertRaises(environment.ConfigError):
                self.resolve()
            self.preset["baseline"][key] = saved
        self.preset_path.write_text('{"id":"chartsearch-research","id":"duplicate"}')
        with self.assertRaises(environment.ConfigError):
            self.resolve()

    def test_main_reports_useful_errors_without_echoing_secret_inputs(self):
        self.settings("alpha", "PRESET=chartsearch-research\nHARNESS_PROXY_HTTP_PORT=secret-sentinel\n")
        import io
        errors = io.StringIO()
        with patch.object(environment, "ROOT", self.root), patch(
                "sys.argv", ["environment.py", "config", "--environment", "alpha"]), \
                patch("sys.stderr", errors):
            self.assertEqual(environment.main(), 1)
        self.assertIn("HARNESS_PROXY_HTTP_PORT", errors.getvalue())
        self.assertNotIn("secret-sentinel", errors.getvalue())


class StatusTests(EnvironmentFixture):
    def test_native_commands_receive_owned_names_paths_and_user_without_ambient_overrides(self):
        config = self.resolve()
        with patch.dict(os.environ, {"STACK_CONTAINER_PREFIX": "other",
                                     "STACK_ARTIFACTS_DIR": "/another-checkout"}), patch.object(
                subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 0, stdout="{}", stderr="")) as run:
            environment.inspect_command(config, ["docker", "compose", "version"])
        values = run.call_args.kwargs["env"]
        self.assertEqual(values["STACK_CONTAINER_PREFIX"], "openclinai-alpha")
        self.assertEqual(values["STACK_ARTIFACTS_DIR"], str(config["artifacts"]))
        self.assertEqual(values["MED_AGENT_HUB_UID"], str(os.getuid()))
        self.assertEqual(values["MED_AGENT_HUB_GID"], str(os.getgid()))

    def test_storage_alias_to_another_instance_is_refused(self):
        target = self.root / "artifacts/environments/beta"
        target.mkdir(parents=True)
        (target.parent / "alpha").symlink_to(target, target_is_directory=True)
        with self.assertRaisesRegex(environment.ConfigError, "artifact"):
            self.resolve()

    def test_status_is_read_only_redacted_and_does_not_claim_readiness(self):
        config = self.resolve()
        native = {"services": {"db": {"container_name": "harness-openmrs-db"}},
                  "volumes": {"db-data": {"name": "openclinai-alpha_db-data"}}}
        ps = {"Service": "db", "Name": "harness-openmrs-db", "State": "running",
              "Health": "healthy", "Image": "mariadb:10.11.7"}
        calls = []

        def run(args, **kwargs):
            calls.append(args)
            self.assertFalse(kwargs.get("shell", False))
            if args[0] == "git":
                output = "a" * 40
            elif args[1:3] == ["context", "inspect"]:
                output = json.dumps([{"Endpoints": {"docker": {"Host": "unix:///socket"}}}])
            elif args[-3:] == ["config", "--format", "json"]:
                output = json.dumps(native)
            elif args[-4:] == ["ps", "--all", "--format", "json"]:
                output = json.dumps(ps) + "\n"
            else:
                self.fail(f"unexpected command: {args}")
            return subprocess.CompletedProcess(args, 0, stdout=output, stderr="")

        with patch.object(subprocess, "run", side_effect=run):
            result = environment.status(config)
        self.assertEqual(result["services"][0]["health"], "healthy")
        self.assertEqual(result["readiness"], "not_verified")
        self.assertIn("fixed container names", " ".join(result["limitations"]))
        self.assertNotIn(self.credentials["default"], json.dumps(result))
        self.assertFalse(any("up" in call or "down" in call or "exec" in call for call in calls))
        self.assertFalse((self.root / "artifacts").exists())

    def test_docker_error_is_not_an_empty_or_ready_installation(self):
        with patch.object(subprocess, "run", return_value=subprocess.CompletedProcess(
                [], 1, stdout="", stderr="error with secret-sentinel")):
            with self.assertRaises(environment.ConfigError) as error:
                environment.status(self.resolve())
        self.assertNotIn("secret-sentinel", str(error.exception))

    def test_ndjson_and_array_compose_output(self):
        item = {"Service": "db", "State": "running"}
        self.assertEqual(environment.compose_rows(json.dumps([item])), [item])
        self.assertEqual(environment.compose_rows(json.dumps(item) + "\n"), [item])
        self.assertEqual(environment.compose_rows(""), [])

    def test_remote_docker_context_is_refused_without_compose_calls(self):
        context = json.dumps([{"Endpoints": {"docker": {"Host": "tcp://remote:2375"}}}])
        with patch.dict(os.environ, {"DOCKER_CONTEXT": "remote"}), patch.object(
                subprocess, "run", return_value=subprocess.CompletedProcess(
                    [], 0, stdout=context, stderr="")) as run:
            with self.assertRaisesRegex(environment.ConfigError, "local Docker"):
                environment.status(self.resolve())
        self.assertEqual(run.call_count, 1)


class MakeInterfaceTests(unittest.TestCase):
    def test_existing_default_target_is_preserved(self):
        result = subprocess.run(["make", "--no-print-directory", "-qp"], cwd=ROOT,
                                text=True, capture_output=True, check=False)
        self.assertIn(result.returncode, (0, 1))
        default = next((line for line in result.stdout.splitlines()
                        if line.startswith(".DEFAULT_GOAL := ")), None)
        self.assertEqual(default, ".DEFAULT_GOAL := up")


if __name__ == "__main__":
    unittest.main()

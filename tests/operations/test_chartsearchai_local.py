from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_router_launcher_forwards_configured_small_model_limit(tmp_path):
    example = _read(".env.chartsearch.example")
    configured = next(
        line.split("=", 1)[1]
        for line in example.splitlines()
        if line.startswith("LLAMA_ROUTER_MODELS_MAX=")
    )
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    capture = tmp_path / "llama-server-args.txt"
    llama_server = fake_bin / "llama-server"
    llama_server.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$LLAMA_ARGS_CAPTURE"\n',
        encoding="utf-8",
    )
    llama_server.chmod(0o755)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "LLAMA_ARGS_CAPTURE": str(capture),
            "LLAMA_MODEL_DIR": str(model_dir),
            "LLAMA_ROUTER_MODELS_MAX": configured,
            "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
        }
    )

    subprocess.run(
        ["bash", str(ROOT / "scripts/llama-router-up.sh")],
        cwd=ROOT,
        env=env,
        check=True,
    )

    args = capture.read_text(encoding="utf-8").splitlines()
    assert configured == "2"
    assert args[args.index("--models-max") + 1] == configured
    assert args[args.index("--port") + 1] == "8077"
    assert args[args.index("--models-preset") + 1] == str(
        ROOT / "scripts/llama-router.ini"
    )


def test_router_launcher_does_not_mutate_the_real_runtime_symlink(tmp_path):
    """A prior version of this script hardcoded its runtime symlink to
    `${ROOT}/artifacts/llama-router/models` with no override, so any test that ran the
    real script against the real ROOT (as the test above does, to observe the argv it
    forwards) repointed the LIVE repo's runtime symlink at the test's disposable
    tmp_path. Once pytest cleaned that tmp_path up, every subsequent JIT model load
    through the real router failed with "failed to load" for any model not already
    resident in a running llama-server. LLAMA_ROUTER_RUNTIME_DIR must isolate the
    runtime symlink from the real repo without needing a full ROOT copy."""
    real_runtime_models = ROOT / "artifacts/llama-router/models"

    def runtime_state() -> tuple[str, str | None]:
        if real_runtime_models.is_symlink():
            return ("symlink", os.readlink(real_runtime_models))
        if real_runtime_models.exists():
            return ("path", str(real_runtime_models.stat().st_mode))
        return ("missing", None)

    before = runtime_state()

    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    llama_server = fake_bin / "llama-server"
    llama_server.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    llama_server.chmod(0o755)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "LLAMA_MODEL_DIR": str(model_dir),
            "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
        }
    )

    subprocess.run(
        ["bash", str(ROOT / "scripts/llama-router-up.sh")],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert runtime_state() == before, (
        "scripts/llama-router-up.sh mutated the real runtime symlink instead of "
        "honoring LLAMA_ROUTER_RUNTIME_DIR"
    )
    assert (runtime_dir / "models").resolve() == model_dir.resolve()


@pytest.mark.parametrize("launchctl_print_fails", [False, True])
def test_local_router_daemon_uses_launchd_on_macos(
    tmp_path, launchctl_print_fails
):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    ready = tmp_path / "router-ready"
    launchctl_args = tmp_path / "launchctl-args.txt"
    for name, body in {
        "llama-server": "#!/bin/sh\nexit 0\n",
        "uname": "#!/bin/sh\nprintf 'Darwin\\n'\n",
        "curl": (
            "#!/bin/sh\n"
            '[ -f "$ROUTER_READY" ]\n'
        ),
        "launchctl": (
            "#!/bin/sh\n"
            'if [ "$1" = submit ]; then\n'
            '  printf "%s\\n" "$@" > "$LAUNCHCTL_ARGS"\n'
            '  touch "$ROUTER_READY"\n'
            'elif [ "$1" = print ]; then\n'
            '  [ "$LAUNCHCTL_PRINT_FAIL" = 1 ] && exit 1\n'
            "  printf 'pid = 123\\n'\n"
            "fi\n"
        ),
    }.items():
        executable = fake_bin / name
        executable.write_text(body, encoding="utf-8")
        executable.chmod(0o755)

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    home = tmp_path / "home"
    home.mkdir()
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(home),
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "LAUNCHCTL_ARGS": str(launchctl_args),
            "LAUNCHCTL_PRINT_FAIL": "1" if launchctl_print_fails else "0",
            "LLAMA_MODEL_DIR": str(model_dir),
            "LLAMA_ROUTER_MODELS_MAX": "2",
            "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
            "ROUTER_READY": str(ready),
        }
    )

    subprocess.run(
        ["bash", str(ROOT / "scripts/llama-router-up.sh"), "--daemon"],
        cwd=ROOT,
        env=env,
        check=True,
    )

    args = launchctl_args.read_text(encoding="utf-8").splitlines()
    assert args[:3] == ["submit", "-l", "org.openclinai.llama-router"]
    assert ["-o", str(runtime_dir / "router.stdout.log")] == args[3:5]
    assert ["-e", str(runtime_dir / "router.log")] == args[5:7]
    assert f"LLAMA_MODEL_DIR={model_dir}" in args
    assert f"LLAMA_ROUTER_RUNTIME_DIR={runtime_dir}" in args
    assert "LLAMA_ROUTER_MODELS_MAX=2" in args
    assert str(ROOT / "scripts/llama-router-up.sh") in args
    if launchctl_print_fails:
        assert not (runtime_dir / "router.pid").exists()
    else:
        assert (runtime_dir / "router.pid").read_text(encoding="utf-8") == "123\n"


def test_local_router_daemon_removes_launchd_job_when_readiness_times_out(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    launchctl_calls = tmp_path / "launchctl-calls.txt"
    for name, body in {
        "llama-server": "#!/bin/sh\nexit 0\n",
        "uname": "#!/bin/sh\nprintf 'Darwin\\n'\n",
        "curl": "#!/bin/sh\nexit 1\n",
        "launchctl": (
            "#!/bin/sh\n"
            'printf "%s\\n" "$*" >> "$LAUNCHCTL_CALLS"\n'
        ),
    }.items():
        executable = fake_bin / name
        executable.write_text(body, encoding="utf-8")
        executable.chmod(0o755)

    model_dir = tmp_path / "models"
    model_dir.mkdir()
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env.update(
        {
            "HOME": str(tmp_path / "home"),
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "LAUNCHCTL_CALLS": str(launchctl_calls),
            "LLAMA_MODEL_DIR": str(model_dir),
            "LLAMA_ROUTER_READY_TIMEOUT_SECONDS": "1",
            "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
        }
    )

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/llama-router-up.sh"), "--daemon"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "was not ready after 1s" in result.stderr
    calls = launchctl_calls.read_text(encoding="utf-8").splitlines()
    assert calls[0] == "remove org.openclinai.llama-router"
    assert calls[1].startswith("submit -l org.openclinai.llama-router ")
    assert calls[-1] == "remove org.openclinai.llama-router"
    assert not (runtime_dir / "router.pid").exists()


def test_local_router_down_removes_launchd_job_and_pid_file(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    launchctl_calls = tmp_path / "launchctl-calls.txt"
    for name, body in {
        "uname": "#!/bin/sh\nprintf 'Darwin\\n'\n",
        "launchctl": '#!/bin/sh\nprintf "%s\\n" "$*" > "$LAUNCHCTL_CALLS"\n',
    }.items():
        executable = fake_bin / name
        executable.write_text(body, encoding="utf-8")
        executable.chmod(0o755)

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    (runtime_dir / "router.pid").write_text("123\n", encoding="utf-8")
    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
            "LAUNCHCTL_CALLS": str(launchctl_calls),
            "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
        }
    )

    subprocess.run(
        ["bash", str(ROOT / "scripts/llama-router-down.sh")],
        cwd=ROOT,
        env=env,
        check=True,
    )

    assert launchctl_calls.read_text(encoding="utf-8") == (
        "remove org.openclinai.llama-router\n"
    )
    assert not (runtime_dir / "router.pid").exists()


def test_local_router_down_does_not_kill_unrelated_non_macos_pid(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    uname = fake_bin / "uname"
    uname.write_text("#!/bin/sh\nprintf 'Linux\\n'\n", encoding="utf-8")
    uname.chmod(0o755)

    runtime_dir = tmp_path / "runtime"
    runtime_dir.mkdir()
    unrelated = subprocess.Popen(["sleep", "30"])
    try:
        (runtime_dir / "router.pid").write_text(
            f"{unrelated.pid}\n", encoding="utf-8"
        )
        env = os.environ.copy()
        env.update(
            {
                "PATH": f"{fake_bin}{os.pathsep}{env['PATH']}",
                "LLAMA_ROUTER_RUNTIME_DIR": str(runtime_dir),
            }
        )

        result = subprocess.run(
            ["bash", str(ROOT / "scripts/llama-router-down.sh")],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )

        assert unrelated.poll() is None
        assert f"refusing to stop unverified PID {unrelated.pid}" in result.stderr
        assert not (runtime_dir / "router.pid").exists()
    finally:
        unrelated.terminate()
        unrelated.wait(timeout=5)


def test_check_reuses_existing_router_without_selecting_a_profile(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for name in ("curl", "docker", "python3", "git"):
        command = fake_bin / name
        command.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
        command.chmod(0o755)
    env = {
        **os.environ,
        "PATH": f"{fake_bin}:/usr/bin:/bin",
        "LLAMA_MODEL_DIR": "/definitely/not/a/model/directory",
        "CHARTSEARCH_LOCAL_BUILD": "never",
    }

    result = subprocess.run(
        ["bash", str(ROOT / "scripts/chartsearchai-local.sh"), "--check"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "router: existing" in result.stdout
    assert "selected profile" not in result.stdout


def test_local_shell_entrypoint_is_syntactically_valid():
    script = ROOT / "scripts/chartsearchai-local.sh"

    result = subprocess.run(
        ["bash", "-n", str(script)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def _hub_start(tmp_path, uid="1000", **overrides):
    """Run the real `make med-agent-hub-up` recipe in a scratch copy with Docker stubbed."""
    for name in ("Makefile", ".env.chartsearch.example"):
        (tmp_path / name).write_text(_read(name), encoding="utf-8")
    levels = tmp_path / "targets/med-agent-hub/server/levels.yaml"
    levels.parent.mkdir(parents=True)
    levels.touch()
    stubs = tmp_path / "bin"
    stubs.mkdir()
    capture = tmp_path / "compose-env.txt"
    for name, body in {
        "id": f'echo {uid}',
        "git": "echo 0000000000000000000000000000000000000000",
        "curl": "exit 0",
        "docker": (
            'case "$1 $*" in\n'
            '  "compose "*" up "*) printf "%s\\0" "$QUERYSTORE_BASE_URL" "$QUERYSTORE_USERNAME" "$QUERYSTORE_PASSWORD" > "$CAPTURE" ;;\n'
            '  "inspect "*) echo healthy ;;\n'
            "esac"
        ),
    }.items():
        stub = stubs / name
        stub.write_text(f"#!/bin/sh\n{body}\n", encoding="utf-8")
        stub.chmod(0o755)
    env = {
        key: value for key, value in os.environ.items()
        if not key.startswith(("QUERYSTORE_", "CHARTSEARCH_ADMIN_"))
    }
    env.update(overrides, PATH=f"{stubs}:/usr/bin:/bin", CAPTURE=str(capture))
    result = subprocess.run(
        ["make", "--no-print-directory", "med-agent-hub-up"],
        cwd=tmp_path, env=env, capture_output=True, text=True, check=False,
    )
    started = capture.read_text().split("\0")[:-1] if capture.exists() else None
    return result, started


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({}, ["http://backend:8080/openmrs", "admin", "Admin123"]),
        (dict.fromkeys(["QUERYSTORE_BASE_URL", "QUERYSTORE_USERNAME", "QUERYSTORE_PASSWORD"], ""), ["", "", ""]),
        (
            {
                "QUERYSTORE_BASE_URL": "http://alternate/openmrs",
                "QUERYSTORE_USERNAME": "test-reader",
                "QUERYSTORE_PASSWORD": "synthetic-test-password",
            },
            ["http://alternate/openmrs", "test-reader", "synthetic-test-password"],
        ),
    ],
    ids=["unset-uses-demo", "empty-disables-source", "configured-is-preserved"],
)
def test_hub_start_resolves_querystore_source_settings(tmp_path, overrides, expected):
    result, started = _hub_start(tmp_path, **overrides)
    assert result.returncode == 0, result.stdout + result.stderr
    assert started == expected


def test_hub_start_refuses_to_run_as_root(tmp_path):
    result, started = _hub_start(tmp_path, uid="0")
    assert result.returncode != 0
    assert started is None

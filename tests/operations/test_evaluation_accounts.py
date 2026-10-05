import importlib.util
import json
import sys
from pathlib import Path
from unittest.mock import Mock, call

import pytest


ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "evaluation_accounts", ROOT / "scripts/provision-evaluation-users.py"
)
provisioner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provisioner)


@pytest.mark.parametrize("extra_inheritance,extra_user_role", [
    (True, False), (False, True), (True, True), (False, False),
])
def test_existing_accounts_have_exact_roles_without_password_changes(
    monkeypatch, extra_inheritance, extra_user_role,
):
    config = json.loads((ROOT / "environments/chartsearch-research/accounts.json").read_text())
    accounts = {row["username"]: row for row in config["accounts"]}
    admin = Mock()

    def exact(resource, _field, value):
        if resource == "privilege":
            return {"uuid": value}
        if resource == "role":
            if value == config["access_role"]:
                return {
                    "uuid": "research-access",
                    "privileges": [{"uuid": name} for name in config["required_privileges"]],
                    "inheritedRoles": [{"uuid": "administrator"}] if extra_inheritance else [],
                }
            return {"uuid": value}
        role_ids = [accounts[value]["role"], "research-access"]
        if extra_user_role:
            role_ids.append("administrator")
        return {"uuid": value, "roles": [{"uuid": role} for role in role_ids]}

    admin.exact.side_effect = exact

    def client(_url, username, password):
        if username == "admin":
            return admin
        assert password == "existing-demo-password"
        reader = Mock()
        reader.request.return_value = {"authenticated": True, "user": {"uuid": username}}
        return reader

    monkeypatch.setattr(provisioner, "OpenMrsClient", client)
    monkeypatch.setenv("CHARTSEARCH_ADMIN_USER", "admin")
    monkeypatch.setenv("EVALUATION_PASSWORD", "existing-demo-password")
    monkeypatch.setattr(sys, "argv", ["provision-evaluation-users.py"])
    provisioner.main()

    expected = []
    if extra_inheritance:
        expected.append(call("POST", "role/research-access", {
            "privileges": config["required_privileges"], "inheritedRoles": [],
        }))
    if extra_user_role:
        expected.extend(call("POST", f"user/{row['username']}", {
            "roles": [row["role"], "research-access"],
        }) for row in config["accounts"])
    assert admin.request.call_args_list == expected

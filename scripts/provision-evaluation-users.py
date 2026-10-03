#!/usr/bin/env python3
"""Create the saved research accounts on the local synthetic-data instance."""

from __future__ import annotations

import argparse
import json
import os
import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OpenMrsClient = runpy.run_path(
    str(ROOT / "scripts/provision-querystore-service-account.py")
)["OpenMrsClient"]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--accounts", type=Path,
        default=ROOT / "environments/chartsearch-research/accounts.json",
    )
    args = parser.parse_args()
    base_url = os.environ.get(
        "CHARTSEARCH_BASE_URL",
        f"http://localhost:{os.environ.get('HARNESS_PROXY_HTTP_PORT', '8088')}/openmrs",
    )
    client = OpenMrsClient(
        base_url,
        os.environ.get("CHARTSEARCH_ADMIN_USER", "admin"),
        os.environ.get("CHARTSEARCH_ADMIN_PASSWORD", "Admin123"),
    )
    password = os.environ.get("EVALUATION_PASSWORD", "Admin123")
    config = json.loads(args.accounts.read_text())
    privileges = []
    for name in config["required_privileges"]:
        privilege = client.exact("privilege", "name", name)
        if privilege is None:
            raise RuntimeError(f"Required OpenMRS privilege is missing: {name}")
        privileges.append(privilege["uuid"])

    access = client.exact("role", "name", config["access_role"])
    if access is None:
        access = client.request("POST", "role", {
            "name": config["access_role"],
            "description": "ChartSearchAI access for synthetic-data research.",
            "privileges": privileges,
            "inheritedRoles": [],
        })
    elif {item["uuid"] for item in access.get("privileges", [])} != set(privileges):
        client.request("POST", f"role/{access['uuid']}", {"privileges": privileges})

    for account in config["accounts"]:
        role = client.exact("role", "name", account["role"])
        if role is None:
            if account.get("require_existing_role"):
                raise RuntimeError(f"Required OpenMRS role is missing: {account['role']}")
            role = client.request("POST", "role", {
                "name": account["role"],
                "description": "Occupational label for synthetic-data research.",
                "privileges": [],
                "inheritedRoles": [],
            })
        username = account["username"]
        user = client.exact("user", "username", username)
        if user is None:
            user = client.request("POST", "user", {
                "username": username,
                "systemId": username,
                "password": password,
                "roles": [role["uuid"], access["uuid"]],
                "person": {
                    "names": [{"givenName": "Evaluation", "familyName": username[5:]}],
                    "gender": "U",
                },
            })
        session = OpenMrsClient(base_url, username, password).request("GET", "session")
        if not session.get("authenticated") or session.get("user", {}).get("uuid") != user["uuid"]:
            raise RuntimeError(f"Login failed for {username}; no existing password was changed.")
        print(f"{username}: login works ({account['role']})")


if __name__ == "__main__":
    main()

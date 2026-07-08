from __future__ import annotations

import importlib.util
import os
from pathlib import Path


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    mod_path = repo_root / "deploy" / "secrets" / "check_secrets.py"
    spec = importlib.util.spec_from_file_location("check_secrets", mod_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validate_ok_without_rms(tmp_path: Path) -> None:
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secrets.chmod(0o700)
    for name in (
        "github_token",
        "race_mcp_api_key",
        "neo4j_mcp_password",
        "influx_read_token",
    ):
        p = secrets / name
        p.write_text("x", encoding="utf-8")
        p.chmod(0o600)

    errors = mod.validate(secrets, require_rms=False)
    assert errors == []


def test_validate_requires_rms_profile(tmp_path: Path) -> None:
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secrets.chmod(0o700)
    for name in (
        "github_token",
        "race_mcp_api_key",
        "neo4j_mcp_password",
        "influx_read_token",
    ):
        p = secrets / name
        p.write_text("x", encoding="utf-8")
        p.chmod(0o600)

    errors = mod.validate(secrets, require_rms=True)
    assert any("rms_client.ovpn" in err for err in errors)


def test_validate_rejects_open_permissions(tmp_path: Path) -> None:
    if os.name == "nt":
        return
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    secrets.chmod(0o755)
    required = {
        "github_token": 0o644,
        "race_mcp_api_key": 0o644,
        "neo4j_mcp_password": 0o600,
        "influx_read_token": 0o600,
    }
    for name, mode in required.items():
        p = secrets / name
        p.write_text("x", encoding="utf-8")
        p.chmod(mode)

    errors = mod.validate(secrets, require_rms=False)
    assert any("directory permissions too open" in err for err in errors)
    assert any("race_mcp_api_key" in err for err in errors)

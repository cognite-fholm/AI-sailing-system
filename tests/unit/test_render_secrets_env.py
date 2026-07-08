from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    mod_path = repo_root / "deploy" / "secrets" / "render_secrets_env.py"
    spec = importlib.util.spec_from_file_location("render_secrets_env", mod_path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_render_env_file_writes_expected_lines(tmp_path: Path) -> None:
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "race_mcp_api_key").write_text("mcp-key", encoding="utf-8")
    (secrets / "neo4j_mcp_password").write_text("neo-pass", encoding="utf-8")
    (secrets / "influx_read_token").write_text("influx-token", encoding="utf-8")

    out = tmp_path / "deploy" / "env" / "harbor.secrets.env"
    mod.render_env_file(secrets, out, overwrite=False)

    content = out.read_text(encoding="utf-8")
    assert "RACE_MCP_API_KEY=mcp-key" in content
    assert "NEO4J_MCP_PASSWORD=neo-pass" in content
    assert "INFLUX_READ_TOKEN=influx-token" in content


def test_render_env_file_requires_missing_secret(tmp_path: Path) -> None:
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "race_mcp_api_key").write_text("mcp-key", encoding="utf-8")
    (secrets / "neo4j_mcp_password").write_text("neo-pass", encoding="utf-8")
    out = tmp_path / "harbor.secrets.env"

    with pytest.raises(FileNotFoundError):
        mod.render_env_file(secrets, out, overwrite=False)


def test_render_env_file_refuses_overwrite_without_flag(tmp_path: Path) -> None:
    mod = _load_module()
    secrets = tmp_path / "secrets"
    secrets.mkdir()
    (secrets / "race_mcp_api_key").write_text("mcp-key", encoding="utf-8")
    (secrets / "neo4j_mcp_password").write_text("neo-pass", encoding="utf-8")
    (secrets / "influx_read_token").write_text("influx-token", encoding="utf-8")
    out = tmp_path / "harbor.secrets.env"
    out.write_text("existing", encoding="utf-8")

    with pytest.raises(FileExistsError):
        mod.render_env_file(secrets, out, overwrite=False)

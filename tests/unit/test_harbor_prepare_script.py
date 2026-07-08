from __future__ import annotations

from pathlib import Path


def test_harbor_prepare_script_contains_required_steps() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    script = repo_root / "scripts" / "harbor-prepare.sh"
    text = script.read_text(encoding="utf-8")

    assert "render_secrets_env.py" in text
    assert "check_secrets.py" in text
    assert "VPN_PROVIDER" in text

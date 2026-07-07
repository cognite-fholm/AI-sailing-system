"""Load optional runtime-policy.yaml from active race planning folder."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_runtime_policy(data_repo_path: Path, active_race_path: str) -> dict[str, Any]:
    policy_file = data_repo_path / active_race_path / "planning" / "runtime-policy.yaml"
    if not policy_file.is_file():
        return {}
    doc = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return {}
    return doc.get("spec", doc)


def policy_into_state(spec: dict[str, Any]) -> dict[str, Any]:
    """Flatten runtime-policy spec into lifecycle state keys for peer services."""
    if not spec:
        return {}

    sync = spec.get("sync", {})
    live = spec.get("live_sync", {})
    mcp = spec.get("mcp", {})
    watchtower = spec.get("watchtower", {})

    out: dict[str, Any] = {}
    if "poll_interval_minutes" in sync:
        out["sync_poll_minutes"] = int(sync["poll_interval_minutes"])
    if "auto_import_on_change" in sync:
        out["sync_auto_import"] = bool(sync["auto_import_on_change"])
    if "interval_minutes" in live:
        out["live_sync_interval_minutes"] = int(live["interval_minutes"])
    if "online_required" in spec:
        out["online_required"] = bool(spec["online_required"])
    if "enabled" in mcp:
        out["mcp_enabled"] = bool(mcp["enabled"])
    if "enabled" in watchtower:
        out["watchtower_enabled"] = bool(watchtower["enabled"])
    return out

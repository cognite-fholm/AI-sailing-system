"""Load polar thresholds from runtime-policy.yaml (ADR-0027/0028)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class LiveSyncPolicy:
    polar_above_pct: float = 105.0
    polar_below_pct: float = 90.0


def load_live_sync_policy(data_repo: Path, race_folder: str) -> LiveSyncPolicy:
    policy_file = data_repo / race_folder / "planning" / "runtime-policy.yaml"
    if not policy_file.is_file():
        return LiveSyncPolicy()
    doc = yaml.safe_load(policy_file.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return LiveSyncPolicy()
    spec = doc.get("spec", doc)
    live = spec.get("live_sync", {})
    return LiveSyncPolicy(
        polar_above_pct=float(live.get("polar_above_pct", 105.0)),
        polar_below_pct=float(live.get("polar_below_pct", 90.0)),
    )

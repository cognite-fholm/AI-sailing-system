"""Load previous snapshot and compute deltas."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def read_previous_fleet_performance(live_dir: Path) -> list[dict[str, Any]]:
    current = live_dir / "current.yaml"
    if not current.is_file():
        return []
    doc = yaml.safe_load(current.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return []
    return list(doc.get("spec", {}).get("fleet_performance") or [])


def build_deltas(
    sequence: int,
    fleet_performance: list[dict[str, Any]],
    standings: list[dict[str, Any]],
    previous_fleet: list[dict[str, Any]],
) -> dict[str, Any]:
    own = next((f for f in fleet_performance if f.get("is_own")), None)
    own_prev = next((f for f in previous_fleet if f.get("is_own")), None)
    delta: dict[str, Any] = {"sequence_prev": sequence - 1 if sequence > 1 else None}
    if own and own_prev:
        rank_delta = None
        if own.get("rank") is not None and own_prev.get("rank") is not None:
            rank_delta = int(own["rank"]) - int(own_prev["rank"])
        delta["own_boat"] = {
            "sail_number": own.get("sail_number"),
            "rank_delta_since_last": own.get("rank_delta_since_last", rank_delta),
            "performance_pct_delta": _delta(own.get("performance_pct"), own_prev.get("performance_pct")),
            "vmg_pct_delta": _delta(own.get("vmg_pct"), own_prev.get("vmg_pct")),
        }
    rank_changes = [
        {
            "sail_number": f.get("sail_number"),
            "rank_delta_since_last": f.get("rank_delta_since_last"),
        }
        for f in fleet_performance
        if f.get("rank_delta_since_last") not in (None, 0)
    ]
    if rank_changes:
        delta["rank_changes"] = rank_changes
    if standings:
        delta["leader"] = standings[0].get("sail_number")
    return delta


def _delta(current: Any, previous: Any) -> float | None:
    if current is None or previous is None:
        return None
    return round(float(current) - float(previous), 2)

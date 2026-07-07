"""Aggregate fleet_polar_performance records into RaceLiveSnapshot fleet_performance[]."""

from __future__ import annotations

from statistics import mean
from typing import Any


def polar_outlier(
    performance_pct: float | None,
    *,
    above_threshold: float = 105.0,
    below_threshold: float = 90.0,
) -> str:
    if performance_pct is None:
        return "neutral"
    if performance_pct >= above_threshold:
        return "above"
    if performance_pct <= below_threshold:
        return "below"
    return "neutral"


def rollup_fleet_performance(
    records: list[dict[str, Any]],
    *,
    above_threshold: float = 105.0,
    below_threshold: float = 90.0,
) -> list[dict[str, Any]]:
    """Group Influx rows by sail_number; mean performance/vmg; last rank/position."""
    by_sail: dict[str, list[dict[str, Any]]] = {}
    for rec in records:
        sail = str(rec.get("sail_number") or rec.get("mmsi") or "")
        if not sail:
            continue
        by_sail.setdefault(sail, []).append(rec)

    out: list[dict[str, Any]] = []
    for sail_number, group in sorted(by_sail.items()):
        perf_vals = [float(r["performance_pct"]) for r in group if r.get("performance_pct") is not None]
        vmg_vals = [float(r["vmg_pct"]) for r in group if r.get("vmg_pct") is not None]
        last = group[-1]
        performance_pct = mean(perf_vals) if perf_vals else None
        entry: dict[str, Any] = {
            "sail_number": sail_number,
            "is_own": str(last.get("is_own", "false")).lower() == "true",
            "rank": _int_or_none(last.get("rank")),
            "leg_seq": _int_or_none(last.get("leg_seq")),
            "course_pct": _float_or_none(last.get("course_pct")),
            "lat": _float_or_none(last.get("lat")),
            "lon": _float_or_none(last.get("lon")),
            "tws": _mean_or_last(group, "tws"),
            "twa": _mean_or_last(group, "twa"),
            "sog": _float_or_none(last.get("sog")),
            "bsp": _float_or_none(last.get("bsp")),
            "vmg_actual": _float_or_none(last.get("vmg_actual")),
            "vmg_target": _float_or_none(last.get("vmg_target")),
            "vmg_pct": mean(vmg_vals) if vmg_vals else _float_or_none(last.get("vmg_pct")),
            "performance_pct": performance_pct,
            "polar_outlier": polar_outlier(
                performance_pct,
                above_threshold=above_threshold,
                below_threshold=below_threshold,
            ),
            "data_quality": last.get("data_quality", "ok"),
            "polar_source": last.get("polar_source", "slk"),
        }
        out.append(entry)
    return out


def apply_rank_deltas(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prev_rank = {
        str(p.get("sail_number")): p.get("rank")
        for p in previous
        if p.get("sail_number") and p.get("rank") is not None
    }
    updated: list[dict[str, Any]] = []
    for entry in current:
        row = dict(entry)
        sail = str(row.get("sail_number", ""))
        rank = row.get("rank")
        if sail in prev_rank and rank is not None:
            row["rank_delta_since_last"] = int(rank) - int(prev_rank[sail])
        else:
            row["rank_delta_since_last"] = 0
        updated.append(row)
    return updated


def _int_or_none(value: Any) -> int | None:
    if value is None or value == "":
        return None
    return int(float(value))


def _float_or_none(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _mean_or_last(group: list[dict[str, Any]], key: str) -> float | None:
    vals = [float(r[key]) for r in group if r.get(key) is not None]
    if vals:
        return mean(vals)
    return None

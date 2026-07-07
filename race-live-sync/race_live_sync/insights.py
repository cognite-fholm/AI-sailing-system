"""Precomputed tactical insights for RaceLiveSnapshot (ADR-0028)."""

from __future__ import annotations

from statistics import median
from typing import Any


def build_insights(
    fleet_performance: list[dict[str, Any]],
    standings: list[dict[str, Any]],
    *,
    previous_fleet: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    insights: list[dict[str, Any]] = []
    outperformers = [f for f in fleet_performance if f.get("polar_outlier") == "above"]
    underperformers = [f for f in fleet_performance if f.get("polar_outlier") == "below"]

    if outperformers:
        insights.append(
            {
                "type": "polar_outperformers",
                "vessels": [f.get("sail_number") for f in outperformers],
                "summary": _polar_summary(outperformers, "above"),
            }
        )
    if underperformers:
        insights.append(
            {
                "type": "polar_underperformers",
                "vessels": [f.get("sail_number") for f in underperformers],
                "summary": _polar_summary(underperformers, "below"),
            }
        )

    if fleet_performance:
        vmg_leader = max(fleet_performance, key=lambda f: f.get("vmg_actual") or 0.0)
        insights.append(
            {
                "type": "vmg_leaders_leg",
                "leg_seq": vmg_leader.get("leg_seq"),
                "leader": vmg_leader.get("sail_number"),
                "vmg_actual": vmg_leader.get("vmg_actual"),
            }
        )

    progress = _course_progress_leaders(fleet_performance, previous_fleet)
    if progress:
        insights.append(progress)

    wind = _wind_advantage(fleet_performance)
    if wind:
        insights.append(wind)

    if standings:
        leader = standings[0]
        insights.append(
            {
                "type": "corrected_time_if_now",
                "leader": leader.get("sail_number"),
                "corrected_seconds": leader.get("corrected_seconds"),
                "summary": f"Leader {leader.get('sail_number')} at {leader.get('corrected_seconds')}s corrected",
            }
        )

    return insights


def _polar_summary(boats: list[dict[str, Any]], direction: str) -> str:
    parts = []
    for b in boats[:5]:
        parts.append(
            f"{b.get('sail_number')} {b.get('performance_pct', 0):.0f}% "
            f"rank {b.get('rank')} TWS {b.get('tws', 0):.1f}"
        )
    suffix = "…" if len(boats) > 5 else ""
    label = "above" if direction == "above" else "below"
    return f"{len(boats)} boat(s) {label} polar: " + "; ".join(parts) + suffix


def _course_progress_leaders(
    current: list[dict[str, Any]],
    previous: list[dict[str, Any]] | None,
) -> dict[str, Any] | None:
    if not previous:
        return None
    prev_pct = {
        str(p.get("sail_number")): float(p.get("course_pct") or 0)
        for p in previous
        if p.get("sail_number")
    }
    deltas: list[tuple[str, float]] = []
    for row in current:
        sail = str(row.get("sail_number", ""))
        if sail not in prev_pct:
            continue
        cur = float(row.get("course_pct") or 0)
        deltas.append((sail, cur - prev_pct[sail]))
    if not deltas:
        return None
    leader_sail, gain = max(deltas, key=lambda x: x[1])
    return {
        "type": "course_progress_leaders",
        "leader": leader_sail,
        "course_pct_gain": round(gain, 4),
        "summary": f"{leader_sail} gained {gain:.1%} course progress since last tick",
    }


def _wind_advantage(fleet_performance: list[dict[str, Any]]) -> dict[str, Any] | None:
    with_tws = [f for f in fleet_performance if f.get("tws") is not None and f.get("lat")]
    if len(with_tws) < 3:
        return None
    med_lat = median(float(f["lat"]) for f in with_tws)
    east = [f for f in with_tws if float(f["lat"]) >= med_lat]
    west = [f for f in with_tws if float(f["lat"]) < med_lat]
    if not east or not west:
        return None
    east_tws = median(float(f["tws"]) for f in east)
    west_tws = median(float(f["tws"]) for f in west)
    if abs(east_tws - west_tws) < 0.3:
        return None
    better = "east" if east_tws > west_tws else "west"
    return {
        "type": "wind_advantage",
        "better_group": better,
        "east_tws_median": round(east_tws, 2),
        "west_tws_median": round(west_tws, 2),
        "summary": f"{better} group +{abs(east_tws - west_tws):.1f} kn TWS vs other half of fleet",
    }

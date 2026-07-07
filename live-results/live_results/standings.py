"""Corrected-time standings — pure functions and Neo4j row mapping."""

from __future__ import annotations

from typing import Any


def corrected_seconds(elapsed_seconds: float, handicap_factor: float) -> float:
    """SI §23 style: corrected = elapsed × handicap."""
    return elapsed_seconds * handicap_factor


def rank_by_corrected_time(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort by corrected_seconds ascending and assign rank + delta_to_leader."""
    if not rows:
        return []
    sorted_rows = sorted(rows, key=lambda r: float(r.get("corrected_seconds", 1e18)))
    leader = float(sorted_rows[0]["corrected_seconds"])
    out: list[dict[str, Any]] = []
    for idx, row in enumerate(sorted_rows, start=1):
        item = dict(row)
        item["rank"] = idx
        item["delta_to_leader_s"] = int(round(float(item["corrected_seconds"]) - leader))
        out.append(item)
    return out


def format_standing_row(
    *,
    sail_number: str,
    vessel_name: str = "",
    is_own: bool = False,
    elapsed_seconds: float,
    handicap_factor: float,
    course_pct: float | None = None,
    leg_seq: int | None = None,
    rank: int | None = None,
) -> dict[str, Any]:
    """Build one standings[] entry for RaceLiveSnapshot."""
    corrected = corrected_seconds(elapsed_seconds, handicap_factor)
    row: dict[str, Any] = {
        "sail_number": sail_number,
        "vessel_name": vessel_name,
        "is_own": is_own,
        "elapsed_seconds": int(round(elapsed_seconds)),
        "handicap_factor": handicap_factor,
        "corrected_seconds": int(round(corrected)),
    }
    if course_pct is not None:
        row["course_pct"] = round(course_pct, 4)
    if leg_seq is not None:
        row["leg_seq"] = leg_seq
    if rank is not None:
        row["rank"] = rank
    return row


def standings_from_neo4j_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Map Neo4j LiveStanding query rows to snapshot standings[]."""
    mapped: list[dict[str, Any]] = []
    for row in rows:
        corrected = row.get("corrected_time_s")
        elapsed = row.get("elapsed_time_s")
        if corrected is None and elapsed is None:
            continue
        mapped.append(
            {
                "sail_number": row.get("sail_number", ""),
                "vessel_name": row.get("name") or "",
                "is_own": bool(row.get("is_own", False)),
                "rank": row.get("rank"),
                "corrected_seconds": int(corrected) if corrected is not None else None,
                "elapsed_seconds": int(elapsed) if elapsed is not None else None,
                "handicap_factor": row.get("handicap_factor"),
                "course_pct": row.get("course_pct"),
                "leg_seq": row.get("leg") or row.get("leg_seq"),
            }
        )
    valid = [m for m in mapped if m.get("corrected_seconds") is not None]
    if not any(m.get("rank") for m in valid):
        return rank_by_corrected_time(
            [
                {
                    **m,
                    "corrected_seconds": float(m["corrected_seconds"]),
                }
                for m in valid
            ]
        )
    leader = min(float(m["corrected_seconds"]) for m in valid if m["corrected_seconds"])
    for m in valid:
        if m.get("delta_to_leader_s") is None and m.get("corrected_seconds") is not None:
            m["delta_to_leader_s"] = int(float(m["corrected_seconds"]) - leader)
    return sorted(valid, key=lambda m: m.get("rank") or 9999)

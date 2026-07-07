"""Parse race schedule from active race.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class RaceSchedule:
    regatta_id: str
    race_path: str
    timezone: str
    harbor_sync_at: datetime | None
    warning_signal_at: datetime | None
    start_at: datetime | None
    live_sync_enable_at: datetime | None
    estimated_finish_at: datetime | None
    auto_race_mode: bool
    auto_finalize: bool


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def load_schedule(data_repo_path: Path, active_race_path: str) -> RaceSchedule | None:
    race_file = data_repo_path / active_race_path / "race.yaml"
    if not race_file.is_file():
        return None
    doc = yaml.safe_load(race_file.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return None

    spec = doc.get("spec", {})
    sched = spec.get("schedule") or {}
    metadata = doc.get("metadata", {})
    regatta_id = metadata.get("regatta_id") or spec.get("id", "")

    start_at = _parse_dt(sched.get("start_at"))
    lead = int(sched.get("live_sync_lead_minutes", 30))
    live_sync_enable_at = _parse_dt(sched.get("live_sync_enable_at"))
    if live_sync_enable_at is None and start_at is not None:
        live_sync_enable_at = start_at - timedelta(minutes=lead)

    return RaceSchedule(
        regatta_id=str(regatta_id),
        race_path=active_race_path.rstrip("/"),
        timezone=str(spec.get("timezone", "UTC")),
        harbor_sync_at=_parse_dt(sched.get("harbor_sync_at")),
        warning_signal_at=_parse_dt(sched.get("warning_signal_at")),
        start_at=start_at,
        live_sync_enable_at=live_sync_enable_at,
        estimated_finish_at=_parse_dt(sched.get("estimated_finish_at")),
        auto_race_mode=bool(sched.get("auto_race_mode", True)),
        auto_finalize=bool(sched.get("auto_finalize", True)),
    )


def compute_phase(now: datetime, schedule: RaceSchedule, current: str) -> str:
    """Return lifecycle phase name."""
    if current == "archived":
        return "archived"

    t = now.astimezone(UTC)

    if schedule.estimated_finish_at and t >= schedule.estimated_finish_at:
        return "finalize_pending"
    if schedule.start_at and t >= schedule.start_at:
        return "racing"
    if schedule.live_sync_enable_at and t >= schedule.live_sync_enable_at:
        return "armed"
    if schedule.harbor_sync_at and t >= schedule.harbor_sync_at:
        return "harbor_ready"
    return "planned"


def lifecycle_flags(phase: str, schedule: RaceSchedule) -> dict[str, Any]:
    racing = phase in ("armed", "racing", "finalize_pending")
    return {
        "phase": phase,
        "regatta_id": schedule.regatta_id,
        "race_path": schedule.race_path,
        "race_mode": schedule.auto_race_mode and phase in ("racing", "finalize_pending"),
        "sync_auto_pull": phase in ("planned", "harbor_ready"),
        "race_live_sync_enabled": racing,
        "online_mode": True,
        "auto_finalize": schedule.auto_finalize and phase == "finalize_pending",
    }

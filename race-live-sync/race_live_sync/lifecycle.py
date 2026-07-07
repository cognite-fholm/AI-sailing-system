"""Race-live-sync lifecycle helpers."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

LIFECYCLE_STATE = Path(os.environ.get("RACE_LIFECYCLE_STATE", "/var/run/ai-sailing/race-lifecycle.json"))

_PHASE_TO_RACE: dict[str, str] = {
    "planned": "pre_start",
    "harbor_ready": "pre_start",
    "armed": "pre_start",
    "racing": "racing",
    "finalize_pending": "finished",
    "archived": "finished",
}


def read_lifecycle_state() -> dict[str, Any]:
    if not LIFECYCLE_STATE.is_file():
        return {}
    try:
        raw = json.loads(LIFECYCLE_STATE.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}


def lifecycle_allows_live_sync() -> bool:
    state = read_lifecycle_state()
    return bool(state.get("race_live_sync_enabled", True))


def lifecycle_race_phase() -> str:
    phase = str(read_lifecycle_state().get("phase", "racing"))
    return _PHASE_TO_RACE.get(phase, "racing")


def lifecycle_requests_finalize() -> bool:
    state = read_lifecycle_state()
    return bool(state.get("auto_finalize")) and str(state.get("phase")) == "finalize_pending"

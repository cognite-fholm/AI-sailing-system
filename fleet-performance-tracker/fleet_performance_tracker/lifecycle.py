"""Lifecycle gating shared with race-live-sync."""

from __future__ import annotations

import json
from pathlib import Path


def lifecycle_allows_fleet_write(state_path: Path) -> bool:
    if not state_path.is_file():
        return True
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        phase = str(state.get("phase", ""))
        return phase in ("armed", "racing", "finalize_pending")
    except (json.JSONDecodeError, OSError):
        return True

from datetime import datetime, timezone

from expedition_bridge.expedition.models import (
    ExpeditionLaylines,
    ExpeditionMeta,
    ExpeditionSnapshot,
    ExpeditionStartLine,
    ExpeditionTargets,
)
from expedition_bridge.mapping import snapshot_to_delta


def test_snapshot_to_delta_maps_start_line() -> None:
    snap = ExpeditionSnapshot(
        start=ExpeditionStartLine(
            dist_to_line_m=42.5,
            time_to_line_s=38.0,
            bias_boat_lengths=-1.2,
        ),
        meta=ExpeditionMeta(
            connected=True,
            api_version="mock",
            last_poll_at=datetime(2026, 7, 13, 7, 30, tzinfo=timezone.utc),
        ),
    )
    delta = snapshot_to_delta(snap, source_label="expedition-bridge")
    paths = {v.path: v.value for v in delta.updates[0].values}
    assert paths["race.expedition.start.distToLine"] == 42.5
    assert paths["race.expedition.start.timeToLine"] == 38.0
    assert paths["race.expedition.start.biasBoatLengths"] == -1.2
    assert paths["race.expedition.meta.connected"] is True
    assert delta.context == "vessels.self"


def test_snapshot_to_delta_includes_laylines() -> None:
    snap = ExpeditionSnapshot(
        laylines=ExpeditionLaylines(distance_m=500.0, time_s=120.0),
        meta=ExpeditionMeta(connected=True, last_poll_at=datetime.now(timezone.utc)),
    )
    delta = snapshot_to_delta(snap, source_label="test")
    paths = {v.path: v.value for v in delta.updates[0].values}
    assert paths["race.expedition.laylines.distance"] == 500.0
    assert paths["race.expedition.laylines.time"] == 120.0


def test_snapshot_to_delta_targets_knots_converted() -> None:
    snap = ExpeditionSnapshot(
        targets=ExpeditionTargets(
            target_bsp_mps=5.14,
            polar_performance_ratio=0.92,
        ),
        meta=ExpeditionMeta(connected=True, last_poll_at=datetime.now(timezone.utc)),
    )
    delta = snapshot_to_delta(snap, source_label="test")
    paths = {v.path: v.value for v in delta.updates[0].values}
    assert paths["race.expedition.targets.boatSpeed"] == 5.14
    assert paths["race.expedition.targets.polarPerformanceRatio"] == 0.92

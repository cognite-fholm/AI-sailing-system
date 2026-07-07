"""Unit tests — fleet performance rollup."""

import json
from pathlib import Path

from fleet_performance_tracker.rollup import (
    apply_rank_deltas,
    polar_outlier,
    rollup_fleet_performance,
)

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_polar_outlier_thresholds() -> None:
    assert polar_outlier(110, above_threshold=105, below_threshold=90) == "above"
    assert polar_outlier(85, above_threshold=105, below_threshold=90) == "below"
    assert polar_outlier(95, above_threshold=105, below_threshold=90) == "neutral"


def test_rollup_fleet_performance_from_fixture() -> None:
    records = json.loads((FIXTURES / "fleet_polar_window.json").read_text(encoding="utf-8"))
    rolled = rollup_fleet_performance(records)
    by_sail = {r["sail_number"]: r for r in rolled}
    assert len(by_sail) == 3
    assert by_sail["SWE-999"]["polar_outlier"] == "above"
    assert by_sail["DEN-42"]["polar_outlier"] == "below"
    assert by_sail["NOR-10133"]["performance_pct"] == 100.0


def test_apply_rank_deltas() -> None:
    current = [{"sail_number": "A", "rank": 2}, {"sail_number": "B", "rank": 1}]
    previous = [{"sail_number": "A", "rank": 4}, {"sail_number": "B", "rank": 1}]
    out = apply_rank_deltas(current, previous)
    assert out[0]["rank_delta_since_last"] == -2

"""Unit tests — fleet-performance-tracker collector."""

from unittest.mock import patch

from fleet_performance_tracker.collector import collect_own_boat_point
from fleet_performance_tracker.config import FleetTrackerConfig
from fleet_performance_tracker.lifecycle import lifecycle_allows_fleet_write


def test_lifecycle_allows_fleet_write_missing_file(tmp_path) -> None:
    assert lifecycle_allows_fleet_write(tmp_path / "missing.json") is True


def test_lifecycle_allows_fleet_write_racing(tmp_path) -> None:
    state = tmp_path / "state.json"
    state.write_text('{"phase": "racing"}', encoding="utf-8")
    assert lifecycle_allows_fleet_write(state) is True


def test_lifecycle_blocks_planned(tmp_path) -> None:
    state = tmp_path / "state.json"
    state.write_text('{"phase": "planned"}', encoding="utf-8")
    assert lifecycle_allows_fleet_write(state) is False


def test_collect_own_boat_point_from_signalk() -> None:
    config = FleetTrackerConfig(
        regatta_id="test-regatta",
        race_folder="races/2026/test",
        influx_url="http://localhost:8086",
        influx_org="o",
        influx_bucket="race",
        influx_write_token="t",
        influx_signalk_bucket="signalk",
        influx_read_token="t",
        neo4j_uri="bolt://localhost",
        neo4j_user="neo4j",
        neo4j_password="",
        own_sail_number="NOR-10133",
        vessel_id="own-boat",
        interval_seconds=30,
        lifecycle_state=__import__("pathlib").Path("/tmp/none"),
        influx_ais_bucket="ais_tracks",
        polar_manager_url="http://localhost:8092",
    )
    sk = {
        "polar_ratio": 0.98,
        "polar_speed": 6.5,
        "sog": 6.3,
        "lat": 59.1,
        "lon": 10.4,
        "tws": 8.0,
        "twa": 38.0,
        "vmg": 5.0,
    }
    with patch("fleet_performance_tracker.collector._latest_signalk_fields", return_value=sk):
        point = collect_own_boat_point(config)
    assert point is not None
    assert point.performance_pct == 98.0
    assert point.sail_number == "NOR-10133"
    assert point.is_own is True

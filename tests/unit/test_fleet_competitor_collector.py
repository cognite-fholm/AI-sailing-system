"""Unit tests — fleet competitor collector."""

from unittest.mock import patch

from fleet_performance_tracker.collector import collect_competitor_point, collect_fleet_tick
from fleet_performance_tracker.config import FleetTrackerConfig


def _config() -> FleetTrackerConfig:
    return FleetTrackerConfig(
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


def test_collect_competitor_point_derived_polar() -> None:
    config = _config()
    ais_row = {"mmsi": "123", "lat": 59.1, "lon": 10.4, "sog": 6.0, "cog": 50.0}
    vessel = {"mmsi": "123", "sail_number": "SWE-999", "name": "Fast", "is_own": False}
    with patch("fleet_performance_tracker.collector.fetch_target_bsp", return_value=None):
        point = collect_competitor_point(
            config,
            ais_row,
            vessel,
            standing={"rank": 2, "course_pct": 0.3, "handicap_factor": 1.0, "leg_seq": 1},
            proxy_tws=8.0,
            proxy_twd=120.0,
        )
    assert point is not None
    assert point.sail_number == "SWE-999"
    assert point.polar_source == "derived"
    assert point.performance_pct > 0


def test_collect_fleet_tick_own_only_without_ais() -> None:
    config = _config()
    sk = {"polar_ratio": 1.0, "polar_speed": 6.0, "sog": 6.0, "lat": 59.0, "lon": 10.0, "tws": 8.0, "twa": 40.0, "vmg": 5.0}
    with (
        patch("fleet_performance_tracker.collector._latest_signalk_fields", return_value=sk),
        patch("fleet_performance_tracker.collector._latest_ais_positions", return_value=[]),
        patch("fleet_performance_tracker.collector._race_context", return_value=({}, {}, None)),
    ):
        points = collect_fleet_tick(config)
    assert len(points) == 1
    assert points[0].is_own is True

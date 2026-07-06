"""Unit tests for signalk-influx-bridge path mapping and delta conversion."""

from __future__ import annotations

from signalk_influx_bridge.bridge import (
    PATH_FIELD_MAP,
    delta_to_points,
    path_to_field,
    path_to_measurement,
)


def test_path_field_map_includes_adr_0021_paths() -> None:
    assert "navigation.course.calcValues.vmg" in PATH_FIELD_MAP
    assert "performance.polarSpeedRatio" in PATH_FIELD_MAP


def test_path_to_field_known_and_fallback() -> None:
    assert path_to_field("navigation.speedOverGround") == "sog"
    assert path_to_field("custom.unknown.path") == "path"


def test_path_to_measurement() -> None:
    assert path_to_measurement("navigation.speedOverGround") == "navigation"
    assert path_to_measurement("performance.polarSpeed") == "performance"


def test_delta_to_points_numeric_values() -> None:
    delta = {
        "updates": [
            {
                "source": {"label": "test"},
                "values": [
                    {"path": "navigation.speedOverGround", "value": 6.5},
                    {"path": "performance.polarSpeedRatio", "value": 0.98},
                ],
            }
        ]
    }
    points = delta_to_points(delta, "own-boat")
    assert len(points) == 2
    line_protocol = " ".join(p.to_line_protocol() for p in points)
    assert "sog" in line_protocol
    assert "polar_ratio" in line_protocol


def test_delta_to_points_position_dict() -> None:
    delta = {
        "updates": [
            {
                "source": {"label": "test"},
                "values": [
                    {
                        "path": "navigation.position",
                        "value": {"latitude": 59.9, "longitude": 10.6},
                    }
                ],
            }
        ]
    }
    points = delta_to_points(delta, "own-boat")
    assert len(points) == 2

"""Unit tests for Signal K MCP client (ADR-0029)."""

from __future__ import annotations

from unittest.mock import patch

from race_mcp_gateway.signalk_client import SignalKClient, _haversine_m


def test_haversine_zero_distance() -> None:
    assert _haversine_m(59.0, 10.0, 59.0, 10.0) == 0.0


def test_get_ais_targets_sorts_by_distance() -> None:
    client = SignalKClient("http://example.test")
    state = {
        "navigation": {
            "position": {"value": {"latitude": 59.0, "longitude": 10.0}},
        },
        "sensors": {
            "ais": {
                "targets": {
                    "111": {
                        "latitude": {"value": 59.001},
                        "longitude": {"value": 10.0},
                        "name": {"value": "NEAR"},
                    },
                    "222": {
                        "latitude": {"value": 59.01},
                        "longitude": {"value": 10.0},
                        "name": {"value": "FAR"},
                    },
                }
            }
        },
    }
    with patch.object(client, "get_vessel_state", return_value=state):
        result = client.get_ais_targets()
    assert result["count"] == 2
    assert result["targets"][0]["mmsi"] == "111"
    assert result["targets"][0]["distance_meters"] < result["targets"][1]["distance_meters"]


def test_get_ais_targets_max_distance_filter() -> None:
    client = SignalKClient("http://example.test")
    state = {
        "navigation": {
            "position": {"value": {"latitude": 59.0, "longitude": 10.0}},
        },
        "sensors": {
            "ais": {
                "targets": {
                    "111": {
                        "latitude": {"value": 59.001},
                        "longitude": {"value": 10.0},
                    },
                    "222": {
                        "latitude": {"value": 59.05},
                        "longitude": {"value": 10.0},
                    },
                }
            }
        },
    }
    with patch.object(client, "get_vessel_state", return_value=state):
        result = client.get_ais_targets(max_distance_m=5000)
    assert result["count"] == 1
    assert result["targets"][0]["mmsi"] == "111"


def test_list_available_paths_walks_tree() -> None:
    client = SignalKClient("http://example.test")
    state = {
        "navigation": {
            "speedOverGround": {"value": 5.2, "meta": {}},
            "courseOverGroundTrue": {"value": 180.0},
        },
        "environment": {"wind": {"speedApparent": {"value": 12.0}}},
    }
    with patch.object(client, "get_vessel_state", return_value=state):
        paths = client.list_available_paths()
    assert "navigation.speedOverGround" in paths
    assert "environment.wind.speedApparent" in paths


def test_get_path_value_reads_nested_path() -> None:
    client = SignalKClient("http://example.test")
    state = {"navigation": {"speedOverGround": {"value": 6.1}}}
    with patch.object(client, "get_vessel_state", return_value=state):
        assert client.get_path_value("navigation.speedOverGround") == 6.1


def test_get_json_returns_error_on_failure() -> None:
    import urllib.error

    client = SignalKClient("http://example.test")
    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("connection refused")):
        data = client._get_json("/signalk/v1/api/")
    assert "error" in data

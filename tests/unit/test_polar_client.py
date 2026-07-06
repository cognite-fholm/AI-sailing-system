"""Unit tests for signalk-polar-performance polar-manager client."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from signalk_polar_performance.polar_client import PolarManagerClient


def test_fetch_target_success() -> None:
    client = PolarManagerClient("http://polar:8092", "own-boat")
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "target_bsp": 7.26,
        "target_angle_upwind": 38.92,
        "target_angle_downwind": 151.06,
    }
    with patch.object(client._session, "get", return_value=mock_resp):
        result = client.fetch_target(10.0, 52.0)
    assert result is not None
    assert result.polar_speed == 7.26
    assert result.target_angle == 38.92


def test_fetch_target_non_200_returns_none() -> None:
    client = PolarManagerClient("http://polar:8092", "own-boat")
    mock_resp = MagicMock()
    mock_resp.status_code = 503
    mock_resp.text = "unavailable"
    with patch.object(client._session, "get", return_value=mock_resp):
        assert client.fetch_target(10.0, 52.0) is None

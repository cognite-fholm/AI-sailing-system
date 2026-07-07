"""Unit tests — ais-collector parsing."""

from ais_collector.collector import parse_ais_delta


def test_parse_ais_delta_targets() -> None:
    delta = {
        "updates": [
            {
                "values": [
                    {"path": "sensors.ais.targets.123456789.latitude", "value": 59.12},
                    {"path": "sensors.ais.targets.123456789.longitude", "value": 10.45},
                    {"path": "sensors.ais.targets.123456789.speedOverGround", "value": 6.2},
                    {"path": "sensors.ais.targets.123456789.courseOverGroundTrue", "value": 42.0},
                    {"path": "sensors.ais.targets.123456789.name", "value": "SWE-999"},
                ]
            }
        ]
    }
    states = parse_ais_delta(delta)
    assert "123456789" in states
    state = states["123456789"]
    assert state.lat == 59.12
    assert state.lon == 10.45
    assert state.sog == 6.2
    assert state.name == "SWE-999"

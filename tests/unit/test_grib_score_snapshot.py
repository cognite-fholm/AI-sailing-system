"""Unit tests — grib score snapshot mapping."""

import json

from live_results.neo4j import grib_score_to_snapshot


def test_grib_score_to_snapshot_parses_json_string() -> None:
    row = {
        "selected_model": "observed",
        "model_scores": json.dumps({"observed": {"tws_kn": 8.2}}),
        "validation_notes": "test",
        "updated_at": "2026-06-12T12:00:00Z",
    }
    snap = grib_score_to_snapshot(row)
    assert snap["selected_model"] == "observed"
    assert snap["model_scores"]["observed"]["tws_kn"] == 8.2

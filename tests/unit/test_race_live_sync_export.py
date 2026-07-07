"""Unit tests — race-live-sync export and insights (ADR-0028)."""

import json
from pathlib import Path
from unittest.mock import patch

import yaml

from fleet_performance_tracker.rollup import rollup_fleet_performance
from race_live_sync.config import LiveSyncConfig
from race_live_sync.deltas import build_deltas
from race_live_sync.export import build_snapshot
from race_live_sync.insights import build_insights
from race_live_sync.policy import load_live_sync_policy

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _test_config(tmp_path: Path, data_repo: Path | None = None) -> LiveSyncConfig:
    local = data_repo or tmp_path
    cfg_file = tmp_path / "data-repo.yaml"
    cfg_file.write_text(
        yaml.safe_dump(
            {
                "data_repo": {"url": "https://example.com/data.git", "local_path": str(local)},
                "active": {
                    "regatta_id": "test-regatta",
                    "race_path": "races/2026/test-race",
                },
                "live_sync": {"interval_minutes": 5},
                "neo4j": {"uri": "bolt://localhost", "user": "neo4j", "password": ""},
                "influx": {"url": "http://localhost:8086", "org": "o", "bucket": "race"},
            }
        ),
        encoding="utf-8",
    )
    return LiveSyncConfig.from_yaml(cfg_file)


def test_load_policy_thresholds(data_repo_root, tmp_path) -> None:
    if data_repo_root is None:
        import pytest

        pytest.skip("AI-sailing-data not available")
    policy = load_live_sync_policy(
        data_repo_root,
        "races/2026/2026-06-faerderseilasen",
    )
    assert policy.polar_above_pct == 105.0
    assert policy.polar_below_pct == 90.0


def test_build_insights_covers_tactical_types() -> None:
    records = json.loads((FIXTURES / "fleet_polar_window.json").read_text(encoding="utf-8"))
    fleet = rollup_fleet_performance(records)
    standings = [
        {"sail_number": "SWE-999", "rank": 1, "corrected_seconds": 27000},
        {"sail_number": "NOR-10133", "rank": 4, "corrected_seconds": 28000},
    ]
    prev = [{"sail_number": "NOR-10133", "course_pct": 0.28, "rank": 5}]
    insights = build_insights(fleet, standings, previous_fleet=prev)
    types = {i["type"] for i in insights}
    assert "polar_outperformers" in types
    assert "polar_underperformers" in types
    assert "vmg_leaders_leg" in types
    assert "corrected_time_if_now" in types
    assert "course_progress_leaders" in types


def test_build_snapshot_with_mocked_sources(tmp_path) -> None:
    config = _test_config(tmp_path)
    records = json.loads((FIXTURES / "fleet_polar_window.json").read_text(encoding="utf-8"))
    fleet = rollup_fleet_performance(records)
    standings = [{"sail_number": "SWE-999", "rank": 1, "corrected_seconds": 27000, "delta_to_leader_s": 0}]

    with (
        patch("race_live_sync.export.query_standings", return_value=standings),
        patch("race_live_sync.export.query_fleet_performance_rollup", return_value=fleet),
        patch("race_live_sync.export.query_course_selection", return_value={"route_id": "r1", "leg_seq": 2}),
        patch(
            "race_live_sync.export.query_grib_scores",
            return_value={"selected_model": "observed", "model_scores": {"observed": {"tws_kn": 8.0}}},
        ),
    ):
        snap = build_snapshot(config, sequence=2, previous_fleet=[])

    spec = snap["spec"]
    assert spec["sequence"] == 2
    assert spec["standings"][0]["sail_number"] == "SWE-999"
    assert len(spec["fleet_performance"]) == 3
    assert any(i["type"] == "polar_outperformers" for i in spec["insights"])
    assert spec["course_selection"]["route_id"] == "r1"
    assert spec["grib_scores"]["selected_model"] == "observed"


def test_build_deltas_own_boat() -> None:
    fleet = [
        {"sail_number": "NOR-10133", "is_own": True, "rank": 4, "rank_delta_since_last": -1, "performance_pct": 100},
    ]
    prev = [{"sail_number": "NOR-10133", "is_own": True, "rank": 5, "performance_pct": 96}]
    deltas = build_deltas(2, fleet, [{"sail_number": "SWE-1", "rank": 1}], prev)
    assert deltas["own_boat"]["rank_delta_since_last"] == -1
    assert deltas["own_boat"]["performance_pct_delta"] == 4.0

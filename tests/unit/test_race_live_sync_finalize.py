"""Unit tests — race-live-sync finalize (ADR-0024)."""

from pathlib import Path

import yaml

from race_live_sync.config import LiveSyncConfig
from race_live_sync.finalize import (
    build_post_race_documents,
    run_finalize,
    write_post_race_files,
)


def _config(tmp_path: Path) -> LiveSyncConfig:
    data = tmp_path / "data"
    data.mkdir()
    (data / "races" / "2026" / "test-race").mkdir(parents=True)
    (data / "races" / "2026" / "test-race" / "race.yaml").write_text(
        yaml.safe_dump({"spec": {"status": "active"}}),
        encoding="utf-8",
    )
    return LiveSyncConfig(
        repo_url="https://github.com/example/data.git",
        local_path=data,
        branch="main",
        live_branch="race-live/test-regatta",
        regatta_id="test-regatta",
        race_folder="races/2026/test-race",
        interval_minutes=5,
        enabled=True,
        online_required=False,
        github_token="",
        git_user_name="bot",
        git_user_email="bot@test",
        neo4j_uri="bolt://localhost",
        neo4j_user="neo4j",
        neo4j_password="",
        influx_url="http://localhost:8086",
        influx_org="o",
        influx_bucket="race",
        influx_token="",
    )


def test_build_post_race_documents_kinds(tmp_path) -> None:
    config = _config(tmp_path)
    snapshot = {
        "spec": {
            "observed_at": "2026-06-12T12:00:00Z",
            "sequence": 3,
            "standings": [{"rank": 1, "sail_number": "A", "is_own": True}],
            "insights": [{"type": "corrected_time_if_now"}],
            "fleet_performance": [],
            "course_selection": {"route_id": "r1"},
            "grib_scores": {},
            "deltas": {},
        }
    }
    docs = build_post_race_documents(config, snapshot)
    assert set(docs) == {
        "results.yaml",
        "outcome.yaml",
        "insights.yaml",
        "grib-scores.yaml",
        "export-manifest.yaml",
    }
    assert docs["results.yaml"]["kind"] == "RaceResults"
    assert docs["export-manifest.yaml"]["kind"] == "PostRaceExport"


def test_write_post_race_files(tmp_path) -> None:
    config = _config(tmp_path)
    snapshot = {
        "spec": {
            "observed_at": "2026-06-12T12:00:00Z",
            "sequence": 1,
            "standings": [],
            "insights": [],
            "fleet_performance": [],
            "grib_scores": {},
            "deltas": {},
        }
    }
    post_dir = write_post_race_files(config, snapshot)
    assert (post_dir / "results.yaml").is_file()
    race_doc = yaml.safe_load((config.local_path / config.race_folder / "race.yaml").read_text())
    assert race_doc["spec"]["status"] != "archived"


def test_run_finalize_writes_archive(tmp_path, monkeypatch) -> None:
    config = _config(tmp_path)
    live = config.local_path / config.race_folder / "race-live"
    live.mkdir(parents=True)
    (live / "current.yaml").write_text(
        yaml.safe_dump(
            {
                "spec": {
                    "observed_at": "2026-06-12T12:00:00Z",
                    "sequence": 5,
                    "standings": [],
                    "insights": [],
                    "fleet_performance": [],
                    "grib_scores": {},
                    "deltas": {},
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("race_live_sync.finalize.probe_github", lambda _c: False)
    result = run_finalize(config)
    assert result.get("finalized") is True
    assert (config.local_path / config.race_folder / "post-race" / "results.yaml").is_file()
    race_doc = yaml.safe_load((config.local_path / config.race_folder / "race.yaml").read_text())
    assert race_doc["spec"]["status"] == "archived"


def test_merge_live_branch_skips_missing_remote(tmp_path, monkeypatch) -> None:
    from race_live_sync.git_push import merge_live_branch

    config = _config(tmp_path)

    def fake_run(cmd, cwd, check=True):
        class Result:
            returncode = 1 if "rev-parse" in cmd else 0
            stdout = ""
            stderr = ""

        return Result()

    monkeypatch.setattr("race_live_sync.git_push._run", fake_run)
    assert merge_live_branch(config) == "skipped_no_branch"

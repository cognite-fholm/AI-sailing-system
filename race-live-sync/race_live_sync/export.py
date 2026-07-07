"""Build RaceLiveSnapshot YAML from Neo4j + Influx rollup (ADR-0028)."""

from __future__ import annotations

import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from race_live_sync.config import LiveSyncConfig
from race_live_sync.deltas import build_deltas, read_previous_fleet_performance
from race_live_sync.insights import build_insights
from race_live_sync.policy import load_live_sync_policy

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
for _pkg in ("live-results", "fleet-performance-tracker"):
    _path = _REPO_ROOT / _pkg
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from fleet_performance_tracker.influx import InfluxFleetReader  # noqa: E402
from fleet_performance_tracker.rollup import (  # noqa: E402
    apply_rank_deltas,
    rollup_fleet_performance,
)
from live_results.neo4j import (  # noqa: E402
    Neo4jRaceReader,
    course_selection_to_snapshot,
)
from live_results.standings import standings_from_neo4j_rows  # noqa: E402

CONTEXT = [
    "https://sailing.cognite-fholm/schema/v1/context.jsonld",
    {"@base": "https://sailing.cognite-fholm/data/v1/"},
]


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_sequence(manifest_path: Path) -> int:
    if not manifest_path.is_file():
        return 0
    doc = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return 0
    return int(doc.get("spec", {}).get("last_sequence", 0))


def query_standings(config: LiveSyncConfig) -> list[dict[str, Any]]:
    if not config.neo4j_password:
        logger.warning("Neo4j password not set — standings empty")
        return []
    reader = Neo4jRaceReader(config.neo4j_uri, config.neo4j_user, config.neo4j_password)
    try:
        rows = reader.fetch_standings()
        return standings_from_neo4j_rows(rows)
    except Exception:
        logger.exception("Neo4j standings query failed")
        return []
    finally:
        reader.close()


def query_course_selection(config: LiveSyncConfig) -> dict[str, Any] | None:
    if not config.neo4j_password:
        return None
    reader = Neo4jRaceReader(config.neo4j_uri, config.neo4j_user, config.neo4j_password)
    try:
        return course_selection_to_snapshot(reader.fetch_course_selection())
    except Exception:
        logger.exception("Neo4j course selection query failed")
        return None
    finally:
        reader.close()


def query_fleet_performance_rollup(
    config: LiveSyncConfig,
    window_minutes: int,
    *,
    policy_above: float = 105.0,
    policy_below: float = 90.0,
) -> list[dict[str, Any]]:
    if not config.influx_token:
        logger.warning("Influx token not set — fleet_performance empty")
        return []
    reader = InfluxFleetReader(
        config.influx_url,
        config.influx_token,
        config.influx_org,
        config.influx_bucket,
    )
    try:
        records = reader.fetch_window(config.regatta_id, window_minutes)
        return rollup_fleet_performance(
            records,
            above_threshold=policy_above,
            below_threshold=policy_below,
        )
    except Exception:
        logger.exception("Influx fleet rollup failed")
        return []
    finally:
        reader.close()


def build_snapshot(
    config: LiveSyncConfig,
    sequence: int,
    *,
    previous_fleet: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    observed_at = _utc_now()
    race_folder = config.race_folder.rstrip("/")
    ref_suffix = config.regatta_id.replace("-", "_")[:32]

    policy = load_live_sync_policy(config.local_path, race_folder)
    standings = query_standings(config)
    fleet_performance = query_fleet_performance_rollup(
        config,
        config.interval_minutes,
        policy_above=policy.polar_above_pct,
        policy_below=policy.polar_below_pct,
    )
    if previous_fleet:
        fleet_performance = apply_rank_deltas(fleet_performance, previous_fleet)

    insights = build_insights(fleet_performance, standings, previous_fleet=previous_fleet)
    course_selection = query_course_selection(config)
    deltas = build_deltas(
        sequence,
        fleet_performance,
        standings,
        previous_fleet or [],
    )

    return {
        "@context": CONTEXT,
        "@id": f"{race_folder}/race-live/current.yaml",
        "@type": "sailing:RaceLiveSnapshot",
        "apiVersion": "sailing.cognite-fholm/v1",
        "kind": "RaceLiveSnapshot",
        "metadata": {
            "ref": f"live-{config.regatta_id}",
            "@id": f"urn:sailing:entity:live-{config.regatta_id}",
        },
        "spec": {
            "observed_at": observed_at,
            "sequence": sequence,
            "race_phase": "racing",
            "regatta": {
                "@type": "sailing:Regatta",
                "@id": f"urn:sailing:entity:regatta-{ref_suffix}",
            },
            "standings": standings,
            "fleet_performance": fleet_performance,
            "course_selection": course_selection,
            "insights": insights,
            "grib_scores": {},
            "deltas": deltas,
        },
    }


def build_manifest(
    config: LiveSyncConfig,
    sequence: int,
    observed_at: str,
    *,
    commit_sha: str = "",
    push_status: str = "pending",
) -> dict[str, Any]:
    race_folder = config.race_folder.rstrip("/")
    return {
        "@context": CONTEXT,
        "@id": f"{race_folder}/race-live/sync-manifest.yaml",
        "@type": "sailing:RaceLiveSyncManifest",
        "apiVersion": "sailing.cognite-fholm/v1",
        "kind": "RaceLiveSyncManifest",
        "metadata": {
            "ref": f"live-sync-{config.regatta_id}",
            "@id": f"urn:sailing:entity:live-sync-{config.regatta_id}",
        },
        "spec": {
            "last_observed_at": observed_at,
            "last_sequence": sequence,
            "last_commit_sha": commit_sha,
            "last_push_at": _utc_now() if push_status == "ok" else None,
            "branch": config.live_branch,
            "push_status": push_status,
            "regatta_id": config.regatta_id,
        },
    }


def write_live_files(config: LiveSyncConfig) -> tuple[Path, Path, int, str]:
    race_path = config.local_path / config.race_folder
    live_dir = race_path / "race-live"
    live_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = live_dir / "sync-manifest.yaml"
    sequence = read_sequence(manifest_path) + 1
    previous_fleet = read_previous_fleet_performance(live_dir)

    snapshot = build_snapshot(config, sequence, previous_fleet=previous_fleet)
    observed_at = snapshot["spec"]["observed_at"]

    current_path = live_dir / "current.yaml"
    current_path.write_text(yaml.safe_dump(snapshot, sort_keys=False), encoding="utf-8")
    manifest = build_manifest(config, sequence, observed_at)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    logger.info("Wrote race-live seq=%s observed_at=%s", sequence, observed_at)
    return current_path, manifest_path, sequence, observed_at

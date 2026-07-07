"""Build RaceLiveSnapshot YAML from Neo4j + Influx rollup (ADR-0028)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from race_live_sync.config import LiveSyncConfig

logger = logging.getLogger(__name__)

CONTEXT = [
    "https://sailing.cognite-fholm/schema/v1/context.jsonld",
    {"@base": "https://sailing.cognite-fholm/data/v1/"},
]

POLAR_ABOVE_PCT = 105.0
POLAR_BELOW_PCT = 90.0


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _polar_outlier(performance_pct: float | None) -> str:
    if performance_pct is None:
        return "neutral"
    if performance_pct >= POLAR_ABOVE_PCT:
        return "above"
    if performance_pct <= POLAR_BELOW_PCT:
        return "below"
    return "neutral"


def read_sequence(manifest_path: Path) -> int:
    if not manifest_path.is_file():
        return 0
    doc = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return 0
    return int(doc.get("spec", {}).get("last_sequence", 0))


def query_standings(_config: LiveSyncConfig) -> list[dict[str, Any]]:
    """Corrected-time standings if race finished now — from live-results / Neo4j."""
    # TODO: Cypher per schema/neo4j-mapping.yaml
    return []


def query_fleet_performance_rollup(_config: LiveSyncConfig, _window_minutes: int) -> list[dict[str, Any]]:
    """5 min mean from Influx fleet_polar_performance per sail_number."""
    # TODO: Flux query + join AIS positions
    return []


def build_insights(fleet_performance: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Precompute tactical insight blocks for shore agents."""
    insights: list[dict[str, Any]] = []
    outperformers = [f for f in fleet_performance if f.get("polar_outlier") == "above"]
    underperformers = [f for f in fleet_performance if f.get("polar_outlier") == "below"]
    if outperformers:
        insights.append(
            {
                "type": "polar_outperformers",
                "vessels": [f.get("sail_number") for f in outperformers],
                "summary": f"{len(outperformers)} boat(s) above polar threshold",
            }
        )
    if underperformers:
        insights.append(
            {
                "type": "polar_underperformers",
                "vessels": [f.get("sail_number") for f in underperformers],
                "summary": f"{len(underperformers)} boat(s) below polar threshold",
            }
        )
    if fleet_performance:
        vmg_leader = max(fleet_performance, key=lambda f: f.get("vmg_actual") or 0.0)
        insights.append(
            {
                "type": "vmg_leaders_leg",
                "leg_seq": vmg_leader.get("leg_seq"),
                "leader": vmg_leader.get("sail_number"),
                "vmg_actual": vmg_leader.get("vmg_actual"),
            }
        )
    return insights


def build_snapshot(config: LiveSyncConfig, sequence: int) -> dict[str, Any]:
    """Query Neo4j + Influx and map to RaceLiveSnapshot."""
    observed_at = _utc_now()
    race_folder = config.race_folder.rstrip("/")
    ref_suffix = config.regatta_id.replace("-", "_")[:32]

    standings = query_standings(config)
    fleet_performance = query_fleet_performance_rollup(config, config.interval_minutes)
    for entry in fleet_performance:
        entry.setdefault("polar_outlier", _polar_outlier(entry.get("performance_pct")))
    insights = build_insights(fleet_performance)

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
            "course_selection": None,
            "insights": insights,
            "grib_scores": {},
            "deltas": {"sequence_prev": sequence - 1 if sequence > 1 else None},
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

    snapshot = build_snapshot(config, sequence)
    observed_at = snapshot["spec"]["observed_at"]

    current_path = live_dir / "current.yaml"
    current_path.write_text(yaml.safe_dump(snapshot, sort_keys=False), encoding="utf-8")
    manifest = build_manifest(config, sequence, observed_at)
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    logger.info("Wrote race-live seq=%s observed_at=%s", sequence, observed_at)
    return current_path, manifest_path, sequence, observed_at

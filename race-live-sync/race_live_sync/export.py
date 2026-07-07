"""Build RaceLiveSnapshot YAML from Neo4j (stub until Neo4j queries land)."""

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


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_sequence(manifest_path: Path) -> int:
    if not manifest_path.is_file():
        return 0
    doc = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return 0
    return int(doc.get("spec", {}).get("last_sequence", 0))


def build_snapshot(config: LiveSyncConfig, sequence: int) -> dict[str, Any]:
    """Query Neo4j and map to RaceLiveSnapshot. Placeholder until Cypher wired."""
    observed_at = _utc_now()
    race_folder = config.race_folder.rstrip("/")
    ref_suffix = config.regatta_id.replace("-", "_")[:32]

    # TODO: query Neo4j per schema/neo4j-mapping.yaml live_projections
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
            "standings": [],
            "course_selection": None,
            "insights": [],
            "grib_scores": {},
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

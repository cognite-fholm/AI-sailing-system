"""Finalize race — split live snapshot into post-race archive kinds (ADR-0024)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from race_live_sync.config import LiveSyncConfig
from race_live_sync.export import CONTEXT, build_snapshot, read_sequence
from race_live_sync.git_push import commit_finalize, probe_github

logger = logging.getLogger(__name__)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_snapshot_for_finalize(config: LiveSyncConfig) -> dict[str, Any]:
    current = config.local_path / config.race_folder / "race-live" / "current.yaml"
    if current.is_file():
        doc = yaml.safe_load(current.read_text(encoding="utf-8"))
        if isinstance(doc, dict) and doc.get("spec"):
            return doc
    manifest = config.local_path / config.race_folder / "race-live" / "sync-manifest.yaml"
    sequence = read_sequence(manifest) or 1
    return build_snapshot(config, sequence)


def _ref_suffix(regatta_id: str) -> str:
    return regatta_id.replace("-", "_")[:32]


def build_post_race_documents(
    config: LiveSyncConfig,
    snapshot: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    spec = snapshot.get("spec", {})
    race_folder = config.race_folder.rstrip("/")
    ref_suffix = _ref_suffix(config.regatta_id)
    regatta_entity = f"urn:sailing:entity:regatta-{ref_suffix}"
    observed_at = spec.get("observed_at", _utc_now())

    standings = spec.get("standings", [])
    own = next((s for s in standings if s.get("is_own")), None)

    return {
        "results.yaml": {
            "@context": CONTEXT,
            "@id": f"{race_folder}/post-race/results.yaml",
            "@type": "sailing:RaceResults",
            "apiVersion": "sailing.cognite-fholm/v1",
            "kind": "RaceResults",
            "metadata": {
                "ref": f"results-{config.regatta_id}",
                "@id": f"urn:sailing:entity:results-{config.regatta_id}",
            },
            "spec": {
                "regatta": {"@type": "sailing:Regatta", "@id": regatta_entity},
                "source": "live_results",
                "finished_at": observed_at,
                "standings": standings,
            },
        },
        "outcome.yaml": {
            "@context": CONTEXT,
            "@id": f"{race_folder}/post-race/outcome.yaml",
            "@type": "sailing:RaceOutcome",
            "apiVersion": "sailing.cognite-fholm/v1",
            "kind": "RaceOutcome",
            "metadata": {
                "ref": f"outcome-{config.regatta_id}",
                "@id": f"urn:sailing:entity:outcome-{config.regatta_id}",
            },
            "spec": {
                "regatta": {"@type": "sailing:Regatta", "@id": regatta_entity},
                "course_selection": spec.get("course_selection"),
                "own_boat_finish": own,
                "observed_at": observed_at,
            },
        },
        "insights.yaml": {
            "@context": CONTEXT,
            "@id": f"{race_folder}/post-race/insights.yaml",
            "@type": "sailing:RaceInsightArchive",
            "apiVersion": "sailing.cognite-fholm/v1",
            "kind": "RaceInsightArchive",
            "metadata": {
                "ref": f"insights-{config.regatta_id}",
                "@id": f"urn:sailing:entity:insights-{config.regatta_id}",
            },
            "spec": {
                "regatta": {"@type": "sailing:Regatta", "@id": regatta_entity},
                "insights": spec.get("insights", []),
                "fleet_performance_summary": spec.get("fleet_performance", []),
                "deltas": spec.get("deltas", {}),
            },
        },
        "grib-scores.yaml": {
            "@context": CONTEXT,
            "@id": f"{race_folder}/post-race/grib-scores.yaml",
            "@type": "sailing:GribModelOutcome",
            "apiVersion": "sailing.cognite-fholm/v1",
            "kind": "GribModelOutcome",
            "metadata": {
                "ref": f"grib-{config.regatta_id}",
                "@id": f"urn:sailing:entity:grib-{config.regatta_id}",
            },
            "spec": {
                "regatta": {"@type": "sailing:Regatta", "@id": regatta_entity},
                "grib_scores": spec.get("grib_scores", {}),
            },
        },
        "export-manifest.yaml": {
            "@context": CONTEXT,
            "@id": f"{race_folder}/post-race/export-manifest.yaml",
            "@type": "sailing:PostRaceExport",
            "apiVersion": "sailing.cognite-fholm/v1",
            "kind": "PostRaceExport",
            "metadata": {
                "ref": f"export-{config.regatta_id}",
                "@id": f"urn:sailing:entity:export-{config.regatta_id}",
            },
            "spec": {
                "regatta_id": config.regatta_id,
                "exported_at": _utc_now(),
                "source_sequence": spec.get("sequence"),
                "source_observed_at": observed_at,
                "live_branch": config.live_branch,
                "export_status": "ok",
            },
        },
    }


def archive_race_yaml(config: LiveSyncConfig, *, sequence: int | None = None) -> Path:
    race_yaml = config.local_path / config.race_folder / "race.yaml"
    doc = yaml.safe_load(race_yaml.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise ValueError(f"Invalid race.yaml: {race_yaml}")
    spec = doc.setdefault("spec", {})
    spec["status"] = "archived"
    spec["post_race_exported_at"] = _utc_now()
    if sequence is not None:
        spec["live_sync_sequence"] = sequence
    race_yaml.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return race_yaml


def write_post_race_files(config: LiveSyncConfig, snapshot: dict[str, Any]) -> Path:
    post_dir = config.local_path / config.race_folder / "post-race"
    post_dir.mkdir(parents=True, exist_ok=True)
    for filename, document in build_post_race_documents(config, snapshot).items():
        (post_dir / filename).write_text(
            yaml.safe_dump(document, sort_keys=False),
            encoding="utf-8",
        )
    logger.info("Wrote post-race archive to %s", post_dir)
    return post_dir


def run_finalize(config: LiveSyncConfig) -> dict[str, object]:
    if not config.race_folder or not config.regatta_id:
        return {"skipped": True, "reason": "missing active.regatta_id or race_folder"}

    snapshot = load_snapshot_for_finalize(config)
    sequence = int(snapshot.get("spec", {}).get("sequence", 0))
    write_post_race_files(config, snapshot)
    archive_race_yaml(config, sequence=sequence)

    push_status = "skipped_offline"
    commit_sha = ""
    if probe_github(config):
        try:
            commit_sha, push_status = commit_finalize(config)
        except Exception as exc:
            logger.exception("Finalize git push failed")
            push_status = f"failed: {exc}"

    return {
        "finalized": True,
        "regatta_id": config.regatta_id,
        "sequence": sequence,
        "commit_sha": commit_sha,
        "push_status": push_status,
    }

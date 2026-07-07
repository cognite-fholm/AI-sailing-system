"""Main loop: export Neo4j snapshot → git commit → push on LTE."""

from __future__ import annotations

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

import yaml

from race_live_sync.config import LiveSyncConfig
from race_live_sync.export import build_manifest, write_live_files
from race_live_sync.git_push import commit_and_push, probe_github

logger = logging.getLogger(__name__)

LIFECYCLE_STATE = Path(os.environ.get("RACE_LIFECYCLE_STATE", "/var/run/ai-sailing/race-lifecycle.json"))


def lifecycle_allows_live_sync() -> bool:
    if not LIFECYCLE_STATE.is_file():
        return True
    try:
        state = json.loads(LIFECYCLE_STATE.read_text(encoding="utf-8"))
        return bool(state.get("race_live_sync_enabled", True))
    except (json.JSONDecodeError, OSError):
        return True


def write_status(path: Path, status: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def run_tick(config: LiveSyncConfig) -> dict[str, object]:
    if not config.enabled:
        return {"skipped": True, "reason": "RACE_LIVE_SYNC_ENABLED=false"}

    if not lifecycle_allows_live_sync():
        return {"skipped": True, "reason": "lifecycle: not armed/racing"}

    if config.online_required and os.environ.get("ONLINE_MODE", "true").lower() != "true":
        return {"skipped": True, "reason": "ONLINE_MODE=false"}

    if not probe_github(config):
        return {"skipped": True, "reason": "offline_or_no_token"}

    if not config.race_folder or not config.regatta_id:
        return {"skipped": True, "reason": "missing active.regatta_id or race_folder"}

    _, manifest_path, sequence, observed_at = write_live_files(config)

    try:
        commit_sha, push_status = commit_and_push(config, sequence, observed_at)
    except Exception as exc:
        logger.exception("Git push failed")
        push_status = f"failed: {exc}"
        commit_sha = ""

    manifest = build_manifest(
        config,
        sequence,
        observed_at,
        commit_sha=commit_sha,
        push_status=push_status,
    )
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    status: dict[str, object] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sequence": sequence,
        "observed_at": observed_at,
        "commit_sha": commit_sha,
        "push_status": push_status,
        "branch": config.live_branch,
    }
    write_status(config.local_path.parent / "live-sync-status.json", status)
    return status


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config_path = Path(os.environ.get("DATA_REPO_CONFIG", "/config/data-repo.yaml"))
    if not config_path.is_file():
        logger.error("Missing config: %s", config_path)
        sys.exit(1)

    config = LiveSyncConfig.from_yaml(config_path)
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    interval = config.interval_minutes * 60
    logger.info(
        "race-live-sync regatta=%s interval=%sm branch=%s",
        config.regatta_id,
        config.interval_minutes,
        config.live_branch,
    )

    while running:
        try:
            result = run_tick(config)
            logger.info("Tick result: %s", result)
        except Exception:
            logger.exception("Tick failed")
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()

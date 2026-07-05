"""Git pull AI-sailing-data and optionally trigger race-import."""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from race_data_sync.config import SyncConfig

logger = logging.getLogger(__name__)


def clone_or_pull(config: SyncConfig) -> dict[str, str | bool]:
    path = config.local_path
    path.parent.mkdir(parents=True, exist_ok=True)
    if not (path / ".git").is_dir():
        logger.info("Cloning %s -> %s", config.repo_url, path)
        subprocess.run(
            ["git", "clone", "--branch", config.branch, config.repo_url, str(path)],
            check=True,
            capture_output=True,
            text=True,
        )
        head = _git_head(path)
        return {"action": "clone", "head": head, "changed": True}

    subprocess.run(["git", "fetch", "origin", config.branch], cwd=path, check=True)
    before = _git_head(path)
    subprocess.run(["git", "checkout", config.branch], cwd=path, check=True)
    subprocess.run(["git", "pull", "--ff-only", "origin", config.branch], cwd=path, check=True)
    after = _git_head(path)
    return {"action": "pull", "head": after, "changed": before != after}


def _git_head(path: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()


def trigger_import(url: str) -> bool:
    req = urllib.request.Request(url, method="POST", data=b"{}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read().decode()
            logger.info("race-import response: %s", body)
            return resp.status == 200
    except urllib.error.URLError as exc:
        logger.error("race-import trigger failed: %s", exc)
        return False


def write_status(path: Path, status: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, indent=2), encoding="utf-8")


def run_once(config: SyncConfig) -> dict[str, object]:
    if config.online_required and os.environ.get("ONLINE_MODE", "true").lower() != "true":
        return {"skipped": True, "reason": "ONLINE_MODE=false"}

    if not config.auto_pull:
        return {"skipped": True, "reason": "auto_pull disabled"}

    result = clone_or_pull(config)
    status: dict[str, object] = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "repo_path": str(config.local_path),
        **result,
    }
    if result.get("changed") and config.auto_import_neo4j:
        status["import_triggered"] = trigger_import(config.import_url)
    write_status(config.local_path.parent / "sync-status.json", status)
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
    config = SyncConfig.from_yaml(config_path)

    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    interval = config.poll_interval_minutes * 60
    logger.info("race-data-sync path=%s interval=%sm", config.local_path, config.poll_interval_minutes)
    while running:
        try:
            status = run_once(config)
            logger.info("Sync result: %s", status)
        except subprocess.CalledProcessError as exc:
            logger.error("Git sync failed: %s", exc.stderr or exc)
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()

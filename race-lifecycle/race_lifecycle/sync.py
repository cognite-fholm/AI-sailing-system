"""Poll schedule and write lifecycle state for peer services."""

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
from datetime import UTC, datetime
from pathlib import Path

import yaml

from race_lifecycle.policy import load_runtime_policy, policy_into_state
from race_lifecycle.schedule import compute_phase, lifecycle_flags, load_schedule

logger = logging.getLogger(__name__)

STATE_PATH = Path(os.environ.get("RACE_LIFECYCLE_STATE", "/var/run/ai-sailing/race-lifecycle.json"))


def load_active_race_path(config_path: Path, data_repo: Path) -> str | None:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    active = raw.get("active", {})
    race_path = active.get("race_path")
    if race_path:
        return str(race_path).rstrip("/")

    index_file = active.get("index_file", "index.yaml")
    index_path = data_repo / index_file
    if not index_path.is_file():
        return None
    index = yaml.safe_load(index_path.read_text(encoding="utf-8"))
    regatta_id = index.get("spec", {}).get("active", {}).get("regatta_id")
    for race in index.get("spec", {}).get("races", []):
        if race.get("id") == regatta_id:
            return str(race.get("path", "")).rstrip("/") or None
    return None


def sync_active_context(config_path: Path, data_repo: Path) -> bool:
    """Update data-repo.yaml active section from index.yaml."""
    script = Path(__file__).resolve().parents[2] / "scripts" / "sync_active_context.py"
    if not script.is_file():
        return False
    try:
        subprocess.run(
            [sys.executable, str(script), "--config", str(config_path), "--data-repo", str(data_repo)],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as exc:
        logger.warning("sync_active_context failed: %s", exc.stderr or exc)
        return False


def trigger_import(url: str) -> bool:
    req = urllib.request.Request(url, method="POST", data=b"{}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return resp.status == 200
    except urllib.error.URLError as exc:
        logger.error("race-import failed: %s", exc)
        return False


def write_state(state: dict[str, object]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, indent=2), encoding="utf-8")


def run_tick(config_path: Path, data_repo: Path, import_url: str) -> dict[str, object]:
    race_path = load_active_race_path(config_path, data_repo)
    if not race_path:
        return {"skipped": True, "reason": "no active race path"}

    schedule = load_schedule(data_repo, race_path)
    if schedule is None:
        return {"skipped": True, "reason": "no race.yaml schedule"}

    prev: dict[str, object] = {}
    if STATE_PATH.is_file():
        prev = json.loads(STATE_PATH.read_text(encoding="utf-8"))

    prev_phase = str(prev.get("phase", "planned"))
    now = datetime.now(UTC)
    phase = compute_phase(now, schedule, prev_phase)
    flags = lifecycle_flags(phase, schedule)
    policy_spec = load_runtime_policy(data_repo, race_path)
    flags.update(policy_into_state(policy_spec))

    # Transition actions (idempotent)
    if phase == "harbor_ready" and not prev.get("import_triggered"):
        sync_active_context(config_path, data_repo)
        flags["import_triggered"] = trigger_import(import_url)
    elif prev.get("import_triggered"):
        flags["import_triggered"] = prev.get("import_triggered")

    state: dict[str, object] = {
        "updated_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "schedule_timezone": schedule.timezone,
        "start_at": schedule.start_at.isoformat() if schedule.start_at else None,
        **flags,
    }
    write_state(state)
    return state


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    config_path = Path(os.environ.get("DATA_REPO_CONFIG", "/config/data-repo.yaml"))
    data_repo = Path(os.environ.get("DATA_REPO_PATH", "/opt/ai-sailing-data"))
    import_url = os.environ.get("RACE_IMPORT_URL", "http://race-import:8080/import")
    interval = int(os.environ.get("RACE_LIFECYCLE_POLL_SECONDS", "60"))

    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    logger.info("race-lifecycle data_repo=%s poll=%ss", data_repo, interval)
    while running:
        try:
            result = run_tick(config_path, data_repo, import_url)
            logger.info("Lifecycle: %s", result)
        except Exception:
            logger.exception("Lifecycle tick failed")
        for _ in range(interval):
            if not running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()

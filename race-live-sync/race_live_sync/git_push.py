"""Git commit and push for race-live branch."""

from __future__ import annotations

import logging
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import yaml

from race_live_sync.config import LiveSyncConfig

logger = logging.getLogger(__name__)


def _run(cmd: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)


def configure_git_identity(config: LiveSyncConfig) -> None:
    path = config.local_path
    _run(["git", "config", "user.name", config.git_user_name], path)
    _run(["git", "config", "user.email", config.git_user_email], path)


def probe_github(config: LiveSyncConfig) -> bool:
    if not config.github_token:
        logger.warning("No GITHUB_TOKEN — push disabled")
        return False
    try:
        _run(
            [
                "git",
                "ls-remote",
                "--heads",
                f"https://x-access-token:{config.github_token}@github.com/cognite-fholm/AI-sailing-data.git",
                config.branch,
            ],
            config.local_path,
        )
        return True
    except subprocess.CalledProcessError as exc:
        logger.error("GitHub probe failed: %s", exc.stderr or exc)
        return False


def _remote_url(config: LiveSyncConfig) -> str:
    remote_url = config.repo_url
    if remote_url.startswith("https://github.com") and config.github_token:
        remote_url = remote_url.replace(
            "https://github.com",
            f"https://x-access-token:{config.github_token}@github.com",
        )
    return remote_url


def update_race_live_sync_fields(
    config: LiveSyncConfig,
    sequence: int,
    observed_at: str,
) -> Path | None:
    race_yaml = config.local_path / config.race_folder / "race.yaml"
    if not race_yaml.is_file():
        return None
    doc = yaml.safe_load(race_yaml.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        return None
    spec = doc.setdefault("spec", {})
    spec["live_sync_sequence"] = sequence
    spec["last_live_sync_at"] = observed_at
    race_yaml.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")
    return race_yaml


def commit_and_push(
    config: LiveSyncConfig,
    sequence: int,
    observed_at: str,
) -> tuple[str, str]:
    """Returns (commit_sha, push_status)."""
    path = config.local_path
    configure_git_identity(config)

    rel_live = f"{config.race_folder.rstrip('/')}/race-live"
    rel_race = f"{config.race_folder.rstrip('/')}/race.yaml"
    _run(["git", "fetch", "origin"], path)

    # Checkout or create live branch
    branches = _run(["git", "branch", "--list", config.live_branch], path).stdout
    if config.live_branch in branches:
        _run(["git", "checkout", config.live_branch], path)
    else:
        _run(["git", "checkout", "-b", config.live_branch, "origin/" + config.branch], path, check=False)
        try:
            _run(["git", "checkout", "-b", config.live_branch], path)
        except subprocess.CalledProcessError:
            _run(["git", "checkout", "-b", config.live_branch, "HEAD"], path)

    update_race_live_sync_fields(config, sequence, observed_at)
    _run(["git", "add", rel_live, rel_race], path)
    msg = f"race-live: {config.regatta_id} seq={sequence} @ {observed_at}"

    diff = _run(["git", "diff", "--cached", "--quiet"], path, check=False)
    if diff.returncode == 0:
        logger.info("No changes to commit")
        head = _run(["git", "rev-parse", "HEAD"], path).stdout.strip()
        return head, "no_changes"

    _run(["git", "commit", "-m", msg], path)
    commit_sha = _run(["git", "rev-parse", "HEAD"], path).stdout.strip()

    if not config.github_token:
        return commit_sha, "skipped_no_token"

    _run(["git", "push", _remote_url(config), f"HEAD:{config.live_branch}"], path)
    logger.info("Pushed %s to %s", commit_sha[:8], config.live_branch)
    return commit_sha, "ok"


def commit_finalize(config: LiveSyncConfig) -> tuple[str, str]:
    """Commit post-race archive on main and push."""
    path = config.local_path
    configure_git_identity(config)
    rel_post = f"{config.race_folder.rstrip('/')}/post-race"
    rel_race = f"{config.race_folder.rstrip('/')}/race.yaml"
    _run(["git", "fetch", "origin"], path)
    _run(["git", "checkout", config.branch], path)
    _run(["git", "pull", "--ff-only", _remote_url(config), config.branch], path, check=False)
    _run(["git", "add", rel_post, rel_race], path)
    msg = f"post-race: {config.regatta_id} archived @ {datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')}"
    diff = _run(["git", "diff", "--cached", "--quiet"], path, check=False)
    if diff.returncode == 0:
        head = _run(["git", "rev-parse", "HEAD"], path).stdout.strip()
        return head, "no_changes"
    _run(["git", "commit", "-m", msg], path)
    commit_sha = _run(["git", "rev-parse", "HEAD"], path).stdout.strip()
    if not config.github_token:
        return commit_sha, "skipped_no_token"
    _run(["git", "push", _remote_url(config), f"HEAD:{config.branch}"], path)
    logger.info("Finalize pushed %s to %s", commit_sha[:8], config.branch)
    return commit_sha, "ok"

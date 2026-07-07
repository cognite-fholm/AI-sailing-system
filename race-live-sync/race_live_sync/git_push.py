"""Git commit and push for race-live branch."""

from __future__ import annotations

import logging
import subprocess
from pathlib import Path

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


def commit_and_push(
    config: LiveSyncConfig,
    sequence: int,
    observed_at: str,
) -> tuple[str, str]:
    """Returns (commit_sha, push_status)."""
    path = config.local_path
    configure_git_identity(config)

    rel_live = f"{config.race_folder.rstrip('/')}/race-live"
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

    _run(["git", "add", rel_live], path)
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

    remote_url = config.repo_url
    if remote_url.startswith("https://github.com"):
        remote_url = remote_url.replace(
            "https://github.com",
            f"https://x-access-token:{config.github_token}@github.com",
        )

    _run(["git", "push", remote_url, f"HEAD:{config.live_branch}"], path)
    logger.info("Pushed %s to %s", commit_sha[:8], config.live_branch)
    return commit_sha, "ok"

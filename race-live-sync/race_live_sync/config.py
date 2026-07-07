"""Load race-live-sync configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class LiveSyncConfig:
    repo_url: str
    local_path: Path
    branch: str
    live_branch: str
    regatta_id: str
    race_folder: str
    interval_minutes: int
    enabled: bool
    online_required: bool
    github_token: str
    git_user_name: str
    git_user_email: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    influx_url: str
    influx_org: str
    influx_bucket: str
    influx_token: str

    @classmethod
    def from_yaml(cls, path: Path) -> LiveSyncConfig:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        repo = raw["data_repo"]
        active = raw.get("active", {})
        sync = raw.get("live_sync", {})
        neo4j = raw.get("neo4j", {})
        influx = raw.get("influx", {})

        regatta_id = active.get("regatta_id", os.environ.get("ACTIVE_REGATTA_ID", ""))
        race_folder = (
            active.get("race_folder")
            or active.get("race_path")
            or os.environ.get("ACTIVE_RACE_PATH", "")
        )

        token_file = os.environ.get("GITHUB_TOKEN_FILE", "/run/secrets/github_token")
        token = os.environ.get("GITHUB_TOKEN", "")
        if not token and Path(token_file).is_file():
            token = Path(token_file).read_text(encoding="utf-8").strip()

        influx_token = os.environ.get("INFLUX_READ_TOKEN") or os.environ.get(
            "INFLUX_WRITE_TOKEN", influx.get("token", "")
        )

        live_branch = sync.get("branch_pattern", "race-live/{regatta_id}").format(
            regatta_id=regatta_id
        )

        return cls(
            repo_url=repo["url"],
            local_path=Path(os.environ.get("DATA_REPO_PATH", repo["local_path"])),
            branch=repo.get("branch", "main"),
            live_branch=os.environ.get("RACE_LIVE_BRANCH", live_branch),
            regatta_id=regatta_id,
            race_folder=str(race_folder).rstrip("/"),
            interval_minutes=int(
                os.environ.get(
                    "RACE_LIVE_SYNC_INTERVAL_MINUTES",
                    sync.get("interval_minutes", 5),
                )
            ),
            enabled=str(
                os.environ.get("RACE_LIVE_SYNC_ENABLED", sync.get("enabled", True))
            ).lower()
            == "true",
            online_required=str(
                os.environ.get("ONLINE_MODE", sync.get("online_required", True))
            ).lower()
            == "true",
            github_token=token,
            git_user_name=os.environ.get("GIT_USER_NAME", sync.get("git_user_name", "race-live-sync")),
            git_user_email=os.environ.get(
                "GIT_USER_EMAIL", sync.get("git_user_email", "race-live-sync@local")
            ),
            neo4j_uri=os.environ.get("NEO4J_URI", neo4j.get("uri", "bolt://neo4j:7687")),
            neo4j_user=os.environ.get("NEO4J_USER", neo4j.get("user", "neo4j")),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", neo4j.get("password", "")),
            influx_url=os.environ.get("INFLUX_URL", influx.get("url", "http://influxdb:8086")),
            influx_org=os.environ.get("INFLUX_ORG", influx.get("org", "ai-sailing")),
            influx_bucket=os.environ.get("INFLUX_BUCKET", influx.get("bucket", "race")),
            influx_token=influx_token,
        )

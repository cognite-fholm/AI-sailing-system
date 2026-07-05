"""Load sync configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class SyncConfig:
    repo_url: str
    local_path: Path
    branch: str
    poll_interval_minutes: int
    auto_pull: bool
    auto_import_neo4j: bool
    online_required: bool
    import_url: str

    @classmethod
    def from_yaml(cls, path: Path) -> SyncConfig:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        repo = raw["data_repo"]
        sync = raw.get("sync", {})
        return cls(
            repo_url=repo["url"],
            local_path=Path(os.environ.get("DATA_REPO_PATH", repo["local_path"])),
            branch=repo.get("branch", "main"),
            poll_interval_minutes=int(
                os.environ.get("SYNC_POLL_MINUTES", sync.get("poll_interval_minutes", 60))
            ),
            auto_pull=str(os.environ.get("SYNC_AUTO_PULL", sync.get("auto_pull", True))).lower()
            == "true",
            auto_import_neo4j=str(
                os.environ.get("SYNC_AUTO_IMPORT", sync.get("auto_import_neo4j", False))
            ).lower()
            == "true",
            online_required=str(
                os.environ.get("ONLINE_MODE", sync.get("online_required", True))
            ).lower()
            == "true",
            import_url=os.environ.get("RACE_IMPORT_URL", "http://race-import:8080/import"),
        )

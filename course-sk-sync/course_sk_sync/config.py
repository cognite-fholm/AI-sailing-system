"""Configuration for course-sk-sync."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from course_sk_sync.models import DataRepoActive, DataRepoConfig


class CourseSkSyncSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_repo_config: Path = Path("/config/data-repo.yaml")
    data_repo_path: Path = Path("/opt/ai-sailing-data")
    signalk_url: str = "http://127.0.0.1:3000"
    poll_interval_s: float = 30.0
    source_label: str = "course-sk-sync"


def load_data_repo_config(path: Path, data_repo_path: Path | None = None) -> DataRepoConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data_repo_path:
        raw.setdefault("data_repo", {})["local_path"] = str(data_repo_path)
    raw["data_repo"] = {
        key: str(value)
        for key, value in raw.get("data_repo", {}).items()
        if value is not None
    }
    return DataRepoConfig.model_validate(raw)


def resolve_active(settings: CourseSkSyncSettings) -> tuple[Path, DataRepoActive]:
    cfg = load_data_repo_config(settings.data_repo_config, settings.data_repo_path)
    repo = Path(cfg.data_repo.get("local_path", settings.data_repo_path))
    return repo, DataRepoActive.model_validate(cfg.active)

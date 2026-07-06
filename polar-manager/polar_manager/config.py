"""Configuration for polar-manager."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from polar_manager.models import DataRepoActive, DataRepoConfig


class PolarManagerSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    data_repo_config: Path = Path("/config/data-repo.yaml")
    data_repo_path: Path = Path("/opt/ai-sailing-data")
    polar_manager_port: int = 8092
    default_vessel_id: str = "own-boat"


def load_data_repo_config(path: Path, data_repo_path: Path | None = None) -> DataRepoConfig:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if data_repo_path:
        raw.setdefault("data_repo", {})["local_path"] = str(data_repo_path)
    return DataRepoConfig.model_validate(raw)


def resolve_polar_path(settings: PolarManagerSettings) -> tuple[Path, str, DataRepoActive]:
    cfg = load_data_repo_config(settings.data_repo_config, settings.data_repo_path)
    repo = Path(cfg.data_repo.get("local_path", settings.data_repo_path))
    active = DataRepoActive.model_validate(cfg.active)
    if not active.own_boat_path or not active.active_certificate_ref:
        raise FileNotFoundError("active.own_boat_path and active_certificate_ref required")
    cert_dir = active.active_certificate_ref.removeprefix("cert-")
    year = active.certificate_year or 2024
    assets = repo / active.own_boat_path / str(year) / "certificates" / cert_dir / "assets"
    target_file = assets / "7710-target-speeds.txt"
    if not target_file.is_file():
        slk = assets / "7710.slk"
        if slk.is_file():
            raise FileNotFoundError(
                f"SLK present but target-speeds missing: {target_file} (full SLK parser is Phase 2C)"
            )
        raise FileNotFoundError(f"Polar assets not found under {assets}")
    return target_file, settings.default_vessel_id, active

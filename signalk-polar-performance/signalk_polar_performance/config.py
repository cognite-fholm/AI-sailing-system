"""Configuration for signalk-polar-performance."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class PolarPerformanceSettings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    signalk_url: str = "http://127.0.0.1:3000"
    signalk_ws_url: str = "ws://127.0.0.1:3000/signalk/v1/stream?subscribe=all"
    polar_manager_url: str = "http://127.0.0.1:8092"
    vessel_id: str = "own-boat"
    update_interval_s: float = 2.0
    source_label: str = "signalk-polar-performance"

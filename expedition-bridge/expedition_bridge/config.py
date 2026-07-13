"""Service configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

FederationMode = Literal["local_only", "upstream_only", "dual_publish"]


class BridgeSettings(BaseSettings):
    """expedition-bridge environment configuration."""

    model_config = SettingsConfigDict(env_prefix="EXPEDITION_BRIDGE_", extra="ignore")

    poll_hz: float = Field(default=1.0, gt=0, le=10, description="ExpDLL poll rate")
    local_signalk_url: str = Field(
        default="http://127.0.0.1:3000",
        description="Signal K on nav laptop",
    )
    upstream_signalk_url: str | None = Field(
        default="http://telemetry.local:3000",
        description="SLA-1 Pi Signal K for federation",
    )
    federation_mode: FederationMode = Field(
        default="dual_publish",
        description="Where to PUT race.expedition.* deltas",
    )
    source_label: str = Field(default="expedition-bridge")
    expedition_mock: bool = Field(
        default=False,
        description="Use MockExpeditionClient (dev/CI without Windows)",
    )
    knots_to_mps: float = Field(default=0.514444, description="Expedition knot fields → m/s")

    def publish_urls(self) -> list[str]:
        local = self.local_signalk_url.rstrip("/")
        upstream = (self.upstream_signalk_url or "").rstrip("/")
        if self.federation_mode == "local_only":
            return [local]
        if self.federation_mode == "upstream_only" and upstream:
            return [upstream]
        if self.federation_mode == "dual_publish":
            urls = [local]
            if upstream:
                urls.append(upstream)
            return urls
        return [local]

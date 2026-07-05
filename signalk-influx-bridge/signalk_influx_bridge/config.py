"""Bridge configuration from environment."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class BridgeConfig:
    signalk_ws_url: str
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str
    vessel_id: str
    batch_size: int
    flush_interval_s: float

    @classmethod
    def from_env(cls) -> BridgeConfig:
        return cls(
            signalk_ws_url=os.environ.get(
                "SIGNALK_WS_URL",
                "ws://signalk-server:3000/signalk/v1/stream?subscribe=all",
            ),
            influx_url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
            influx_token=os.environ["INFLUX_TOKEN"],
            influx_org=os.environ.get("INFLUX_ORG", "ai-sailing"),
            influx_bucket=os.environ.get("INFLUX_BUCKET", "signalk"),
            vessel_id=os.environ.get("VESSEL_ID", "own-boat"),
            batch_size=int(os.environ.get("BRIDGE_BATCH_SIZE", "100")),
            flush_interval_s=float(os.environ.get("BRIDGE_FLUSH_INTERVAL_S", "1.0")),
        )

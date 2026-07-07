"""Configuration for ais-collector."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class AisCollectorConfig:
    signalk_ws_url: str
    influx_url: str
    influx_token: str
    influx_org: str
    influx_bucket: str
    race_id: str
    own_mmsi: str
    flush_interval_s: float

    @classmethod
    def from_env(cls) -> AisCollectorConfig:
        return cls(
            signalk_ws_url=os.environ.get(
                "SIGNALK_WS_URL",
                "ws://signalk-server:3000/signalk/v1/stream?subscribe=all",
            ),
            influx_url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
            influx_token=os.environ["INFLUX_WRITE_TOKEN"],
            influx_org=os.environ.get("INFLUX_ORG", "ai-sailing"),
            influx_bucket=os.environ.get("INFLUX_AIS_BUCKET", "ais_tracks"),
            race_id=os.environ.get("ACTIVE_REGATTA_ID", ""),
            own_mmsi=os.environ.get("OWN_MMSI", ""),
            flush_interval_s=float(os.environ.get("AIS_FLUSH_INTERVAL_S", "5")),
        )

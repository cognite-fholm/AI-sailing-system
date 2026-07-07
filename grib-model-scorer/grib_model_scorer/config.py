"""Configuration for grib-model-scorer."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class GribScorerConfig:
    influx_url: str
    influx_read_token: str
    influx_org: str
    influx_signalk_bucket: str
    vessel_id: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    race_id: str
    interval_seconds: int
    lifecycle_state: str

    @classmethod
    def from_env(cls) -> GribScorerConfig:
        return cls(
            influx_url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
            influx_read_token=os.environ.get("INFLUX_READ_TOKEN", os.environ.get("INFLUX_WRITE_TOKEN", "")),
            influx_org=os.environ.get("INFLUX_ORG", "ai-sailing"),
            influx_signalk_bucket=os.environ.get("INFLUX_SIGNALK_BUCKET", "signalk"),
            vessel_id=os.environ.get("VESSEL_ID", "own-boat"),
            neo4j_uri=os.environ.get("NEO4J_URI", "bolt://neo4j:7687"),
            neo4j_user=os.environ.get("NEO4J_USER", "neo4j"),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", ""),
            race_id=os.environ.get("ACTIVE_REGATTA_ID", ""),
            interval_seconds=int(os.environ.get("GRIB_SCORER_INTERVAL_SECONDS", "300")),
            lifecycle_state=os.environ.get("RACE_LIFECYCLE_STATE", "/var/run/ai-sailing/race-lifecycle.json"),
        )

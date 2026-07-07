"""Fleet performance tracker configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class FleetTrackerConfig:
    regatta_id: str
    race_folder: str
    influx_url: str
    influx_org: str
    influx_bucket: str
    influx_write_token: str
    influx_signalk_bucket: str
    influx_read_token: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    own_sail_number: str
    vessel_id: str
    interval_seconds: int
    lifecycle_state: Path

    @classmethod
    def from_yaml(cls, path: Path) -> FleetTrackerConfig:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        active = raw.get("active", {})
        influx = raw.get("influx", {})
        neo4j = raw.get("neo4j", {})

        regatta_id = active.get("regatta_id", os.environ.get("ACTIVE_REGATTA_ID", ""))
        race_folder = (
            active.get("race_folder")
            or active.get("race_path")
            or os.environ.get("ACTIVE_RACE_PATH", "")
        )

        write_token = os.environ.get("INFLUX_WRITE_TOKEN", influx.get("write_token", ""))
        read_token = (
            os.environ.get("INFLUX_READ_TOKEN")
            or os.environ.get("INFLUX_SIGNALK_READ_TOKEN")
            or write_token
        )

        return cls(
            regatta_id=str(regatta_id),
            race_folder=str(race_folder).rstrip("/"),
            influx_url=os.environ.get("INFLUX_URL", influx.get("url", "http://influxdb:8086")),
            influx_org=os.environ.get("INFLUX_ORG", influx.get("org", "ai-sailing")),
            influx_bucket=os.environ.get("INFLUX_BUCKET", influx.get("bucket", "race")),
            influx_write_token=write_token,
            influx_signalk_bucket=os.environ.get(
                "INFLUX_SIGNALK_BUCKET", influx.get("signalk_bucket", "signalk")
            ),
            influx_read_token=read_token,
            neo4j_uri=os.environ.get("NEO4J_URI", neo4j.get("uri", "bolt://neo4j:7687")),
            neo4j_user=os.environ.get("NEO4J_USER", neo4j.get("user", "neo4j")),
            neo4j_password=os.environ.get("NEO4J_PASSWORD", neo4j.get("password", "")),
            own_sail_number=os.environ.get("OWN_SAIL_NUMBER", "NOR-10133"),
            vessel_id=os.environ.get("VESSEL_ID", "own-boat"),
            interval_seconds=int(os.environ.get("FLEET_PERF_INTERVAL_SECONDS", "30")),
            lifecycle_state=Path(
                os.environ.get("RACE_LIFECYCLE_STATE", "/var/run/ai-sailing/race-lifecycle.json")
            ),
        )

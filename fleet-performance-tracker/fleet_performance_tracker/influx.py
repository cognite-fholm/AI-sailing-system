"""Influx read/write for fleet_polar_performance."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import Any

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

from fleet_performance_tracker.models import FleetPerformancePoint

MEASUREMENT = "fleet_polar_performance"


class InfluxFleetWriter:
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self._client = InfluxDBClient(url=url, token=token, org=org)
        self._bucket = bucket
        self._write = self._client.write_api(write_options=SYNCHRONOUS)

    def close(self) -> None:
        self._client.close()

    def write_point(self, point: FleetPerformancePoint, *, timestamp: datetime | None = None) -> None:
        ts = timestamp or datetime.now(UTC)
        p = (
            Point(MEASUREMENT)
            .tag("race_id", point.race_id)
            .tag("sail_number", point.sail_number)
            .tag("mmsi", point.mmsi or point.sail_number)
            .tag("vessel_name", point.vessel_name)
            .tag("is_own", "true" if point.is_own else "false")
            .tag("leg_seq", str(point.leg_seq))
            .tag("route_id", point.route_id)
            .tag("polar_source", point.polar_source)
            .tag("polar_quality", point.polar_quality)
            .tag("data_quality", point.data_quality)
            .time(ts, WritePrecision.S)
        )
        for key, value in point.to_influx_fields().items():
            p = p.field(key, value)
        self._write.write(bucket=self._bucket, org=self._client.org, record=p)


class InfluxFleetReader:
    def __init__(self, url: str, token: str, org: str, bucket: str) -> None:
        self._client = InfluxDBClient(url=url, token=token, org=org)
        self._bucket = bucket
        self._org = org
        self._query = self._client.query_api()

    def close(self) -> None:
        self._client.close()

    def fetch_window(
        self,
        race_id: str,
        window_minutes: int,
        *,
        stop: datetime | None = None,
    ) -> list[dict[str, Any]]:
        end = stop or datetime.now(UTC)
        start = end - timedelta(minutes=window_minutes)
        flux = f'''
from(bucket: "{self._bucket}")
  |> range(start: {start.isoformat()}, stop: {end.isoformat()})
  |> filter(fn: (r) => r._measurement == "{MEASUREMENT}")
  |> filter(fn: (r) => r.race_id == "{race_id}")
  |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")
'''
        tables = self._query.query(flux, org=self._org)
        return _flux_tables_to_records(tables)


def influx_from_env() -> InfluxFleetReader | None:
    token = os.environ.get("INFLUX_READ_TOKEN") or os.environ.get("INFLUX_WRITE_TOKEN", "")
    url = os.environ.get("INFLUX_URL", "http://influxdb:8086")
    org = os.environ.get("INFLUX_ORG", "ai-sailing")
    bucket = os.environ.get("INFLUX_BUCKET", "race")
    if not token:
        return None
    return InfluxFleetReader(url=url, token=token, org=org, bucket=bucket)


def _flux_tables_to_records(tables: Any) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for table in tables:
        for record in table.records:
            row = dict(record.values)
            row["_time"] = record.get_time()
            records.append(row)
    return records

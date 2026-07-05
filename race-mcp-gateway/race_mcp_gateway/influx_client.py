from __future__ import annotations

import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any

from influxdb_client import InfluxDBClient
from influxdb_client.client.flux_table import FluxTable

FORBIDDEN_FLUX = re.compile(
    r"\b(bucketWriter|to\(|delete\(|drop\(|experimental\.to)\b",
    re.IGNORECASE,
)


class InfluxReadClient:
    def __init__(
        self,
        url: str,
        token: str,
        org: str,
        default_bucket: str,
        max_range_hours: int = 48,
    ) -> None:
        self._org = org
        self._default_bucket = default_bucket
        self._max_range = timedelta(hours=max_range_hours)
        self._client = InfluxDBClient(url=url, token=token, org=org)

    def close(self) -> None:
        self._client.close()

    def _validate_flux(self, query: str) -> str:
        q = query.strip()
        if FORBIDDEN_FLUX.search(q):
            raise ValueError("Write/delete Flux operations are not allowed.")
        return q

    def query_flux(self, query: str) -> list[dict[str, Any]]:
        q = self._validate_flux(query)
        tables: list[FluxTable] = self._client.query_api().query(q, org=self._org)
        rows: list[dict[str, Any]] = []
        for table in tables:
            for record in table.records:
                rows.append(
                    {
                        "time": record.get_time().isoformat() if record.get_time() else None,
                        "measurement": record.get_measurement(),
                        "field": record.get_field(),
                        "value": record.get_value(),
                        "tags": {k: record.values.get(k) for k in record.values if k.startswith("_") is False},
                    }
                )
        return rows

    def latest_instruments(
        self,
        bucket: str | None,
        measurement: str = "signalk",
        fields: list[str] | None = None,
        window_minutes: int = 5,
    ) -> list[dict[str, Any]]:
        bucket = bucket or self._default_bucket
        field_filter = ""
        if fields:
            quoted = ", ".join(f'"{f}"' for f in fields)
            field_filter = f'|> filter(fn: (r) => contains(value: r._field, set: [{quoted}]))'
        flux = f"""
from(bucket: "{bucket}")
  |> range(start: -{window_minutes}m)
  |> filter(fn: (r) => r._measurement == "{measurement}")
  {field_filter}
  |> last()
"""
        return self.query_flux(flux)

    def wind_history(self, bucket: str | None, minutes: int = 30) -> list[dict[str, Any]]:
        if minutes > int(self._max_range.total_seconds() // 60):
            raise ValueError(f"Range exceeds max_flux_range_hours ({self._max_range}).")
        bucket = bucket or self._default_bucket
        flux = f"""
from(bucket: "{bucket}")
  |> range(start: -{minutes}m)
  |> filter(fn: (r) => r._measurement == "signalk")
  |> filter(fn: (r) => r._field == "twa" or r._field == "tws" or r._field == "awa" or r._field == "aws")
  |> aggregateWindow(every: 30s, fn: mean, createEmpty: false)
"""
        return self.query_flux(flux)

    def list_buckets(self) -> list[str]:
        api = self._client.buckets_api()
        buckets = api.find_buckets().buckets or []
        return sorted({b.name for b in buckets if b.name})


def format_influx_rows(rows: list[dict[str, Any]], limit: int = 500) -> str:
    if not rows:
        return "No series points returned."
    payload = {"point_count": len(rows), "points": rows[:limit]}
    if len(rows) > limit:
        payload["truncated"] = True
    return json.dumps(payload, indent=2, default=str)

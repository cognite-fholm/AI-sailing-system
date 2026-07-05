from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from race_mcp_gateway.config import load_config
from race_mcp_gateway.influx_client import InfluxReadClient, format_influx_rows

mcp = FastMCP("race-influx")

_client: InfluxReadClient | None = None


def _client_or_raise() -> InfluxReadClient:
    global _client
    if _client is None:
        cfg_path = os.environ.get("MCP_GATEWAY_CONFIG")
        cfg = load_config(Path(cfg_path) if cfg_path else None)
        if not cfg.influx_token:
            raise RuntimeError("INFLUX_READ_TOKEN or INFLUX_TOKEN is not set.")
        _client = InfluxReadClient(
            url=cfg.influx_url,
            token=cfg.influx_token,
            org=cfg.influx_org,
            default_bucket=cfg.influx_bucket,
            max_range_hours=cfg.max_flux_range_hours,
        )
    return _client


@mcp.tool()
def flux_query(query: str) -> str:
    """Run a read-only Flux query against InfluxDB (signalk / race / ais_tracks buckets).

    Writes (to, delete, drop) are rejected. Keep time ranges within max_flux_range_hours.
    """
    client = _client_or_raise()
    rows = client.query_flux(query)
    return format_influx_rows(rows)


@mcp.tool()
def get_latest_instruments(
    fields: str = "twa,tws,awa,aws,sog,cog,vmg",
    window_minutes: int = 5,
    bucket: str = "",
) -> str:
    """Latest instrument fields from the signalk bucket (default last 5 minutes)."""
    client = _client_or_raise()
    field_list = [f.strip() for f in fields.split(",") if f.strip()]
    rows = client.latest_instruments(
        bucket=bucket or None,
        fields=field_list,
        window_minutes=window_minutes,
    )
    return format_influx_rows(rows)


@mcp.tool()
def get_wind_history(minutes: int = 30, bucket: str = "") -> str:
    """TWA/TWS/AWA/AWS history aggregated in 30s windows."""
    client = _client_or_raise()
    rows = client.wind_history(bucket=bucket or None, minutes=minutes)
    return format_influx_rows(rows)


@mcp.tool()
def list_buckets() -> str:
    """List Influx buckets visible to the read token."""
    client = _client_or_raise()
    names = client.list_buckets()
    return format_influx_rows([{"bucket": n} for n in names])


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

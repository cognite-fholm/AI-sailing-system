from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from race_mcp_gateway.config import load_config
from race_mcp_gateway.influx_client import InfluxReadClient, format_influx_rows
from race_mcp_gateway.neo4j_client import (
    COURSE_SELECTION_QUERY,
    FLEET_POSITIONS_QUERY,
    Neo4jReadClient,
    SCHEMA_LABELS_QUERY,
    STANDINGS_QUERY,
    format_rows,
)
from race_mcp_gateway.signalk_client import SignalKClient

mcp = FastMCP("race-boat")

_neo4j: Neo4jReadClient | None = None
_influx: InfluxReadClient | None = None
_signalk: SignalKClient | None = None


def _load_cfg():
    cfg_path = os.environ.get("MCP_GATEWAY_CONFIG")
    return load_config(Path(cfg_path) if cfg_path else None)


def _neo4j() -> Neo4jReadClient:
    global _neo4j
    if _neo4j is None:
        cfg = _load_cfg()
        if not cfg.neo4j_password:
            raise RuntimeError("NEO4J_MCP_PASSWORD or NEO4J_PASSWORD is not set.")
        _neo4j = Neo4jReadClient(cfg.neo4j_uri, cfg.neo4j_user, cfg.neo4j_password)
    return _neo4j


def _influx() -> InfluxReadClient:
    global _influx
    if _influx is None:
        cfg = _load_cfg()
        if not cfg.influx_token:
            raise RuntimeError("INFLUX_READ_TOKEN or INFLUX_TOKEN is not set.")
        _influx = InfluxReadClient(
            url=cfg.influx_url,
            token=cfg.influx_token,
            org=cfg.influx_org,
            default_bucket=cfg.influx_bucket,
            max_range_hours=cfg.max_flux_range_hours,
        )
    return _influx


def _signalk() -> SignalKClient:
    global _signalk
    if _signalk is None:
        cfg = _load_cfg()
        if not cfg.signalk_url:
            raise RuntimeError("SIGNALK_URL is not configured.")
        _signalk = SignalKClient(cfg.signalk_url)
    return _signalk


# --- Neo4j tools ---


@mcp.tool()
def cypher_query(query: str, params_json: str = "{}") -> str:
    """Read-only Cypher against race Neo4j (MATCH/RETURN only)."""
    import json

    rows = _neo4j().run_read(query, json.loads(params_json or "{}"))
    return format_rows(rows)


@mcp.tool()
def get_live_standings() -> str:
    """Corrected-time standings from Neo4j LiveStanding nodes."""
    return format_rows(_neo4j().run_read(STANDINGS_QUERY))


@mcp.tool()
def get_course_selection() -> str:
    """Active CourseSelection from Neo4j."""
    return format_rows(_neo4j().run_read(COURSE_SELECTION_QUERY))


@mcp.tool()
def get_fleet_positions() -> str:
    """Fleet lat/lon/cog/sog from Neo4j Vessel nodes."""
    return format_rows(_neo4j().run_read(FLEET_POSITIONS_QUERY))


@mcp.tool()
def get_graph_schema() -> str:
    """Neo4j node labels in the race graph."""
    return format_rows(_neo4j().run_read(SCHEMA_LABELS_QUERY))


# --- Influx tools ---


@mcp.tool()
def flux_query(query: str) -> str:
    """Read-only Flux query (signalk / race / ais_tracks buckets)."""
    return format_influx_rows(_influx().query_flux(query))


@mcp.tool()
def get_latest_instruments(
    fields: str = "twa,tws,awa,aws,sog,cog,vmg",
    window_minutes: int = 5,
    bucket: str = "",
) -> str:
    """Latest instrument values from Influx."""
    field_list = [f.strip() for f in fields.split(",") if f.strip()]
    rows = _influx().latest_instruments(
        bucket=bucket or None,
        fields=field_list,
        window_minutes=window_minutes,
    )
    return format_influx_rows(rows)


@mcp.tool()
def get_wind_history(minutes: int = 30, bucket: str = "") -> str:
    """Wind angle/speed history from Influx."""
    rows = _influx().wind_history(bucket=bucket or None, minutes=minutes)
    return format_influx_rows(rows)


@mcp.tool()
def list_influx_buckets() -> str:
    """Buckets visible to the Influx read token."""
    api = _influx().list_buckets()
    return format_influx_rows([{"bucket": n} for n in api])


# --- Signal K tools (signalk-mcp-server compatible) ---


@mcp.tool()
def get_vessel_state() -> str:
    """Current navigation, environment, and performance from Signal K."""
    import json

    return json.dumps(_signalk().get_vessel_state(), indent=2)


@mcp.tool()
def get_ais_targets(max_distance_m: float = 0) -> str:
    """Nearby AIS targets with optional distance filter in metres (0 = all)."""
    import json

    limit = max_distance_m if max_distance_m > 0 else None
    return json.dumps(_signalk().get_ais_targets(max_distance_m=limit), indent=2)

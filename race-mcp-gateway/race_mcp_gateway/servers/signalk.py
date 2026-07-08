"""Signal K MCP tools — ecosystem-aligned with signalk-mcp-server (ADR-0029)."""

from __future__ import annotations

import json
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from race_mcp_gateway.config import load_config
from race_mcp_gateway.signalk_client import SignalKClient

mcp = FastMCP("race-signalk")

_client: SignalKClient | None = None


def _signalk() -> SignalKClient:
    global _client
    if _client is None:
        cfg_path = os.environ.get("MCP_GATEWAY_CONFIG")
        cfg = load_config(Path(cfg_path) if cfg_path else None)
        if not cfg.signalk_url:
            raise RuntimeError("SIGNALK_URL is not configured.")
        _client = SignalKClient(cfg.signalk_url)
    return _client


@mcp.tool()
def get_initial_context() -> str:
    """SignalK server and vessel overview (signalk-mcp-server compatible)."""
    return json.dumps(_signalk().get_initial_context(), indent=2)


@mcp.tool()
def get_vessel_state() -> str:
    """Current navigation, environment, and performance from Signal K."""
    return json.dumps(_signalk().get_vessel_state(), indent=2)


@mcp.tool()
def get_ais_targets(max_distance_m: float = 0) -> str:
    """Nearby AIS targets with optional distance filter in metres (0 = all)."""
    limit = max_distance_m if max_distance_m > 0 else None
    return json.dumps(_signalk().get_ais_targets(max_distance_m=limit), indent=2)


@mcp.tool()
def get_active_alarms() -> str:
    """Active Signal K notifications and alarms."""
    return json.dumps(_signalk().get_active_alarms(), indent=2)


@mcp.tool()
def list_available_paths() -> str:
    """Discover Signal K data paths on the vessel."""
    return json.dumps({"paths": _signalk().list_available_paths()}, indent=2)


@mcp.tool()
def get_path_value(path: str) -> str:
    """Read one Signal K path, e.g. navigation.speedOverGround."""
    return json.dumps({"path": path, "value": _signalk().get_path_value(path)}, indent=2)

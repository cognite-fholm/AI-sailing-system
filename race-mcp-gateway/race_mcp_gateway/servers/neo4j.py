from __future__ import annotations

import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from race_mcp_gateway.config import load_config
from race_mcp_gateway.neo4j_client import (
    COURSE_SELECTION_QUERY,
    FLEET_POSITIONS_QUERY,
    Neo4jReadClient,
    SCHEMA_LABELS_QUERY,
    STANDINGS_QUERY,
    format_rows,
)

mcp = FastMCP("race-neo4j")

_client: Neo4jReadClient | None = None


def _client_or_raise() -> Neo4jReadClient:
    global _client
    if _client is None:
        cfg_path = os.environ.get("MCP_GATEWAY_CONFIG")
        cfg = load_config(Path(cfg_path) if cfg_path else None)
        if not cfg.neo4j_password:
            raise RuntimeError("NEO4J_MCP_PASSWORD or NEO4J_PASSWORD is not set.")
        _client = Neo4jReadClient(cfg.neo4j_uri, cfg.neo4j_user, cfg.neo4j_password)
    return _client


@mcp.tool()
def cypher_query(query: str, params_json: str = "{}") -> str:
    """Run a read-only Cypher query against the race Neo4j graph.

    Use MATCH/RETURN only. Params are JSON object string, e.g. {"sail": "NOR-10133"}.
    """
    import json

    client = _client_or_raise()
    params = json.loads(params_json or "{}")
    rows = client.run_read(query, params)
    return format_rows(rows)


@mcp.tool()
def get_live_standings() -> str:
    """Corrected-time standings and ranks from LiveStanding nodes."""
    client = _client_or_raise()
    return format_rows(client.run_read(STANDINGS_QUERY))


@mcp.tool()
def get_course_selection() -> str:
    """Active CourseSelection for the current race session."""
    client = _client_or_raise()
    return format_rows(client.run_read(COURSE_SELECTION_QUERY))


@mcp.tool()
def get_fleet_positions() -> str:
    """Latest vessel positions (lat/lon/cog/sog) from the graph."""
    client = _client_or_raise()
    return format_rows(client.run_read(FLEET_POSITIONS_QUERY))


@mcp.tool()
def get_graph_schema() -> str:
    """List Neo4j node labels available in the race graph."""
    client = _client_or_raise()
    return format_rows(client.run_read(SCHEMA_LABELS_QUERY))


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

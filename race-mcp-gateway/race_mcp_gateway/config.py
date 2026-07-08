from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GatewayConfig:
    listen_port: int
    influx_url: str
    influx_org: str
    influx_bucket: str
    influx_token: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    signalk_url: str
    max_flux_range_hours: int
    max_cypher_per_minute: int
    data_repo_path: Path | None


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_config(path: Path | None = None) -> GatewayConfig:
    cfg: dict[str, Any] = {}
    if path and path.is_file():
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        cfg = raw.get("spec", raw)

    upstreams = cfg.get("upstreams", {})
    limits = cfg.get("limits", {})
    paths = cfg.get("paths", {})

    influx_token_env = upstreams.get("influx_token_env", "INFLUX_READ_TOKEN")
    neo4j_password_env = upstreams.get("neo4j_password_env", "NEO4J_MCP_PASSWORD")

    return GatewayConfig(
        listen_port=int(cfg.get("listen_port", 3100)),
        influx_url=upstreams.get("influx_url", _env("INFLUX_URL", "http://localhost:8086")),
        influx_org=upstreams.get("influx_org", _env("INFLUX_ORG", "ai-sailing")),
        influx_bucket=upstreams.get("influx_bucket", _env("INFLUX_BUCKET", "signalk")),
        influx_token=_env(influx_token_env) or _env("INFLUX_TOKEN"),
        neo4j_uri=upstreams.get("neo4j_uri", _env("NEO4J_URI", "bolt://localhost:7687")),
        neo4j_user=upstreams.get("neo4j_user", _env("NEO4J_USER", "mcp_analyst")),
        neo4j_password=_env(neo4j_password_env) or _env("NEO4J_PASSWORD"),
        signalk_url=upstreams.get("signalk_url", _env("SIGNALK_URL", "http://telemetry.local:3000")),
        max_flux_range_hours=int(limits.get("max_flux_range_hours", 48)),
        max_cypher_per_minute=int(limits.get("max_cypher_per_minute", 30)),
        data_repo_path=Path(paths.get("data_repo", _env("DATA_REPO_PATH", "")))
        if paths.get("data_repo") or _env("DATA_REPO_PATH")
        else None,
    )

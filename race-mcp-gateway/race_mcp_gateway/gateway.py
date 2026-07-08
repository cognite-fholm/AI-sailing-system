"""HTTP gateway mounting Neo4j and Influx MCP servers for boat LAN Cursor clients."""

from __future__ import annotations

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from race_mcp_gateway.auth import BearerAuthMiddleware
from race_mcp_gateway.config import load_config
from race_mcp_gateway.servers import combined as combined_server
from race_mcp_gateway.servers import influx as influx_server
from race_mcp_gateway.servers import neo4j as neo4j_server
from race_mcp_gateway.servers import signalk as signalk_server


def health(_request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "race-mcp-gateway"})


def create_app(config_path: Path | None = None) -> Starlette:
    cfg = load_config(config_path)
    os.environ.setdefault("MCP_GATEWAY_CONFIG", str(config_path) if config_path else "")

    app = Starlette(
        routes=[
            Route("/health", health),
            Mount("/mcp/neo4j", app=neo4j_server.mcp.sse_app()),
            Mount("/mcp/influx", app=influx_server.mcp.sse_app()),
            Mount("/mcp/signalk", app=signalk_server.mcp.sse_app()),
            Mount("/mcp", app=combined_server.mcp.sse_app()),
        ],
    )
    app.add_middleware(BearerAuthMiddleware)
    return app


def main() -> None:
    import uvicorn

    cfg_path = os.environ.get("MCP_GATEWAY_CONFIG")
    path = Path(cfg_path) if cfg_path else Path("/opt/ai-sailing-system/config/mcp-gateway.yaml")
    if not path.is_file():
        path = Path(__file__).resolve().parents[2] / "config" / "mcp-gateway.yaml.example"
    cfg = load_config(path if path.is_file() else None)
    app = create_app(path if path.is_file() else None)
    uvicorn.run(app, host="0.0.0.0", port=cfg.listen_port, log_level="info")


if __name__ == "__main__":
    main()

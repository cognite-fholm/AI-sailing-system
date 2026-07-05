"""HTTP API for race-import."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import yaml
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from race_import.importer import connect_driver, run_import

logger = logging.getLogger(__name__)


def _load_active(config_path: Path) -> tuple[Path, dict]:
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    data_repo = Path(os.environ.get("DATA_REPO_PATH", raw["data_repo"]["local_path"]))
    return data_repo, raw.get("active", {})


async def health(_request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "service": "race-import"})


async def import_graph(_request: Request) -> JSONResponse:
    config_path = Path(os.environ.get("DATA_REPO_CONFIG", "/config/data-repo.yaml"))
    if not config_path.is_file():
        return JSONResponse({"error": "missing data-repo config"}, status_code=500)
    data_repo, active = _load_active(config_path)
    if not data_repo.is_dir():
        return JSONResponse(
            {"error": f"data repo not mounted: {data_repo}"},
            status_code=503,
        )
    uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ["NEO4J_PASSWORD"]
    driver = connect_driver(uri, user, password)
    try:
        result = run_import(driver, data_repo, active)
    finally:
        driver.close()
    logger.info("Import complete: %s", result)
    return JSONResponse(result)


def create_app() -> Starlette:
    return Starlette(
        routes=[
            Route("/health", health),
            Route("/import", import_graph, methods=["POST"]),
        ],
    )


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    port = int(os.environ.get("RACE_IMPORT_PORT", "8080"))
    uvicorn.run(create_app(), host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()

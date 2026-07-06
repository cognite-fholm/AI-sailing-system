"""HTTP API for polar-manager."""

from __future__ import annotations

import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from polar_manager.config import PolarManagerSettings, resolve_polar_path
from polar_manager.models import HealthResponse, PolarGrid, TargetResponse
from polar_manager.target_speeds import parse_target_speeds, target_at

logger = logging.getLogger(__name__)

_grid: PolarGrid | None = None


def _load_grid(settings: PolarManagerSettings) -> PolarGrid:
    global _grid
    if _grid is not None:
        return _grid
    path, vessel_id, active = resolve_polar_path(settings)
    cert_ref = active.active_certificate_ref or "unknown"
    _grid = parse_target_speeds(path, vessel_id, cert_ref)
    return _grid


async def health(request: Request) -> JSONResponse:
    settings: PolarManagerSettings = request.app.state.settings
    loaded = False
    vessel_id: str | None = None
    try:
        grid = _load_grid(settings)
        loaded = True
        vessel_id = grid.vessel_id
    except Exception as exc:
        logger.warning("Polar not loaded: %s", exc)
    return JSONResponse(
        HealthResponse(polar_loaded=loaded, vessel_id=vessel_id).model_dump()
    )


async def polar_target(request: Request) -> JSONResponse:
    settings: PolarManagerSettings = request.app.state.settings
    vessel_id = request.path_params["vessel_id"]
    try:
        tws = float(request.query_params.get("tws", "0"))
        twa = float(request.query_params.get("twa", "0"))
    except ValueError:
        return JSONResponse({"error": "tws and twa must be numbers"}, status_code=400)
    try:
        grid = _load_grid(settings)
    except FileNotFoundError as exc:
        return JSONResponse({"error": str(exc)}, status_code=503)
    except Exception as exc:
        logger.exception("Polar load failed")
        return JSONResponse({"error": str(exc)}, status_code=500)
    if vessel_id not in {grid.vessel_id, "own-boat"}:
        return JSONResponse({"error": f"unknown vessel: {vessel_id}"}, status_code=404)
    result: TargetResponse = target_at(grid, tws, twa)
    return JSONResponse(result.model_dump())


def create_app(settings: PolarManagerSettings | None = None) -> Starlette:
    app_settings = settings or PolarManagerSettings()
    app = Starlette(
        routes=[
            Route("/health", health),
            Route("/polars/{vessel_id}/target", polar_target),
        ],
    )
    app.state.settings = app_settings
    return app


def main() -> None:
    import uvicorn

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = PolarManagerSettings()
    port = settings.polar_manager_port
    uvicorn.run(create_app(settings), host="0.0.0.0", port=port, log_level="info")


if __name__ == "__main__":
    main()

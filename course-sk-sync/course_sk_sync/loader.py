"""Load WaypointList YAML from AI-sailing-data."""

from __future__ import annotations

import logging
from pathlib import Path

import yaml

from course_sk_sync.models import ActiveRoute, DataRepoActive, Waypoint

logger = logging.getLogger(__name__)


def _cert_dir_name(cert_ref: str) -> str:
    return cert_ref.removeprefix("cert-")


def list_route_files(data_repo: Path, active: DataRepoActive) -> list[Path]:
    if not active.race_path:
        return []
    routes_dir = data_repo / active.race_path / "courses" / "routes"
    if not routes_dir.is_dir():
        return []
    return sorted(routes_dir.glob("*.yaml"))


def load_route_file(path: Path) -> ActiveRoute | None:
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict) or doc.get("kind") != "WaypointList":
        return None
    meta = doc.get("metadata", {})
    spec = doc.get("spec", {})
    waypoints: list[Waypoint] = []
    skipped = 0
    for wp in spec.get("waypoints") or []:
        lat, lon = wp.get("lat"), wp.get("lon")
        if lat is None or lon is None:
            skipped += 1
            continue
        waypoints.append(
            Waypoint(
                seq=int(wp.get("seq", 0)),
                name=str(wp.get("name", "")),
                lat=float(lat),
                lon=float(lon),
                type=str(wp.get("type", "mark")),
                rounding=wp.get("rounding"),
            )
        )
    if not waypoints:
        logger.warning("No resolved waypoints in %s", path)
        return None
    return ActiveRoute(
        race_id=str(meta.get("race_id", "unknown")),
        route_id=str(meta.get("route_id", spec.get("section", path.stem))),
        name=str(spec.get("name", path.stem)),
        waypoints=waypoints,
    )


def resolve_active_route(data_repo: Path, active: DataRepoActive) -> tuple[ActiveRoute | None, int]:
    files = list_route_files(data_repo, active)
    if not files:
        return None, 0
    if active.active_route_id:
        for path in files:
            route = load_route_file(path)
            if route and route.route_id == active.active_route_id:
                skipped = sum(
                    1
                    for p in files
                    if load_route_file(p) is None
                )
                return route, skipped
    for path in files:
        route = load_route_file(path)
        if route:
            return route, 0
    return None, 0

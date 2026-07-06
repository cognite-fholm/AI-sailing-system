"""Step definitions for service scaffold and contract scenarios."""

from __future__ import annotations

import re
from pathlib import Path

import yaml
from pytest_bdd import given, parsers, then, when

from tests.bdd.steps.common import require_data_repo


@then(parsers.parse('file "{path}" contains service "{service}"'))
def file_contains_service(repo_root: Path, path: str, service: str) -> None:
    text = (repo_root / path).read_text(encoding="utf-8")
    if path.endswith(".yml") and "docker-compose" in path:
        pattern = rf"^\s{{2}}{re.escape(service)}:"
        assert re.search(pattern, text, re.MULTILINE), f"Service {service!r} not in {path}"
    else:
        assert service in text, f"Service {service!r} not in {path}"


@then(parsers.parse('adr/README.md lists ADR "{number}"'))
def adr_readme_lists_number(repo_root: Path, number: str) -> None:
    readme = (repo_root / "adr" / "README.md").read_text(encoding="utf-8")
    assert f"[{number}]" in readme or f"{number}-" in readme, f"ADR {number} not in adr/README.md"


@then(parsers.parse('signalk-influx-bridge maps path "{signalk_path}"'))
def bridge_maps_path(repo_root: Path, signalk_path: str) -> None:
    bridge_py = repo_root / "signalk-influx-bridge" / "signalk_influx_bridge" / "bridge.py"
    text = bridge_py.read_text(encoding="utf-8")
    assert f'"{signalk_path}"' in text, f"Path {signalk_path!r} not in PATH_FIELD_MAP"


@then(parsers.parse('race-import exposes route "{route}"'))
def race_import_exposes_route(repo_root: Path, route: str) -> None:
    api_py = (repo_root / "race-import" / "race_import" / "api.py").read_text(encoding="utf-8")
    assert f'"{route}"' in api_py, f"Route {route!r} not in race-import api"


@then(parsers.parse('polar-manager api exposes route "{route}"'))
def polar_manager_exposes_route(repo_root: Path, route: str) -> None:
    api_py = (repo_root / "polar-manager" / "polar_manager" / "api.py").read_text(encoding="utf-8")
    assert route in api_py, f"Route {route!r} not in polar-manager api"


@given("the active data-repo config is loaded")
def active_data_repo_config(repo_root: Path) -> dict:
    cfg_path = repo_root / "config" / "data-repo.yaml"
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    return raw


@when("course-sk-sync resolves the active route from config")
def course_sk_sync_resolves_route(
    repo_root: Path, data_repo_root: Path | None, bdd_context: dict
) -> None:
    require_data_repo(data_repo_root)
    from course_sk_sync.config import load_data_repo_config
    from course_sk_sync.loader import resolve_active_route
    from course_sk_sync.models import DataRepoActive

    cfg = load_data_repo_config(repo_root / "config" / "data-repo.yaml", data_repo_root)
    active = DataRepoActive.model_validate(cfg.active)
    route, skipped = resolve_active_route(data_repo_root, active)
    bdd_context["active_route"] = route
    bdd_context["skipped_waypoints"] = skipped


@then(parsers.parse("at least {count:d} resolved waypoints are available for sync"))
def resolved_waypoints_count(bdd_context: dict, count: int) -> None:
    route = bdd_context.get("active_route")
    assert route is not None, "No active route resolved from data repo"
    assert len(route.waypoints) >= count, (
        f"Expected >={count} waypoints, got {len(route.waypoints)}"
    )


@when("polar-manager loads the active certificate target-speeds file")
def polar_manager_loads_target_speeds(
    repo_root: Path, data_repo_root: Path | None, bdd_context: dict
) -> None:
    require_data_repo(data_repo_root)
    from polar_manager.config import PolarManagerSettings, resolve_polar_path
    from polar_manager.target_speeds import parse_target_speeds, target_at

    settings = PolarManagerSettings(
        data_repo_config=repo_root / "config" / "data-repo.yaml",
        data_repo_path=data_repo_root,
    )
    path, vessel_id, active = resolve_polar_path(settings)
    grid = parse_target_speeds(path, vessel_id, active.active_certificate_ref or "cert")
    bdd_context["polar_grid"] = grid
    bdd_context["polar_target_fn"] = target_at


@then(
    parsers.parse(
        "polar target BSP at TWS {tws:g} and TWA {twa:g} is approximately {knots:g} knots"
    )
)
def polar_target_bsp_approx(bdd_context: dict, tws: float, twa: float, knots: float) -> None:
    target_at = bdd_context["polar_target_fn"]
    grid = bdd_context["polar_grid"]
    result = target_at(grid, tws, twa)
    assert abs(result.target_bsp - knots) < 0.05, (
        f"Expected ~{knots} kn, got {result.target_bsp}"
    )

"""Collect own-boat and fleet AIS performance for fleet_polar_performance."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fleet_performance_tracker.config import FleetTrackerConfig
from fleet_performance_tracker.models import FleetPerformancePoint
from fleet_performance_tracker.polar_client import fetch_target_bsp

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[2]
_live_results = _REPO_ROOT / "live-results"
if _live_results.is_dir() and str(_live_results) not in sys.path:
    sys.path.insert(0, str(_live_results))

from live_results.neo4j import Neo4jRaceReader  # noqa: E402
from live_results.standings import standings_from_neo4j_rows  # noqa: E402

SIGNALK_FIELDS = (
    "polar_ratio",
    "polar_speed",
    "sog",
    "lat",
    "lon",
    "tws",
    "twa",
    "vmg",
    "cog",
    "twd",
)


def _latest_signalk_fields(
    url: str,
    token: str,
    org: str,
    bucket: str,
    vessel_id: str,
    *,
    lookback_seconds: int = 120,
) -> dict[str, float]:
    from influxdb_client import InfluxDBClient

    end = datetime.now(UTC)
    start = end - timedelta(seconds=lookback_seconds)
    field_filter = " or ".join(f'r._field == "{f}"' for f in SIGNALK_FIELDS)
    flux = f'''
from(bucket: "{bucket}")
  |> range(start: {start.isoformat()}, stop: {end.isoformat()})
  |> filter(fn: (r) => r.vessel == "{vessel_id}")
  |> filter(fn: (r) => {field_filter})
  |> last()
'''
    client = InfluxDBClient(url=url, token=token, org=org)
    try:
        tables = client.query_api().query(flux, org=org)
        out: dict[str, float] = {}
        for table in tables:
            for record in table.records:
                field = record.get_field()
                value = record.get_value()
                if isinstance(value, (int, float)):
                    out[str(field)] = float(value)
        return out
    finally:
        client.close()


def _latest_ais_positions(
    url: str,
    token: str,
    org: str,
    bucket: str,
    race_id: str,
    *,
    lookback_seconds: int = 120,
) -> list[dict[str, Any]]:
    from influxdb_client import InfluxDBClient

    end = datetime.now(UTC)
    start = end - timedelta(seconds=lookback_seconds)
    flux = f'''
from(bucket: "{bucket}")
  |> range(start: {start.isoformat()}, stop: {end.isoformat()})
  |> filter(fn: (r) => r._measurement == "ais_position")
  |> filter(fn: (r) => r.race_id == "{race_id}")
  |> group(columns: ["mmsi"])
  |> last()
  |> group()
'''
    client = InfluxDBClient(url=url, token=token, org=org)
    try:
        tables = client.query_api().query(flux, org=org)
        rows: list[dict[str, Any]] = []
        for table in tables:
            for record in table.records:
                rows.append(dict(record.values))
        return rows
    finally:
        client.close()


def _race_context(config: FleetTrackerConfig) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any] | None]:
    standings_map: dict[str, dict[str, Any]] = {}
    vessels_by_mmsi: dict[str, dict[str, Any]] = {}
    if not config.neo4j_password:
        return vessels_by_mmsi, standings_map, None
    reader = Neo4jRaceReader(config.neo4j_uri, config.neo4j_user, config.neo4j_password)
    try:
        for row in standings_from_neo4j_rows(reader.fetch_standings()):
            sail = str(row.get("sail_number", ""))
            if sail:
                standings_map[sail] = row
        for vessel in reader.fetch_fleet_vessels():
            mmsi = str(vessel.get("mmsi") or "")
            if mmsi:
                vessels_by_mmsi[mmsi] = vessel
        own = next((s for s in standings_map.values() if s.get("is_own")), None)
        if own is None:
            own = standings_map.get(config.own_sail_number)
        return vessels_by_mmsi, standings_map, own
    except Exception:
        logger.exception("Neo4j race context read failed")
        return vessels_by_mmsi, standings_map, None
    finally:
        reader.close()


def collect_own_boat_point(
    config: FleetTrackerConfig,
    *,
    standing: dict[str, Any] | None = None,
    sk: dict[str, float] | None = None,
) -> FleetPerformancePoint | None:
    """Build one FleetPerformancePoint for the own boat."""
    if not config.regatta_id:
        logger.warning("ACTIVE_REGATTA_ID missing — skip tick")
        return None

    sk = sk or _latest_signalk_fields(
        config.influx_url,
        config.influx_read_token,
        config.influx_org,
        config.influx_signalk_bucket,
        config.vessel_id,
    )
    if not sk:
        logger.debug("No signalk samples in window")
        return None

    polar_ratio = sk.get("polar_ratio")
    performance_pct = round(polar_ratio * 100.0, 1) if polar_ratio is not None else 0.0
    polar_speed = sk.get("polar_speed", 0.0)
    sog = sk.get("sog", 0.0)
    vmg_actual = sk.get("vmg", 0.0)
    vmg_target = polar_speed if polar_speed > 0 else sog
    vmg_pct = round((vmg_actual / vmg_target) * 100.0, 1) if vmg_target > 0 else 0.0

    return FleetPerformancePoint(
        race_id=config.regatta_id,
        sail_number=config.own_sail_number,
        is_own=True,
        leg_seq=int((standing or {}).get("leg_seq") or 0),
        route_id=str((standing or {}).get("route_id", "")),
        lat=sk.get("lat", 0.0),
        lon=sk.get("lon", 0.0),
        sog=sog,
        tws=sk.get("tws", 0.0),
        twa=sk.get("twa", 0.0),
        cog=sk.get("cog", 0.0),
        bsp_target=polar_speed,
        vmg_target=vmg_target,
        vmg_actual=vmg_actual,
        performance_pct=performance_pct,
        vmg_pct=vmg_pct,
        handicap_value=float((standing or {}).get("handicap_factor") or 1.0),
        course_pct=float((standing or {}).get("course_pct") or 0.0),
        rank=(standing or {}).get("rank"),
        polar_source="slk",
        polar_quality="high",
        data_quality="ok",
    )


def _estimate_twa(cog: float, twd: float | None) -> float:
    if twd is None:
        return 45.0
    diff = abs((cog - twd + 180) % 360 - 180)
    return min(diff, 180 - diff) or 45.0


def collect_competitor_point(
    config: FleetTrackerConfig,
    ais_row: dict[str, Any],
    vessel: dict[str, Any],
    *,
    standing: dict[str, Any] | None,
    proxy_tws: float,
    proxy_twd: float | None,
) -> FleetPerformancePoint | None:
    mmsi = str(ais_row.get("mmsi") or vessel.get("mmsi") or "")
    sail_number = str(vessel.get("sail_number") or mmsi)
    if not mmsi or vessel.get("is_own"):
        return None
    sog = float(ais_row.get("sog") or 0.0)
    cog = float(ais_row.get("cog") or 0.0)
    lat = float(ais_row.get("lat") or 0.0)
    lon = float(ais_row.get("lon") or 0.0)
    if sog <= 0 or lat == 0.0:
        return None

    twa = _estimate_twa(cog, proxy_twd)
    vessel_id = str(vessel.get("vessel_id") or sail_number)
    bsp_target = fetch_target_bsp(config.polar_manager_url, vessel_id, proxy_tws, twa)
    polar_source = "slk"
    polar_quality = "high"
    if not bsp_target or bsp_target <= 0:
        bsp_target = sog * 1.05
        polar_source = "derived"
        polar_quality = "low"
    performance_pct = round((sog / bsp_target) * 100.0, 1)
    vmg_target = bsp_target * 0.85
    vmg_actual = sog * 0.85
    vmg_pct = round((vmg_actual / vmg_target) * 100.0, 1) if vmg_target > 0 else 0.0

    return FleetPerformancePoint(
        race_id=config.regatta_id,
        mmsi=mmsi,
        sail_number=sail_number,
        vessel_name=str(vessel.get("name") or ""),
        is_own=False,
        leg_seq=int((standing or {}).get("leg_seq") or 0),
        lat=lat,
        lon=lon,
        sog=sog,
        cog=cog,
        tws=proxy_tws,
        twa=twa,
        bsp_target=bsp_target,
        vmg_target=vmg_target,
        vmg_actual=vmg_actual,
        performance_pct=performance_pct,
        vmg_pct=vmg_pct,
        handicap_value=float((standing or {}).get("handicap_factor") or 1.0),
        course_pct=float((standing or {}).get("course_pct") or 0.0),
        rank=(standing or {}).get("rank"),
        polar_source=polar_source,
        polar_quality=polar_quality,
        data_quality="estimated_wind",
    )


def collect_fleet_tick(config: FleetTrackerConfig) -> list[FleetPerformancePoint]:
    """Own boat + AIS competitors (ADR-0016 loop v2)."""
    vessels_by_mmsi, standings_map, own_standing = _race_context(config)
    sk = _latest_signalk_fields(
        config.influx_url,
        config.influx_read_token,
        config.influx_org,
        config.influx_signalk_bucket,
        config.vessel_id,
    )
    points: list[FleetPerformancePoint] = []
    own = collect_own_boat_point(config, standing=own_standing, sk=sk)
    if own:
        points.append(own)

    proxy_tws = sk.get("tws", 8.0) if sk else 8.0
    proxy_twd = sk.get("twd") if sk else None
    ais_rows = _latest_ais_positions(
        config.influx_url,
        config.influx_read_token,
        config.influx_org,
        config.influx_ais_bucket,
        config.regatta_id,
    )
    for ais_row in ais_rows:
        mmsi = str(ais_row.get("mmsi", ""))
        vessel = vessels_by_mmsi.get(mmsi, {"mmsi": mmsi, "sail_number": mmsi, "is_own": False})
        sail = str(vessel.get("sail_number") or mmsi)
        point = collect_competitor_point(
            config,
            ais_row,
            vessel,
            standing=standings_map.get(sail),
            proxy_tws=proxy_tws,
            proxy_twd=proxy_twd,
        )
        if point:
            points.append(point)
    return points

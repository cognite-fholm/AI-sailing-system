"""Collect own-boat fleet performance from Influx signalk + Neo4j standings."""

from __future__ import annotations

import logging
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from fleet_performance_tracker.config import FleetTrackerConfig
from fleet_performance_tracker.models import FleetPerformancePoint

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


def _own_standing_row(config: FleetTrackerConfig) -> dict[str, Any] | None:
    if not config.neo4j_password:
        return None
    reader = Neo4jRaceReader(config.neo4j_uri, config.neo4j_user, config.neo4j_password)
    try:
        rows = standings_from_neo4j_rows(reader.fetch_standings())
        for row in rows:
            if row.get("is_own"):
                return row
        for row in rows:
            if str(row.get("sail_number")) == config.own_sail_number:
                return row
        return rows[0] if rows else None
    except Exception:
        logger.exception("Neo4j standing read failed")
        return None
    finally:
        reader.close()


def collect_own_boat_point(config: FleetTrackerConfig) -> FleetPerformancePoint | None:
    """Build one FleetPerformancePoint for the own boat (ADR-0016 loop v1)."""
    if not config.regatta_id:
        logger.warning("ACTIVE_REGATTA_ID missing — skip tick")
        return None

    sk = _latest_signalk_fields(
        config.influx_url,
        config.influx_read_token,
        config.influx_org,
        config.influx_signalk_bucket,
        config.vessel_id,
    )
    if not sk:
        logger.debug("No signalk samples in window")
        return None

    standing = _own_standing_row(config)
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
        leg_seq=int(standing.get("leg_seq") or 0) if standing else 0,
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

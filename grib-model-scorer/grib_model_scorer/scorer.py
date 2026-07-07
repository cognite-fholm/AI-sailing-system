"""Write observed wind baseline to Neo4j GribModelScore (loop v1)."""

from __future__ import annotations

import json
import logging
import signal
import sys
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from grib_model_scorer.config import GribScorerConfig
from neo4j import GraphDatabase

logger = logging.getLogger(__name__)

MERGE_SCORE = """
MERGE (g:GribModelScore {race_id: $race_id})
SET g.selected_model = $selected_model,
    g.model_scores = $model_scores,
    g.validation_notes = $validation_notes,
    g.updated_at = $updated_at
"""


def _latest_tws(config: GribScorerConfig) -> float | None:
    from influxdb_client import InfluxDBClient

    end = datetime.now(UTC)
    start = end - timedelta(minutes=5)
    flux = f'''
from(bucket: "{config.influx_signalk_bucket}")
  |> range(start: {start.isoformat()}, stop: {end.isoformat()})
  |> filter(fn: (r) => r.vessel == "{config.vessel_id}")
  |> filter(fn: (r) => r._field == "tws")
  |> last()
'''
    client = InfluxDBClient(url=config.influx_url, token=config.influx_read_token, org=config.influx_org)
    try:
        tables = client.query_api().query(flux, org=config.influx_org)
        for table in tables:
            for record in table.records:
                value = record.get_value()
                if isinstance(value, (int, float)):
                    return float(value)
        return None
    finally:
        client.close()


def _lifecycle_allows(state_path: str) -> bool:
    path = Path(state_path)
    if not path.is_file():
        return True
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
        return str(state.get("phase", "")) in ("armed", "racing", "finalize_pending")
    except (json.JSONDecodeError, OSError):
        return True


def write_score(config: GribScorerConfig) -> bool:
    if not config.race_id or not config.neo4j_password:
        return False
    tws = _latest_tws(config)
    if tws is None:
        logger.debug("No observed TWS for grib score")
        return False
    observed_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    model_scores = {"observed": {"tws_kn": tws, "source": "signalk"}}
    driver = GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_user, config.neo4j_password))
    try:
        with driver.session() as session:
            session.run(
                MERGE_SCORE,
                race_id=config.race_id,
                selected_model="observed",
                model_scores=json.dumps(model_scores),
                validation_notes="Loop v1 baseline from onboard instruments; GRIB compare deferred",
                updated_at=observed_at,
            )
        logger.info("Updated GribModelScore race_id=%s tws=%.1f", config.race_id, tws)
        return True
    finally:
        driver.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = GribScorerConfig.from_env()
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info("grib-model-scorer race_id=%s interval=%ss", config.race_id, config.interval_seconds)
    while running:
        if _lifecycle_allows(config.lifecycle_state):
            try:
                write_score(config)
            except Exception:
                logger.exception("grib-model-scorer tick failed")
        for _ in range(config.interval_seconds):
            if not running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()

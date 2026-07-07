"""Periodic fleet polar performance writer (ADR-0016) — 30 s own-boat loop."""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from fleet_performance_tracker.collector import collect_own_boat_point
from fleet_performance_tracker.config import FleetTrackerConfig
from fleet_performance_tracker.influx import InfluxFleetWriter
from fleet_performance_tracker.lifecycle import lifecycle_allows_fleet_write

logger = logging.getLogger(__name__)


def write_tick(writer: InfluxFleetWriter, config: FleetTrackerConfig) -> bool:
    if not lifecycle_allows_fleet_write(config.lifecycle_state):
        logger.debug("Lifecycle phase — fleet write paused")
        return False
    point = collect_own_boat_point(config)
    if point is None:
        return False
    writer.write_point(point, timestamp=datetime.now(UTC))
    logger.info(
        "Wrote fleet_polar_performance sail=%s perf=%.1f%% rank=%s",
        point.sail_number,
        point.performance_pct,
        point.rank,
    )
    return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config_path = Path(os.environ.get("DATA_REPO_CONFIG", "/config/data-repo.yaml"))
    if not config_path.is_file():
        logger.error("Missing config: %s", config_path)
        sys.exit(1)

    config = FleetTrackerConfig.from_yaml(config_path)
    if not config.influx_write_token:
        logger.error("INFLUX_WRITE_TOKEN required")
        sys.exit(1)

    writer = InfluxFleetWriter(
        config.influx_url,
        config.influx_write_token,
        config.influx_org,
        config.influx_bucket,
    )
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info(
        "fleet-performance-tracker race_id=%s interval=%ss sail=%s",
        config.regatta_id,
        config.interval_seconds,
        config.own_sail_number,
    )
    try:
        while running:
            try:
                write_tick(writer, config)
            except Exception:
                logger.exception("Fleet performance tick failed")
            for _ in range(config.interval_seconds):
                if not running:
                    break
                time.sleep(1)
    finally:
        writer.close()


if __name__ == "__main__":
    main()

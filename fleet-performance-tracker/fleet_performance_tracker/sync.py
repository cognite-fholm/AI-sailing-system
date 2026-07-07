"""Periodic fleet polar performance writer (ADR-0016) — 30 s loop scaffold."""

from __future__ import annotations

import logging
import os
import signal
import sys
import time
from datetime import UTC, datetime

from fleet_performance_tracker.influx import InfluxFleetWriter
from fleet_performance_tracker.models import FleetPerformancePoint

logger = logging.getLogger(__name__)


def write_sample_tick(writer: InfluxFleetWriter, race_id: str) -> None:
    """Placeholder until live-results + AIS integration lands."""
    point = FleetPerformancePoint(
        race_id=race_id,
        sail_number=os.environ.get("OWN_SAIL_NUMBER", "NOR-10133"),
        is_own=True,
        performance_pct=100.0,
        vmg_pct=95.0,
    )
    writer.write_point(point, timestamp=datetime.now(UTC))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    token = os.environ.get("INFLUX_WRITE_TOKEN", "")
    if not token:
        logger.error("INFLUX_WRITE_TOKEN required")
        sys.exit(1)
    writer = InfluxFleetWriter(
        url=os.environ.get("INFLUX_URL", "http://influxdb:8086"),
        token=token,
        org=os.environ.get("INFLUX_ORG", "ai-sailing"),
        bucket=os.environ.get("INFLUX_BUCKET", "race"),
    )
    race_id = os.environ.get("ACTIVE_REGATTA_ID", "")
    interval = int(os.environ.get("FLEET_PERF_INTERVAL_SECONDS", "30"))
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info("fleet-performance-tracker race_id=%s interval=%ss", race_id, interval)
    try:
        while running:
            if race_id:
                write_sample_tick(writer, race_id)
            for _ in range(interval):
                if not running:
                    break
                time.sleep(1)
    finally:
        writer.close()


if __name__ == "__main__":
    main()

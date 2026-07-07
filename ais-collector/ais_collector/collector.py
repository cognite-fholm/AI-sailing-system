"""Parse Signal K AIS target deltas and write ais_position points."""

from __future__ import annotations

import json
import logging
import re
import signal
import sys
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from websocket import WebSocketApp

from ais_collector.config import AisCollectorConfig

logger = logging.getLogger(__name__)

AIS_TARGET_RE = re.compile(
    r"^sensors\.ais\.targets\.(?P<mmsi>\d+)\.(?P<field>.+)$"
)


@dataclass
class AisTargetState:
    mmsi: str
    name: str = ""
    lat: float | None = None
    lon: float | None = None
    sog: float | None = None
    cog: float | None = None
    heading: float | None = None
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class AisInfluxWriter:
    def __init__(self, config: AisCollectorConfig) -> None:
        self._config = config
        self._client = InfluxDBClient(
            url=config.influx_url,
            token=config.influx_token,
            org=config.influx_org,
        )
        self._write = self._client.write_api(write_options=SYNCHRONOUS)

    def close(self) -> None:
        self._client.close()

    def write_target(self, state: AisTargetState, *, is_own: bool) -> None:
        if state.lat is None or state.lon is None:
            return
        p = (
            Point("ais_position")
            .tag("race_id", self._config.race_id)
            .tag("mmsi", state.mmsi)
            .tag("name", state.name or state.mmsi)
            .tag("is_own", "true" if is_own else "false")
            .field("lat", float(state.lat))
            .field("lon", float(state.lon))
            .time(state.updated_at, WritePrecision.S)
        )
        if state.sog is not None:
            p = p.field("sog", float(state.sog))
        if state.cog is not None:
            p = p.field("cog", float(state.cog))
        if state.heading is not None:
            p = p.field("heading", float(state.heading))
        self._write.write(
            bucket=self._config.influx_bucket,
            org=self._config.influx_org,
            record=p,
        )


def _apply_value(state: AisTargetState, field_name: str, value: Any) -> None:
    if not isinstance(value, (int, float, str)):
        return
    if field_name in ("latitude", "lat"):
        state.lat = float(value)
    elif field_name in ("longitude", "lon"):
        state.lon = float(value)
    elif field_name in ("speedOverGround", "sog", "speed"):
        state.sog = float(value)
    elif field_name in ("courseOverGroundTrue", "cog", "course"):
        state.cog = float(value)
    elif field_name in ("headingTrue", "heading"):
        state.heading = float(value)
    elif field_name == "name":
        state.name = str(value)


def parse_ais_delta(delta: dict[str, Any]) -> dict[str, AisTargetState]:
    states: dict[str, AisTargetState] = {}
    now = datetime.now(UTC)
    for update in delta.get("updates") or []:
        for item in update.get("values") or []:
            path = item.get("path")
            if not path or not isinstance(path, str):
                continue
            match = AIS_TARGET_RE.match(path)
            if not match:
                continue
            mmsi = match.group("mmsi")
            field_name = match.group("field")
            state = states.setdefault(mmsi, AisTargetState(mmsi=mmsi, updated_at=now))
            raw = item.get("value")
            if isinstance(raw, dict) and "latitude" in raw and "longitude" in raw:
                state.lat = float(raw["latitude"])
                state.lon = float(raw["longitude"])
            else:
                _apply_value(state, field_name, raw)
            ts = item.get("timestamp")
            if ts:
                try:
                    state.updated_at = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                except ValueError:
                    state.updated_at = now
    return states


class AisCollector:
    def __init__(self, config: AisCollectorConfig) -> None:
        self.config = config
        self.writer = AisInfluxWriter(config)
        self._running = True
        self._last_flush = time.monotonic()

    def stop(self, *_args: object) -> None:
        self._running = False

    def on_message(self, _ws: WebSocketApp, message: str) -> None:
        if not self.config.race_id:
            return
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        for mmsi, state in parse_ais_delta(payload).items():
            is_own = bool(self.config.own_mmsi and mmsi == self.config.own_mmsi)
            self.writer.write_target(state, is_own=is_own)

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        backoff = 2.0
        while self._running:
            ws = WebSocketApp(
                self.config.signalk_ws_url,
                on_open=lambda *_: logger.info("ais-collector connected to Signal K"),
                on_message=self.on_message,
                on_error=lambda _w, err: logger.error("Signal K error: %s", err),
                on_close=lambda _w, status, msg: logger.warning("Signal K closed: %s %s", status, msg),
            )
            try:
                ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as exc:
                logger.error("ais-collector loop error: %s", exc)
            if not self._running:
                break
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 60.0)
        self.writer.close()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        config = AisCollectorConfig.from_env()
    except KeyError as exc:
        logger.error("Missing env: %s", exc)
        sys.exit(1)
    logger.info("ais-collector race_id=%s bucket=%s", config.race_id, config.influx_bucket)
    AisCollector(config).run()


if __name__ == "__main__":
    main()

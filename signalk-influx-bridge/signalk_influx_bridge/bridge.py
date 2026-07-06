"""Subscribe to Signal K and write numeric deltas to InfluxDB."""

from __future__ import annotations

import json
import logging
import signal
import sys
import time
from typing import Any

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from websocket import WebSocketApp

from signalk_influx_bridge.config import BridgeConfig

logger = logging.getLogger(__name__)

# Signal K path suffix -> Influx field name (subset; extend per spec §7.2)
PATH_FIELD_MAP: dict[str, str] = {
    "navigation.speedOverGround": "sog",
    "navigation.courseOverGroundTrue": "cog",
    "navigation.courseOverGroundMagnetic": "cog_magnetic",
    "navigation.headingTrue": "heading_true",
    "navigation.headingMagnetic": "heading_magnetic",
    "navigation.position.latitude": "lat",
    "navigation.position.longitude": "lon",
    "environment.wind.speedTrue": "tws",
    "environment.wind.angleTrueWater": "twa",
    "environment.wind.directionTrue": "twd",
    "environment.wind.speedApparent": "aws",
    "environment.wind.angleApparent": "awa",
    "navigation.leewayAngle": "leeway",
    "navigation.rateOfTurn": "rot",
    "navigation.depthBelowTransducer": "depth",
    "navigation.log": "log",
    "heel": "heel",
    "attitude.roll": "heel",
    "navigation.course.calcValues.vmg": "vmg",
    "navigation.course.calcValues.xte": "xte",
    "navigation.course.calcValues.dtm": "dtm",
    "navigation.course.calcValues.bearingToMark": "btm",
    "navigation.course.calcValues.distanceToMark": "dtm_mark",
    "navigation.course.calcValues.timeToGo": "ttg",
    "performance.polarSpeed": "polar_speed",
    "performance.polarSpeedRatio": "polar_ratio",
    "performance.targetAngle": "target_angle",
}


def path_to_measurement(signalk_path: str) -> str:
    """Derive Influx measurement from Signal K path root."""
    root = signalk_path.split(".")[0]
    return root.replace("@", "_")


def path_to_field(signalk_path: str) -> str:
    if signalk_path in PATH_FIELD_MAP:
        return PATH_FIELD_MAP[signalk_path]
    return signalk_path.split(".")[-1]


def delta_to_points(delta: dict[str, Any], vessel_id: str) -> list[Point]:
    points: list[Point] = []
    updates = delta.get("updates") or []
    for update in updates:
        source = update.get("source", {}).get("label", "unknown")
        for value in update.get("values") or []:
            path = value.get("path")
            if not path:
                continue
            raw = value.get("value")
            if isinstance(raw, dict):
                if path.endswith("position") and "latitude" in raw and "longitude" in raw:
                    ts = value.get("timestamp")
                    for sub_path, sub_val in (
                        (f"{path}.latitude", raw["latitude"]),
                        (f"{path}.longitude", raw["longitude"]),
                    ):
                        if isinstance(sub_val, (int, float)):
                            pt = (
                                Point(path_to_measurement(sub_path))
                                .tag("vessel", vessel_id)
                                .tag("source", source)
                                .field(path_to_field(sub_path), float(sub_val))
                            )
                            if ts:
                                pt.time(ts)
                            points.append(pt)
                continue
            if not isinstance(raw, (int, float)):
                continue
            pt = (
                Point(path_to_measurement(path))
                .tag("vessel", vessel_id)
                .tag("source", source)
                .field(path_to_field(path), float(raw))
            )
            ts = value.get("timestamp")
            if ts:
                pt.time(ts)
            points.append(pt)
    return points


class SignalKInfluxBridge:
    def __init__(self, config: BridgeConfig) -> None:
        self.config = config
        self._client = InfluxDBClient(
            url=config.influx_url,
            token=config.influx_token,
            org=config.influx_org,
        )
        self._write_api = self._client.write_api(write_options=SYNCHRONOUS)
        self._buffer: list[Point] = []
        self._last_flush = time.monotonic()
        self._ws: WebSocketApp | None = None
        self._running = True

    def flush(self) -> None:
        if not self._buffer:
            return
        batch, self._buffer = self._buffer, []
        self._write_api.write(
            bucket=self.config.influx_bucket,
            org=self.config.influx_org,
            record=batch,
        )
        self._last_flush = time.monotonic()
        logger.debug("Wrote %s points to Influx", len(batch))

    def on_message(self, _ws: WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if not isinstance(payload, dict):
            return
        self._buffer.extend(delta_to_points(payload, self.config.vessel_id))
        if len(self._buffer) >= self.config.batch_size:
            self.flush()
        elif time.monotonic() - self._last_flush >= self.config.flush_interval_s:
            self.flush()

    def on_error(self, _ws: WebSocketApp, error: Exception) -> None:
        logger.error("Signal K websocket error: %s", error)

    def on_close(self, _ws: WebSocketApp, status: int, msg: str) -> None:
        logger.warning("Signal K websocket closed: %s %s", status, msg)

    def on_open(self, _ws: WebSocketApp) -> None:
        logger.info("Connected to Signal K stream")

    def stop(self, *_args: object) -> None:
        self._running = False
        self.flush()
        if self._ws:
            self._ws.close()
        self._client.close()

    def run(self) -> None:
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        backoff = 2.0
        while self._running:
            self._ws = WebSocketApp(
                self.config.signalk_ws_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close,
            )
            try:
                self._ws.run_forever(ping_interval=20, ping_timeout=10)
            except Exception as exc:
                logger.error("Bridge loop error: %s", exc)
            self.flush()
            if not self._running:
                break
            logger.info("Reconnecting in %.0fs", backoff)
            time.sleep(backoff)
            backoff = min(backoff * 1.5, 60.0)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    try:
        config = BridgeConfig.from_env()
    except KeyError as exc:
        logger.error("Missing required environment variable: %s", exc)
        sys.exit(1)
    bridge = SignalKInfluxBridge(config)
    logger.info(
        "Starting bridge vessel=%s bucket=%s",
        config.vessel_id,
        config.influx_bucket,
    )
    bridge.run()


if __name__ == "__main__":
    main()

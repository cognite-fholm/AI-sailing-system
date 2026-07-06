"""Signal K REST + WebSocket helpers."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any

import requests
from websocket import WebSocketApp

from signalk_polar_performance.models import TelemetrySnapshot

logger = logging.getLogger(__name__)

PATH_STW = "navigation.speedThroughWater"
PATH_SOG = "navigation.speedOverGround"
PATH_TWS = "environment.wind.speedTrue"
PATH_TWA = "environment.wind.angleTrueWater"


class TelemetryCache:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot = TelemetrySnapshot()

    def update(self, path: str, value: float) -> None:
        with self._lock:
            if path == PATH_STW:
                self._snapshot.stw = value
            elif path == PATH_SOG:
                self._snapshot.sog = value
            elif path == PATH_TWS:
                self._snapshot.tws = value
            elif path == PATH_TWA:
                self._snapshot.twa = value

    def read(self) -> TelemetrySnapshot:
        with self._lock:
            return self._snapshot.model_copy()


class SignalKPublisher:
    def __init__(self, base_url: str, source_label: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.source_label = source_label
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def publish_performance(
        self,
        polar_speed: float,
        polar_speed_ratio: float,
        target_angle: float,
    ) -> None:
        payload = {
            "context": "vessels.self",
            "updates": [
                {
                    "source": {"label": self.source_label, "type": "signalk-polar-performance"},
                    "values": [
                        {"path": "performance.polarSpeed", "value": polar_speed},
                        {"path": "performance.polarSpeedRatio", "value": polar_speed_ratio},
                        {"path": "performance.targetAngle", "value": target_angle},
                    ],
                }
            ],
        }
        resp = self._session.put(
            f"{self.base_url}/signalk/v1/api/vessels/self",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()


def _extract_values(delta: dict[str, Any], cache: TelemetryCache) -> None:
    for update in delta.get("updates") or []:
        for item in update.get("values") or []:
            path = item.get("path")
            value = item.get("value")
            if path in {PATH_STW, PATH_SOG, PATH_TWS, PATH_TWA} and isinstance(value, (int, float)):
                cache.update(path, float(value))


class SignalKStream:
    def __init__(self, ws_url: str, cache: TelemetryCache) -> None:
        self.ws_url = ws_url
        self.cache = cache
        self._ws: WebSocketApp | None = None
        self._thread: threading.Thread | None = None
        self._running = False

    def _on_message(self, _ws: WebSocketApp, message: str) -> None:
        try:
            payload = json.loads(message)
        except json.JSONDecodeError:
            return
        if isinstance(payload, dict):
            _extract_values(payload, self.cache)

    def start(self) -> None:
        self._running = True
        self._ws = WebSocketApp(
            self.ws_url,
            on_message=self._on_message,
            on_error=lambda _ws, err: logger.error("SK stream error: %s", err),
            on_close=lambda _ws, *_: logger.warning("SK stream closed"),
            on_open=lambda _ws: logger.info("SK stream connected"),
        )
        self._thread = threading.Thread(
            target=lambda: self._ws.run_forever(ping_interval=20, ping_timeout=10),
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        if self._ws:
            self._ws.close()

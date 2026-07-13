"""Publish RaceExtensionDelta to one or more Signal K servers."""

from __future__ import annotations

import logging
from typing import Protocol

import requests

from expedition_bridge.signalk.models import RaceExtensionDelta

logger = logging.getLogger(__name__)


class SignalKPublisher(Protocol):
    def publish(self, delta: RaceExtensionDelta) -> None: ...


class HttpSignalKPublisher:
    def __init__(self, base_urls: list[str], *, timeout_s: float = 5.0) -> None:
        self._urls = [u.rstrip("/") for u in base_urls]
        self._timeout_s = timeout_s
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def publish(self, delta: RaceExtensionDelta) -> None:
        body = delta.to_signalk_json()
        for base in self._urls:
            url = f"{base}/signalk/v1/api/vessels/self"
            try:
                resp = self._session.put(url, json=body, timeout=self._timeout_s)
                resp.raise_for_status()
                logger.debug("Published %d paths to %s", len(delta.updates[0].values), base)
            except requests.RequestException as exc:
                logger.warning("Signal K publish failed for %s: %s", base, exc)


class CollectingSignalKPublisher:
    """Test double — records published deltas."""

    def __init__(self) -> None:
        self.deltas: list[RaceExtensionDelta] = []

    def publish(self, delta: RaceExtensionDelta) -> None:
        self.deltas.append(delta)

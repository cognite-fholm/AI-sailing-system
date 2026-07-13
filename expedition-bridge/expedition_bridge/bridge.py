"""Poll Expedition and federate to Signal K."""

from __future__ import annotations

import logging
import time

from expedition_bridge.config import BridgeSettings
from expedition_bridge.expedition.client import ExpeditionClient, create_expedition_client
from expedition_bridge.mapping import snapshot_to_delta
from expedition_bridge.signalk.models import RaceExtensionDelta
from expedition_bridge.signalk.publisher import HttpSignalKPublisher, SignalKPublisher

logger = logging.getLogger(__name__)


class ExpeditionBridge:
    def __init__(
        self,
        settings: BridgeSettings,
        *,
        expedition: ExpeditionClient | None = None,
        publisher: SignalKPublisher | None = None,
    ) -> None:
        self._settings = settings
        self._expedition = expedition or create_expedition_client(settings)
        self._publisher = publisher or HttpSignalKPublisher(settings.publish_urls())
        self._running = False

    def poll_once(self) -> RaceExtensionDelta:
        snapshot = self._expedition.poll_snapshot()
        delta = snapshot_to_delta(snapshot, source_label=self._settings.source_label)
        self._publisher.publish(delta)
        return delta

    def run(self) -> None:
        interval = 1.0 / self._settings.poll_hz
        self._running = True
        logger.info(
            "expedition-bridge started (poll_hz=%.2f, targets=%s)",
            self._settings.poll_hz,
            self._settings.publish_urls(),
        )
        while self._running:
            loop_start = time.perf_counter()
            try:
                self.poll_once()
            except Exception:
                logger.exception("Poll cycle failed")
            elapsed = time.perf_counter() - loop_start
            time.sleep(max(0.0, interval - elapsed))

    def stop(self) -> None:
        self._running = False


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    settings = BridgeSettings()
    ExpeditionBridge(settings).run()


if __name__ == "__main__":
    main()

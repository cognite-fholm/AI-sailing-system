"""Polar performance publish loop."""

from __future__ import annotations

import logging
import signal
import sys
import time

from signalk_polar_performance.config import PolarPerformanceSettings
from signalk_polar_performance.models import PublishResult
from signalk_polar_performance.polar_client import PolarManagerClient
from signalk_polar_performance.sk_client import SignalKPublisher, SignalKStream, TelemetryCache

logger = logging.getLogger(__name__)


def compute_once(
    settings: PolarPerformanceSettings,
    cache: TelemetryCache,
    polar: PolarManagerClient,
    publisher: SignalKPublisher,
) -> PublishResult | None:
    snap = cache.read()
    tws, twa = snap.tws, snap.twa
    actual = snap.stw if snap.stw is not None else snap.sog
    if tws is None or twa is None or actual is None:
        logger.debug("Waiting for telemetry tws=%s twa=%s speed=%s", tws, twa, actual)
        return None
    target = polar.fetch_target(tws, abs(twa))
    if target is None:
        return None
    ratio = actual / target.polar_speed if target.polar_speed > 0 else 0.0
    publisher.publish_performance(target.polar_speed, ratio, target.target_angle)
    return PublishResult(
        actual_speed=actual,
        target_bsp=target.polar_speed,
        ratio=ratio,
        target_angle=target.target_angle,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = PolarPerformanceSettings()
    cache = TelemetryCache()
    stream = SignalKStream(settings.signalk_ws_url, cache)
    polar = PolarManagerClient(settings.polar_manager_url, settings.vessel_id)
    publisher = SignalKPublisher(settings.signalk_url, settings.source_label)
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    stream.start()
    logger.info(
        "signalk-polar-performance signalk=%s polar=%s interval=%ss",
        settings.signalk_url,
        settings.polar_manager_url,
        settings.update_interval_s,
    )
    while running:
        try:
            result = compute_once(settings, cache, polar, publisher)
            if result:
                logger.info("Published performance: %s", result.model_dump())
        except Exception as exc:
            logger.error("Publish failed: %s", exc)
        time.sleep(settings.update_interval_s)
    stream.stop()


if __name__ == "__main__":
    main()
    sys.exit(0)

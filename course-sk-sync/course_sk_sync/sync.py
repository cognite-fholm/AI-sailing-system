"""Course sync loop."""

from __future__ import annotations

import logging
import signal
import sys
import time

from course_sk_sync.config import CourseSkSyncSettings, resolve_active
from course_sk_sync.loader import resolve_active_route
from course_sk_sync.models import SyncResult
from course_sk_sync.sk_client import SignalKClient

logger = logging.getLogger(__name__)


def run_once(settings: CourseSkSyncSettings) -> SyncResult | None:
    data_repo, active = resolve_active(settings)
    route, skipped = resolve_active_route(data_repo, active)
    if route is None:
        logger.warning("No active route with resolved waypoints")
        return None
    client = SignalKClient(settings.signalk_url, settings.source_label)
    if not client.health():
        raise RuntimeError(f"Signal K unreachable at {settings.signalk_url}")
    client.publish_route_points(route)
    return SyncResult(
        route_id=route.route_id,
        waypoints_pushed=len(route.waypoints),
        next_point=route.waypoints[1].name if len(route.waypoints) > 1 else route.waypoints[0].name,
        previous_point=route.waypoints[0].name if len(route.waypoints) > 1 else None,
        skipped_unresolved=skipped,
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    settings = CourseSkSyncSettings()
    running = True

    def stop(*_args: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    logger.info(
        "course-sk-sync signalk=%s interval=%ss",
        settings.signalk_url,
        settings.poll_interval_s,
    )
    while running:
        try:
            result = run_once(settings)
            if result:
                logger.info("Sync OK: %s", result.model_dump())
        except Exception as exc:
            logger.error("Sync failed: %s", exc)
        for _ in range(int(settings.poll_interval_s)):
            if not running:
                break
            time.sleep(1)


if __name__ == "__main__":
    main()
    sys.exit(0)

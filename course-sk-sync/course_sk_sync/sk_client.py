"""Signal K REST client for course updates."""

from __future__ import annotations

import logging
from typing import Any

import requests

from course_sk_sync.models import ActiveRoute, Waypoint

logger = logging.getLogger(__name__)


class SignalKClient:
    def __init__(self, base_url: str, source_label: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.source_label = source_label
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def health(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/signalk/v1/api/", timeout=5)
            return resp.status_code == 200
        except requests.RequestException as exc:
            logger.debug("Signal K health failed: %s", exc)
            return False

    def _put_delta(self, values: list[dict[str, Any]]) -> None:
        payload = {
            "context": "vessels.self",
            "updates": [
                {
                    "source": {"label": self.source_label, "type": "course-sk-sync"},
                    "values": values,
                }
            ],
        }
        resp = self._session.put(
            f"{self.base_url}/signalk/v1/api/vessels/self",
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()

    @staticmethod
    def _position_value(wp: Waypoint) -> dict[str, float]:
        return {"latitude": wp.lat, "longitude": wp.lon}

    def publish_course_leg(self, route: ActiveRoute, previous: Waypoint | None, nxt: Waypoint) -> None:
        values: list[dict[str, Any]] = [
            {"path": "navigation.course.activeRoute.name", "value": route.name},
            {"path": "navigation.course.activeRoute.href", "value": f"route:{route.route_id}"},
            {"path": "navigation.course.nextPoint.name", "value": nxt.name},
            {"path": "navigation.course.nextPoint.position", "value": self._position_value(nxt)},
            {"path": "navigation.course.nextPoint.type", "value": nxt.type},
        ]
        if previous:
            values.extend(
                [
                    {"path": "navigation.course.previousPoint.name", "value": previous.name},
                    {
                        "path": "navigation.course.previousPoint.position",
                        "value": self._position_value(previous),
                    },
                ]
            )
        self._put_delta(values)
        logger.info(
            "Published course leg route=%s prev=%s next=%s",
            route.route_id,
            previous.name if previous else None,
            nxt.name,
        )

    def publish_route_points(self, route: ActiveRoute) -> None:
        """Set first leg prev/next for course-provider; full route in metadata."""
        if len(route.waypoints) == 1:
            self.publish_course_leg(route, None, route.waypoints[0])
            return
        self.publish_course_leg(route, route.waypoints[0], route.waypoints[1])

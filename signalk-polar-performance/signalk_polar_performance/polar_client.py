"""Polar-manager HTTP client."""

from __future__ import annotations

import logging

import requests

from signalk_polar_performance.models import PerformanceDelta

logger = logging.getLogger(__name__)


class PolarManagerClient:
    def __init__(self, base_url: str, vessel_id: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.vessel_id = vessel_id
        self._session = requests.Session()

    def fetch_target(self, tws: float, twa: float) -> PerformanceDelta | None:
        try:
            resp = self._session.get(
                f"{self.base_url}/polars/{self.vessel_id}/target",
                params={"tws": tws, "twa": twa},
                timeout=3,
            )
            if resp.status_code != 200:
                logger.warning("polar-manager returned %s: %s", resp.status_code, resp.text[:200])
                return None
            data = resp.json()
            target_bsp = float(data["target_bsp"])
            upwind = float(data.get("target_angle_upwind") or 45)
            downwind = float(data.get("target_angle_downwind") or 150)
            target_angle = upwind if twa < 90 else downwind
            return PerformanceDelta(
                polar_speed=target_bsp,
                polar_speed_ratio=0.0,
                target_angle=target_angle,
            )
        except requests.RequestException as exc:
            logger.warning("polar-manager unreachable: %s", exc)
            return None

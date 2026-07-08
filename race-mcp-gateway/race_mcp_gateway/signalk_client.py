"""Read-only Signal K REST client — aligned with signalk-mcp-server tool contracts."""

from __future__ import annotations

import json
import math
import urllib.error
import urllib.request
from typing import Any


class SignalKClient:
    def __init__(self, base_url: str, *, timeout_s: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s

    def _get_json(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data if isinstance(data, dict) else {"value": data}
        except (urllib.error.URLError, OSError, TimeoutError) as exc:
            return {"error": str(exc), "url": url}

    def get_initial_context(self) -> dict[str, Any]:
        root = self._get_json("/signalk/v1/api/")
        vessels = self._get_json("/signalk/v1/api/vessels")
        return {
            "server": root,
            "vessel_keys": list(vessels.keys()) if isinstance(vessels, dict) else [],
            "ecosystem": "signalk-mcp-server compatible (HTTP gateway)",
        }

    def get_vessel_state(self, vessel: str = "self") -> dict[str, Any]:
        return self._get_json(f"/signalk/v1/api/vessels/{vessel}")

    def list_available_paths(self, vessel: str = "self") -> list[str]:
        state = self.get_vessel_state(vessel)
        paths: list[str] = []

        def walk(prefix: str, node: Any) -> None:
            if not isinstance(node, dict):
                return
            if "value" in node and len(node) <= 3:
                paths.append(prefix)
                return
            for key, child in node.items():
                if key.startswith("_"):
                    continue
                child_prefix = f"{prefix}.{key}" if prefix else key
                walk(child_prefix, child)

        walk("", state)
        return sorted(paths)[:500]

    def get_path_value(self, path: str, vessel: str = "self") -> Any:
        node: Any = self.get_vessel_state(vessel)
        for part in path.split("."):
            if not isinstance(node, dict):
                return None
            node = node.get(part)
        if isinstance(node, dict) and "value" in node:
            return node.get("value")
        return node

    def get_ais_targets(self, *, max_distance_m: float | None = None) -> dict[str, Any]:
        state = self.get_vessel_state("self")
        own_lat, own_lon = _position_from_state(state)
        targets = _ais_targets_from_state(state)
        if own_lat is not None and own_lon is not None:
            for target in targets:
                lat = target.get("lat")
                lon = target.get("lon")
                if lat is not None and lon is not None:
                    target["distance_meters"] = round(_haversine_m(own_lat, own_lon, lat, lon), 1)
            targets.sort(key=lambda t: t.get("distance_meters") or 1e9)
        if max_distance_m is not None:
            targets = [t for t in targets if (t.get("distance_meters") or 0) <= max_distance_m]
        return {"count": len(targets), "targets": targets}

    def get_active_alarms(self) -> dict[str, Any]:
        notifications = self._get_json("/signalk/v1/api/notifications")
        alarms: list[dict[str, Any]] = []
        if isinstance(notifications, dict):
            for key, item in notifications.items():
                if isinstance(item, dict):
                    alarms.append({"id": key, **item})
        return {"alarms": alarms, "count": len(alarms)}


def _position_from_state(state: dict[str, Any]) -> tuple[float | None, float | None]:
    nav = state.get("navigation", {}) if isinstance(state, dict) else {}
    pos = nav.get("position", {}) if isinstance(nav, dict) else {}
    value = pos.get("value") if isinstance(pos, dict) else None
    if isinstance(value, dict):
        return value.get("latitude"), value.get("longitude")
    return None, None


def _ais_targets_from_state(state: dict[str, Any]) -> list[dict[str, Any]]:
    sensors = state.get("sensors", {}) if isinstance(state, dict) else {}
    ais = sensors.get("ais", {}) if isinstance(sensors, dict) else {}
    targets_node = ais.get("targets", {}) if isinstance(ais, dict) else {}
    out: list[dict[str, Any]] = []
    if not isinstance(targets_node, dict):
        return out
    for mmsi, body in targets_node.items():
        if not isinstance(body, dict):
            continue
        entry: dict[str, Any] = {"mmsi": mmsi}
        for field, node in body.items():
            if isinstance(node, dict) and "value" in node:
                val = node["value"]
                if field in ("latitude", "longitude", "lat", "lon"):
                    entry[field if field != "latitude" else "lat"] = val
                    if field == "longitude":
                        entry["lon"] = val
                elif field in ("speedOverGround", "sog", "speed"):
                    entry["sog"] = val
                elif field in ("courseOverGroundTrue", "cog", "course"):
                    entry["cog"] = val
                elif field == "name":
                    entry["name"] = val
        out.append(entry)
    return out


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

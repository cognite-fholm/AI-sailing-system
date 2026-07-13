"""Expedition client protocol and implementations."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from expedition_bridge.config import BridgeSettings
from expedition_bridge.expedition.models import (
    ExpeditionBoatPositionCommand,
    ExpeditionMeta,
    ExpeditionMobCommand,
    ExpeditionSnapshot,
    ExpeditionUserChannelCommand,
    GeoPosition,
)
from expedition_bridge.expedition.reader import build_snapshot_from_vars


@runtime_checkable
class ExpeditionClient(Protocol):
    """Testable boundary over Expedition-Python / ExpDLL."""

    def poll_snapshot(self) -> ExpeditionSnapshot: ...

    def set_mob(self, command: ExpeditionMobCommand) -> None: ...

    def set_boat_position(self, command: ExpeditionBoatPositionCommand) -> None: ...

    def set_user_channel(self, command: ExpeditionUserChannelCommand) -> None: ...


class MockExpeditionClient:
    """Deterministic client for CI and laptop dev without ExpDLL."""

    def __init__(self, snapshot: ExpeditionSnapshot | None = None) -> None:
        self._snapshot = snapshot or ExpeditionSnapshot(
            meta=ExpeditionMeta(connected=True, api_version="mock"),
        )

    def poll_snapshot(self) -> ExpeditionSnapshot:
        snap = self._snapshot.model_copy(deep=True)
        snap.meta.connected = True
        snap.meta.api_version = "mock"
        snap.meta.last_poll_at = datetime.now(timezone.utc)
        return snap

    def set_mob(self, command: ExpeditionMobCommand) -> None:
        return None

    def set_boat_position(self, command: ExpeditionBoatPositionCommand) -> None:
        return None

    def set_user_channel(self, command: ExpeditionUserChannelCommand) -> None:
        return None


class WindowsExpeditionClient:
    """Wraps Expedition-Python ExpDLL on Windows with Expedition running."""

    def __init__(self, settings: BridgeSettings) -> None:
        self._settings = settings
        try:
            from Expedition import ExpeditionDLL  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "Expedition-Python not installed. pip install Expedition-Python on Windows."
            ) from exc

        self._dll = ExpeditionDLL.from_default_location()
        self._boat = 0

    def poll_snapshot(self) -> ExpeditionSnapshot:
        t0 = time.perf_counter()
        try:
            from Expedition.enums import SysVar, Var  # type: ignore[import-untyped]

            var_values: dict[str, float | None] = {}
            sys_values: dict[str, float | None] = {}

            for name in _VAR_NAMES:
                var_values[name] = self._dll.get_exp_var_value(getattr(Var, name), self._boat)

            for name in _SYS_VAR_NAMES:
                sys_values[name] = self._dll.get_sys_var(getattr(SysVar, name))

            port_lat = var_values.get("StartPortEndLat")
            port_lon = var_values.get("StartPortEndLon")
            stbd_lat = var_values.get("StartStrbEndLat")
            stbd_lon = var_values.get("StartStrbEndLon")

            port_end = None
            if port_lat is not None and port_lon is not None:
                port_end = GeoPosition(latitude=port_lat, longitude=port_lon)
            starboard_end = None
            if stbd_lat is not None and stbd_lon is not None:
                starboard_end = GeoPosition(latitude=stbd_lat, longitude=stbd_lon)

            snap = build_snapshot_from_vars(
                var_values,
                sys_values,
                api_version=getattr(self._dll, "api_version", "unknown"),
                port_end=port_end,
                starboard_end=starboard_end,
                knots_to_mps=self._settings.knots_to_mps,
            )
            snap.meta.poll_duration_ms = (time.perf_counter() - t0) * 1000
            snap.meta.connected = True
            return snap
        except Exception:
            return ExpeditionSnapshot(
                meta=ExpeditionMeta(
                    connected=False,
                    poll_duration_ms=(time.perf_counter() - t0) * 1000,
                ),
            )

    def set_mob(self, command: ExpeditionMobCommand) -> None:
        self._dll.set_mob(command.latitude, command.longitude)

    def set_boat_position(self, command: ExpeditionBoatPositionCommand) -> None:
        self._dll.set_boat_position(
            command.boat_index,
            (command.position.latitude, command.position.longitude),
        )

    def set_user_channel(self, command: ExpeditionUserChannelCommand) -> None:
        from Expedition.enums import Var  # type: ignore[import-untyped]

        user_var = Var[f"User{command.channel}"]
        self._dll.set_exp_var_value(user_var, command.value, self._boat)


_VAR_NAMES = [
    "StartDistToLine",
    "StartTimeToLine",
    "StartTimeToBurn",
    "StartTimeToGun",
    "StartLineBiasDeg",
    "StartLineBiasLen",
    "StartTimeToPort",
    "StartTimeToStrb",
    "StartTimeToPortBurn",
    "StartTimeToStrbBurn",
    "StartPortEndLat",
    "StartPortEndLon",
    "StartStrbEndLat",
    "StartStrbEndLon",
    "LayDist",
    "LayTime",
    "LayBear",
    "LayDistOnPort",
    "LayTimeOnPort",
    "LayPortBear",
    "LayDistOnStrb",
    "LayTimeOnStrb",
    "LayStrbBear",
    "MarkBrg",
    "MarkRng",
    "NextMarkBrg",
    "NextMarkRng",
    "NextMarkTimeOnPort",
    "NextMarkTimeOnStrb",
    "TargTwa",
    "TargBsp",
    "TargVmg",
    "PolarBsp",
    "PolarBspPercent",
    "HeadingToSteer",
    "SailNow",
    "SailMark",
    "SailNext",
    "PredTwd",
    "PredTws",
    "PredSet",
    "PredDrift",
    "OptVmc",
    "OptVmcHdg",
    "OptVmcTwa",
    "WaveSigHeight",
    "WaveSigPeriod",
]

_SYS_VAR_NAMES = [
    "StartDistToPort",
    "StartDistToStrb",
]


def create_expedition_client(settings: BridgeSettings) -> ExpeditionClient:
    if settings.expedition_mock:
        return MockExpeditionClient()
    return WindowsExpeditionClient(settings)

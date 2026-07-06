"""Pydantic models for signalk-polar-performance."""

from __future__ import annotations

from pydantic import BaseModel


class TelemetrySnapshot(BaseModel):
    stw: float | None = None
    sog: float | None = None
    tws: float | None = None
    twa: float | None = None


class PerformanceDelta(BaseModel):
    polar_speed: float
    polar_speed_ratio: float
    target_angle: float


class PublishResult(BaseModel):
    actual_speed: float
    target_bsp: float
    ratio: float
    target_angle: float

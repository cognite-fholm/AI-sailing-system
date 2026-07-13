"""Grouped Expedition state — Pydantic models over ExpDLL Var channels."""

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class GeoPosition(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ExpeditionStartLine(BaseModel):
    dist_to_line_m: float | None = None
    time_to_line_s: float | None = None
    time_to_burn_s: float | None = None
    time_to_gun_s: float | None = None
    bias_angle_deg: float | None = None
    bias_boat_lengths: float | None = None
    time_to_port_s: float | None = None
    time_to_starboard_s: float | None = None
    burn_port_s: float | None = None
    burn_starboard_s: float | None = None
    dist_to_port_m: float | None = None
    dist_to_starboard_m: float | None = None
    port_end: GeoPosition | None = None
    starboard_end: GeoPosition | None = None


class ExpeditionLaylines(BaseModel):
    distance_m: float | None = None
    time_s: float | None = None
    bearing_deg: float | None = None
    port_distance_m: float | None = None
    port_time_s: float | None = None
    port_bearing_deg: float | None = None
    starboard_distance_m: float | None = None
    starboard_time_s: float | None = None
    starboard_bearing_deg: float | None = None
    mark_bearing_deg: float | None = None
    mark_distance_m: float | None = None
    next_mark_bearing_deg: float | None = None
    next_mark_distance_m: float | None = None
    next_mark_time_on_port_s: float | None = None
    next_mark_time_on_starboard_s: float | None = None


class ExpeditionTargets(BaseModel):
    target_twa_deg: float | None = None
    target_bsp_mps: float | None = None
    target_vmg_mps: float | None = None
    polar_bsp_mps: float | None = None
    polar_performance_ratio: float | None = None
    heading_to_steer_deg: float | None = None
    sail_now: str | None = None
    sail_at_mark: str | None = None
    sail_next_leg: str | None = None


class ExpeditionRouting(BaseModel):
    predicted_twd_deg: float | None = None
    predicted_tws_mps: float | None = None
    predicted_set_deg: float | None = None
    predicted_drift_mps: float | None = None
    optimal_vmc_mps: float | None = None
    optimal_heading_deg: float | None = None
    optimal_twa_deg: float | None = None
    wave_significant_height_m: float | None = None
    wave_significant_period_s: float | None = None


class ExpeditionMeta(BaseModel):
    connected: bool = False
    api_version: str = "unknown"
    last_poll_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    poll_duration_ms: float | None = None


class ExpeditionSnapshot(BaseModel):
    """Semantic snapshot read from Expedition ExpDLL (boat index 0 = own ship)."""

    start: ExpeditionStartLine = Field(default_factory=ExpeditionStartLine)
    laylines: ExpeditionLaylines = Field(default_factory=ExpeditionLaylines)
    targets: ExpeditionTargets = Field(default_factory=ExpeditionTargets)
    routing: ExpeditionRouting = Field(default_factory=ExpeditionRouting)
    meta: ExpeditionMeta = Field(default_factory=ExpeditionMeta)


class ExpeditionMobCommand(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ExpeditionBoatPositionCommand(BaseModel):
    boat_index: int = Field(ge=1, description="Own ship is 0 — use ≥1 for competitors")
    position: GeoPosition


class ExpeditionUserChannelCommand(BaseModel):
    channel: int = Field(ge=0, le=31, description="User0–User31")
    value: float

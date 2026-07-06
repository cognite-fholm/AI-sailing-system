"""Pydantic models for course-sk-sync."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    seq: int
    name: str
    lat: float
    lon: float
    type: str = "mark"
    rounding: str | None = None


class ActiveRoute(BaseModel):
    race_id: str
    route_id: str
    name: str
    waypoints: list[Waypoint]


class DataRepoActive(BaseModel):
    regatta_id: str | None = None
    race_path: str | None = None
    own_boat_path: str | None = None
    active_certificate_ref: str | None = None
    certificate_year: int | None = None
    active_route_id: str | None = Field(
        default=None,
        description="Route section id e.g. 11.1; defaults to first resolved route file",
    )


class DataRepoConfig(BaseModel):
    data_repo: dict[str, str]
    active: DataRepoActive


class SyncResult(BaseModel):
    route_id: str
    waypoints_pushed: int
    next_point: str | None = None
    previous_point: str | None = None
    skipped_unresolved: int = 0

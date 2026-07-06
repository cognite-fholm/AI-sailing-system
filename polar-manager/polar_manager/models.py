"""Pydantic models for polar-manager."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PolarPoint(BaseModel):
    twa: float
    bsp: float


class PolarRow(BaseModel):
    tws: float
    points: list[PolarPoint]


class PolarGrid(BaseModel):
    vessel_id: str
    certificate_ref: str
    source_file: str
    rows: list[PolarRow]


class TargetResponse(BaseModel):
    vessel_id: str
    tws: float
    twa: float
    target_bsp: float
    target_angle_upwind: float | None = None
    target_angle_downwind: float | None = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "polar-manager"
    polar_loaded: bool = False
    vessel_id: str | None = None


class DataRepoActive(BaseModel):
    own_boat_path: str | None = None
    active_certificate_ref: str | None = None
    certificate_year: int | None = None


class DataRepoConfig(BaseModel):
    data_repo: dict[str, str]
    active: DataRepoActive

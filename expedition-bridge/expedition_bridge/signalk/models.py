"""Signal K race extension — Pydantic delta models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SignalKSource(BaseModel):
    label: str
    type: str = "expedition-bridge"


class SignalKPathUpdate(BaseModel):
    path: str = Field(min_length=1)
    value: float | int | str | bool | dict[str, Any]


class SignalKDeltaUpdate(BaseModel):
    source: SignalKSource
    timestamp: datetime
    values: list[SignalKPathUpdate] = Field(min_length=1)


class RaceExtensionDelta(BaseModel):
    """Validated PUT body for /signalk/v1/api/vessels/self."""

    context: Literal["vessels.self"] = "vessels.self"
    updates: list[SignalKDeltaUpdate] = Field(min_length=1)

    def to_signalk_json(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

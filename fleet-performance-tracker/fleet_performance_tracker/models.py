"""Fleet performance point model — matches spec §7.22.3."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FleetPerformancePoint:
    race_id: str
    sail_number: str
    mmsi: str = ""
    vessel_name: str = ""
    is_own: bool = False
    leg_seq: int = 0
    route_id: str = ""
    lat: float = 0.0
    lon: float = 0.0
    sog: float = 0.0
    bsp: float | None = None
    tws: float = 0.0
    twa: float = 0.0
    cog: float = 0.0
    bsp_target: float = 0.0
    vmg_target: float = 0.0
    vmg_actual: float = 0.0
    performance_pct: float = 0.0
    vmg_pct: float = 0.0
    handicap_value: float = 1.0
    course_pct: float = 0.0
    rank: int | None = None
    polar_source: str = "slk"
    polar_quality: str = "high"
    data_quality: str = "ok"

    def to_influx_fields(self) -> dict[str, float]:
        fields: dict[str, float] = {
            "lat": self.lat,
            "lon": self.lon,
            "sog": self.sog,
            "tws": self.tws,
            "twa": self.twa,
            "cog": self.cog,
            "bsp_target": self.bsp_target,
            "vmg_target": self.vmg_target,
            "vmg_actual": self.vmg_actual,
            "performance_pct": self.performance_pct,
            "vmg_pct": self.vmg_pct,
            "handicap_value": self.handicap_value,
            "course_pct": self.course_pct,
        }
        if self.bsp is not None:
            fields["bsp"] = self.bsp
        if self.rank is not None:
            fields["rank"] = float(self.rank)
        return fields

    def to_influx_tags(self) -> dict[str, str]:
        return {
            "race_id": self.race_id,
            "mmsi": self.mmsi or self.sail_number,
            "sail_number": self.sail_number,
            "vessel_name": self.vessel_name,
            "is_own": "true" if self.is_own else "false",
            "leg_seq": str(self.leg_seq),
            "route_id": self.route_id,
            "polar_source": self.polar_source,
            "polar_quality": self.polar_quality,
            "data_quality": self.data_quality,
        }

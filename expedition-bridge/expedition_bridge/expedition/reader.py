"""Map raw ExpDLL floats into ExpeditionSnapshot."""

from __future__ import annotations

from datetime import datetime, timezone

from expedition_bridge.expedition.models import (
    ExpeditionLaylines,
    ExpeditionMeta,
    ExpeditionRouting,
    ExpeditionSnapshot,
    ExpeditionStartLine,
    ExpeditionTargets,
    GeoPosition,
)


def _knots_to_mps(knots: float | None, factor: float) -> float | None:
    if knots is None:
        return None
    return knots * factor


def _ratio_from_percent(pct: float | None) -> float | None:
    if pct is None:
        return None
    return pct / 100.0


def _str_val(raw: float | None) -> str | None:
    if raw is None:
        return None
    return str(int(raw)) if raw == int(raw) else str(raw)


def build_snapshot_from_vars(
    var: dict[str, float | None],
    sys_var: dict[str, float | None],
    *,
    api_version: str,
    port_end: GeoPosition | None,
    starboard_end: GeoPosition | None,
    knots_to_mps: float,
) -> ExpeditionSnapshot:
    return ExpeditionSnapshot(
        start=ExpeditionStartLine(
            dist_to_line_m=var.get("StartDistToLine"),
            time_to_line_s=var.get("StartTimeToLine"),
            time_to_burn_s=var.get("StartTimeToBurn"),
            time_to_gun_s=var.get("StartTimeToGun"),
            bias_angle_deg=var.get("StartLineBiasDeg"),
            bias_boat_lengths=var.get("StartLineBiasLen"),
            time_to_port_s=var.get("StartTimeToPort"),
            time_to_starboard_s=var.get("StartTimeToStrb"),
            burn_port_s=var.get("StartTimeToPortBurn"),
            burn_starboard_s=var.get("StartTimeToStrbBurn"),
            dist_to_port_m=sys_var.get("StartDistToPort"),
            dist_to_starboard_m=sys_var.get("StartDistToStrb"),
            port_end=port_end,
            starboard_end=starboard_end,
        ),
        laylines=ExpeditionLaylines(
            distance_m=var.get("LayDist"),
            time_s=var.get("LayTime"),
            bearing_deg=var.get("LayBear"),
            port_distance_m=var.get("LayDistOnPort"),
            port_time_s=var.get("LayTimeOnPort"),
            port_bearing_deg=var.get("LayPortBear"),
            starboard_distance_m=var.get("LayDistOnStrb"),
            starboard_time_s=var.get("LayTimeOnStrb"),
            starboard_bearing_deg=var.get("LayStrbBear"),
            mark_bearing_deg=var.get("MarkBrg"),
            mark_distance_m=var.get("MarkRng"),
            next_mark_bearing_deg=var.get("NextMarkBrg"),
            next_mark_distance_m=var.get("NextMarkRng"),
            next_mark_time_on_port_s=var.get("NextMarkTimeOnPort"),
            next_mark_time_on_starboard_s=var.get("NextMarkTimeOnStrb"),
        ),
        targets=ExpeditionTargets(
            target_twa_deg=var.get("TargTwa"),
            target_bsp_mps=_knots_to_mps(var.get("TargBsp"), knots_to_mps),
            target_vmg_mps=_knots_to_mps(var.get("TargVmg"), knots_to_mps),
            polar_bsp_mps=_knots_to_mps(var.get("PolarBsp"), knots_to_mps),
            polar_performance_ratio=_ratio_from_percent(var.get("PolarBspPercent")),
            heading_to_steer_deg=var.get("HeadingToSteer"),
            sail_now=_str_val(var.get("SailNow")),
            sail_at_mark=_str_val(var.get("SailMark")),
            sail_next_leg=_str_val(var.get("SailNext")),
        ),
        routing=ExpeditionRouting(
            predicted_twd_deg=var.get("PredTwd"),
            predicted_tws_mps=_knots_to_mps(var.get("PredTws"), knots_to_mps),
            predicted_set_deg=var.get("PredSet"),
            predicted_drift_mps=_knots_to_mps(var.get("PredDrift"), knots_to_mps),
            optimal_vmc_mps=_knots_to_mps(var.get("OptVmc"), knots_to_mps),
            optimal_heading_deg=var.get("OptVmcHdg"),
            optimal_twa_deg=var.get("OptVmcTwa"),
            wave_significant_height_m=var.get("WaveSigHeight"),
            wave_significant_period_s=var.get("WaveSigPeriod"),
        ),
        meta=ExpeditionMeta(
            connected=True,
            api_version=api_version,
            last_poll_at=datetime.now(timezone.utc),
        ),
    )

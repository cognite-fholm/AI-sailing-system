"""ExpeditionSnapshot → race.expedition.* Signal K paths."""

from __future__ import annotations

from expedition_bridge.expedition.models import ExpeditionSnapshot, GeoPosition
from expedition_bridge.signalk.models import (
    RaceExtensionDelta,
    SignalKDeltaUpdate,
    SignalKPathUpdate,
    SignalKSource,
)


def _f(path: str, value: float | int | str | bool | None) -> SignalKPathUpdate | None:
    if value is None:
        return None
    return SignalKPathUpdate(path=path, value=value)


def _pos(path: str, position: GeoPosition | None) -> SignalKPathUpdate | None:
    if position is None:
        return None
    return SignalKPathUpdate(
        path=path,
        value={
            "latitude": position.latitude,
            "longitude": position.longitude,
        },
    )


def snapshot_to_delta(snapshot: ExpeditionSnapshot, *, source_label: str) -> RaceExtensionDelta:
    s = snapshot.start
    ll = snapshot.laylines
    t = snapshot.targets
    r = snapshot.routing
    m = snapshot.meta

    values: list[SignalKPathUpdate] = []
    for item in (
        _f("race.expedition.start.distToLine", s.dist_to_line_m),
        _f("race.expedition.start.timeToLine", s.time_to_line_s),
        _f("race.expedition.start.timeToBurn", s.time_to_burn_s),
        _f("race.expedition.start.timeToGun", s.time_to_gun_s),
        _f("race.expedition.start.biasAngle", s.bias_angle_deg),
        _f("race.expedition.start.biasBoatLengths", s.bias_boat_lengths),
        _f("race.expedition.start.timeToPort", s.time_to_port_s),
        _f("race.expedition.start.timeToStarboard", s.time_to_starboard_s),
        _f("race.expedition.start.burnPort", s.burn_port_s),
        _f("race.expedition.start.burnStarboard", s.burn_starboard_s),
        _f("race.expedition.start.distToPort", s.dist_to_port_m),
        _f("race.expedition.start.distToStarboard", s.dist_to_starboard_m),
        _pos("race.expedition.start.portEnd.position", s.port_end),
        _pos("race.expedition.start.starboardEnd.position", s.starboard_end),
        _f("race.expedition.laylines.distance", ll.distance_m),
        _f("race.expedition.laylines.time", ll.time_s),
        _f("race.expedition.laylines.bearing", ll.bearing_deg),
        _f("race.expedition.laylines.port.distance", ll.port_distance_m),
        _f("race.expedition.laylines.port.time", ll.port_time_s),
        _f("race.expedition.laylines.port.bearing", ll.port_bearing_deg),
        _f("race.expedition.laylines.starboard.distance", ll.starboard_distance_m),
        _f("race.expedition.laylines.starboard.time", ll.starboard_time_s),
        _f("race.expedition.laylines.starboard.bearing", ll.starboard_bearing_deg),
        _f("race.expedition.laylines.mark.bearing", ll.mark_bearing_deg),
        _f("race.expedition.laylines.mark.distance", ll.mark_distance_m),
        _f("race.expedition.laylines.nextMark.bearing", ll.next_mark_bearing_deg),
        _f("race.expedition.laylines.nextMark.distance", ll.next_mark_distance_m),
        _f("race.expedition.laylines.nextMark.timeOnPort", ll.next_mark_time_on_port_s),
        _f("race.expedition.laylines.nextMark.timeOnStarboard", ll.next_mark_time_on_starboard_s),
        _f("race.expedition.targets.trueWindAngle", t.target_twa_deg),
        _f("race.expedition.targets.boatSpeed", t.target_bsp_mps),
        _f("race.expedition.targets.vmg", t.target_vmg_mps),
        _f("race.expedition.targets.polarBoatSpeed", t.polar_bsp_mps),
        _f("race.expedition.targets.polarPerformanceRatio", t.polar_performance_ratio),
        _f("race.expedition.targets.headingToSteer", t.heading_to_steer_deg),
        _f("race.expedition.targets.sailNow", t.sail_now),
        _f("race.expedition.targets.sailAtMark", t.sail_at_mark),
        _f("race.expedition.targets.sailNextLeg", t.sail_next_leg),
        _f("race.expedition.routing.predicted.trueWindDirection", r.predicted_twd_deg),
        _f("race.expedition.routing.predicted.trueWindSpeed", r.predicted_tws_mps),
        _f("race.expedition.routing.predicted.set", r.predicted_set_deg),
        _f("race.expedition.routing.predicted.drift", r.predicted_drift_mps),
        _f("race.expedition.routing.optimal.vmc", r.optimal_vmc_mps),
        _f("race.expedition.routing.optimal.heading", r.optimal_heading_deg),
        _f("race.expedition.routing.optimal.trueWindAngle", r.optimal_twa_deg),
        _f("race.expedition.routing.wave.significantHeight", r.wave_significant_height_m),
        _f("race.expedition.routing.wave.significantPeriod", r.wave_significant_period_s),
        _f("race.expedition.meta.connected", m.connected),
        _f("race.expedition.meta.apiVersion", m.api_version),
        _f("race.expedition.meta.lastPollAt", m.last_poll_at.isoformat()),
        _f("race.expedition.meta.pollDurationMs", m.poll_duration_ms),
    ):
        if item is not None:
            values.append(item)

    if not values:
        values.append(SignalKPathUpdate(path="race.expedition.meta.connected", value=False))

    return RaceExtensionDelta(
        updates=[
            SignalKDeltaUpdate(
                source=SignalKSource(label=source_label, type=source_label),
                timestamp=m.last_poll_at,
                values=values,
            )
        ]
    )

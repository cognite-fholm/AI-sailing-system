"""Unit tests for signalk-polar-performance models and ratio logic."""

from __future__ import annotations

import pytest

from signalk_polar_performance.models import PerformanceDelta, PublishResult, TelemetrySnapshot


def test_telemetry_snapshot_defaults() -> None:
    snap = TelemetrySnapshot()
    assert snap.stw is None
    assert snap.tws is None


def test_publish_result_ratio() -> None:
    result = PublishResult(
        actual_speed=7.0,
        target_bsp=7.26,
        ratio=7.0 / 7.26,
        target_angle=38.92,
    )
    assert result.ratio == pytest.approx(0.964, abs=0.01)


def test_performance_delta_fields() -> None:
    delta = PerformanceDelta(polar_speed=7.26, polar_speed_ratio=0.0, target_angle=52.0)
    assert delta.polar_speed == 7.26

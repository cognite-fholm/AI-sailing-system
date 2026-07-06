"""Unit tests for course-sk-sync route loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from course_sk_sync.loader import load_route_file, resolve_active_route
from course_sk_sync.models import DataRepoActive


def test_load_route_skips_null_coordinates(tmp_path: Path) -> None:
    route_file = tmp_path / "test-route.yaml"
    route_file.write_text(
        """
kind: WaypointList
metadata:
  race_id: test-race
  route_id: "1.1"
spec:
  name: Test
  section: "1.1"
  waypoints:
    - seq: 1
      name: Start
      lat: null
      lon: null
    - seq: 2
      name: Mark A
      lat: 59.9
      lon: 10.6
    - seq: 3
      name: Mark B
      lat: 59.8
      lon: 10.5
""",
        encoding="utf-8",
    )
    route = load_route_file(route_file)
    assert route is not None
    assert route.route_id == "1.1"
    assert len(route.waypoints) == 2
    assert route.waypoints[0].name == "Mark A"


def test_resolve_active_route_from_data_repo(data_repo_root: Path | None) -> None:
    if data_repo_root is None:
        pytest.skip("AI-sailing-data not available")
    active = DataRepoActive(
        race_path="races/2026/2026-06-faerderseilasen",
        active_route_id="11.1",
    )
    route, _skipped = resolve_active_route(data_repo_root, active)
    assert route is not None
    assert route.route_id == "11.1"
    assert len(route.waypoints) >= 2

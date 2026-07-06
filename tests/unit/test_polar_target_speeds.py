"""Unit tests for polar-manager target-speeds parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from polar_manager.target_speeds import parse_target_speeds, target_at


def test_parse_target_speeds_row_count(polar_target_speeds_file: Path) -> None:
    grid = parse_target_speeds(polar_target_speeds_file, "own-boat", "cert-test")
    assert len(grid.rows) >= 7


def test_target_at_known_orc_point(polar_target_speeds_file: Path) -> None:
    grid = parse_target_speeds(polar_target_speeds_file, "own-boat", "cert-test")
    result = target_at(grid, 10.0, 52.0)
    assert result.target_bsp == pytest.approx(7.26, abs=0.05)
    assert result.target_angle_upwind is not None
    assert 30 < result.target_angle_upwind < 50


def test_target_at_interpolates_tws(polar_target_speeds_file: Path) -> None:
    grid = parse_target_speeds(polar_target_speeds_file, "own-boat", "cert-test")
    low = target_at(grid, 9.0, 90.0).target_bsp
    high = target_at(grid, 11.0, 90.0).target_bsp
    mid = target_at(grid, 10.0, 90.0).target_bsp
    assert low < mid < high or high < mid < low


def test_target_at_normalizes_twa(polar_target_speeds_file: Path) -> None:
    grid = parse_target_speeds(polar_target_speeds_file, "own-boat", "cert-test")
    port = target_at(grid, 10.0, 52.0).target_bsp
    starboard = target_at(grid, 10.0, 308.0).target_bsp
    assert port == pytest.approx(starboard, abs=0.01)

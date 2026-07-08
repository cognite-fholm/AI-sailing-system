"""Fixtures for unit tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]

for _pkg in (
    "course-sk-sync",
    "polar-manager",
    "signalk-polar-performance",
    "signalk-influx-bridge",
    "race-import",
    "live-results",
    "fleet-performance-tracker",
    "race-live-sync",
    "ais-collector",
    "grib-model-scorer",
    "race-mcp-gateway",
):
    _path = REPO_ROOT / _pkg
    if _path.is_dir() and str(_path) not in sys.path:
        sys.path.insert(0, str(_path))


@pytest.fixture(scope="session")
def repo_root() -> Path:
    return REPO_ROOT


@pytest.fixture(scope="session")
def data_repo_root() -> Path | None:
    env = os.environ.get("AI_SAILING_DATA_ROOT")
    if env:
        path = Path(env)
        return path if path.is_dir() else None
    sibling = REPO_ROOT.parent / "AI-sailing-data"
    return sibling if sibling.is_dir() else None


@pytest.fixture(scope="session")
def polar_target_speeds_file(data_repo_root: Path | None) -> Path:
    if data_repo_root is None:
        pytest.skip("AI-sailing-data not available")
    path = (
        data_repo_root
        / "boats/NOR-10133/2024/certificates/international-034400038T6/assets/7710-target-speeds.txt"
    )
    if not path.is_file():
        pytest.skip(f"Polar sample missing: {path}")
    return path

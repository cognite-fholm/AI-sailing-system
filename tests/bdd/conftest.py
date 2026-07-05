"""Shared fixtures for BDD acceptance tests."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest_plugins = ["tests.bdd.steps.shared_steps"]

REPO_ROOT = Path(__file__).resolve().parents[2]
FEATURES_DIR = Path(__file__).resolve().parent / "features"


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


def pytest_configure(config: pytest.Config) -> None:
    for phase in (
        "phase_00",
        "phase_01",
        "phase_02a",
        "phase_02b",
        "phase_02c",
        "phase_02d",
        "phase_02e",
        "phase_02f",
        "phase_02g",
        "phase_03",
        "phase_04",
        "phase_05",
    ):
        config.addinivalue_line("markers", f"{phase}: implementation phase acceptance tests")
    config.addinivalue_line("markers", "wip: not yet implemented — skipped in CI until phase ships")


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-wip",
        action="store_true",
        default=False,
        help="Run scenarios tagged @wip (live integration)",
    )


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    if config.getoption("--run-wip"):
        return
    skip_wip = pytest.mark.skip(reason="WIP scenario — pass --run-wip when runtime is ready")
    for item in items:
        if "wip" in item.keywords:
            item.add_marker(skip_wip)

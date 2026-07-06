"""Unit tests for polar-manager HTTP API."""

from __future__ import annotations

from pathlib import Path

import pytest
from starlette.testclient import TestClient

from polar_manager.api import create_app
from polar_manager.config import PolarManagerSettings


@pytest.fixture
def polar_client(data_repo_root: Path | None, repo_root: Path) -> TestClient:
    if data_repo_root is None:
        pytest.skip("AI-sailing-data not available")
    settings = PolarManagerSettings(
        data_repo_config=repo_root / "config" / "data-repo.yaml",
        data_repo_path=data_repo_root,
        polar_manager_port=8092,
    )
    return TestClient(create_app(settings))


def test_health_returns_polar_loaded(polar_client: TestClient) -> None:
    resp = polar_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["polar_loaded"] is True
    assert body["vessel_id"] == "own-boat"


def test_target_endpoint_interpolates(polar_client: TestClient) -> None:
    resp = polar_client.get("/polars/own-boat/target", params={"tws": 10, "twa": 52})
    assert resp.status_code == 200
    body = resp.json()
    assert body["target_bsp"] == pytest.approx(7.26, abs=0.05)


def test_target_unknown_vessel_returns_404(polar_client: TestClient) -> None:
    resp = polar_client.get("/polars/UNKNOWN-99/target", params={"tws": 10, "twa": 52})
    assert resp.status_code == 404

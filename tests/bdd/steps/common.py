"""Shared step helpers and skip utilities."""

from __future__ import annotations

import pytest


def skip_phase(phase: str, detail: str = "") -> None:
    message = f"Phase {phase} not implemented"
    if detail:
        message = f"{message}: {detail}"
    pytest.skip(message)


def require_data_repo(data_repo_root) -> None:
    if data_repo_root is None:
        pytest.skip(
            "AI-sailing-data repo not found — set AI_SAILING_DATA_ROOT or clone sibling AI-sailing-data"
        )

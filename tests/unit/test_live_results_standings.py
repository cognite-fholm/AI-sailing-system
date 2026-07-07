"""Unit tests — live-results standings."""

import pytest

from live_results.standings import (
    corrected_seconds,
    format_standing_row,
    rank_by_corrected_time,
    standings_from_neo4j_rows,
)


def test_corrected_seconds() -> None:
    assert corrected_seconds(3600, 1.042) == pytest.approx(3751.2)


def test_rank_by_corrected_time() -> None:
    rows = [
        {"sail_number": "A", "corrected_seconds": 30000.0},
        {"sail_number": "B", "corrected_seconds": 29000.0},
    ]
    ranked = rank_by_corrected_time(rows)
    assert ranked[0]["sail_number"] == "B"
    assert ranked[0]["rank"] == 1
    assert ranked[0]["delta_to_leader_s"] == 0
    assert ranked[1]["delta_to_leader_s"] == 1000


def test_format_standing_row() -> None:
    row = format_standing_row(
        sail_number="NOR-10133",
        elapsed_seconds=3600,
        handicap_factor=1.042,
        course_pct=0.32,
        leg_seq=2,
    )
    assert row["corrected_seconds"] == 3751
    assert row["course_pct"] == 0.32


def test_standings_from_neo4j_rows_assigns_rank() -> None:
    rows = [
        {
            "sail_number": "NOR-1",
            "name": "Boat",
            "corrected_time_s": 28000,
            "elapsed_time_s": 27000,
        },
        {
            "sail_number": "SWE-2",
            "name": "Fast",
            "corrected_time_s": 27000,
            "elapsed_time_s": 26000,
        },
    ]
    out = standings_from_neo4j_rows(rows)
    assert out[0]["rank"] == 1
    assert out[0]["sail_number"] == "SWE-2"

"""Read LiveStanding and CourseSelection from Neo4j."""

from __future__ import annotations

import json
import re
from typing import Any

from neo4j import GraphDatabase

WRITE_PATTERN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH|CALL\s+\{)\b",
    re.IGNORECASE,
)

STANDINGS_QUERY = """
MATCH (r:Regatta)<-[:IN_RACE]-(v:Vessel)
OPTIONAL MATCH (v)-[:HAS_STANDING]->(s:LiveStanding)
RETURN v.sail_number AS sail_number,
       v.name AS name,
       coalesce(s.is_own, v.is_own, false) AS is_own,
       s.rank AS rank,
       s.corrected_time_s AS corrected_time_s,
       s.elapsed_time_s AS elapsed_time_s,
       s.handicap_factor AS handicap_factor,
       s.course_pct AS course_pct,
       coalesce(s.leg, s.leg_seq) AS leg
ORDER BY coalesce(s.rank, 9999), v.sail_number
"""

COURSE_SELECTION_QUERY = """
MATCH (cs:CourseSelection)
RETURN cs.race_id AS race_id,
       cs.route_id AS route_id,
       cs.route_name AS route_name,
       cs.leg_seq AS leg_seq,
       cs.selected_at AS selected_at
ORDER BY cs.selected_at DESC
LIMIT 1
"""

FLEET_VESSELS_QUERY = """
MATCH (v:Vessel)
RETURN v.mmsi AS mmsi,
       v.sail_number AS sail_number,
       v.name AS name,
       coalesce(v.is_own, false) AS is_own
ORDER BY v.sail_number
"""

GRIB_MODEL_SCORE_QUERY = """
MATCH (g:GribModelScore)
RETURN g.model_scores AS model_scores,
       g.selected_model AS selected_model,
       g.validation_notes AS validation_notes,
       g.updated_at AS updated_at
ORDER BY g.updated_at DESC
LIMIT 1
"""


class Neo4jRaceReader:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()

    def run_read(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        q = query.strip()
        if WRITE_PATTERN.search(q):
            raise ValueError("Only read-only Cypher is allowed.")
        with self._driver.session() as session:
            result = session.run(q, params or {})
            return [dict(record) for record in result]

    def fetch_standings(self) -> list[dict[str, Any]]:
        return self.run_read(STANDINGS_QUERY)

    def fetch_course_selection(self) -> dict[str, Any] | None:
        rows = self.run_read(COURSE_SELECTION_QUERY)
        return rows[0] if rows else None

    def fetch_fleet_vessels(self) -> list[dict[str, Any]]:
        return self.run_read(FLEET_VESSELS_QUERY)

    def fetch_grib_model_score(self) -> dict[str, Any] | None:
        rows = self.run_read(GRIB_MODEL_SCORE_QUERY)
        return rows[0] if rows else None


def course_selection_to_snapshot(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "route_id": row.get("route_id"),
        "route_name": row.get("route_name"),
        "leg_seq": row.get("leg_seq"),
        "selected_at": row.get("selected_at"),
    }


def grib_score_to_snapshot(row: dict[str, Any] | None) -> dict[str, Any]:
    if not row:
        return {}
    model_scores = row.get("model_scores") or {}
    if isinstance(model_scores, str):
        try:
            model_scores = json.loads(model_scores)
        except json.JSONDecodeError:
            model_scores = {}
    return {
        "selected_model": row.get("selected_model"),
        "model_scores": model_scores,
        "validation_notes": row.get("validation_notes"),
        "updated_at": row.get("updated_at"),
    }

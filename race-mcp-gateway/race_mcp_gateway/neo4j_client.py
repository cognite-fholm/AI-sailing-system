from __future__ import annotations

import json
import re
from typing import Any

from neo4j import GraphDatabase

WRITE_PATTERN = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD\s+CSV|FOREACH|CALL\s+\{)\b",
    re.IGNORECASE,
)


class Neo4jReadClient:
    def __init__(self, uri: str, user: str, password: str) -> None:
        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()

    def run_read(self, query: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        q = query.strip()
        if WRITE_PATTERN.search(q):
            raise ValueError("Only read-only Cypher is allowed (MATCH/RETURN/WITH/UNWIND).")
        if ";" in q.rstrip(";"):
            raise ValueError("Multiple Cypher statements are not allowed.")
        with self._driver.session() as session:
            result = session.run(q, params or {})
            return [dict(record) for record in result]


def format_rows(rows: list[dict[str, Any]], limit: int = 100) -> str:
    if not rows:
        return "No rows returned."
    trimmed = rows[:limit]
    payload = {"row_count": len(rows), "rows": trimmed}
    if len(rows) > limit:
        payload["truncated"] = True
        payload["limit"] = limit
    return json.dumps(payload, indent=2, default=str)


STANDINGS_QUERY = """
MATCH (r:Regatta)<-[:IN_RACE]-(v:Vessel)
OPTIONAL MATCH (v)-[:HAS_STANDING]->(s:LiveStanding)
RETURN v.sail_number AS sail_number,
       v.name AS name,
       s.rank AS rank,
       s.corrected_time_s AS corrected_time_s,
       s.elapsed_time_s AS elapsed_time_s,
       s.leg AS leg
ORDER BY coalesce(s.rank, 9999), v.sail_number
"""

COURSE_SELECTION_QUERY = """
MATCH (cs:CourseSelection)
RETURN cs.race_id AS race_id,
       cs.route_id AS route_id,
       cs.route_name AS route_name,
       cs.selected_at AS selected_at
ORDER BY cs.selected_at DESC
LIMIT 1
"""

FLEET_POSITIONS_QUERY = """
MATCH (v:Vessel)
WHERE v.lat IS NOT NULL AND v.lon IS NOT NULL
RETURN v.sail_number AS sail_number,
       v.name AS name,
       v.lat AS lat,
       v.lon AS lon,
       v.cog AS cog,
       v.sog AS sog,
       v.updated_at AS updated_at
ORDER BY v.sail_number
"""

SCHEMA_LABELS_QUERY = """
SHOW LABELS YIELD label
RETURN collect(label) AS labels
"""

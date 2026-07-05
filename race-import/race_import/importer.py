"""Neo4j import from AI-sailing-data YAML bundles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml
from neo4j import Driver, GraphDatabase

logger = logging.getLogger(__name__)

RUNTIME_LABELS = frozenset({"LiveStanding", "InsightAlert", "CourseSelection"})


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def import_document(session, doc: dict[str, Any], base_dir: Path) -> int:
    kind = doc.get("kind")
    if kind == "Neo4jBundle":
        return import_bundle(session, doc, base_dir)
    if kind == "Neo4jNode":
        import_node(session, doc)
        return 1
    if kind == "Neo4jRelationship":
        import_relationship(session, doc)
        return 1
    if kind == "WaypointList":
        return import_waypoint_list(session, doc)
    logger.warning("Unsupported kind %s in %s", kind, base_dir)
    return 0


def import_bundle(session, doc: dict[str, Any], base_dir: Path) -> int:
    order = doc.get("spec", {}).get("import_order") or []
    count = 0
    for rel_path in order:
        path = (base_dir / rel_path).resolve()
        if not path.is_file():
            logger.warning("Missing import file: %s", path)
            continue
        child = load_yaml(path)
        count += import_document(session, child, path.parent)
    return count


def import_node(session, doc: dict[str, Any]) -> None:
    spec = doc["spec"]
    labels = spec["labels"]
    if any(label in RUNTIME_LABELS for label in labels):
        logger.info("Skip runtime label import: %s", labels)
        return
    merge_keys = spec["merge_keys"]
    props = dict(spec.get("properties") or {})
    import_ref = doc.get("metadata", {}).get("ref")
    if import_ref:
        props["_import_ref"] = import_ref
    key_props = {k: props[k] for k in merge_keys if k in props}
    label_str = ":".join(labels)
    merge_pairs = ", ".join(f"{k}: ${k}" for k in key_props)
    cypher = f"MERGE (n:{label_str} {{{merge_pairs}}}) SET n += $props"
    session.run(cypher, props=props, **key_props)


def import_relationship(session, doc: dict[str, Any]) -> None:
    spec = doc["spec"]
    rel_type = spec["type"]
    props = dict(spec.get("properties") or {})
    session.run(
        f"""
        MATCH (a {{_import_ref: $from_ref}})
        MATCH (b {{_import_ref: $to_ref}})
        MERGE (a)-[r:{rel_type}]->(b)
        SET r += $props
        """,
        from_ref=spec["from_ref"],
        to_ref=spec["to_ref"],
        props=props,
    )


def import_waypoint_list(session, doc: dict[str, Any]) -> int:
    meta = doc.get("metadata", {})
    spec = doc.get("spec", {})
    route_id = meta.get("route_id", spec.get("section", "unknown"))
    race_id = meta.get("race_id", "unknown")
    count = 0
    for wp in spec.get("waypoints") or []:
        lat, lon = wp.get("lat"), wp.get("lon")
        if lat is None or lon is None:
            continue
        session.run(
            """
            MERGE (w:Waypoint {race_id: $race_id, route_id: $route_id, seq: $seq})
            SET w.name = $name,
                w.type = $type,
                w.lat = $lat,
                w.lon = $lon,
                w.rounding = $rounding
            """,
            race_id=race_id,
            route_id=route_id,
            seq=wp.get("seq"),
            name=wp.get("name"),
            type=wp.get("type"),
            lat=float(lat),
            lon=float(lon),
            rounding=wp.get("rounding"),
        )
        count += 1
    return count


def _certificate_dir_name(cert_ref: str) -> str:
    return cert_ref.removeprefix("cert-")


def default_import_paths(data_repo: Path, active: dict[str, Any]) -> list[Path]:
    paths: list[Path] = []
    boat_path = active.get("own_boat_path")
    cert_ref = active.get("active_certificate_ref")
    year = active.get("certificate_year")
    if boat_path:
        vessel = data_repo / boat_path / "neo4j" / "nodes" / "vessel.yaml"
        if vessel.is_file():
            paths.append(vessel)
    if boat_path and cert_ref and year:
        bundle = (
            data_repo
            / boat_path
            / str(year)
            / "certificates"
            / _certificate_dir_name(cert_ref)
            / "neo4j"
            / "import-order.yaml"
        )
        if bundle.is_file():
            paths.append(bundle)

    race_path = active.get("race_path")
    if race_path:
        race_bundle = data_repo / race_path / "neo4j" / "import-order.yaml"
        if race_bundle.is_file():
            paths.append(race_bundle)
        routes_dir = data_repo / race_path / "courses" / "routes"
        if routes_dir.is_dir():
            paths.extend(sorted(routes_dir.glob("*.yaml")))
    return paths


def run_import(
    driver: Driver,
    data_repo: Path,
    active: dict[str, Any],
    extra_paths: list[Path] | None = None,
) -> dict[str, Any]:
    targets = list(extra_paths or []) + default_import_paths(data_repo, active)
    total = 0
    files: list[str] = []
    with driver.session() as session:
        for path in targets:
            if not path.is_file():
                logger.warning("Skip missing %s", path)
                continue
            doc = load_yaml(path)
            count = import_document(session, doc, path.parent)
            total += count
            files.append(str(path.relative_to(data_repo)))
    return {"imported": total, "files": files}


def connect_driver(uri: str, user: str, password: str) -> Driver:
    return GraphDatabase.driver(uri, auth=(user, password))

---
name: yaml-ld-read
description: >-
  Read AI-sailing-data YAML as W3C YAML-LD 1.0 in Python services and agents.
  Use when implementing race-import, course-sk-sync, polar-manager, race-data-sync,
  or any code that loads boats/, races/, config/data-repo.yaml kinds from the data
  repo. Neo4j is runtime projection only — SHACL runs in shore CI. See DATA_SCHEMA.md.
---

# YAML-LD read — AI-sailing-system (runtime)

**Data-repo normative docs:** [AI-sailing-data schema/yaml-ld](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/README.md) · [context.jsonld](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/context.jsonld) · [ADR-0022](../../adr/0022-yaml-ld-interconnected-data.md) · [ADR-0023](../../adr/0023-shacl-neo4j-projection-no-fuseki.md)

**How it fits together:** [AI-sailing-data DATA_SCHEMA.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md)

**Companion (authoring):** [AI-sailing-data yaml-ld-write](https://github.com/cognite-fholm/AI-sailing-data/blob/main/.cursor/skills/yaml-ld-write/SKILL.md)

---

## Schema mental model (runtime services)

Services on the boat read **layer 1** (YAML-LD facts). They do **not** run SHACL or Fuseki.

| Layer | Where | Runtime service behavior |
|-------|-------|--------------------------|
| Facts | `DATA_REPO_PATH` mount | Load with this skill → Pydantic |
| Vocabulary | `context.jsonld` | Optional expand; structural checks in skill |
| Constraints | SHACL in CI | **Trust CI** — log warning if `@context` missing (legacy) |
| Neo4j graph | SLA-2 | `race-import` MERGE; live writers add runtime nodes |

**Projection:** [neo4j-mapping.yaml](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/neo4j-mapping.yaml) documents label/relationship contract. `race-import` uses `metadata.ref` as `_import_ref` for relationship MATCH.

**Runtime-only Neo4j labels** (never import from git): `LiveStanding`, `CourseSelection`, `InsightAlert`, `StartLineState`.

---

## Scope

This skill applies when Python code in **AI-sailing-system** reads YAML from the mounted **AI-sailing-data** clone (`DATA_REPO_PATH`, `/opt/ai-sailing-data`).

Config-only files (`deploy/env/*.env`, `docker-compose*.yml`) are **not** YAML-LD.

---

## Mandatory load pattern

```python
from pathlib import Path

import yaml

YAML_LD_BASE = "https://sailing.cognite-fholm/data/v1/"
ENTITY_URN_PREFIX = "urn:sailing:entity:"


def load_yaml_ld(path: Path) -> dict:
    """Load one YAML-LD document. YAML 1.2 safe loader only."""
    raw = path.read_text(encoding="utf-8")
    doc = yaml.safe_load(raw)  # MUST NOT use yaml.UnsafeLoader
    if not isinstance(doc, dict):
        raise ValueError(f"Expected mapping root in {path}")
    return doc


def entity_iri(doc: dict) -> str:
    meta = doc.get("metadata") or {}
    if "@id" in meta:
        return meta["@id"]
    ref = meta.get("ref")
    if not ref:
        raise ValueError("metadata.ref or metadata['@id'] required")
    return f"{ENTITY_URN_PREFIX}{ref}"
```

After load → **Pydantic** `model_validate` on `spec` (+ metadata) per [.agents/skills/pydantic-first-coding/SKILL.md](../pydantic-first-coding/SKILL.md).

---

## DO — strict requirements

| # | Rule |
|---|------|
| D1 | **DO** use `yaml.safe_load` / PyYAML with YAML 1.2 semantics. |
| D2 | **DO** validate UTF-8 encoding when reading files. |
| D3 | **DO** check `doc.get("@context")` — if present, enforce `kind` ↔ `@type` consistency before business logic. |
| D4 | **DO** resolve links via `node["@id"]` — implement `resolve_entity(urn)` and `resolve_document(relative_path)`. |
| D5 | **DO** map `kind` to Pydantic models (one model per kind). |
| D6 | **DO** treat `metadata.ref` as the Neo4j merge slug when `spec.properties.id` absent. |
| D7 | **DO** log legacy files missing `@context` at WARNING — still parse via legacy rules. |
| D8 | **DO** use `pathlib.Path` and `DATA_REPO_PATH` — never hardcode boat-specific paths in code. |
| D9 | **DO** strip or ignore `@context`/`@id`/`@type` at Pydantic boundary if models use `model_config = extra="ignore"`. |
| D10 | **DO** read [AI-sailing-data yaml-ld-read](https://github.com/cognite-fholm/AI-sailing-data/blob/main/.cursor/skills/yaml-ld-read/SKILL.md) for graph walk semantics. |
| D11 | **DO** consult [neo4j-mapping.yaml](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/neo4j-mapping.yaml) when implementing `race-import` label/relationship handling. |

---

## DON'T — violations (never do these)

| # | Rule |
|---|------|
| X1 | **DON'T** use `yaml.load` without SafeLoader. |
| X2 | **DON'T** treat entire doc as `dict[str, Any]` through business logic — parse into models. |
| X3 | **DON'T** resolve bare strings as entity links without explicit legacy mode flag. |
| X4 | **DON'T** assume `kind` strings are case-insensitive. |
| X5 | **DON'T** write back to data repo from SLA-1/SLA-2 services except documented APIs (`course-editor` → waypoints). |
| X6 | **DON'T** silently coerce `yes`/`no` YAML booleans — reject document if marine string fields hold booleans incorrectly. |
| X7 | **DON'T** cache parsed documents without file mtime invalidation (`course-sk-sync` poll pattern). |
| X8 | **DON'T** merge YAML documents from multiple files into one dict without tracking provenance IRIs. |
| X9 | **DON'T** invent kinds not in [schema/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md). |
| X10 | **DON'T** expand YAML anchors into persistent IDs in Influx/Neo4j. |

---

## Legacy compatibility (required until migration complete)

```python
def is_yaml_ld(doc: dict) -> bool:
    return "@context" in doc


def parse_kind(doc: dict) -> str:
    if is_yaml_ld(doc):
        t = doc.get("@type", "")
        if t.startswith("sailing:"):
            kind = t.split(":", 1)[1]
        else:
            kind = t
        if doc.get("kind") and doc["kind"] != kind:
            raise ValueError(f"kind {doc['kind']!r} != @type {kind!r}")
        return kind
    return doc["kind"]  # legacy
```

---

## Services and kinds

| Service | Kinds loaded |
|---------|----------------|
| `race-import` | `Neo4jNode`, `Neo4jRelationship`, import bundles |
| `race-data-sync` | `DataIndex`, sync metadata in `config/data-repo.yaml` |
| `course-sk-sync` | `WaypointList`, active race paths from config |
| `polar-manager` | `PolarSource`, `OrcCertificate`, `BoatSeason` |

---

## CI validation (data repo)

Shore CI runs `validate_yaml_ld.py`: JSON-LD expand + pyshacl + entity-ref resolution. Services may assume migrated YAML-LD passed CI at the git ref pinned for the race.

When adding `pyld` to service code, expand with local `context.jsonld` before `model_validate` for parity with CI.

---

## Related

- **Big picture:** [DATA_SCHEMA.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md)
- Pydantic patterns: [pydantic-first-coding](../pydantic-first-coding/SKILL.md)
- ADR: [0022](../../adr/0022-yaml-ld-interconnected-data.md) · [0023](../../adr/0023-shacl-neo4j-projection-no-fuseki.md)

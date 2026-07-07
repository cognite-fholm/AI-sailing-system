# ADR-0023: SHACL constraints and Neo4j projection (no Fuseki on Pi)

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0022](./0022-yaml-ld-interconnected-data.md), [ADR-0009](./0009-dual-repository-race-data.md), [spec §7.15.10](../spec.md#71510-ontology-constraints-and-neo4j-projection), [spec §11.15](../spec.md#1115-shacl-constraints-and-neo4j-projection)

---

## Context

[ADR-0022](./0022-yaml-ld-interconnected-data.md) adopted **YAML-LD** with a shared vocabulary (`context.jsonld`) for interconnected fact YAML in AI-sailing-data. CI validates JSON-LD expand/compatibility.

Open questions after ADR-0022:

| Question | Risk if unanswered |
|----------|-------------------|
| Who owns the **ontology** beyond vocabulary terms? | Neo4j labels and YAML `kind` drift apart |
| How do we enforce **semantic constraints** (cardinality, required links)? | Bad graph templates reach the boat |
| Do we need **RDF infrastructure** (Apache Jena Fuseki, SPARQL endpoint)? | Ops burden on Pi; duplicate graphs |
| How does **pySHACL** fit? | Ad hoc Python checks instead of standard shapes |

**Neo4j (SLA-2)** is the **runtime** property graph for fleet, courses, standings, and tactical queries. It is not an RDF triple store and does not natively enforce SHACL or OWL.

---

## Decision

### 1. Three-layer schema model

| Layer | Artifact | Role | Runs where |
|-------|----------|------|------------|
| **Vocabulary** | `schema/yaml-ld/context.jsonld` | IRIs, `sailing:` namespace, `kind` ↔ `@type` | Shore + CI |
| **Constraints** | `schema/shacl/*.shacl.ttl` | SHACL shapes — cardinality, required fields, relationship rules | **CI only** (shore) |
| **Runtime projection** | `schema/neo4j-mapping.yaml` | Maps `sailing:` types / YAML `kind` → Neo4j labels, MERGE keys, relationship types | `race-import` + docs |

Neo4j holds the **materialized runtime view** of declarative templates plus live overlay (AIS, standings). It is **not** the ontology source of truth.

### 2. SHACL + pyshacl in CI (not on Pi)

- Expand YAML-LD → RDF (N-Quads via PyLD).
- Validate the **combined dataset** (all migrated fact files) with **pyshacl** against committed SHACL shapes.
- Supplement with Python **entity-ref resolution** (`from_ref` / `to_ref` → `urn:sailing:entity:{ref}`) where cross-file checks are clearer than SPARQL.
- Script: `AI-sailing-data/scripts/validate_yaml_ld.py` (expand + SHACL + entity refs).

**No SHACL engine on the Raspberry Pi.** Validation completes before `race-data-sync` / `harbor-sync` pushes data to the boat.

### 3. No Apache Jena Fuseki on SLA-1 or SLA-2

We **reject** hosting Fuseki (or any RDF triple store) on the race node for v1.

| Alternative | Why rejected for v1 |
|-------------|---------------------|
| Fuseki on Pi | Extra container, memory, sync with Neo4j |
| RDF as primary store | Crew and agents author YAML, not Turtle |
| OWL reasoning at runtime | Not needed for regatta-scale graphs |

Fuseki remains a **future option** for shore-only SPARQL analytics if external RDF consumers appear. It is not on the critical path.

### 4. Neo4j projection map

`schema/neo4j-mapping.yaml` documents:

- `kind` → primary Neo4j label(s)
- Graph entity types (`sailing:Regatta`, `sailing:Vessel`, …) used in relationship `@type` links
- Allowed relationship types and endpoint label pairs
- Runtime-only labels that `race-import` must never MERGE from git (`LiveStanding`, `CourseSelection`, …)

`race-import` continues to read `Neo4jNode` / `Neo4jRelationship` templates; the mapping file is the **contract** between ontology and Cypher MERGE.

### 5. Pydantic remains the service boundary

SHACL validates the **linked-data graph** in CI. Pydantic models in `race-import` and related services validate **in-process** at import time. Both layers are complementary:

- SHACL — global constraints across files (shore, pre-merge)
- Pydantic — operational parsing and API contracts (runtime)

---

## Rationale

- **YAML-LD context** is already a lightweight ontology; SHACL adds machine-readable rules without changing the authoring format.
- **pyshacl in CI** gives standard validation with zero new onboard services.
- **Explicit Neo4j projection** prevents namespace/label drift between `context.jsonld`, YAML `kind`, and Cypher labels.
- **Neo4j stays fast** for race-time queries; RDF tooling stays on shore where git and GitHub Actions live.

---

## Consequences

### Positive

- Verifiable semantic constraints before data reaches the boat (FR-197–FR-201)
- Clear answer to “what does Neo4j use?” — `neo4j-mapping.yaml`
- pySHACL aligns with W3C SHACL; shapes are portable to Fuseki later if needed
- No additional Pi container or memory for RDF infrastructure

### Negative

| Risk | Mitigation |
|------|------------|
| SHACL only on migrated YAML-LD files | Legacy files skipped until migration; same as ADR-0022 |
| Dual validation (SHACL + Pydantic) | SHACL = cross-file; Pydantic = per-service |
| SHACL shapes lag new `kind` values | Register kind in context + mapping + shape in same PR |
| PyLD expand quirks (`apiVersion` as `@id`) | Shapes target expanded IRIs; document in `schema/shacl/README.md` |

---

## Alternatives considered

| Option | Outcome |
|--------|---------|
| **Neo4j constraints only** | No cross-file link validation before import |
| **Fuseki on harbor laptop** | Acceptable future shore tool; not v1 default |
| **Full OWL ontology** | Heavy; deferred |
| **Custom Python-only rules** | Replaced by SHACL for standard constraints; Python kept for entity-ref index |

---

## Implementation artifacts

| Artifact | Repository |
|----------|------------|
| `schema/shacl/` | AI-sailing-data |
| `schema/neo4j-mapping.yaml` | AI-sailing-data |
| `scripts/validate_yaml_ld.py` (SHACL step) | AI-sailing-data |
| `requirements-dev.txt` (`pyshacl`, `rdflib`) | AI-sailing-data |
| CI workflow step | AI-sailing-data + AI-sailing-system |
| Spec §7.15.10, §11.15, G33 | AI-sailing-system |

**Starter shapes:** Færder 2026 high-traffic bundle — `Boat`, `Race`, `Fleet`, `DataIndex`, `Neo4jNode`, `Neo4jRelationship`, `Neo4jBundle`.

---

## References

- [SHACL](https://www.w3.org/TR/shacl/)
- [pySHACL](https://github.com/RDFLib/pySHACL)
- [ADR-0022 YAML-LD](./0022-yaml-ld-interconnected-data.md)
- [AI-sailing-data schema/shacl](https://github.com/cognite-fholm/AI-sailing-data/tree/main/schema/shacl)

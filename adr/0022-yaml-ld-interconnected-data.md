# ADR-0022: YAML-LD for interconnected data (AI-sailing-data)

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [ADR-0020](./0020-course-editor-coordinate-system-of-record.md), [spec §7.15](../spec.md#715-race--boat-data-repository-ai-sailing-data), [spec §7.15.8](../spec.md#7158-yaml-ld-linked-data-format), [spec §11.14](../spec.md#1114-yaml-ld-linked-data-ai-sailing-data), [W3C YAML-LD 1.0](https://w3c.github.io/yaml-ld/)

---

## Context

[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) stores boats, races, certificates, courses, and Neo4j import templates as YAML files linked by `metadata.ref`, file paths, and implicit conventions.

Problems with the pre-YAML-LD model:

| Issue | Impact |
|-------|--------|
| Cross-file refs are bare strings | Agents and services guess link semantics |
| No global document identity | Hard to version, diff, or audit a specific file as a resource |
| YAML 1.1 boolean coercion risk | Country codes and labels (`NO`, `OFF`) can become booleans |
| Kind registry separate from semantics | `kind: Boat` is convention only, not machine-linked data |
| Multiple consumers | `race-import`, `course-sk-sync`, `polar-manager`, Cursor skills all parse ad hoc |

[W3C YAML-LD 1.0](https://w3c.github.io/yaml-ld/) defines YAML serialization of JSON-LD: same semantics as JSON-LD, UTF-8, YAML 1.2, convertible to JSON-LD without semantic loss. Media type: `application/ld+yaml`.

---

## Decision

### 1. Standard and profile

- **All interconnected fact YAML** in AI-sailing-data MUST conform to **YAML-LD 1.0 Basic profile**.
- Encoding: **UTF-8**. YAML: **1.2+** (never YAML 1.1 default loaders for authoring).
- One YAML-LD document per file (no multi-document streams).

### 2. Vocabulary and context

- Shared `@context`: [`AI-sailing-data/schema/yaml-ld/context.jsonld`](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/context.jsonld)
- Canonical URL: `https://sailing.cognite-fholm/schema/v1/context.jsonld`
- `@vocab` / `sailing:` namespace: `https://sailing.cognite-fholm/schema/v1/`
- Each registered `kind` has a `sailing:{Kind}` term in the context.

### 3. Identity

| Layer | Rule |
|-------|------|
| **Document** | `@id` = repo-relative POSIX path (e.g. `boats/NOR-10133/boat.yaml`) |
| **Document base** | `@base` = `https://sailing.cognite-fholm/data/v1/` |
| **Entity** | `metadata["@id"]` = `urn:sailing:entity:{metadata.ref}` |
| **Type** | `@type` = `sailing:{Kind}`; `kind` field retained and MUST match |

### 4. Envelope (unchanged for humans)

Retain Kubernetes-style fields for familiarity and existing Pydantic models:

- `apiVersion: sailing.cognite-fholm/v1`
- `kind`, `metadata`, `spec`

### 5. Cross-document links

New and edited files MUST link with JSON-LD node objects:

```yaml
active_certificate:
  "@type": "sailing:OrcCertificate"
  "@id": "urn:sailing:entity:cert-international-034400038T6"
```

Bare slug strings (`cert-foo`) are **legacy only**.

### 6. Enforcement

| Mechanism | Location |
|-----------|----------|
| Write skill (strict do/don't) | AI-sailing-data `.cursor/skills/yaml-ld-write/` |
| Read skill | AI-sailing-data `.cursor/skills/yaml-ld-read/` |
| Runtime read skill | AI-sailing-system `.agents/skills/yaml-ld-read/` |
| Config/fixture write | AI-sailing-system `.agents/skills/yaml-ld-write/` |
| `race-preparation` orchestrator | Must call `yaml-ld-write` for fact YAML |
| User guide | AI-sailing-data `docs/YAML_LD.md` |

### 7. Runtime

Services in AI-sailing-system (`race-import`, `course-sk-sync`, `polar-manager`, `race-data-sync`) resolve YAML per YAML-LD read rules; **Pydantic models** remain the in-process boundary.

### 8. Legacy

Files without `@context` are legacy. Migrate on substantive edit. Services support [legacy fallback](https://github.com/cognite-fholm/AI-sailing-data/blob/main/.cursor/skills/yaml-ld-read/SKILL.md#legacy-fallback) until bulk migration completes.

### 9. Exclusions

Not YAML-LD: `collected/**/*.json`, binaries, OKF/wiki markdown, compose/env files in AI-sailing-system.

---

## Rationale

- **Linked Data** gives one resolution algorithm for humans, agents, and services.
- **YAML-LD Basic** constrains YAML so round-trip to JSON-LD is safe (no cycles, string keys only).
- **Keeping `kind`/`spec`** avoids rewriting all Pydantic models and Neo4j import logic at once.
- **URN entity ids** stay stable when files move, as long as `metadata.ref` is preserved.
- **W3C standard** avoids a bespoke `ref:` URI scheme and enables JSON-LD tooling (expand, frame, validate).

---

## Consequences

### Positive

- Verifiable cross-document references (FR-189–FR-196)
- Standard media type for future HTTP APIs
- JSON-LD tooling for graph export and CI validation
- Agent skills with explicit do/don't contracts
- Fixes YAML 1.1 Norway-problem class of bugs

### Negative

| Risk | Mitigation |
|------|------------|
| Legacy files without `@context` | Migrate on edit; read skill legacy mode |
| Dual identity (`ref` + URN) | Canonical resolution in read skill |
| Context URL not yet HTTPS-hosted | File committed in repo; host before regatta |
| Stricter authoring burden | `yaml-ld-write` skill; Cursor does heavy lifting |
| Section renumbering in spec | §7.15.9 dual-repo (was 7.15.7) |

---

## Alternatives considered

| Option | Rejected because |
|--------|------------------|
| Plain YAML + JSON Schema only | No standard link semantics across files |
| JSON-LD only (no YAML) | Loses human editability for sailors |
| Full RDF/Turtle in repo | Too heavy for crew-edited race prep |
| Custom `ref:` URI scheme | Reinvents Linked Data; poor tooling |
| Kubernetes CRD OpenAPI only | No cross-repo linked semantics |

---

## Compliance matrix

| FR | Requirement | Status |
|----|-------------|--------|
| FR-189 | Basic profile conformance | Spec + skills |
| FR-190 | Required headers | `schema/yaml-ld/README.md` |
| FR-191 | Node-object links | `yaml-ld-write` skill |
| FR-192 | `context.jsonld` | Committed |
| FR-193 | Agent skills | Both repos |
| FR-194 | Runtime resolution | Read skills + legacy fallback |
| FR-195 | CI JSON-LD expand | Done — see [ADR-0023](./0023-shacl-neo4j-projection-no-fuseki.md) for SHACL |
| FR-196 | `kind` ↔ `@type` match | Validation rule in skills |

---

## Implementation artifacts

| Artifact | Location |
|----------|----------|
| Context | [schema/yaml-ld/context.jsonld](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/context.jsonld) |
| Normative conventions | [schema/yaml-ld/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/README.md) |
| User guide | [docs/YAML_LD.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/YAML_LD.md) |
| Examples | [schema/yaml-ld/examples/](https://github.com/cognite-fholm/AI-sailing-data/tree/main/schema/yaml-ld/examples) |
| Write skill | AI-sailing-data `.cursor/skills/yaml-ld-write/` |
| Read skills | AI-sailing-data + AI-sailing-system (see above) |
| Spec | [§7.15.8](../spec.md#7158-yaml-ld-linked-data-format), [§11.14](../spec.md#1114-yaml-ld-linked-data-ai-sailing-data), goal G32 |
| Follow-on | [ADR-0023](./0023-shacl-neo4j-projection-no-fuseki.md) — SHACL + Neo4j projection |

---

## References

- [W3C YAML-LD 1.0](https://w3c.github.io/yaml-ld/)
- [JSON-LD 1.1](https://www.w3.org/TR/json-ld11/)
- [AI-sailing-data schema/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md)

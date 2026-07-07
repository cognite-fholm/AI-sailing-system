# ADR-0024: Post-race export — Neo4j insights to AI-sailing-data (YAML-LD)

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [ADR-0022](./0022-yaml-ld-interconnected-data.md), [ADR-0023](./0023-shacl-neo4j-projection-no-fuseki.md), [ADR-0025](./0025-race-live-sync-github-temporal.md) (live sync during race), [spec §7.24](../spec.md#724-race-live-sync-and-archive), [spec §11.16](../spec.md#1116-post-race-analysis-export)

> **Amended by [ADR-0025](./0025-race-live-sync-github-temporal.md):** During the race, `race-live-sync` pushes `race-live/current.yaml` to GitHub every 5 minutes on branch `race-live/{regatta_id}`. This ADR covers **finalize** → `post-race/*.yaml` archive kinds on `main`.

---

## Context

[ADR-0009](./0009-dual-repository-race-data.md) established a **one-way import** path: declarative YAML in **AI-sailing-data** → `race-import` → **Neo4j** on the boat. During a regatta, Neo4j accumulates **runtime knowledge** that never existed in git:

| Neo4j (runtime) | Examples |
|-----------------|----------|
| `CourseSelection` | Which route was signaled and sailed |
| `LiveStanding` | Final corrected-time order (provisional → finish) |
| `InsightAlert` | Tactical insights fired during the race |
| GRIB model scores | Best-performing forecast model per leg ([ADR-0019](./0019-predictwind-multi-model-grib.md)) |
| Maneuver summaries | Tacks, mark roundings (when detected) |

After the race, this knowledge is **lost** if only InfluxDB raw telemetry is kept. Sailors already write `wiki/results.md`, but that is unstructured and not machine-linked to boats, courses, or fleet entities.

Goals:

1. **Learn from past races** — next regatta prep reads archived outcomes and competitor patterns.
2. **Structured post-race analysis** — insights and standings in **YAML-LD**, not only prose.
3. **No telemetry dump** — high-frequency Influx series stay in Influx (or expire); export **summaries** only.
4. **Symmetric ontology** — same `sailing:` vocabulary, entity URNs, and SHACL as pre-race facts ([ADR-0022](./0022-yaml-ld-interconnected-data.md), [ADR-0023](./0023-shacl-neo4j-projection-no-fuseki.md)).

---

## Decision

### 1. Reverse projection: Neo4j → YAML-LD (finalize / harbor)

Add service **`race-live-sync`** (SLA-2, system repo) — see [ADR-0025](./0025-race-live-sync-github-temporal.md) for the **during-race** git push loop. **Finalize** mode of the same service:

1. Queries Neo4j for **whitelisted runtime labels** for one `race_id`.
2. Maps graph nodes to **new post-race YAML `kind`s** (see below).
3. Writes YAML-LD files under `races/{year}/{race}/post-race/` in the mounted data repo.
4. Updates `race.yaml` → `spec.status: archived`, `spec.post_race_exported_at`.
5. Optionally merges **official results** from `collected/` portal JSON into `RaceResults`.

**Direction:**

```text
Pre-race:  AI-sailing-data (git) ──race-import──► Neo4j (boat)
Post-race: Neo4j (boat) ──race-live-sync finalize──► AI-sailing-data post-race/ on main
```

`race-live-sync` finalize is the **inverse contract** of `race-import` for archive kinds, documented in `schema/neo4j-mapping.yaml` → `export_projections`. Live push uses `live_projections` ([ADR-0025](./0025-race-live-sync-github-temporal.md)).

### 2. Post-race folder layout (AI-sailing-data)

```
races/{year}/{year}-{month}-{slug}/
  post-race/
    results.yaml          # kind: RaceResults
    outcome.yaml          # kind: RaceOutcome (own boat)
    insights.yaml         # kind: RaceInsightArchive
    grib-scores.yaml      # kind: GribModelOutcome
    export-manifest.yaml  # kind: PostRaceExport (provenance)
  wiki/
    debrief.md            # human narrative (optional, not YAML-LD)
  collected/
    results/              # raw portal JSON/PDF (existing pattern)
```

All `post-race/*.yaml` files are **YAML-LD fact documents** with `@context`, `@id`, `@type`, `metadata["@id"]`, and links to `urn:sailing:entity:regatta-{id}`.

### 3. New YAML `kind`s (post-race only)

| `kind` | File | Source (Neo4j / other) |
|--------|------|------------------------|
| `RaceResults` | `results.yaml` | Final `LiveStanding` snapshot + optional portal results |
| `RaceOutcome` | `outcome.yaml` | `CourseSelection`, own-boat finish row, certificate used |
| `RaceInsightArchive` | `insights.yaml` | `InsightAlert` nodes (deduplicated, severity, leg) |
| `GribModelOutcome` | `grib-scores.yaml` | Per-leg / race-best GRIB model scores |
| `PostRaceExport` | `export-manifest.yaml` | Export run metadata (`prov:wasGeneratedBy`) |

**Explicitly excluded from export:** `AisTrack`, raw Influx buckets, per-second `LiveStanding` history, full GRIB binaries.

### 4. Entity linking rules

Post-race documents MUST link to pre-race entities:

```yaml
regatta:
  "@type": "sailing:Regatta"
  "@id": "urn:sailing:entity:regatta-faerder-2026"
own_boat:
  "@type": "sailing:Vessel"
  "@id": "urn:sailing:entity:vessel-xbox"
course_route:
  "@type": "sailing:CourseRoute"
  "@id": "urn:sailing:entity:route-11-1"
```

Standings rows reference `urn:sailing:entity:vessel-*` where fleet boats were imported. Unknown competitors may use sail number + provisional slug until fleet stubs exist.

### 5. Workflow (after race)

| Step | Actor | Action |
|------|-------|--------|
| 1 | Crew | Set `RACE_MODE=false` or explicit harbor mode |
| 2 | `race-live-sync finalize` | CLI or `POST /finalize` with `race_id` |
| 3 | Crew / agent | Review `post-race/*.yaml`; edit `wiki/debrief.md` |
| 4 | Shore | `git commit` + `push` AI-sailing-data |
| 5 | Future prep | `race-preparation` reads archived races for competitor history |

Validation: `validate_yaml_ld.py` + SHACL shapes in `schema/shacl/post-race.shacl.ttl` on PR.

### 6. Re-import safety

Exported post-race kinds are **never** MERGE'd back as runtime `LiveStanding` / `InsightAlert` nodes via `race-import`. They are **historical facts** in git only. A future race's Neo4j starts clean from pre-race templates + new runtime overlay.

Optional: `race-import` may read `RaceResults` for OKF / MCP context without writing to Neo4j.

### 7. Human + collected layers (unchanged role)

| Layer | Format | Role |
|-------|--------|------|
| `wiki/debrief.md` | Markdown | Strategy narrative, lessons learned |
| `collected/results/` | JSON / PDF | Official portal scrape (manage2sail, SailRace System) |
| `post-race/*.yaml` | YAML-LD | Machine-readable standings, insights, outcomes |

Portal results **supplement** `RaceResults`; Neo4j export is authoritative for **what the boat computed** during the race.

---

## Rationale

- Closes the loop on [ADR-0009](./0009-dual-repository-race-data.md) — competitor and own-boat history accumulates in git across seasons.
- YAML-LD keeps post-race facts linkable to boats, routes, and certificates already in the repo.
- Summaries without telemetry respect Pi storage and git size limits.
- Symmetric `neo4j-mapping.yaml` export section avoids ad hoc Cypher in agents.
- Future race prep agents query structured past outcomes without live Neo4j.

---

## Consequences

### Positive

- Past race insight available for following regatta preparation (FR-202–FR-211)
- MCP / tactical-coach can cite archived `RaceInsightArchive` on shore
- Fleet `boats/` stubs enriched from `RaceResults` entrant rows
- SHACL-validated post-race dataset in CI

### Negative

| Risk | Mitigation |
|------|------------|
| Export before race truly finished | Require explicit trigger; `PostRaceExport` records timestamp |
| Neo4j schema drift breaks export | `export_projections` versioned in `neo4j-mapping.yaml` |
| Duplicate export overwrites git | `export-manifest.yaml` + git diff review before commit |
| Provisional vs official results differ | `RaceResults.spec.source` = `live_results` \| `portal` \| `merged` |

---

## Alternatives considered

| Option | Outcome |
|--------|---------|
| Export to Influx only | Poor versioning; no entity links for agents |
| Keep Neo4j snapshot on Pi | Lost on rebuild; not in GitHub workflow |
| Turtle/RDF files in repo | Rejected per ADR-0022 — YAML-LD only |
| Wiki-only post-race | Insufficient for machine learning / agent prep |
| Full AIS track in git | Too large; use Influx export separately if needed |

---

## Implementation artifacts

| Artifact | Repository |
|----------|------------|
| `race-live-sync` service (planned) | AI-sailing-system — live loop + finalize |
| `schema/neo4j-mapping.yaml` → `export_projections` | AI-sailing-data |
| `schema/yaml-ld/context.jsonld` — new kinds | AI-sailing-data |
| `schema/shacl/post-race.shacl.ttl` | AI-sailing-data |
| `docs/RACE_LIVE_SYNC.md` | AI-sailing-data |
| `docs/POST_RACE_ANALYSIS.md` | AI-sailing-data |
| `.cursor/skills/post-race-export/` | AI-sailing-data |

---

## References

- [ADR-0009 Dual repository](./0009-dual-repository-race-data.md)
- [ADR-0022 YAML-LD](./0022-yaml-ld-interconnected-data.md)
- [ADR-0023 SHACL + Neo4j projection](./0023-shacl-neo4j-projection-no-fuseki.md)
- [docs/DATA_SCHEMA.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md)

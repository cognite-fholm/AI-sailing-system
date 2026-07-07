# Architecture overview

Consolidated map of the **AI Sailing System** — how repositories, SLA tiers, data stores, and reference products fit together. Normative detail remains in [spec.md](../spec.md) and [adr/](../adr/).

**Last updated:** 2026-07-07 · **Spec version:** 0.24.0-draft

---

## Repositories

| Repository | Role | Onboard path |
|------------|------|--------------|
| **[AI-sailing-system](https://github.com/cognite-fholm/AI-sailing-system)** (this repo) | Code, Docker images, CI/CD, ADRs, spec | `/opt/ai-sailing-system/` |
| **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | Races, boats, ORC certs, planning **YAML-LD**, Neo4j templates | `/opt/ai-sailing-data/` |

**YAML format:** Interconnected facts use [W3C YAML-LD 1.0](https://w3c.github.io/yaml-ld/) — [ADR-0022](../adr/0022-yaml-ld-interconnected-data.md) · [ADR-0023](../adr/0023-shacl-neo4j-projection-no-fuseki.md) · [ADR-0024](../adr/0024-post-race-neo4j-export-to-data-repo.md) · [ADR-0025](../adr/0025-race-live-sync-github-temporal.md) · [data repo schema/yaml-ld](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/yaml-ld/README.md)

**Rule:** Prepare regattas in **AI-sailing-data** on shore (Cursor + Git). Freeze **both** git refs and system image digests before a race ([ADR-0009](../adr/0009-dual-repository-race-data.md)). **`race-lifecycle`** drives harbor pull/import, race mode, and live sync from `race.yaml` `spec.schedule` + `index.yaml` active regatta ([ADR-0026](../adr/0026-race-lifecycle-scheduled-harbor-automation.md)). **One `harbor.env` on the Pi** — no per-regatta env swap ([ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md)). During the race, **`race-live-sync`** pushes Neo4j summaries to GitHub every 5 minutes on LTE ([ADR-0025](../adr/0025-race-live-sync-github-temporal.md)).

**User guide:** [Race preparation guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md) (data repo).

---

## SLA tiers

| Tier | Priority | Hardware | Compose file |
|------|----------|----------|--------------|
| **SLA-1** | Critical | Pi 5 + PiCAN-M | `docker-compose.sla-1.yml` |
| **SLA-2** | Important | Pi 5 (8 GB) | `docker-compose.sla-2.yml` |
| **SLA-3** | Best-effort | Pi 5 + Coral + GoPro | `docker-compose.sla-3.yml` |
| **SLA-S** | Harbor only | Gaming PC (CUDA) | `shore/docker-compose.sla-shore.yml` |

**Golden rule:** SLA-1 telemetry survives SLA-2/SLA-3 failure ([ADR-0002](../adr/0002-three-tier-sla-architecture.md)).

```mermaid
flowchart TB
  subgraph sla1 [SLA-1 Telemetry]
    N2K[NMEA 2000 / 0183 + H5000]
    SK[Signal K]
    IFX[InfluxDB]
    N2K --> SK --> IFX
  end

  subgraph sla2 [SLA-2 Race]
    NEO[Neo4j]
    RI[race-intelligence]
    LR[live-results]
    PM[polar-manager]
    GF[grafana-race]
    SK --> RI
    SK --> PM
    RI --> GF
    LR --> GF
    NEO --> LR
  end

  subgraph data [AI-sailing-data Git]
    YAML[YAML + OKF]
    YAML -->|race-import| NEO
    NEO -->|race-live-sync| YAML
  end

  subgraph shore [Shore / LTE / GitHub]
    GIT[GitHub]
    GIT -->|race-data-sync pull| data
    NEO -->|race-live-sync push| GIT
  end

  subgraph laptop [Navigator laptop]
    CUR[Cursor + MCP]
    CUR -.->|boat LAN Wi‑Fi| GW
  end

  subgraph mcp [SLA-2 MCP]
    GW[race-mcp-gateway]
    GW --> NEO
    GW --> IFX
  end
```

Spec: [§5 Three-tier SLA](../spec.md#5-three-tier-sla-architecture) · [§6 Data flow](../spec.md#6-system-context-and-data-flow)

---

## Data stores

| Store | SLA | Holds |
|-------|-----|-------|
| **Signal K** | 1 | Live marine deltas (canonical) |
| **InfluxDB** | 1 | High-frequency telemetry |
| **Neo4j** | 2 | Races, vessels, courses, runtime standings |
| **Grafana** | 1–3 | Dashboards per tier |
| **Git (data repo)** | Shore ↔ boat | Pre-race YAML; **during race** `race-live/` on branch `race-live/{regatta_id}`; **after race** `post-race/` on `main` |
| **OKF bundles** | 2–3 | LLM concept context |

**Git temporal model ([ADR-0025](../adr/0025-race-live-sync-github-temporal.md)):** `race-live-sync` commits `race-live/current.yaml` every 5 min when LTE is up. Git history on `race-live/{regatta_id}` is the playback timeline. Finalize merges archive kinds to `post-race/*.yaml` on `main`.

**Not in git (raw runtime):** Live AIS tracks, per-second standing history, raw GRIB binaries. **Summarized in git:** standings, course, insights via `race-live/` and `post-race/` ([ADR-0024](../adr/0024-post-race-neo4j-export-to-data-repo.md)).

---

## Reference products (parity targets)

The Pi stack **extends** familiar sailing tools; it does not replace helm instruments in v1.

| Product | ADR | Spec | Our surfaces |
|---------|-----|------|--------------|
| **[iRegatta](https://zifigo.com/)** v2.86 | [0010](../adr/0010-iregatta-reference-model.md) | [§7.16](../spec.md#716-iregatta-reference-model--feature-traceability) | `grafana-race`, `course-editor`, `race-intelligence` |
| **[B&G H5000](https://www.bandg.com/bg/series/h5000/)** | [0011](../adr/0011-bg-h5000-reference-model.md) | [§7.17](../spec.md#717-bg-h5000-reference-model--integration) | Signal K ingest, SailSteer/Start Grafana pages, `InstrumentProfile` YAML |
| **Laptop Cursor + MCP** | [0012](../adr/0012-race-side-mcp-laptop-cursor.md) | [§7.18](../spec.md#718-race-side-mcp--laptop-cursor) | `race-mcp-gateway` on boat LAN |

**Beyond reference products:** AIS fleet, live ORC corrected standings, GRIB wind zones, SI PDF courses, start-boat flags, LLM coach, **race-side MCP**, **cloud AI via GitHub live sync**.

---

## Bidirectional git sync (AI-sailing-data)

| Direction | Service | When | Branch |
|-----------|---------|------|--------|
| GitHub → boat | `race-data-sync` | Harbor; optional ashore updates during week | `main` |
| Boat → GitHub | `race-live-sync` | Every 5 min when LTE up during race | `race-live/{regatta_id}` |
| Finalize | `race-live-sync finalize` | After race | merge → `main` |

```mermaid
flowchart LR
  subgraph github [GitHub]
    MAIN[main]
    LIVE[race-live/regatta_id]
  end

  subgraph pi [SLA-2 Pi]
    PULL[race-data-sync]
    NEO[(Neo4j)]
    PUSH[race-live-sync]
  end

  MAIN --> PULL --> NEO
  NEO --> PUSH --> LIVE
  LIVE -->|finalize| MAIN
```

**Secrets:** `GITHUB_TOKEN` via Docker secret or `deploy/env/race.env` — never baked into images ([ADR-0025](../adr/0025-race-live-sync-github-temporal.md)).

User guide: [AI-sailing-data RACE_LIVE_SYNC.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIVE_SYNC.md) · [POST_RACE_ANALYSIS.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/POST_RACE_ANALYSIS.md)

Manuals: [docs/references/README.md](./references/README.md)

---

## Architecture Decision Records

| ADR | Topic |
|-----|-------|
| [0001](../adr/0001-system-architecture-and-technology-choices.md) | Core stack (Signal K, Influx, Neo4j, Grafana, LLaMA) |
| [0002](../adr/0002-three-tier-sla-architecture.md) | Three isolated SLA tiers |
| [0003](../adr/0003-gopro-capture-and-shore-training.md) | GoPro HERO13 + TrimTransformer |
| [0004](../adr/0004-grib-polars-ais-wind-analysis.md) | GRIB, polars, AIS, wind-on-course |
| [0005](../adr/0005-course-parsing-handicaps-live-results.md) | SI parse, handicaps, live results |
| [0006](../adr/0006-start-boat-course-flags.md) | Multi-course / start-boat flags |
| [0008](../adr/0008-github-docker-deployment-lifecycle.md) | GitHub Actions, GHCR, race freeze |
| [0009](../adr/0009-dual-repository-race-data.md) | Dual repo + Teltonika sync |
| [0010](../adr/0010-iregatta-reference-model.md) | iRegatta UX benchmark |
| [0011](../adr/0011-bg-h5000-reference-model.md) | H5000 instrument benchmark |
| [0012](../adr/0012-race-side-mcp-laptop-cursor.md) | Race-side MCP for laptop Cursor |
| [0013](../adr/0013-orc-certificate-fleet-collection.md) | Automated ORC certificate fleet collection (shore skill) |
| [0014](../adr/0014-shore-weather-current-collection.md) | Shore weather/current — MET GRIB, Oslofjord plots, SMHI |
| [0015](../adr/0015-tactical-insight-alerts-annunciation.md) | Tactical insight alerts, UX feed, optional voice (Piper TTS) |
| [0016](../adr/0016-fleet-polar-performance-influx.md) | Fleet polar performance timeline in InfluxDB |
| [0017](../adr/0017-marine-map-gpx-export.md) | Marine map GPX export (PredictWind-compatible zip) |
| [0021](../adr/0021-sla1-signalk-plugin-strategy.md) | SLA-1 Signal K plugins — course geometry + polar performance |
| [0022](../adr/0022-yaml-ld-interconnected-data.md) | YAML-LD linked data (AI-sailing-data) |
| [0023](../adr/0023-shacl-neo4j-projection-no-fuseki.md) | SHACL constraints + Neo4j projection (shore CI) |
| [0024](../adr/0024-post-race-neo4j-export-to-data-repo.md) | Post-race finalize → data repo archive kinds |
| [0025](../adr/0025-race-live-sync-github-temporal.md) | Race live sync — 5 min Neo4j → GitHub on LTE |
| [0026](../adr/0026-race-lifecycle-scheduled-harbor-automation.md) | Race lifecycle — schedule-driven harbor automation |
| [0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md) | Data-repo runtime policy — zero per-race Pi env |
| [0028](../adr/0028-enriched-live-snapshot-fleet-performance-temporal.md) | Enriched live snapshot — fleet performance 5 min rollup |

Full index: [adr/README.md](../adr/README.md)

---

## Shore collection pipeline (race prep)

Before a regatta, **AI-sailing-data** is populated on shore via Cursor skills:

```mermaid
flowchart LR
  M2S[manage2sail / sailracesystem]
  FLEET[fleet.yaml]
  ORC[orc-sailor-services]
  WX[weather skills]
  IDX[collected/orc/]
  WIDX[collected/weather/]
  BOATS[boats/certificates/]
  SYNC[race-data-sync]

  M2S --> FLEET --> ORC --> IDX --> BOATS
  FLEET --> WX --> WIDX
  BOATS --> SYNC
  WIDX --> SYNC
```

| Skill | Output |
|-------|--------|
| **sailracesystem** | Fleet, SI PDFs, `collected/sailracesystem/` |
| **manage2sail** | Fleet, documents, `collected/manage2sail/` |
| **orc-sailor-services** | ORC index, PDFs, `boats/{sail}/certificates/` |
| **metno-oslofjord-weather** | GRIB manifests, `collected/weather/grib/` (binaries gitignored) |
| **oslofjord-current-plots** | Current PNG maps + interpretation reference |
| **smhi-wind-observations** | Skagerrak wind obs JSON for forecast validation |
| **marine-map-gpx-export** | GPX route zip → `export/marine-map/` for chartplotter import |
| **insight-alerts** | Tactical alert broker — Grafana + course-editor + optional speaker TTS |

Detail: [spec §7.19](../spec.md#719-orc-certificate-collection--fleet-enrichment) · [spec §7.20](../spec.md#720-shore-weather--current-collection) · [spec §7.21](../spec.md#721-tactical-insight-alerts--annunciation) · [spec §7.23](../spec.md#723-marine-map-gpx-export) · [data repo prep guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md)

---

## AI-sailing-data schema (summary)

| Kind | Typical path |
|------|----------------|
| `Boat`, `BoatSeason`, `OrcCertificate`, `PolarSource` | `boats/{sail_number}/` |
| `InstrumentProfile`, `InstrumentCalibration` | `boats/{sail}/instrumentation/` |
| `Race`, `Fleet`, `CourseCatalog`, `WaypointList` | `races/{year}/{race}/` |
| `RaceLiveSnapshot`, `RaceLiveSyncManifest` | `races/.../race-live/` (during race, git timeline) |
| `RaceResults`, `RaceOutcome`, … | `races/.../post-race/` (after finalize) |
| `LaylinePreferences`, `StartLinePreferences`, `GribPlan`, `WeatherCollection`, `InsightAlertProfile`, `MarineMapExport` | `races/.../planning/`, `collected/weather/`, `export/marine-map/` |
| `H5000VariableMap` | `schema/h5000-variable-map.yaml` |

Detail: [data repo schema/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md)

**Schema layers (shore, CI-validated):**

| Layer | Path |
|-------|------|
| Vocabulary | `schema/yaml-ld/context.jsonld` |
| SHACL constraints | `schema/shacl/*.shacl.ttl` |
| Neo4j projection | `schema/neo4j-mapping.yaml` |

Neo4j on SLA-2 is the **runtime** graph; RDF/SHACL validation runs in GitHub Actions only ([ADR-0023](../adr/0023-shacl-neo4j-projection-no-fuseki.md)).

---

## Key services (SLA-1)

| Service | Responsibility |
|---------|----------------|
| `signalk-server` | NMEA hub + `@signalk/course-provider` (VMG, XTE, DTM) |
| `course-sk-sync` | Active `WaypointList` YAML → `navigation.course` (SLA-2 offline OK) |
| `signalk-polar-performance` | `performance.*` from `polar-manager` target speeds |
| `signalk-influx-bridge` | WebSocket → Influx `signalk` bucket |
| `grafana-telemetry` | SOG, wind, course calc values, polar % history |

ADR: [0021](../adr/0021-sla1-signalk-plugin-strategy.md) · Spec: [§7.1](../spec.md#71-signal-k-server-hub--sla-1-only)

---

## Key services (SLA-2)

| Service | Responsibility |
|---------|----------------|
| `race-data-sync` | `git pull` data repo via LTE/Wi‑Fi |
| `race-import` | MERGE `neo4j/*.yaml` bundles |
| `race-lifecycle` | Poll `race.yaml` schedule; write `/var/run/ai-sailing/race-lifecycle.json`; trigger import at harbor time ([ADR-0026](../adr/0026-race-lifecycle-scheduled-harbor-automation.md)) |
| `race-live-sync` | Export Neo4j → `race-live/*.yaml` + git push every 5 min on LTE; finalize → `post-race/` ([ADR-0025](../adr/0025-race-live-sync-github-temporal.md)) |
| `polar-manager` | ORC target-speeds API (`GET /polars/{id}/target`); full SLK parser in Phase 2C |
| `race-intelligence` | Start line, lift, laylines, steering hints |
| `live-results` | VMG, corrected-time fleet rank |
| `fleet-performance-tracker` | Fleet polar % vs certificate — 30 s series in Influx `race` bucket |
| `wind-field-analyzer` | GRIB + AIS + polar fusion |
| `course-parser` / `course-editor` | SI → waypoints; manual edit + start flags |
| `handicap-manager` | ORC multi-number + WRS TCF |
| `ais-collector` | Fleet AIS from Signal K |
| `tactical-coach` | Local LLM advisory |
| `insight-alerts` | Tactical alert broker — UI feed, ack, Piper TTS to speaker |
| `race-mcp-gateway` | MCP tools for laptop Cursor — **Neo4j** (`/mcp/neo4j`) + **Influx** (`/mcp/influx`) ([guide](./race-laptop-mcp.md), [tools](./mcp-neo4j-influx.md)) |

---

## Race laptop (Cursor + MCP)

Bring a **laptop** on boat Wi‑Fi; Cursor connects to `race-mcp-gateway` at `http://race.local:3100` for live standings, Influx queries, Neo4j, and YAML context — ad hoc analysis during the race.

| Doc | Content |
|-----|---------|
| [race-laptop-mcp.md](./race-laptop-mcp.md) | Laptop setup, MCP config, example prompts |
| [ADR-0012](../adr/0012-race-side-mcp-laptop-cursor.md) | Architecture decision |

**Note:** MCP stays **enabled** when `RACE_MODE=true` (read-only; does not auto-update containers).

---

| Doc | Content |
|-----|---------|
| [USER_GUIDE.md](./USER_GUIDE.md) | **Sailor user guide** — links to data-repo prep + onboard |
| [deployment-lifecycle.md](./deployment-lifecycle.md) | Harbor vs race mode, scripts |
| [deploy/README.md](../deploy/README.md) | Env templates, digest locks |
| [spec §9](../spec.md#9-deployment-architecture) | Full deployment architecture |

**Harbor:** `harbor-pull.sh` (images) + `harbor-sync.sh` (models, OKF, data repo).  
**Race:** Lifecycle `race_mode` — no Watchtower, no `race-data-sync` pull during racing; **`race-live-sync` push** when phase is `armed`/`racing` and LTE is up.

---

## Implementation status

Phases match [spec §1.1](../spec.md#11-implementation-map) and [spec §14](../spec.md#14-implementation-phases). ADR build order: [adr/README.md](../adr/README.md#implementation-order).

| Phase | Status |
|-------|--------|
| **0 — Foundation** | **Done** — spec v0.21, ADRs 0001–0021, BDD scaffold |
| **1 — SLA-1 telemetry** | **Scaffold** — `course-provider`, `course-sk-sync`, `signalk-polar-performance`, bridge, Grafana; PiCAN ingest pending |
| **2A — Shore race prep** | **Partial** — data repo skills, Færder examples, **YAML-LD** (ADR-0022); waypoint gaps remain |
| **2B — Graph import** | **Scaffold** — `docker-compose.sla-2.yml`, `race-import`, `race-data-sync`, `race-live-sync` |
| **2C — GRIB, polars, AIS** | **Stub** — `polar-manager` target-speeds API only |
| **2D — Courses & results** | Not started |
| **2E — Race UX** | Not started |
| **2F — Analytics & alerts** | Not started |
| **2G — Laptop MCP** | Scaffold only (`race-mcp-gateway/`) |
| **2H — Live sync & archive** | **Partial** — enriched rollup; `fleet-performance-tracker` 30 s own-boat writer; `race-live-sync finalize`; lifecycle auto-finalize |
| **3 — SLA-3 vision** | Not started |
| **4 — CI/CD multi-Pi** | **Partial** — CI + publish-sla-1/2 + release; publish-sla-3 pending |
| **5 — Shore training** | Spec only |

Detail: [spec §14](../spec.md#14-implementation-phases) · BDD: [tests/bdd/README.md](../tests/bdd/README.md)

### Onboard runtime (Phase 1 & 2B)

| Compose | Services (v1) |
|---------|-----------------|
| `docker-compose.sla-1.yml` | `signalk-server`, `course-sk-sync`, `signalk-polar-performance`, `influxdb`, `signalk-influx-bridge`, `grafana-telemetry` |
| `docker-compose.sla-2.yml` | `neo4j`, `polar-manager`, `race-import`, `race-data-sync`, `race-lifecycle`, `race-live-sync`, `race-mcp-gateway` (profile `mcp`) |
| `docker-compose.dev.yml` | SLA-1 laptop overlay — bridge network |
| `docker-compose.dev-sla2.yml` | SLA-2 laptop overlay — data-repo mount, sync policy |
| `docker-compose.harbor.yml` | Watchtower overlay (SLA-2/3 only) |

Local dev: [deploy/README.md](../deploy/README.md#local-dev-single-machine).

---

## Related links

- [spec.md](../spec.md) — full specification
- [README.md](../README.md) — project entry point
- [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) — race/boat content
- [cogsail-python](https://github.com/cognite-fholm/cogsail-python) — prior art

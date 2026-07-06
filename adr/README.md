# Architecture Decision Records

This directory contains [Architecture Decision Records](https://adr.github.io/) for the AI Sailing System.

**Implementing?** Read ADRs in [implementation order](#implementation-order) below — not by ADR number. Full phase map: [spec §1.1](../spec.md#11-implementation-map) and [spec §14](../spec.md#14-implementation-phases).

## Implementation order

ADR numbers are permanent (chronological). Build sequence groups related decisions.

| Phase | ADRs | Title |
|-------|------|-------|
| **0 — Foundation** | [0001](./0001-system-architecture-and-technology-choices.md) | System architecture and technology choices |
| | [0002](./0002-three-tier-sla-architecture.md) | Three-tier SLA architecture with isolated containers |
| | [0008](./0008-github-docker-deployment-lifecycle.md) | GitHub + Docker CI/CD, lifecycle, guardrails, gaming PC shore training |
| | [0009](./0009-dual-repository-race-data.md) | Dual repo: AI-sailing-system + AI-sailing-data, Teltonika LTE sync |
| **1 — SLA-1 telemetry** | [0001](./0001-system-architecture-and-technology-choices.md) | (stack — see Phase 0) |
| | [0011](./0011-bg-h5000-reference-model.md) | B&G H5000 instrument and race-display reference (ingest paths) |
| | [0021](./0021-sla1-signalk-plugin-strategy.md) | SLA-1 Signal K plugins — course-provider, course-sk-sync, polar performance |
| **2A — Shore race prep** | [0009](./0009-dual-repository-race-data.md) | (data repo model — see Phase 0) |
| | [0013](./0013-orc-certificate-fleet-collection.md) | Automated ORC certificate collection for race fleets |
| | [0014](./0014-shore-weather-current-collection.md) | Shore weather and current collection (PredictWind GRIB, MET, SMHI) |
| | [0017](./0017-marine-map-gpx-export.md) | Marine map GPX export bundle (PredictWind-compatible) |
| | [0019](./0019-predictwind-multi-model-grib.md) | PredictWind multi-model GRIB shore workflow |
| **2B — Graph import** | [0009](./0009-dual-repository-race-data.md) | (sync contract — see Phase 0) |
| **2C — GRIB, polars, AIS** | [0004](./0004-grib-polars-ais-wind-analysis.md), [0019](./0019-predictwind-multi-model-grib.md) | GRIB + PredictWind multi-model scoring, polars, AIS, wind analysis |
| **2D — Courses & results** | [0005](./0005-course-parsing-handicaps-live-results.md), [0020](./0020-course-editor-coordinate-system-of-record.md) | Course parsing; **course-editor** SoR for coordinates |
| | [0006](./0006-start-boat-course-flags.md) | Multiple courses per race and start-boat flag signaling |
| **2E — Race UX** | [0010](./0010-iregatta-reference-model.md), [0011](./0011-bg-h5000-reference-model.md), [0018](./0018-helm-ux-three-pi-dual-speaker.md) | iRegatta/H5000 parity in `race-ui` + Grafana |
| **2F — Analytics & alerts** | [0016](./0016-fleet-polar-performance-influx.md) | Fleet polar performance timeline stored in InfluxDB |
| | [0015](./0015-tactical-insight-alerts-annunciation.md) | Tactical insight alerts, UX feed, and optional voice annunciation |
| **2G — Laptop MCP** | [0012](./0012-race-side-mcp-laptop-cursor.md) | Race-side MCP for laptop Cursor and ad hoc analysis |
| **3 — SLA-3 vision** | [0003](./0003-gopro-capture-and-shore-training.md) | GoPro HERO13 fleet capture and onshore TrimTransformer training |
| **4 — CI/CD** | [0008](./0008-github-docker-deployment-lifecycle.md) | (deployment lifecycle — see Phase 0) |
| **5 — Shore training** | [0003](./0003-gopro-capture-and-shore-training.md) | (TrimTransformer pipeline — see Phase 3) |

## ADR index (by number)

| ADR | Title | Phase | Status |
|-----|-------|-------|--------|
| [0001](./0001-system-architecture-and-technology-choices.md) | System architecture and technology choices | 0, 1 | Accepted |
| [0002](./0002-three-tier-sla-architecture.md) | Three-tier SLA architecture with isolated containers | 0 | Accepted |
| [0003](./0003-gopro-capture-and-shore-training.md) | GoPro HERO13 fleet capture and onshore TrimTransformer training | 3, 5 | Accepted |
| [0004](./0004-grib-polars-ais-wind-analysis.md) | GRIB scheduling, polar fleet registry, AIS ingest, wind-on-course analysis | 2C | Accepted |
| [0005](./0005-course-parsing-handicaps-live-results.md) | Course parsing from SI PDFs, multi-handicap scoring, live results | 2D | Accepted |
| [0006](./0006-start-boat-course-flags.md) | Multiple courses per race and start-boat flag signaling | 2D | Accepted |
| [0008](./0008-github-docker-deployment-lifecycle.md) | GitHub + Docker CI/CD, lifecycle, guardrails, gaming PC shore training | 0, 4 | Accepted |
| [0009](./0009-dual-repository-race-data.md) | Dual repo: AI-sailing-system + AI-sailing-data, Teltonika LTE sync | 0, 2A, 2B | Accepted |
| [0010](./0010-iregatta-reference-model.md) | iRegatta v2.86 as functional reference for race UX | 2E | Accepted |
| [0011](./0011-bg-h5000-reference-model.md) | B&G H5000 instrument and race-display reference | 1, 2E | Accepted |
| [0012](./0012-race-side-mcp-laptop-cursor.md) | Race-side MCP for laptop Cursor and ad hoc analysis | 2G | Accepted |
| [0013](./0013-orc-certificate-fleet-collection.md) | Automated ORC certificate collection for race fleets | 2A | Accepted |
| [0014](./0014-shore-weather-current-collection.md) | Shore weather and current collection (MET GRIB, Oslofjord plots, SMHI) | 2A | Accepted |
| [0015](./0015-tactical-insight-alerts-annunciation.md) | Tactical insight alerts, UX feed, and optional voice annunciation | 2F | Accepted |
| [0016](./0016-fleet-polar-performance-influx.md) | Fleet polar performance timeline stored in InfluxDB | 2F | Accepted |
| [0017](./0017-marine-map-gpx-export.md) | Marine map GPX export bundle (PredictWind-compatible) | 2A | Accepted |
| [0018](./0018-helm-ux-three-pi-dual-speaker.md) | Helm UX — `race-ui`, Grafana scope, three-Pi, dual speaker, H5000-only safety | 0, 2E, 2F | Accepted |
| [0019](./0019-predictwind-multi-model-grib.md) | PredictWind multi-model GRIB and onboard model scoring | 2A, 2C | Accepted |
| [0020](./0020-course-editor-coordinate-system-of-record.md) | course-editor as coordinate system of record | 2A, 2D | Accepted |
| [0021](./0021-sla1-signalk-plugin-strategy.md) | SLA-1 Signal K plugin strategy (course-provider, sidecars) | 1, 2C | Accepted |

## Format

Each ADR follows the structure:

1. **Context** — what forces are at play
2. **Decision** — what we chose
3. **Rationale** — why
4. **Consequences** — positive, negative, risks
5. **Alternatives considered**

New decisions should use the next sequential number: `0021-short-title.md`.

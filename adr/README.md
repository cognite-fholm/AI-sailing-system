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
| | [0022](./0022-yaml-ld-interconnected-data.md) | YAML-LD for interconnected data (W3C) |
| | [0023](./0023-shacl-neo4j-projection-no-fuseki.md) | SHACL constraints + Neo4j projection (no Fuseki on Pi) |
| | [0013](./0013-orc-certificate-fleet-collection.md) | Automated ORC certificate collection for race fleets |
| | [0014](./0014-shore-weather-current-collection.md) | Shore weather and current collection (PredictWind GRIB, MET, SMHI) |
| | [0017](./0017-marine-map-gpx-export.md) | Marine map GPX export bundle (PredictWind-compatible) |
| | [0019](./0019-predictwind-multi-model-grib.md) | PredictWind multi-model GRIB shore workflow |
| **2B — Graph import** | [0009](./0009-dual-repository-race-data.md) | (sync contract — see Phase 0) |
| | [0022](./0022-yaml-ld-interconnected-data.md) | YAML-LD for interconnected data |
| | [0023](./0023-shacl-neo4j-projection-no-fuseki.md) | SHACL + Neo4j projection map |
| **2C — GRIB, polars, AIS** | [0004](./0004-grib-polars-ais-wind-analysis.md), [0019](./0019-predictwind-multi-model-grib.md) | GRIB + PredictWind multi-model scoring, polars, AIS, wind analysis |
| **2D — Courses & results** | [0005](./0005-course-parsing-handicaps-live-results.md), [0020](./0020-course-editor-coordinate-system-of-record.md) | Course parsing; **course-editor** SoR for coordinates |
| | [0006](./0006-start-boat-course-flags.md) | Multiple courses per race and start-boat flag signaling |
| **2E — Race UX** | [0010](./0010-iregatta-reference-model.md), [0011](./0011-bg-h5000-reference-model.md), [0018](./0018-helm-ux-three-pi-dual-speaker.md) | iRegatta/H5000 parity in `race-ui` + Grafana |
| **2F — Analytics & alerts** | [0016](./0016-fleet-polar-performance-influx.md) | Fleet polar performance timeline stored in InfluxDB |
| | [0015](./0015-tactical-insight-alerts-annunciation.md) | Tactical insight alerts, UX feed, and optional voice annunciation |
| **2H — Race live sync & archive** | [0024](./0024-post-race-neo4j-export-to-data-repo.md), [0025](./0025-race-live-sync-github-temporal.md), [0026](./0026-race-lifecycle-scheduled-harbor-automation.md), [0027](./0027-data-repo-runtime-policy-zero-pi-config.md), [0028](./0028-enriched-live-snapshot-fleet-performance-temporal.md) | Live sync + enriched fleet snapshot |
| **2G — Laptop MCP** | [0012](./0012-race-side-mcp-laptop-cursor.md), [0029](./0029-signalk-mcp-ecosystem-vpn-remote-access.md) | Race-side MCP; Signal K ecosystem + VPN remote access |
| **3 — SLA-3 vision** | [0003](./0003-gopro-capture-and-shore-training.md) | GoPro HERO13 fleet capture and onshore TrimTransformer training |
| **4 — CI/CD** | [0008](./0008-github-docker-deployment-lifecycle.md) | (deployment lifecycle — see Phase 0) |
| | [0030](./0030-simple-hybrid-secrets-model.md) | Simple hybrid secrets model (GitHub CI + on-device runtime secrets) |
| | [0031](./0031-race-decision-intelligence-playbook.md) | Race decision intelligence playbook and answer contract |
| | [0032](./0032-yaml-ld-ontology-pyshacl-dq-reports.md) | YAML-LD ontology and pySHACL DQ reports (AI-sailing-data) |
| | [0033](./0033-vault-ld-okf-advisory-layer.md) | Vault-LD for OKF advisory layer only |
| **2I — Boat domotics & power** | [0035](./0035-home-assistant-non-nmea-domotics.md), [0036](./0036-victron-vecan-nmea2000-power.md) | Home Assistant non-NMEA; Victron VE.Can on N2K ingest |
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
| [0022](./0022-yaml-ld-interconnected-data.md) | YAML-LD for interconnected data in AI-sailing-data | 2A, 2B | Accepted |
| [0023](./0023-shacl-neo4j-projection-no-fuseki.md) | SHACL constraints and Neo4j projection (no Fuseki on Pi) | 2A, 2B | Accepted |
| [0024](./0024-post-race-neo4j-export-to-data-repo.md) | Post-race export — Neo4j insights to AI-sailing-data | 2H, 2F | Accepted |
| [0025](./0025-race-live-sync-github-temporal.md) | Race live sync — 5 min Neo4j → GitHub on LTE | 2H | Accepted |
| [0026](./0026-race-lifecycle-scheduled-harbor-automation.md) | Race lifecycle — schedule-driven harbor import & race mode | 2H | Accepted |
| [0027](./0027-data-repo-runtime-policy-zero-pi-config.md) | Data-repo runtime policy — zero per-race Pi env | 2H | Accepted |
| [0028](./0028-enriched-live-snapshot-fleet-performance-temporal.md) | Enriched live snapshot — fleet performance 5 min rollup | 2H, 2F | Accepted |
| [0029](./0029-signalk-mcp-ecosystem-vpn-remote-access.md) | Signal K MCP ecosystem alignment + VPN remote access | 2G | Accepted |
| [0030](./0030-simple-hybrid-secrets-model.md) | Simple hybrid secrets model for race operations | 4 | Accepted |
| [0031](./0031-race-decision-intelligence-playbook.md) | Race decision intelligence playbook | 2F, 2G | Accepted |
| [0032](./0032-yaml-ld-ontology-pyshacl-dq-reports.md) | YAML-LD ontology + pySHACL DQ reports | 2A | Accepted |
| [0033](./0033-vault-ld-okf-advisory-layer.md) | Vault-LD for OKF advisory layer only | 2A | Accepted |
| [0034](./0034-expedition-laptop-signalk-federation.md) | Expedition laptop bridge and Signal K federation | 2G | Accepted |
| [0035](./0035-home-assistant-non-nmea-domotics.md) | Home Assistant for non-NMEA boat systems on SLA-2 | 2I | Accepted |
| [0036](./0036-victron-vecan-nmea2000-power.md) | Victron VE.Can power system on NMEA 2000 (SLA-1 ingest) | 2I | Accepted |

## Format

Each ADR follows the structure:

1. **Context** — what forces are at play
2. **Decision** — what we chose
3. **Rationale** — why
4. **Consequences** — positive, negative, risks
5. **Alternatives considered**

New decisions should use the next sequential number: `0037-short-title.md`.

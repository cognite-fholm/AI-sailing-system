# AI Sailing System

An edge-first, AI-assisted competitive sailing platform built on [Signal K](https://signalk.org), designed to run aboard a Raspberry Pi with marine bus connectivity.

## Status

**Phase 0 — Specification.** Architecture, ADRs, deploy scaffolding, and GitHub Actions workflow stubs.

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/USER_GUIDE.md](./docs/USER_GUIDE.md) | **User guide** — shore prep links + onboard overview |
| [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) | Architecture index — repos, tiers, ADRs |
| [spec.md](./spec.md) | Full system specification |
| [docs/deployment-lifecycle.md](./docs/deployment-lifecycle.md) | GitHub + Docker CI/CD, Pi deploy, race freeze |
| [docs/race-laptop-mcp.md](./docs/race-laptop-mcp.md) | Laptop + Cursor + MCP at the regatta |
| [docs/mcp-neo4j-influx.md](./docs/mcp-neo4j-influx.md) | Neo4j & Influx MCP tool reference |
| [AI-sailing-data docs](https://github.com/cognite-fholm/AI-sailing-data/tree/main/docs) | **Race preparation** user guides |
| [docs/references/README.md](./docs/references/README.md) | iRegatta + H5000 manual links |
| [deploy/README.md](./deploy/README.md) | Env templates, digest locks, guardrails checklist |
| [adr/README.md](./adr/README.md) | All Architecture Decision Records |

## Goal

Help sailors **win races** by combining real-time onboard sensor data, historical performance analytics, tactical knowledge graphs, and local AI coaching — with or without internet connectivity.

## Three SLA tiers

| Tier | Domain | Runs on |
|------|--------|---------|
| **SLA-1** | On-boat telemetry (Signal K, InfluxDB) | Dedicated Pi + PiCAN-M |
| **SLA-2** | Race & competitor info (Neo4j, GRIB, polars, AIS, wind zones) | Separate Pi (or shared with SLA-3) |
| **SLA-3** | Sail performance vision (GoPro HERO13, Coral, vision LLM) | Separate Pi with Coral dongle |
| **SLA-S** | Onshore TrimTransformer training (gaming PC + CUDA) | Home — harbor only |

Each onboard tier has its own Docker Compose stack and may run on a **different Raspberry Pi**. See [spec.md §5](./spec.md#5-three-tier-sla-architecture) and [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

**Data repo:** Race and boat YAML live in [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) — synced onboard via `race-data-sync`.

**GoPro + ML loop:** HERO13 cameras → onboard geometry → harbor export → **TrimTransformer on gaming PC** → GHCR → boat. See [spec.md §7.9–7.11](./spec.md#79-gopro-hero13-black-fleet).

**Delivery:** **GitHub Actions** builds arm64 images to **GHCR**; Pis run **Docker Compose** with harbor-only **Watchtower** ([§9](./spec.md#9-deployment-architecture), [ADR-0008](./adr/0008-github-docker-deployment-lifecycle.md)).

**Wind & fleet:** GRIB refresh, polars, AIS, and wind-on-course analysis ([§7.12](./spec.md#712-grib-polars-ais--wind-on-course-analysis)).

**Courses & results:** SI PDF course parsing (Færderseilasen §11; Høstcup Bane A/B + start-boat flags), React waypoint + **Start Line** course selection, optional vision flag detection, live corrected-time standings, multi-handicap ORC + WRS ([§7.13–7.14](./spec.md#713-race-courses-waypoints--live-results)).

**Race UX reference:** [iRegatta](https://zifigo.com/) v2.86 ([§7.16](./spec.md#716-iregatta-reference-model--feature-traceability), [ADR-0010](./adr/0010-iregatta-reference-model.md)).

**Instrument reference:** [B&G H5000](https://www.bandg.com/bg/series/h5000/) ([§7.17](./spec.md#717-bg-h5000-reference-model--integration), [ADR-0011](./adr/0011-bg-h5000-reference-model.md)).

**Race laptop:** [Cursor + MCP on boat LAN](./docs/race-laptop-mcp.md) — live standings and ad hoc analysis ([§7.18](./spec.md#718-race-side-mcp--laptop-cursor), [ADR-0012](./adr/0012-race-side-mcp-laptop-cursor.md)).

## Quick stack

- **Marine data hub:** Signal K Server (Node.js)
- **Time series:** InfluxDB
- **Knowledge graph:** Neo4j
- **Dashboards:** Grafana
- **AI:** LLaMA via llama.cpp (local inference)
- **Hardware:** Raspberry Pi + PiCAN-M HAT + Google Coral accelerator

## Prior work

This system evolves the [cognite-fholm](https://github.com/cognite-fholm) CogSail ecosystem, replacing cloud CDF dependencies with open, edge-native storage and adding competitive-sailing AI.

See [spec.md §10 Lineage](./spec.md#10-lineage-from-cognite-fholm--cogsail) for the full mapping.

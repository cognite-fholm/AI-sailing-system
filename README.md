# AI Sailing System

An edge-first, AI-assisted competitive sailing platform built on [Signal K](https://signalk.org), designed to run aboard a Raspberry Pi with marine bus connectivity.

## Status

**Phase 0 — Specification.** This repository currently contains architecture documentation only.

## Documentation

| Document | Purpose |
|----------|---------|
| [spec.md](./spec.md) | System specification, architecture, technology choices, and lineage from prior CogSail work |
| [adr/0005-course-parsing-handicaps-live-results.md](./adr/0005-course-parsing-handicaps-live-results.md) | SI course parsing, handicaps, live results |
| [adr/0006-start-boat-course-flags.md](./adr/0006-start-boat-course-flags.md) | Multi-course regattas, start-boat flag signaling, vision assist |

## Goal

Help sailors **win races** by combining real-time onboard sensor data, historical performance analytics, tactical knowledge graphs, and local AI coaching — with or without internet connectivity.

## Three SLA tiers

| Tier | Domain | Runs on |
|------|--------|---------|
| **SLA-1** | On-boat telemetry (Signal K, InfluxDB) | Dedicated Pi + PiCAN-M |
| **SLA-2** | Race & competitor info (Neo4j, GRIB, polars, AIS, wind zones) | Separate Pi (or shared with SLA-3) |
| **SLA-3** | Sail performance vision (GoPro HERO13, Coral, vision LLM) | Separate Pi with Coral dongle |
| **SLA-S** | Onshore TrimTransformer training (GPU servers, harbor export) | Shore only — not at sea |

Each onboard tier has its own Docker Compose stack and may run on a **different Raspberry Pi**. See [spec.md §5](./spec.md#5-three-tier-sla-architecture).

**GoPro + ML loop:** HERO13 cameras capture sail/boom imagery → geometry & condition matching onboard → harbor export trains **TrimTransformer** onshore → quantized model returns to boat. See [spec.md §7.9–7.11](./spec.md#79-gopro-hero13-black-fleet).

**Wind & fleet:** GRIB refresh, polars, AIS, and wind-on-course analysis ([§7.12](./spec.md#712-grib-polars-ais--wind-on-course-analysis)).

**Courses & results:** SI PDF course parsing (Færderseilasen §11; Høstcup Bane A/B + start-boat flags), React waypoint + **Start Line** course selection, optional vision flag detection, live corrected-time standings, multi-handicap ORC + WRS ([§7.13–7.14](./spec.md#713-race-courses-waypoints--live-results)).

## Quick stack

- **Marine data hub:** Signal K Server (Node.js)
- **Time series:** InfluxDB
- **Knowledge graph:** Neo4j
- **Dashboards:** Grafana
- **AI:** LLaMA via llama.cpp (local inference)
- **Hardware:** Raspberry Pi + PiCAN-M HAT + Google Coral accelerator

## Prior work

This system evolves the [cognite-fholm](https://github.com/cognite-fholm) CogSail ecosystem, replacing cloud CDF dependencies with open, edge-native storage and adding competitive-sailing AI.

See [spec.md § Lineage](./spec.md#9-lineage-from-cognite-fholm--cogsail) for the full mapping.

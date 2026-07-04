# AI Sailing System

An edge-first, AI-assisted competitive sailing platform built on [Signal K](https://signalk.org), designed to run aboard a Raspberry Pi with marine bus connectivity.

## Status

**Phase 0 — Specification.** This repository currently contains architecture documentation only.

## Documentation

| Document | Purpose |
|----------|---------|
| [spec.md](./spec.md) | System specification, architecture, technology choices, and lineage from prior CogSail work |
| [adr/0001-system-architecture-and-technology-choices.md](./adr/0001-system-architecture-and-technology-choices.md) | Architecture Decision Record for core platform choices |

## Goal

Help sailors **win races** by combining real-time onboard sensor data, historical performance analytics, tactical knowledge graphs, and local AI coaching — with or without internet connectivity.

## Three SLA tiers

| Tier | Domain | Runs on |
|------|--------|---------|
| **SLA-1** | On-boat telemetry (Signal K, InfluxDB) | Dedicated Pi + PiCAN-M |
| **SLA-2** | Race & competitor info (Neo4j, tactical LLM) | Separate Pi (or shared with SLA-3) |
| **SLA-3** | Sail performance vision (GoPro HERO13, Coral, vision LLM) | Separate Pi with Coral dongle |
| **SLA-S** | Onshore TrimTransformer training (GPU servers, harbor export) | Shore only — not at sea |

Each onboard tier has its own Docker Compose stack and may run on a **different Raspberry Pi**. See [spec.md §5](./spec.md#5-three-tier-sla-architecture).

**GoPro + ML loop:** HERO13 cameras capture sail/boom imagery → geometry & condition matching onboard → harbor export trains **TrimTransformer** onshore → quantized model returns to boat. See [spec.md §7.9–7.11](./spec.md#79-gopro-hero13-black-fleet).

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

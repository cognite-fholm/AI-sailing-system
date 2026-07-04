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

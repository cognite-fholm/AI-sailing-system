# ADR-0001: System architecture and technology choices

**Status:** Accepted (SLA-2 tech table below superseded — see note)  
**Date:** 2026-07-04  
**Deciders:** cognite-fholm  
**Supersedes:** N/A (greenfield evolution of CogSail)

> **2026-07-20 update:** the SLA-2 "Knowledge graph: Neo4j" / "Coach / analytics API: Python"
> rows below are superseded by
> [AI-sailing-system-jvm ADR-0001](https://github.com/cognite-fholm/AI-sailing-system-jvm/blob/main/adr/0001-java-consolidated-sla2-graph-spatial-store.md):
> SLA-2 becomes one consolidated Java process (MCP folded in) with an embedded
> YouTrackDB graph store and an embedded H2GIS spatial store, replacing Neo4j and
> the 13 Python SLA-2 services. Signal K, InfluxDB, Grafana, and llama.cpp
> (this ADR's other rows) are unchanged. See also
> [ADR-0002](./0002-three-tier-sla-architecture.md)'s note.

---

## Context

We are building an **AI-assisted competitive sailing system** that must run aboard a vessel on a **Raspberry Pi**, connected to **NMEA 0183** and **NMEA 2000** marine buses via a **PiCAN-M HAT**, with optional **Google Coral** acceleration and the ability to operate **without internet** during races.

Prior work under [cognite-fholm](https://github.com/cognite-fholm) established a working pipeline:

```
Signal K WebSocket → RabbitMQ Streams → Cognite Data Fusion (time series + assets)
```

Key repositories:

- **cogsail-python** — production-quality Signal K delta parsing and CDF ingestion
- **subscribe_to_websocket** / **push_to_cdf** — stream buffer and cloud sink
- **cogsail-scripts** — MMSI-based vessel asset hierarchy in CDF
- **crawl_web** — race document crawling
- **CogSail** / **cogsail-raspberry** — earlier Java/Android onboard experiments

The new system must:

1. Help sailors **win races** (not just log data).
2. Remain **edge-first** and **offline-capable**.
3. Support **remote upgrades** when connectivity exists.
4. Reuse proven ingestion logic while **removing cloud lock-in** to CDF.

---

## Decision

We will implement the **AI Sailing System** with the following architecture:

| Layer | Technology |
|-------|------------|
| Marine data hub | **Signal K Server** (Node.js) |
| Field buses | **PiCAN-M HAT** — SocketCAN + serial |
| Time series | **InfluxDB 2.x** |
| Knowledge graph | **Neo4j 5.x** (Community) |
| Visualization | **Grafana OSS** |
| LLM inference | **LLaMA** via **llama.cpp** (GGUF, CPU on Pi) |
| Edge ML (non-LLM) | **Google Coral** + TFLite |
| Coach / analytics API | **Python** (FastAPI) |
| Deployment | **Docker Compose** on `linux/arm64` |
| CI/CD | **GitHub Actions** → **GHCR** |
| Remote updates | **Watchtower** (harbor mode only, SLA-2/3) + manual digest-pinned compose |
| Shore training | **Gaming PC** (SLA-S) — see [ADR-0008](./0008-github-docker-deployment-lifecycle.md) |

### Architectural principles

1. **Signal K is canonical** for live marine telemetry — all buses normalize to Signal K paths before downstream processing.
2. **InfluxDB for "when/how much"** — high-frequency numeric telemetry.
3. **Neo4j for "who/what/why"** — races, marks, tactics, vessels, maneuvers.
4. **Grafana for human consumption** — live and debrief dashboards.
5. **LLaMA runs on CPU** via llama.cpp; Coral handles separate ML tasks, not transformer LLMs.
6. **Offline by default** — cloud is optional; no runtime dependency on Cognite or external APIs during races.
7. **Three SLA tiers** — see [ADR-0002](./0002-three-tier-sla-architecture.md); isolated containers, optional multi-Pi deployment.
8. **GitHub + Docker for delivery** — Actions CI, GHCR registry, Compose on Pi; no cloud orchestration ([ADR-0008](./0008-github-docker-deployment-lifecycle.md)).

---

## Rationale

### Why Signal K (not custom NMEA parsing)?

- Already proven in **cogsail-python** (`ws://signalk:3000/signalk/v1/stream/?subscribe=all`).
- Native NMEA 0183/2000 support with PiCAN-M ([OpenPlotter](https://openplotter.org/), [CANboat](https://github.com/canboat/canboat) ecosystem).
- Plugin model allows incremental delivery (Influx, Neo4j, AI bridge) without forking core server.
- The Signal K project deprecated the Java server; **Node.js is the maintained reference implementation**.

### Why InfluxDB instead of CDF time series?

| CDF (prior) | InfluxDB (new) |
|-------------|----------------|
| Cloud SaaS; OAuth required | Local container; no auth dependency at sea |
| `externalId` per path | Measurement + tags (same mapping from `parse_signalK`) |
| Grafana via Cognite plugins | Native Grafana datasource |
| Extraction pipelines for monitoring | Built-in tasks + Grafana alerts |

The `parse_signalK()` function in cogsail-python already extracts `(timestamp, path, value)` tuples — this maps cleanly to Influx line protocol.

### Why Neo4j instead of CDF assets / graphs?

CDF provided:

- Asset hierarchy (country → fleet → MMSI vessel) via **cogsail-scripts**
- Data model instances for offsets and metadata

Neo4j provides:

- Explicit **tactical relationships** (mark roundings, leg sequences, fleet interactions).
- **Cypher** queries for coaching context ("last three times on this leg in 12 kt breeze").
- Local Community Edition — no cloud for graph queries at sea.

### Why Grafana?

Industry standard pairing with InfluxDB; supports alerting, annotations (race start/end), and mobile-friendly dashboards on the boat LAN.

### Why LLaMA + llama.cpp (not cloud LLM)?

- **FR-21:** No off-device data without opt-in.
- **FR-33:** 72+ hours without internet.
- llama.cpp delivers usable token rates on Pi 5 ARM cores with quantized models.
- LLaMA 3.2 1B–3B instruct models fit in 8 GB RAM with headroom for other containers.

### Why Coral if LLaMA runs on CPU?

[google-coral/coralnpu](https://github.com/google-coral/coralnpu) and Coral Edge TPU are optimized for **CNN / TFLite** workloads, not transformer attention at LLM scale. We still include Coral because:

- Maneuver/wake **event classifiers** can run at &lt;10 ms latency.
- Future **camera** inputs (crew, sail trim) benefit from hardware acceleration.
- Keeps AI architecture extensible without blocking v1 on Coral LLM support (which is not feasible).

### Why Docker Compose + Watchtower?

- **Reproducible** arm64 images across dev and Pi.
- **Remote upgrades:** GitHub Actions publishes to GHCR; Watchtower pulls when `RACE_MODE=false` and network is available (SLA-2/3 only).
- **Regatta freeze:** digest lock files in `deploy/locks/` — see ADR-0008.
- **Signal K caveat:** use host networking for CAN/serial stability; restart only in harbor per spec §8.2.
- **Offline fallback:** `docker load` from USB.

### Why not keep RabbitMQ?

cogsail-python used RabbitMQ Streams for decoupling WebSocket from CDF writes. On a single Pi:

- **Option A (v1 default):** Signal K plugin writes directly to InfluxDB (simpler, fewer containers).
- **Option B:** Redis Streams as lightweight buffer if write backpressure occurs.

RabbitMQ is heavier for Pi resource budgets; we defer unless load testing proves need.

---

## Consequences

### Positive

- **Offline-first** operation with no Cognite subscription or OAuth at sea.
- **Open stack** — each component is replaceable and well documented.
- **Clear migration** from cogsail-python parsing and MMSI models.
- **Grafana + Influx** is a familiar ops pattern for many teams.
- **Neo4j** unlocks tactical queries impossible in flat time series alone.

### Negative / trade-offs

- **Operational burden** — we own backups, upgrades, and monitoring (previously partly in CDF).
- **Neo4j + Influx + Grafana + Signal K + llama.cpp** is multiple containers; Pi 5 8 GB recommended.
- **LLM quality** — 3B quantized on Pi is not GPT-4 class; coaching must be grounded in structured data (RAG).
- **Coral underutilized** in v1 if no custom TFLite models ship early.
- **Remote updates** risk brief Signal K restarts — mitigated by harbor-only Watchtower policy.

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| SD card wear | NVMe on Pi 5; Influx retention policies |
| Power loss corruption | UPS; `restart: unless-stopped`; ext4 journaling |
| LLM hallucination in tactics | RAG-only answers; cite Influx/Neo4j facts; disallow autonomous actuation |
| CAN bus mis-wiring | Document PiCAN-M terminator jumper; pre-flight `candump` check |
| Image pull fails at sea | Pin digests; USB offline load; never auto-update in race mode |

---

## Alternatives considered

### A. Keep Cognite Data Fusion

**Rejected.** Requires internet and OAuth; latency and cost unsuitable for live race coaching; vendor lock-in for a personal/hobby competitive sailing stack.

### B. TimescaleDB instead of InfluxDB

**Deferred.** Viable Postgres-compatible option; InfluxDB chosen for Grafana ergonomics and prior team familiarity. May revisit if SQL joins with race metadata become critical.

### C. Ollama instead of llama.cpp

**Deferred.** Ollama is simpler UX but adds daemon overhead; llama.cpp offers finer control for embedded Pi deployment. Ollama may wrap llama.cpp in a later convenience layer.

### D. Java Signal K server

**Rejected.** Deprecated upstream; prior CogSail Java repos are stale.

### E. Single SQLite store for everything

**Rejected.** Cannot handle high-frequency multi-path telemetry and graph queries in one embedded DB at race scale.

### F. Kubernetes (k3s) on Pi

**Rejected for v1.** Compose is sufficient; k3s adds complexity without benefit for a single-node boat computer.

---

## Compliance with requirements

| Requirement | How this ADR satisfies it |
|-------------|---------------------------|
| Signal K based | Signal K Server is hub |
| Neo4j not CDF graph | Neo4j Community for tactical graph |
| InfluxDB for sensors | Primary telemetry store |
| Grafana visualization | Dashboard layer |
| LLaMA for AI | llama.cpp + GGUF |
| Raspberry Pi | arm64 Compose target |
| Coral dongle | TFLite edge ML sidecar |
| PiCAN-M HAT | SocketCAN + serial in Signal K config |
| Remote container deploy | Watchtower + GHCR |
| Offline operation | All services local; no cloud runtime deps |

---

## Related documents

- [spec.md](../spec.md) — full system specification
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) — consolidated architecture index
- [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) — race/boat content repo ([ADR-0009](./0009-dual-repository-race-data.md))
- [cogsail-python](https://github.com/cognite-fholm/cogsail-python) — prior Signal K → CDF pipeline
- [ADR-0010](./0010-iregatta-reference-model.md) — iRegatta race UX reference
- [ADR-0011](./0011-bg-h5000-reference-model.md) — B&G H5000 instrument reference
- [ADR template](https://adr.github.io/) — format reference

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-04 | Initial accepted decision |
| 1.1 | 2026-07-05 | Related docs: dual repo, iRegatta, H5000 ADRs |

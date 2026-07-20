# ADR-0002: Three-tier SLA architecture with isolated containers

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** cognite-fholm  
**Supersedes:** Partial refinement of ADR-0001 (single-stack assumption)  
**Related:** [ADR-0001](./0001-system-architecture-and-technology-choices.md), [spec.md §5](../spec.md#5-three-tier-sla-architecture)

> **2026-07-20 update:** SLA-2's "13 separate containers, Neo4j" model below is
> superseded by [AI-sailing-system-jvm ADR-0001](https://github.com/cognite-fholm/AI-sailing-system-jvm/blob/main/adr/0001-java-consolidated-sla2-graph-spatial-store.md) —
> SLA-2 is now one consolidated Java process (internal module boundaries with
> bounded executors per module, not OS-level container isolation), embedding
> YouTrackDB + H2GIS. SLA-1 and SLA-3 as described here are unchanged.

---

## Context

ADR-0001 defined a single Docker Compose stack on one Raspberry Pi. In practice, the AI Sailing System serves three workloads with **very different reliability and compute profiles**:

1. **On-boat telemetry** — NMEA ingest, live instruments. Must not fail or lag during a race.
2. **Race and competitor information** — Neo4j graph, fleet tracking, tactical text LLM. Important but tolerates brief outages.
3. **Sail performance vision** — camera capture, Coral preprocessing, vision LLM analysis of sail trim. CPU/RAM intensive; best-effort latency.

Running all three on one Pi without isolation risks vision or LLM workloads starving Signal K and InfluxDB during a start sequence or mark rounding — exactly when telemetry matters most.

---

## Decision

Partition the system into **three SLA tiers**, each with:

- A **dedicated Docker Compose file** (`docker-compose.sla-1.yml`, `.sla-2.yml`, `.sla-3.yml`).
- **Separate containers** per concern — no shared processes across tiers.
- **Optional dedicated Raspberry Pi hardware** per tier in the recommended race profile.
- **One-way data dependencies** — SLA-2 and SLA-3 may **read** from SLA-1; they never write to SLA-1 storage.

### Tier summary

| Tier | Name | SLA | Primary store | LLM | Hardware |
|------|------|-----|---------------|-----|----------|
| **SLA-1** | Telemetry | 99.99% | InfluxDB | None | Pi 5 + PiCAN-M (dedicated in race profile) |
| **SLA-2** | Race & competitors | 99.9% | Neo4j | Text (llama.cpp) | Pi 5 8 GB |
| **SLA-3** | Sail performance vision | 95% | Image store | Vision (llama.cpp multimodal) | Pi 5 8 GB + Coral + cameras |

### Deployment profiles

| Profile | Topology |
|---------|----------|
| **Compact** | 1× Pi — all tiers with cgroup limits + tier-watchdog |
| **Standard** | 2× Pi — SLA-1 isolated; SLA-2 + SLA-3 shared |
| **Race** | 3× Pi — one tier per node (**chosen deployment for this project**) |

### Inter-tier rules

- SLA-1 exposes InfluxDB read API and optional Signal K WebSocket fan-out.
- SLA-2 publishes race context to SLA-3; SLA-3 publishes `SailAnalysis` to SLA-2.
- SLA-1 auto-update via Watchtower: **never** during race mode.
- SLA-3 may be paused by tier-watchdog when SLA-1 write latency degrades.

---

## Rationale

### Why three tiers instead of one Compose stack?

| Concern | Single stack | Three tiers |
|---------|--------------|-------------|
| Telemetry during vision inference spike | Risk of CPU starvation | SLA-1 isolated on own Pi |
| Independent upgrade | All-or-nothing restart | Upgrade SLA-3 without touching Signal K |
| SLA measurement | One uptime number | Per-domain targets |
| Hardware fit | One 8 GB Pi overloaded | PiCAN-M on telemetry; Coral on vision |

### Why separate LLMs for SLA-2 and SLA-3?

- **SLA-2 text LLM** (3B instruct) — fast tactical Q&A, debrief; low token latency.
- **SLA-3 vision LLM** (multimodal) — sail image analysis; larger model, slower, different container lifecycle.

Mixing both in one `llama.cpp` process couples failure modes and memory pressure.

### Why Neo4j only in SLA-2?

Race and competitor data is relational/tactical — graph fits SLA-2's "important but not sub-second" profile. Telemetry stays in InfluxDB (SLA-1) to keep the critical path simple.

### Why cameras only in SLA-3?

Image capture and vision inference are the heaviest workloads. Isolating them prevents USB bandwidth and CPU contention with CAN/serial on the PiCAN-M HAT (SLA-1).

---

## Consequences

### Positive

- Clear **failure domains** — vision crash does not stop instruments.
- **Independent scaling** — add a third Pi only when sail analysis is needed.
- **Targeted SLAs** — crew can trust SLA-1 numbers even if coaching is degraded.
- **Per-tier CI/CD** — publish `ghcr.io/.../sla-1-*` images separately.

### Negative

- **More moving parts** — 3 compose files, 3 Grafana instances, boat LAN DNS.
- **Cross-tier latency** — sail analysis depends on network hop to SLA-1 Influx (typically &lt;5 ms on boat LAN).
- **Compact profile complexity** — cgroup limits and tier-watchdog required on single Pi.

### Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Boat LAN partition | SLA-1 fully autonomous; SLA-2/3 show degraded banner |
| Crew confusion (3 Grafana URLs) | Unified landing page on `telemetry.local` linking all three |
| Vision LLM too slow on Pi | Reduce capture rate; use smaller vision quant; dedicated SLA-3 Pi |
| Accidental SLA-1 upgrade at sea | Watchtower disabled on `docker-compose.sla-1.yml` always |

---

## Alternatives considered

### A. Single Pi, single Compose, no tiers

**Rejected.** Vision + text LLM + Signal K compete for RAM and CPU; violates telemetry SLA.

### B. Two tiers (telemetry vs. everything else)

**Deferred.** Lumps race graph and sail vision together; vision still starves Neo4j queries under load.

### C. Cloud tier for vision

**Rejected.** Conflicts with offline-first requirement and FR-31 (no off-device data without opt-in).

### D. Kubernetes (k3s) for tier orchestration

**Rejected for v1.** Compose per tier is sufficient; k3s adds complexity on resource-constrained Pis.

---

## Compliance

| Requirement | Satisfied by |
|-------------|--------------|
| Separate containers per domain | 3 compose files, no cross-tier containers |
| Different RPi devices | Race profile: 3 nodes; documented in spec §5.4 |
| On-boat telemetry SLA | SLA-1: 99.99%, dedicated Pi + PiCAN-M |
| Race/competitor info | SLA-2: Neo4j, competitor-sync, crawl_web lineage |
| Sail picture LLM analysis | SLA-3: cameras, Coral, llama-vision |

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-04 | Initial accepted decision |

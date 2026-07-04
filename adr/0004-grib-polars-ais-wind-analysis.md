# ADR-0004: GRIB scheduling, polar fleet registry, AIS ingest, and wind-on-course analysis

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** cognite-fholm  
**Related:** [ADR-0002](./0002-three-tier-sla-architecture.md), [spec.md §7.12](../spec.md#712-grib-polars-ais--wind-on-course-analysis)

---

## Context

Competitive sailing tactics depend on knowing **where better wind exists on the course** — not only from forecast models but from **how the fleet is actually performing**. The system must:

1. Keep **GRIB** wind grids current via regular upload/download.
2. Load **polar diagrams** for the own boat and competitors to know expected vs actual speed.
3. Collect **AIS** for own boat and fleet from the onboard NMEA 2000 network.
4. Run **runtime analysis** fusing these inputs during a race without cloud dependency.

Prior CogSail work (`cogsail-scripts`) organized vessels by MMSI but did not integrate GRIB, polars, or tactical wind mapping.

---

## Decision

Implement in **SLA-2** as dedicated containers:

| Service | Responsibility |
|---------|----------------|
| `grib-ingest` | Scheduled fetch (6 h), manual upload, USB inbox |
| `grib-parser` | GRIB2 → queryable wind grid |
| `polar-manager` | Own-boat **SLK** parse + canonical YAML serve |
| `polar-certificate-extractor` | Competitor **PNG/PDF** ORC certificate → derived polar |
| `ais-collector` | AIS from SLA-1 Signal K stream → Influx + Neo4j |
| `wind-field-analyzer` | Fuse GRIB + instruments + AIS/polar deltas → `WindAdvantageZone` |

**AIS ingest path:** N2K AIS PGNs → PiCAN-M → Signal K (SLA-1) → WebSocket fan-out → `ais-collector` (SLA-2). No duplicate AIS decoder on SLA-2.

**GRIB schedule:** Automatic every 6 hours when `ONLINE_MODE=true`; parsed grids persist for offline race use.

**Wind analysis:** Course sectors scored every 30–60 s using GRIB TWS/TWD, instrument bias correction, and fleet **SOG minus polar-expected SOG** as observed wind-pressure proxy.

**Polar sources:**

- **Own boat:** SYLK file `7710 (3).slk` (dev: `C:\Repositories\boat_system\7710 (3).slk`).
- **Competitors:** ORC certificate images/PDFs (e.g. `off_course.png`) → OCR + VPP-lite → derived polar with confidence score.

---

## Rationale

### Why GRIB on a schedule?

Forecast models update on fixed cycles (GFS 6 h). Harbor connectivity enables automatic refresh; parsed grids remain available offshore.

### Why polars for competitors?

AIS SOG alone is ambiguous (better trim vs better wind). Comparing to **each vessel's polar** isolates geographic wind advantages.

### Why AIS via Signal K?

Single N2K decode path on SLA-1 preserves the telemetry SLA. SLA-2 consumes read-only streams — no second CAN listener.

### Why runtime wind zones vs GRIB-only?

GRIB resolution (0.25°+) misses micro-scale pressure. Fleet overperformance on one side of a beat is a strong local signal — standard grand-prix analytics practice.

---

## Consequences

### Positive

- Unified tactical picture: forecast + observations + fleet behavior.
- Works offline after last GRIB sync (degraded but functional).
- Polar % dashboards for own boat and selected competitors.

### Negative

- GRIB storage and parse CPU on SLA-2 Pi.
- Competitor polars may be unavailable — analyzer falls back to SOG ranking without polar normalization.
- AIS class B sparse updates reduce fleet signal quality.

### Risks

| Risk | Mitigation |
|------|------------|
| Stale GRIB | Age warning; instrument bias correction |
| Missing competitor polar | Flag `polar_confidence: low`; weight fleet term down |
| AIS dropout | Decay track confidence; show last-known position |

---

## Alternatives considered

### A. Cloud GRIB API at race time

**Rejected.** Offline requirement.

### B. Single polar for entire fleet

**Rejected.** Different hulls have different speed potential — normalization requires per-MMSI polars.

### C. GRIB only (no AIS fusion)

**Rejected.** Does not satisfy "where good wind exists" from live fleet evidence.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-04 | Initial accepted decision |

# ADR-0005: Course parsing from SI PDFs, multi-handicap scoring, and live results

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0004](./0004-grib-polars-ais-wind-analysis.md), [ADR-0010](./0010-iregatta-reference-model.md), [spec.md §7.13–7.14](../spec.md#713-race-courses-waypoints--live-results)

---

## Context

Norwegian and international regattas publish **course descriptions** in Sailing Instructions (SI) as narrative text — often with partial GPS coordinates (e.g. Færderseilasen 2026 §11). Results use **multiple handicap systems** on the same ORC certificate, and **ORC Weather Routing Scoring (WRS)** introduces **per-race TCF** values.

The system must:

1. Parse courses from competition PDFs into waypoint sequences with coordinates where stated.
2. Allow manual coordinate entry when marks are named only (React/TS on Pi).
3. Compute **VMG** and **live corrected-time standings** for own boat and competitors.
4. Store **several handicap numbers per boat** and select the active one per race rules.

For regattas with **multiple courses per race** signaled from the start boat (e.g. Høstcup Bane A/B), see [ADR-0006](./0006-start-boat-course-flags.md).

**Reference files:**

- `Seilingsbestemmelser_Færderseilasen26_2.pdf` — chapter 11 routes
- `ORC Certificate for Off Course.pdf` — APH ToT 1.2082, triple-number options, CertNo 667232

---

## Decision

### Course parsing (`course-parser`)

- Ingest SI/NOR PDFs; detect chapter 11 (Løpene) and route subsections (11.1–11.5).
- Regex-parse Norwegian coordinate format `N59°52,50' Ø010°38,76' (WGS)`.
- Store `CourseRoute` + `Waypoint` nodes; `coords: null` where only names given.

### Waypoint editor (`course-editor`)

- React + TypeScript SPA on `race.local:3010`.
- Map pin placement for missing coordinates; sync to Neo4j via REST.

### Live results (`live-results`)

- Fuse AIS progress + waypoint route + active handicap.
- Rank fleet: `corrected_time = elapsed × handicap` (SI §23).
- Publish `LiveStanding` every 30 s; VMG toward next mark for all tracked vessels.

### Handicaps (`handicap-manager`)

- Parse **all** scoring options from ORC certificate PDF (not just one TCF).
- Support **per-race WRS TCF** override when issued by ORC.
- Selection: WRS &gt; SI-specified method &gt; triple-number by TWS &gt; default APH.

---

## Rationale

Manual transcription of §11 routes at sea is error-prone. Automated PDF parse + map editor covers both stated coordinates and named marks.

Multiple handicaps on one certificate (Norwegian "Singeltall", "Trippeltall", etc.) cannot be reduced to a single number without knowing SI scoring method.

WRS TCF is race-specific — must not overwrite certificate ratings in the database.

---

## Consequences

### Positive

- VMG and standings grounded in actual course geometry.
- Live scratch sheet during distance races.
- Correct handicap applied per regatta rules.

### Negative

- PDF layout variance across regattas requires parser maintenance.
- WRS TCF may arrive late — need manual upload workflow.
- React editor adds frontend build to SLA-2 image pipeline.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial accepted decision |

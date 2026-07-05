# ADR-0006: Multiple courses per race and start-boat flag signaling

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0005](./0005-course-parsing-handicaps-live-results.md), [spec.md §7.13.2–7.13.3](../spec.md#7132-multiple-courses-per-race--start-boat-flag-signaling)

---

## Context

Many Norwegian regattas publish **several course options** for the same race. The active course is not fixed in the NOR — it is communicated at the **start line** by flags on the **committee / start boat**.

**Høstcup 2025** (`Seilingsbestemmelser Høstcup 2025 ENDELIG.pdf`) is the reference:

| Signal | Course |
|--------|--------|
| Numeral pennant **2** on start boat | **Bane A** (Vedlegg 1, ~22 nm) |
| Numeral pennant **3** on start boat | **Bane B** (Vedlegg 1, ~23 nm) |
| Flag **T** on start boat | First mark rounded **starboard** (else port) |
| Class flags **Oscar / Echo / Foxtrot** | Fleet classes 1–3 (§7) |
| Vedlegg 2 (baneseilaser) | No numeral / **2** / **3** → different WL sequences |

The system must model all variants, show the crew their **class flag** and available **course signals**, let them **confirm** the course observed on the start boat, and optionally **suggest** a course from a GoPro photo — with **user override** always available.

This differs from **Færderseilasen**-style parsing (ADR-0005), where routes are named sections in §11 narrative text.

---

## Decision

### Data model (Neo4j)

Add node labels:

- `ClassFlag` — fleet class ICS flag (Oscar, Echo, Foxtrot)
- `StartBoatSignal` — display on start boat → `CourseRoute`
- `SupplementarySignal` — modifier (e.g. **T** → first-mark rounding)
- `CourseSelection` — active route for a `race_id` + `source` (`user` | `vision` | `default`)

Relationships:

```cypher
(Regatta)-[:HAS_CLASS]->(ClassFlag)
(Regatta)-[:OFFERS_COURSE]->(CourseRoute)
(CourseRoute)-[:REQUIRES_SIGNAL]->(StartBoatSignal)
(Race)-[:USES_SELECTION]->(CourseSelection)
(CourseSelection)-[:SELECTED_ROUTE]->(CourseRoute)
(Vessel)-[:SAILS_IN_CLASS]->(ClassFlag)
```

### Parsing profile `flag_signaled`

`course-parser` detects Vedlegg-style tables and emits `courses/{regatta_id}.json` with `class_flags`, `start_boat_signals`, `supplementary_signals`, and all `CourseRoute` variants. Coordinates extracted where present in appendix tables.

### UX — `course-editor` Start Line panel (`:3010/start`)

1. Show **own class flag** (from `vessel.yaml` `regatta.class_no` or harbor setup).
2. Show **course signal options** for that class (numeral pennants + route names).
3. Toggle **supplementary flags** (e.g. **T**).
4. If vision suggestion exists: show confidence + **Accept** / **Override**.
5. **Confirm** → `POST /courses/selection` → locks route for `race_id`.

Downstream services (`live-results`, `wind-field-analyzer`, tactical LLM) use **only** the selected `CourseRoute`.

### Vision — `course-flag-detector` (optional)

- Input: GoPro still or upload including start boat.
- Output: `{ suggested_route_id, flags_detected[], confidence }`.
- **Never auto-lock** by default; user must confirm (configurable high-confidence auto-select for advanced setups).
- Can run on SLA-2 (lightweight) or SLA-3 (shared Coral with sail vision).

### Configuration

- [`config/courses-hostcup.yaml`](../config/courses-hostcup.yaml) — Høstcup example
- [`config/courses.yaml`](../config/courses.yaml) — Færderseilasen narrative routes

---

## Consequences

**Positive**

- Matches real regatta workflow (observe flags → sail the signaled course).
- Same UX covers manual pick (Færderseilasen) and flag-signaled regattas (Høstcup).
- Vision assist reduces errors under pre-start pressure; override preserves crew authority.

**Negative**

- ICS flag rendering and numeral pennant detection add UI and ML scope.
- `CourseSelection` must be set before live results / VMG are meaningful at race start.

**Neutral**

- Extends ADR-0005; does not replace narrative SI parsing.

---

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Single `active_route` in YAML only | Cannot represent multiple variants or start-boat signaling |
| Auto-select course from vision without confirm | SI authority is the committee boat; vision may misread in swell/rain |
| Encode flags only in UI, not Neo4j | Live results and wind analysis need structured `CourseSelection` |

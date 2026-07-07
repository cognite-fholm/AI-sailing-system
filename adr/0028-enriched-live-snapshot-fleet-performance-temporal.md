# ADR-0028: Enriched live snapshot — fleet performance temporal model

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0016](./0016-fleet-polar-performance-influx.md), [ADR-0025](./0025-race-live-sync-github-temporal.md), [ADR-0005](./0005-course-parsing-handicaps-live-results.md), [spec §7.27](../spec.md#727-enriched-live-snapshot), [spec §7.22](../spec.md#722-fleet-polar-performance-timeline), [spec §11.20](../spec.md#1120-enriched-live-snapshot)

---

## Context

[ADR-0025](./0025-race-live-sync-github-temporal.md) pushes `RaceLiveSnapshot` to GitHub every **5 minutes** on LTE. Git commits provide a **timeline**, but each tick only helps tactically when the snapshot answers concrete fleet questions:

| Question | Needs |
|----------|--------|
| Results if the race finished **now**? | Corrected-time rank, Δ to leader, `course_pct`, leg |
| Who sails **above** polar — where, in what conditions? | `performance_pct`, position, TWS/TWA, rank |
| Who sails **below** polar? | Same |
| Who has better **course / speed toward the mark**? | `vmg_actual`, `vmg_pct`, `course_pct` progress vs fleet |
| Who seems to have **better wind or current**? | Position + GRIB / fleet wind proxy + SOG patterns |

[ADR-0016](./0016-fleet-polar-performance-influx.md) and [spec §7.22](../spec.md#722-fleet-polar-performance-timeline) define **30 s** `fleet_polar_performance` in Influx — the high-resolution source on the boat. The 5-minute git export is a **rollup + delta layer** for shore agents and cloud AI, not a replacement for Influx or Neo4j.

**Non-goals:** Replace git/YAML-LD prep, duplicate full AIS tracks in git, or require Dolt (optional analytical add-on in §6).

---

## Decision

### 1. Three-layer temporal model

```text
Layer 1 (30 s)   Influx race.fleet_polar_performance + Neo4j LiveStanding
Layer 2 (5 min)  RaceLiveSnapshot on git branch race-live/{regatta_id}
Layer 3 (opt.)   Dolt tables — row-level DOLT_DIFF between sequences
```

| Layer | SoT for | Consumers |
|-------|---------|-----------|
| Influx | Raw performance time series | Grafana, boat services, rollup job |
| Git `RaceLiveSnapshot` | Agent-readable tick + precomputed insights | Cursor, cloud AI, `git log` playback |
| Dolt (optional) | SQL diffs between ticks | Analytics, “who gained most in 30 min?” |

### 2. Extend `RaceLiveSnapshot.spec`

Keep single file `race-live/current.yaml` per [ADR-0025](./0025-race-live-sync-github-temporal.md). Enrich `spec`:

| Field | Source | Purpose |
|-------|--------|---------|
| `observed_at`, `sequence`, `race_phase` | Export tick | Timeline index |
| `standings[]` | `live-results` | **If finished now** — corrected seconds, rank, Δ leader |
| `fleet_performance[]` | 5 min rollup of Influx + AIS | Per-boat polar %, VMG %, position, env |
| `course_selection` | Neo4j | Active route / leg |
| `insights[]` | Precomputed on boat | Outliers, VMG leaders, wind-advantage groups |
| `grib_scores` | GRIB model scoring | Wind-field context |
| `deltas` | vs `sequence - 1` | Fleet rank change, own-boat summary |

#### `standings[]` (corrected-time if finished now)

```yaml
standings:
  - rank: 4
    sail_number: NOR-10133
    vessel_name: Xbox
    is_own: true
    corrected_seconds: 28800
    delta_to_leader_s: 420
    elapsed_seconds: 27650
    handicap_factor: 1.042
    course_pct: 0.32
    leg_seq: 2
```

#### `fleet_performance[]` (per vessel at tick)

```yaml
fleet_performance:
  - sail_number: NOR-10133
    is_own: true
    rank: 4
    rank_delta_since_last: -1
    lat: 59.12
    lon: 10.45
    leg_seq: 2
    course_pct: 0.32
    tws: 8.2
    twa: 38.0
    sog: 6.8
    bsp: 6.5
    vmg_actual: 5.1
    vmg_target: 5.4
    vmg_pct: 94.4
    performance_pct: 98.6
    polar_outlier: neutral   # above | below | neutral
    data_quality: ok
    polar_source: slk
```

Thresholds (configurable per regatta in `planning/runtime-policy.yaml` or defaults):

- `above`: `performance_pct >= 105`
- `below`: `performance_pct <= 90`
- else `neutral`

#### `insights[]` (precomputed answers)

| `type` | Content |
|--------|---------|
| `polar_outperformers` | Boats above threshold + conditions summary |
| `polar_underperformers` | Boats below threshold + conditions summary |
| `vmg_leaders_leg` | Best VMG toward mark on current leg |
| `course_progress_leaders` | Largest `course_pct` gain since last tick |
| `wind_advantage` | Geographic / GRIB-based group comparison |
| `corrected_time_if_now` | Optional narrative rank snapshot |

### 3. Rollup contract — `race-live-sync`

Every `RACE_LIVE_SYNC_INTERVAL_MINUTES` (default 5):

1. Read **previous** `sequence` from `sync-manifest.yaml`.
2. Query Influx: `fleet_polar_performance` for `[observed_at - 5m, observed_at]` — aggregate **mean** `performance_pct`, `vmg_pct`, last `rank`, `lat`, `lon`, `tws`, `twa` per `sail_number`.
3. Query `live-results` / Neo4j for `standings` and `course_selection`.
4. Compute `rank_delta_since_last` vs prior snapshot (in memory or read prior tick from Neo4j cache).
5. Run **insight rules** (polar outliers, VMG leaders, wind groups).
6. Write `current.yaml` + `sync-manifest.yaml`; git commit + push.

**Does not** re-sample raw AIS at 5 min — uses Layer 1 aggregates.

### 4. Question → field mapping

| Tactical question | Primary fields |
|-------------------|----------------|
| Results if finished now? | `standings[]` sorted by `corrected_seconds` |
| Above polar? | `fleet_performance[].polar_outlier == above` + `insights[type=polar_outperformers]` |
| Below polar? | `polar_outlier == below` + `polar_underperformers` |
| Better toward mark? | Sort `fleet_performance` by `vmg_actual` or `vmg_pct` on same `leg_seq`; `insights[vmg_leaders_leg]` |
| Better wind/current? | `insights[wind_advantage]`; compare `tws`/`twa` at `lat`/`lon` vs fleet median; GRIB from `grib_scores` |

### 5. Services and ownership

| Service | Role |
|---------|------|
| `fleet-performance-tracker` | Write 30 s Influx ([ADR-0016](./0016-fleet-polar-performance-influx.md)) |
| `live-results` | Corrected-time rank, leg, `course_pct` |
| `polar-manager` | Target BSP/VMG |
| `race-live-sync` | 5 min rollup → YAML + git push |
| `wind-field-analyzer` | GRIB at fleet positions → `wind_advantage` insight |

### 6. Optional — Dolt analytical mirror

For row-level “diff tick 41 → 42” without parsing YAML:

- Tables: `live_tick`, `live_standing`, `live_fleet_performance` (one row per boat per `sequence`).
- Dual-write from `race-live-sync` after YAML write.
- Git remains agent + archive format; Dolt is **not** SoT.

Defer implementation until Layer 1–2 are stable.

---

## Consequences

### Positive

- 5-minute git timeline answers tactical fleet questions in one YAML read
- Cloud AI / Cursor need no VPN to boat Neo4j or Influx
- Composes with existing Influx schema (§7.22) — no duplicate 30 s data in git
- Playback: `git log` + `sequence` or optional Dolt `DOLT_DIFF`

### Negative

| Risk | Mitigation |
|------|------------|
| Competitor wind is estimated | Tag `data_quality`; own boat uses instruments |
| Large fleets → big YAML | Cap tracked fleet; summarize tail boats |
| Rollup lag | `observed_at` on every row; Influx for sub-5 min |
| Insight rules wrong | Tune thresholds; insights are advisory |

---

## Implementation artifacts

| Artifact | Repository | Status |
|----------|------------|--------|
| `RaceLiveSnapshot` schema extension | AI-sailing-data `schema/neo4j-mapping.yaml` | Done |
| `race-live/current.yaml.example` | AI-sailing-data `races/.../race-live/` | Done (fixture) |
| `live-results` — corrected-time standings | AI-sailing-system `live-results/` | Partial (Neo4j reader + rank) |
| `fleet-performance-tracker` — 30 s Influx rollup | AI-sailing-system `fleet-performance-tracker/` | Partial (rollup + writer scaffold) |
| `race_live_sync/export.py` — 5 min rollup | AI-sailing-system `race-live-sync/` | Done (insights, deltas, policy) |
| Unit + BDD tests | AI-sailing-system `tests/unit`, `tests/bdd/features/phase_02h_*` | Done |
| `docs/RACE_LIVE_SYNC.md` | AI-sailing-data | Done |
| Spec §7.27, §11.20 | AI-sailing-system | Done |
| Layer 3 Dolt dual-write | — | Deferred |

**Loop engineering:** Layer 1 (30 s Influx) and Layer 2 (5 min git) ship first; Dolt row diffs follow when rollups are stable in production.

---

## References

- [ADR-0025 Race live sync](./0025-race-live-sync-github-temporal.md)
- [ADR-0016 Fleet polar Influx](./0016-fleet-polar-performance-influx.md)
- [ADR-0005 Live results](./0005-course-parsing-handicaps-live-results.md)
- [Dolt](https://github.com/dolthub/dolt) — optional Layer 3

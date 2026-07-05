# ADR-0019: PredictWind multi-model GRIB and onboard model scoring

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0004](./0004-grib-polars-ais-wind-analysis.md), [ADR-0014](./0014-shore-weather-current-collection.md), [spec §7.12](../spec.md#712-grib-polars-ais--wind-on-course-analysis), [PredictWind models](https://www.predictwind.com/features/models), [PredictWind Marine app](https://apps.apple.com/us/app/predictwind-marine-forecasts/id477048487)

---

## Context

Oslofjord and Skagerrak races need **the best available forecast resolution**, not a single coarse global model. [PredictWind](https://www.predictwind.com/features/models) provides multiple high-resolution models (e.g. ECMWF, GFS, SPIRE, HARMONIE/AROME-class regional products — exact set per subscription and region). MET Norway remains valuable for **current** and **waves** in the fjord.

The system must:

1. Ingest **multiple GRIB files** per cycle (PredictWind download and/or shore export).
2. Prefer **highest practical resolution** for the active race bbox.
3. Run **ongoing onboard assessment** of which model best matches observed wind for **this race** and **this time window**.

---

## Decision

### 1. Primary forecast source — PredictWind

| Channel | When | Responsibility |
|---------|------|----------------|
| **PredictWind GRIB download** | Harbor + when `ONLINE_MODE=true` | `grib-ingest` — multiple models per fetch cycle |
| **PredictWind web / Marine app** | Shore prep, manual | Crew validates; export GRIB to `collected/weather/grib/` in data repo |
| **MET Norway gribfiles** | Supplement | Current, waves, Oslofjord context ([ADR-0014](./0014-shore-weather-current-collection.md)) |
| **Manual upload** | Anytime | USB / `POST /grib/upload` |

Shore skill **`predictwind-grib`** in AI-sailing-data documents download paths, model list, and manifest layout.

### 2. Multi-model storage

Each ingest registers a `GribModel` node with:

- `provider` (`predictwind`, `metno`, `manual`)
- `model_id` (e.g. `ecmwf`, `gfs`, `spire`, `harmonie` — from file metadata or manifest)
- `resolution_km`, `valid_from`, `valid_to`, `bbox`

All parsed models remain available offline after harbor sync.

### 3. Onboard model scoring — `grib-model-scorer`

New SLA-2 service (or module in `wind-field-analyzer`) runs **continuously during active `race_id`**:

1. Sample **observed** TWD/TWS from SLA-1 instruments (and optional SMHI validation at harbor).
2. For each ingested model, compare forecast at boat position vs observation over rolling windows (e.g. 30 min, 2 h, leg-to-date).
3. Compute **error scores** (vector wind RMSE, bias).
4. Publish **`ActiveWindModel`** selection per race/time — highest score with minimum sample count.
5. `wind-field-analyzer` uses **active model** for heatmap; fuses fleet AIS signal across models when scores are close.

Scores stored in Influx (`grib_model_score`) and Neo4j for debrief and Grafana panel **“Best model this leg”**.

### 4. Resolution policy

- **Always ingest the finest resolution** available from PredictWind for the race bbox (clip on ingest if needed).
- Do **not** default to 0.25° GFS when regional/high-res PredictWind GRIB exists.
- MET coarse GFS is **fallback only** when PredictWind files are absent.

---

## Rationale

- PredictWind is already used for route export (ADR-0017 GPX compatibility) and marine forecasts.
- Multi-model ensemble with **observation-based selection** beats picking one model at harbor time for long races (Færder, overnight legs).
- MET Norway adds current/waves MET cannot get from PredictWind alone in the fjord.

---

## Consequences

### Positive

- Best available resolution on the boat
- Adaptive model choice as conditions evolve
- Clear provenance per model in debrief

### Negative

- PredictWind subscription and manual export steps on shore
- More GRIB storage and parse CPU on SLA-2 Pi
- Scorer needs sufficient instrument data before switching models mid-race

### Risks

| Risk | Mitigation |
|------|------------|
| PredictWind API/export changes | Manual upload path; manifest in data repo |
| All models wrong in thermal bubble | Fleet AIS overperformance signal (ADR-0004) |
| Storage full | Per-race retention; prune models &gt; 7 days |

---

## Follow-up

- [ ] `predictwind-grib` skill in AI-sailing-data
- [ ] `config/grib-sources.yaml` — PredictWind source entries
- [ ] `grib-model-scorer` service
- [ ] Grafana panel + `race-ui` model indicator
- [ ] Update `grib-plan.yaml` on Færder 2026

---

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| GFS 0.25° only (OQ-1) | Too coarse; user requires best resolution |
| Pick one model at harbor | No adaptation during long races |
| Cloud-only PredictWind | Offline race requirement |

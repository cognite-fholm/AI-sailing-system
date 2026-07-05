# ADR-0014: Shore weather and current collection (Oslofjord)

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0004](./0004-grib-polars-ais-wind-analysis.md), [ADR-0009](./0009-dual-repository-race-data.md), [spec §7.20](../spec.md#720-shore-weather--current-collection), [AI-sailing-data weather skills](https://github.com/cognite-fholm/AI-sailing-data/tree/main/.cursor/skills)

## Context

Many regattas (Færderseilasen, Hankø, Sandvika, Drøbak) sail in **Oslofjorden** and **Skagerrak**. Tactical prep needs:

1. **Wind/wave/current forecasts** at fjord resolution — not only global GFS
2. **Visual current maps** for tidal strategy (start line, Færder approach)
3. **Observed wind** at Skagerrak boundaries for forecast validation

Sources identified by the team:

| Source | Data | Format |
|--------|------|--------|
| [MET gribfiles API](https://api.met.no/weatherapi/gribfiles/1.1/) | Wind, current, waves | GRIB2 |
| [Oslofjord varsler](https://projects.met.no/~nilsmk/oslofjord/) | Links to GRIB + current PNG plots | GRIB + PNG |
| [YR GRIB help](https://hjelp.yr.no/hc/en-us/articles/360009342993-GRIB-weather-data) | Same files, human docs | — |
| [Oslofjord 0.1 API](https://api.met.no/weatherapi/oslofjord/0.1/) | Current forecast maps (`ferder1`–`ferder4`) | PNG |
| [SMHI MetObs](https://opendata-download-metobs.smhi.se/) | Wind obs (e.g. Väderöarna 81350) | JSON |

GRIB binaries are too large for routine git commit; **metadata and manifests** live in **AI-sailing-data** per race.

## Decision

1. **Weather collection is shore-side** in **AI-sailing-data**, linked to each race via `planning/grib-plan.yaml` and `collected/weather/`.
2. **Three Cursor skills:**
   - `metno-oslofjord-weather` — GRIB download + `WeatherCollection` manifest
   - `oslofjord-current-plots` — PNG fetch + **agent interpretation** guide (no CV pipeline in v1)
   - `smhi-wind-observations` — MetObs JSON for validation stations
3. **Primary model stack for Oslofjord:** MET Norway `gribfiles` (`weather` + `current` + `waves` area `oslofjord`).
4. **Onboard:** `grib-ingest` (SLA-2) reads files from `/data/grib/` copied at harbor — unchanged from ADR-0004.
5. **Human layer:** `planning/weather-notes.md` records interpretation (current images, SMHI vs GRIB).

## Rationale

- **MET gribfiles** is stable, machine-friendly, and matches YR / OpenCPN local models sailors already use.
- **PNG current plots** are faster for humans/agents to reason about than raw u/v grids alone — dedicated interpretation skill reduces errors.
- **SMHI** fills the Skagerrak observation gap; station 81350 is exposed and API is simple JSON.
- Keeping collection in the **data repo** ties weather to the same race folder as fleet, courses, and planning.

## Consequences

### Positive

- Repeatable pre-race weather pull with provenance
- Færder-specific areas (`ferder4` etc.) documented
- Clear split: git = plans + manifests; boat disk = GRIB binaries

### Negative

- Oslofjord 0.1 PNG API is legacy/low-maintenance — must cross-check GRIB
- SMHI stations are Swedish coast — not inside inner Oslofjord
- Agent interpretation of PNGs is qualitative until numeric GRIB sampling is automated

### Risks

| Risk | Mitigation |
|------|------------|
| MET API terms violation | User-Agent + license link in manifest |
| Stale GRIB at start | `updated` timestamp in manifest; 12 h re-fetch in grib-plan |
| Misread current arrows | reference.md + cross-check GRIB |

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| GFS-only | Too coarse for fjord current |
| Commit GRIB to git | Repo size; use manifest + harbor copy |
| Automated CV on PNGs | Over-engineering for v1; agent + reference sufficient |

## Follow-up

- [ ] MET Frost skill for Norwegian land stations
- [ ] Kartverket tide API in weather bundle
- [ ] `wind-field-analyzer` ingest `WeatherCollection` metadata at harbor

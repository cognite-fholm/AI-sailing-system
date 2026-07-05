# ADR-0017: Marine map GPX export bundle (PredictWind-compatible)

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0005](./0005-course-parsing-handicaps-live-results.md), [ADR-0006](./0006-start-boat-course-flags.md), [spec §7.23](../spec.md#723-marine-map-gpx-export), [AI-sailing-data marine-map-gpx-export skill](https://github.com/cognite-fholm/AI-sailing-data/tree/main/.cursor/skills/marine-map-gpx-export)

## Context

Race courses in **AI-sailing-data** are structured as `CourseCatalog` + `WaypointList` YAML (parsed from SI/NOR). Helm crews also need routes on **marine chart apps** — Navionics, PredictWind Marine, OpenCPN, B&G/VRM, Raymarine — which import **GPX routes**.

A proven bundle format (reference: `Hollenderen2018.zip`) contains:

```
Hollenderen2018/
  RouteBlue.gpx
  RouteRed.gpx
  Routepwe.gpx
  Routepwg.gpx
```

Each GPX file is **GPX 1.1** with a single `<rte>` element and dense `<rtept lat="…" lon="…">` points — created by PredictWind (`creator="www.predictwind.com"`). This imports cleanly into MFD/chartplotter route libraries.

Today course YAML lives in git but there is **no standard export** for onboard chart systems. Manual re-entry at the regatta is error-prone.

## Decision

1. **Generate** PredictWind-compatible GPX route files from race `WaypointList` YAML — shore-side via Cursor skill **`marine-map-gpx-export`** in AI-sailing-data.
2. **Store** per race under `export/marine-map/`:
   - One `.gpx` per route variant
   - Zip bundle `{slug}{year}.zip` (legacy profile) or `{year}-{slug}-marine-map.zip` (standard)
   - `manifest.yaml` (`kind: MarineMapExport`) with provenance and file index
3. **Interpolate** great-circle segments between resolved mark coordinates (default **0.5 NM** step) so chart apps draw a continuous route — not just sparse marks.
4. **Link** export to `CourseCatalog` — regenerate when routes or coordinates change.
5. **Optional** `course-editor` / `course-parser` pipeline calls the same generator post-parse (Phase 2).

### GPX schema (v1)

```xml
<gpx creator="AI-sailing-data" version="1.1" xmlns="http://www.topografix.com/GPX/1/1" …>
  <rte>
    <name>{route_display_name}</name>
    <desc>{section} — {race_name}</desc>
    <src>{route_id}</src>
    <rtept lat="59.51430" lon="10.61730"/>
    …
  </rte>
</gpx>
```

`predictwind_compat` profile sets `creator="www.predictwind.com"` for maximum importer compatibility.

### Zip layout profiles

| Profile | Folder inside zip | File naming |
|---------|-------------------|-------------|
| `predictwind_legacy` | `{RaceName}{Year}` e.g. `Hollenderen2018` | `Route{variant}.gpx` — variant from `export_label` or route name |
| `standard` | `{year}-{slug}` | `route-{route_id}.gpx` |

## Rationale

- **GPX 1.1 `<rte>`** is the lowest-common-denominator for chart apps; PredictWind export is already validated by the team.
- **Git-stored bundle** travels with the race folder via `race-data-sync` — copy zip to SD card / phone at harbor.
- **Interpolation** produces MFD-friendly polylines from sparse SI mark lists.
- **Separate from Neo4j** — static export artifact; live navigation still uses `race-intelligence` + Signal K.

## Consequences

### Positive

- One-click harbor export for all course variants (Færder §11.1–11.6, W/L baner, etc.)
- Same source of truth as `course-editor` and `live-results`
- Debrief can compare sailed track (Influx AIS) vs exported route GPX

### Negative

- SI marks without coordinates produce gaps — export lists `unresolved_waypoints` in manifest
- Interpolated legs are rhumb/great-circle — not tidal-optimized like PredictWind weather routes
- Manual `export_label` needed for legacy color names (`Blue`, `pwe`)

### Risks

| Risk | Mitigation |
|------|------------|
| Wrong route on chart | `manifest.yaml` checksums; version tied to `CourseCatalog` git sha |
| Sparse coords | Flag in manifest; course-parser must fill coords before export |
| Duplicate zip names | Include `race_id` in manifest metadata |

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| KML only | Weaker chartplotter support vs GPX |
| RTZ | Not all apps support; GPX already works for user |
| Generate only on boat | Shore prep should have chart routes before start |
| Waypoints only (no interpolation) | Poor display on Navionics/PredictWind vs Hollenderen reference |

## Follow-up

- [ ] `course-parser` auto-run export after SI PDF parse
- [ ] `course-editor` "Export marine map" button → POST to export API
- [ ] Import sailed track overlay (GPX track from Influx) for debrief

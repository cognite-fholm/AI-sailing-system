# ADR-0010: iRegatta as reference feature catalog and UX benchmark

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [spec.md §7.16](../spec.md#716-iregatta-reference-model--feature-traceability), [ADR-0004](./0004-grib-polars-ais-wind-analysis.md), [ADR-0005](./0005-course-parsing-handicaps-live-results.md), [ADR-0006](./0006-start-boat-course-flags.md)

**Primary reference:** [iRegatta User Manual v2.86](https://zifigo.com/sites/default/files/iRegattaUserManual.pdf) (Let's Create, 2012)

---

## Context

**iRegatta** (iPhone/iPad, since 2009) is a mature racing app used by many sailors for start timing, VMG steering, laylines, polar performance, and waypoint navigation. The product owner uses iRegatta regularly and wants the AI Sailing System to **cover the same functional surface** — while extending it with fleet AIS, GRIB fusion, live handicap standings, and shore-prepared race data from GitHub.

The iRegatta manual documents features across **views**, **settings**, **import/export**, and **NMEA integration**. Without an explicit catalog, implementation risk drifting: we might build advanced fleet analytics but miss basics (e.g. burn/gain start bar, perpendicular distance-to-line).

This ADR records **every iRegatta feature** from the manual and maps each to spec sections, containers, and parity status.

---

## Decision

### 1. Treat iRegatta as the UX and racing-math benchmark

| Principle | Application |
|-----------|-------------|
| **Parity first** | Start line, VMG, laylines, polar %, wind-shift lift — match iRegatta semantics before adding fleet-only features |
| **Same formulas where documented** | Distance-to-line ⊥ extensions; TTL at current COG/SOG; VMG toward mark when navigating |
| **Extend, don't replace** | iRegatta is single-boat + optional NMEA Wi‑Fi; we add AIS fleet, GRIB, Neo4j, corrected-time standings |
| **Import compatibility** | Support **GPX** routes/waypoints and polar data interchange (iRegatta CSV ↔ our SLK/YAML) where practical |

### 2. View catalog (iRegatta → system mapping)

iRegatta navigation: swipe between views (iPhone landscape; iPad merges some views). Our primary UX is **`course-editor`** (start + nav) + **`grafana-race`** (race + fleet).

| iRegatta view | Core features (manual) | AI Sailing System target | Spec / container |
|---------------|------------------------|--------------------------|------------------|
| **Help** | Version, what's new | `okf/` + Grafana about panel | §7.16.1 |
| **Race** | 4 configurable readouts; BIG-mode; COG/SOG damping (3/5/10 s); lift indicator (10 s avg vs current heading, threshold); speed & VMG history graphs (2/4/10/20 min); performance bar vs polar; steering bars (optimum VMG tack/jibe) | `grafana-race` dashboards + `live-results` API | §7.12, §7.13.5, §7.16.2 |
| **Layline** | Tack/jibe lines from polar or manual angles; grey bearing/heading; upwind/downwind from wind vs waypoint bearing | `course-editor` Laylines panel + `polar-manager` | §7.16.3 |
| **Start** | Countdown + sync-to-minute + pause; timer beeps; auto-switch at gun; mark pin/boat ends (or stored waypoints); favored end (green/red); wind arrow vs line; ⊥ distance-to-line; bow offset; time-to-line; over-line red; **burn/gain** bar | `course-editor` Start Line panel + `start-line-calculator` | §7.13.3, §7.16.4 |
| **Wind** | Manual TWD: type / compass shoot / two-tack average; TWS slider; tack/jibe from polar; fields disabled when NMEA wind present | Signal K wind + manual override in `course-editor` | §7.16.5 |
| **Wind history** | 30 min graph; sample every 30 s | InfluxDB `wind_history` + Grafana time series | §7.16.5 |
| **Navigation** | Start/pause nav to waypoint; route prev/next; auto-advance at distance; next-leg bearing, length, est. TWA | `course-editor` + Neo4j `CourseRoute` | §7.13, §7.16.6 |
| **Waypoint admin** | List/add/delete; routes from waypoint list; formats DMS / D°M.m'; temp wpt by bearing+distance; cross-bearing (compass) | `course-editor` + `AI-sailing-data` `courses/` YAML | §7.13.4, §7.16.6 |
| **Statistics** | Max speed, trip odometer, position; optional Google Maps | Grafana stats panel; offline map tiles | §7.16.7 |
| **Polar (stats)** | View/record polars 1–20 kt; update-polar setting; reset; enlarge on iPhone | `polar-manager` SLK; recording optional v2 | §7.12.3, §7.16.8 |
| **Import/Export** | `polarExport.csv` (20×360°); `waypointExport.gpx`; iTunes file sharing | `polar-manager` import; GPX ↔ data repo; harbor sync | §7.16.9 |
| **Polar trim** | Mirror angles; interpolate missing TWA; smooth 10°/4 kt spans | `polar-manager` post-process for derived polars | §7.16.8 |
| **NMEA** | NMEA 0183 over Wi‑Fi TCP/UDP; checksum ignore; magnetic/true heading; true wind from apparent+heading+STW; optional RMB target (beta) | Signal K (SLA-1) — superset of iRegatta NMEA | §7.1, §7.16.10 |
| **Wind instrument** | True vs apparent wind angles on bow diagram; north arrow | Grafana wind rose / `grafana-race` | §7.16.10 |

### 3. Global UI behaviors (iRegatta → system)

| iRegatta feature | Manual detail | System implementation |
|------------------|---------------|----------------------|
| **GPS freshness dot** | Grey/blue/green/yellow/orange/red by age; accuracy number | Signal K `navigation.position` age badge on dashboards |
| **Screen lock** | Swipe lock; optional auto-lock after idle | `course-editor` kiosk/lock mode for wet hands |
| **Display** | White/black theme; speed units (kn etc.); distance units for start | Grafana theme + user prefs in `course-editor` |
| **Units** | Speed + distance tied to knot setting | Config: knots, nm, °T/°M |

### 4. Settings catalog (iRegatta Settings app)

| Settings section | Options | Maps to |
|------------------|---------|---------|
| **Display** | Color theme; show performance bar ON/OFF; show steering bar ON/OFF | Grafana + `course-editor` prefs |
| **GPS** | Damping none/3/5/10 s (COG, SOG); lift threshold °; graph timeframe 2/4/10/20 min | Influx queries / dashboard variables |
| **Start** | Countdown start value; timer beep ON/OFF | `StartSequence` in Neo4j; audio via tablet |
| **Start** | Offset from bow (GPS antenna → bow) | `vessel.yaml` `bow_offset_m` |
| **Polar** | Update polar ON/OFF (record while sailing) | Future: `polar-recorder` — non-goal v1 |
| **Waypoint** | Format: D / D°M' / D°M.m' | `course-editor` coordinate parser |
| **Navigation** | Auto-advance route ON/OFF; auto-advance distance | `live-results` mark-rounding detector |
| **NMEA** | Use NMEA instead of GPS; TCP vs UDP; IP/port; ignore checksum; magnetic vs true; send NMEA target (RMB) | Signal K server config (SLA-1) |
| **Auto lock** | Auto screen lock seconds | `course-editor` |

### 5. Calculation semantics (must match iRegatta)

These formulas are **normative** for parity (see spec §7.16.11):

| Calculation | iRegatta definition | Our service |
|-------------|---------------------|-------------|
| **Lift indicator** | Current heading − 10 s average heading (when steering AWA) | `live-results` / Grafana |
| **Damping** | Rolling average COG/SOG over N seconds | Influx `moving_average` or query |
| **Performance %** | `actual_speed / polar_speed(TWS,TWA) × 100` | `polar-manager` + `live-results` |
| **VMG (navigating)** | Toward bearing to active waypoint | `live-results` §7.13.5 |
| **VMG (not navigating)** | Toward current wind direction | `live-results` fallback |
| **Distance to line** | Perpendicular from position to line **and extensions** — not distance to pin | `start-line-calculator` |
| **Time to line** | Time to cross line/extensions at current COG & SOG; `X:XX` if sailing away; red if OCS | `start-line-calculator` |
| **Burn/gain** | Compare TTL vs countdown; red bar = % speed to burn; green = % speed to add; yellow on target; grey if away/OCS | `start-line-calculator` |
| **Favored end** | Green end upwind beat to first mark; wind arrow exaggerated | `start-line-calculator` + TWD |
| **True wind** | From NMEA apparent + heading + STW; fallback COG+SOG | Signal K `environment.wind` |

### 6. Data interchange

| Format | iRegatta | AI Sailing System |
|--------|----------|-------------------|
| **Polars** | CSV 20 rows TWS × 360 columns TWA | **SLK** primary; import CSV → YAML via `polar-manager`; export YAML → CSV for iRegatta |
| **Waypoints/routes** | GPX export/import (additive import) | `courses/routes/*.yaml` + GPX import/export in `course-editor` |
| **Start line ends** | Tap at boat/pin or pick stored waypoints | `course-editor` map pins + SI waypoints from data repo |
| **Temporary marks** | Bearing+distance from current position; cross-bearing | `course-editor` quick-mark tools |

### 7. Features beyond iRegatta (intentional scope)

| Capability | Why not in iRegatta | Our addition |
|------------|----------------------|--------------|
| Fleet AIS + live standings | Single-boat app | `ais-collector`, `live-results`, §7.13.6 |
| GRIB wind-on-course | No weather model | `wind-field-analyzer`, §7.12 |
| Multi-handicap ORC | Not a scoring app | `handicap-manager`, §7.14 |
| Start-boat course flags | Manual course entry | ADR-0006, `course-flag-detector` |
| Shore Git race prep | On-device only | `AI-sailing-data`, ADR-0009 |
| Competitor polars | Own boat focus | `polar-certificate-extractor` |
| AI coaching | — | SLA-2 LLM + OKF |

### 8. Non-goals (iRegatta features deferred)

| Feature | Reason |
|---------|--------|
| **In-app polar recording** while sailing | v1 uses ORC SLK; recording adds noise without instrument-grade wind |
| **Google Maps live** on water | Offline map tiles only; no internet dependency |
| **NMEA RMB target output** | Beta in iRegatta; low priority vs Signal K hub role |
| **iOS-specific gestures** | Web/React UX instead |

---

## Rationale

iRegatta encodes **15+ years** of racing UX decisions (start line math, burn/gain, laylines). Re-documenting from scratch risks subtle errors (e.g. perpendicular distance-to-line). Explicit traceability ensures `course-editor` and `grafana-race` deliver familiar tools to the crew.

Our system remains **distinct**: edge Pi, NMEA 2000, multi-vessel graph, and shore-prepared regatta data — but the **single-boat racing cockpit** should feel as capable as iRegatta for the skipper.

---

## Consequences

### Positive

- Shared vocabulary between owner and implementers ("burn/gain bar", "BIG-mode readouts").
- Test cases derived from manual (TTL, OCS, favored end).
- GPX/CSV interchange enables migration from iRegatta waypoint libraries.

### Negative

- Large UX surface for `course-editor` — phased delivery required (see spec §14).
- Some iRegatta features (polar recording, RMB out) distract from fleet analytics — explicitly deferred.

### Risks

| Risk | Mitigation |
|------|------------|
| Formula drift vs iRegatta | Unit tests with manual examples; §7.16.11 golden cases |
| Manual outdated (v2.86) | Re-check App Store release notes periodically |
| Grafana ≠ swipe views | `course-editor` emulates Race/Start/Layline as tabs |

---

## Alternatives considered

### A. No formal iRegatta mapping

**Rejected.** Owner expectation is iRegatta-class racing tools.

### B. Use iRegatta on board instead of custom UX

**Rejected.** No fleet AIS, GRIB fusion, Neo4j, or Git-synced regatta data; iOS-only.

### C. Reimplement iRegatta as native iOS app

**Rejected.** Stack is Pi + Grafana + React; cross-platform web fits boat LAN tablets.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial catalog from iRegatta User Manual v2.86 |

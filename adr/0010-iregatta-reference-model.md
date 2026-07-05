# ADR-0010: iRegatta as functional reference model

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [spec.md §7.16](../spec.md#716-iregatta-reference-model--feature-traceability), [ADR-0004](./0004-grib-polars-ais-wind-analysis.md), [ADR-0005](./0005-course-parsing-handicaps-live-results.md), [ADR-0006](./0006-start-boat-course-flags.md)

**Reference manual:** [iRegatta User Manual v2.86](https://zifigo.com/sites/default/files/iRegattaUserManual.pdf) (Let's Create / Zifigo, © 2012)

---

## Context

**iRegatta** (iPhone/iPad, since 2009) is a mature **race and navigation app** used by many competitive sailors. It combines internal GPS, optional **NMEA 0183 over Wi‑Fi**, polar-based performance guidance, start-line tools, laylines, and waypoint/route navigation in a swipe-based UI.

The AI Sailing System targets **grand-prix and ORC handicap racing** with richer fleet, handicap, and course data than a phone app — but the **crew-facing tactical loop** (start → beat → mark → run → finish) should feel as capable and trustworthy as iRegatta for the features sailors already rely on.

This ADR records **every major iRegatta capability** from the v2.86 manual and maps it to our containers, UX surfaces, and functional requirements so nothing is lost in translation.

---

## Decision

Adopt **iRegatta v2.86** as the **functional reference model** for SLA-2 race UX and `race-intelligence` behavior. Implementation surfaces:

| Surface | Role |
|---------|------|
| **`grafana-race`** | Race, start, wind-instrument, history graphs, performance bar, GPS health |
| **`course-editor`** (`:3010`) | Navigation, waypoints, routes, start-line setup, course flags |
| **`race-intelligence`** | Lift detection, steering guidance, start burn/gain, favored end |
| **`polar-manager`** | Polar targets, performance %, tack/jibe angles from SLK |
| **`live-results`** | VMG toward mark, leg progress (extends iRegatta nav VMG) |
| **`handicap-manager` + `live-results`** | Corrected-time fleet ranking (**beyond iRegatta**) |

Polar **source of truth** remains **ORC SLK** in `AI-sailing-data` (not onboard CSV recording). GPX and sparse polar CSV remain **interop formats** for import.

---

## iRegatta feature inventory (manual v2.86)

### Platform and navigation

| Feature | iRegatta behavior |
|---------|-------------------|
| Device | iPhone (landscape) / iPad (landscape + portrait) |
| Main navigation | Horizontal swipe between views; two-level stack on iPhone (e.g. Race → Layline) |
| Page indicator | Dots at bottom of view |
| Settings location | iOS Settings app → iRegatta section |
| Help view | In-app help + release notes on update |

### Global UI and settings

| Feature | iRegatta behavior |
|---------|-------------------|
| GPS freshness dot | Grey / blue (&lt;2 s) / green (&lt;5 s) / yellow (&lt;10 s) / orange (&lt;20 s) / red (&gt;20 s) |
| GPS accuracy | Numeric HDOP/accuracy next to dot |
| Screen lock | Top-center slider; blocks touch; optional auto-lock after idle |
| Display theme | White-on-black or black-on-white |
| Speed units | Configurable (knots, etc.) |
| Distance units | Follow speed units (nm when knots) |
| COG/SOG damping | None, 3, 5, or 10 s rolling average (not compass/STW) |
| Lift threshold | Ignore shifts &lt; N° (default context: 5°) |
| Graph timeframe | Speed/VMG history: 2, 4, 10, or 20 minutes |
| Performance bar | ON/OFF — hide when wind manual-only |
| Steering bars | ON/OFF — VMG steering hints |
| Waypoint coordinate format | DMS or D°M.mmm |
| Auto-lock | Idle seconds → screen lock |

### Race view

| Feature | iRegatta behavior |
|---------|-------------------|
| Four readouts | Center; long-press 2 s → cycle data type per slot |
| BIG-mode | Tap readout → enlarged; tap second → alternates every 3 s |
| Lift indicator | Current heading vs 10 s average heading (wind-shift proxy) |
| Speed history | Bar graph; green faster / red slower / yellow unchanged |
| VMG history | Same as speed graph |
| Performance bar | Current speed vs polar at TWS/TWA → % |
| Steering bars | Five arrows each side → optimum VMG course from tack/jibe angles |

**Readout types (when NMEA available):** SOG, COG, STW, compass, AWA, AWS, TWD, TWS, VMG, etc. (manual lists instrument-dependent set).

### Layline view

| Feature | iRegatta behavior |
|---------|-------------------|
| Activation | Requires active navigation target |
| Upwind/downwind | Inferred from wind vs bearing to waypoint |
| Laylines | Red tack/jibe lines from polar optimum VMG angles or manual angles |
| Bearing line | Grey line to waypoint |
| Heading | Grey arrow for current heading |

### Start view

| Feature | iRegatta behavior |
|---------|-------------------|
| Countdown | Start / Pause / Sync buttons |
| Sync | Rounds to nearest minute (3:25→3:00, 3:42→4:00); paused+sync resets original |
| Timer beep | Optional: each minute, 30 s, 10 s, last 5 s at 1 Hz |
| Auto-switch | At 0:00 → Race view |
| Line ends | Sail to ends; tap Pin / Boat buttons; or pick stored waypoints |
| Favored end | Green = favored, red = unfavored (upwind beat to first mark assumption) |
| Wind vs line | Exaggerated wind arrow above line |
| Distance to line | Perpendicular to line **and extensions**; bow offset configurable |
| Time to line | At current COG/SOG until crossing line/extension |
| Away from line | TTL shows `X:XX` |
| Over line | Readouts in red |
| Burn or gain bar | Visual early (red, top) / on-time (yellow) / late (green, bottom); % speed adjust implied |

### Wind view

| Feature | iRegatta behavior |
|---------|-------------------|
| Wind direction | (1) Type in, (2) Shoot compass, (3) Two close-hauled tacks → bisect |
| Wind speed | Slider |
| Tack/jibe angles | Manual entry OR from polar (“Tack and Jibe from Polar”) |
| NMEA wind | Disables manual entry; display-only |

### Wind history

| Feature | iRegatta behavior |
|---------|-------------------|
| Duration | 30 minutes |
| Sample interval | 30 seconds |
| Data | TWD and TWS trends |

### Navigation view

| Feature | iRegatta behavior |
|---------|-------------------|
| Target | Single waypoint or route |
| Start / Pause | Begin or halt navigation |
| VMG basis | Toward waypoint bearing when navigating |
| Bottom readouts | Bearing and distance to active waypoint |
| Route stepping | Previous / Next buttons |
| Auto-advance | When within configured distance of waypoint |
| Next leg preview | Bearing, length, estimated TWA |

### Waypoint and route administration

| Feature | iRegatta behavior |
|---------|-------------------|
| List / select | Tap to set navigation target |
| Delete | Swipe row; Delete All with confirm |
| Add waypoint | Name + coordinates; prefilled with current position |
| Add route | Name; pick waypoints in order from pool |
| Temp waypoint — bearing & distance | From current position |
| Temp waypoint — cross-bearing | Two positions + compass shots (low accuracy noted) |
| GPX export | `waypointExport.gpx` |
| GPX import | Appends waypoints/routes (no overwrite) |

### Statistics view

| Feature | iRegatta behavior |
|---------|-------------------|
| Max speed | Since reset |
| Trip odometer | Since reset |
| Position | Current lat/lon |
| Map | Google Maps when online; optional start line + waypoint overlay |
| Polar display | Per-wind-speed slider (view only) |
| Polar record | Onboard recording 1–20 kt (needs good wind data) |
| Polar reset | Clears all recorded polars |

### Polar import/export and trim

| Feature | iRegatta behavior |
|---------|-------------------|
| Export format | `polarExport.csv` — 20 TWS rows × 360 TWA columns |
| Import | Via iTunes File Sharing |
| Trim | Mirror port/starboard; interpolate missing TWA; smooth 10° spans; interpolate across TWS; smooth 4 kt spans |
| Update mode | Record performance into polar vs use fixed polar |

### NMEA view and setup

| Feature | iRegatta behavior |
|---------|-------------------|
| Protocol | NMEA 0183 |
| Transport | Wi‑Fi TCP or UDP to instrument bridge |
| Use NMEA vs GPS | Toggle — use instrument GPS when ON |
| Checksum | Optional ignore for non-compliant talkers |
| Compass | Magnetic vs true display |
| True wind | Computed from apparent + heading/STW; fallback COG/SOG |
| Wind instrument | Split true vs apparent; bow angle coloring; north arrow |
| Outbound RMB | Every 8 s when navigating (beta) — autopilot target |
| Logging | Suggests iNMEAlogger for debugging |

### Documented calculations (iRegatta)

| Quantity | Rule |
|----------|------|
| Lift | Current heading − 10 s average heading |
| Damping | Rolling mean over N seconds |
| Performance % | `actual_speed / polar_speed(TWS,TWA) × 100` |
| VMG (navigating) | Toward waypoint bearing |
| VMG (not navigating) | Toward wind direction |
| Distance to line | Perpendicular from position to line and extensions |
| Time to line | Time to cross line/extension at current COG and SOG |
| True wind | From NMEA apparent + heading/STW or COG/SOG fallback |

---

## Traceability — iRegatta → AI Sailing System

| iRegatta area | Our component / UX | Spec | FR | Status |
|---------------|-------------------|------|-----|--------|
| Race readouts | `grafana-race` race panel | §7.16.2 | FR-42 | Planned |
| BIG-mode / configurable tiles | Grafana panel variables + drill-down | §7.16.2 | FR-42 | Planned |
| Lift indicator | `race-intelligence` → Influx + Grafana | §7.16.3 | FR-44 | Planned |
| Speed/VMG history | Grafana time-series panels | §7.16.2 | FR-45 | Planned |
| Performance bar | `polar-manager` + Grafana | §7.12, §7.16.2 | FR-12, FR-46 | Partial |
| Steering bars | `race-intelligence` optimum VMG hints | §7.16.3 | FR-47 | Planned |
| Laylines | `grafana-race` map overlay + `course-editor` | §7.16.4 | FR-48 | Planned |
| Start countdown + sync/beep | `course-editor` Start + `race-intelligence` | §7.16.5 | FR-49 | Planned |
| Line ends + favored end | `course-editor` + `race-intelligence` | §7.16.5 | FR-50 | Planned |
| DTL / TTL / bow offset | `race-intelligence` | §7.16.5 | FR-51, FR-52 | Planned |
| Burn or gain | `race-intelligence` | §7.16.5 | FR-52 | Planned |
| Manual wind + two-tack | `course-editor` Wind panel; degraded mode | §7.16.6 | FR-53 | Planned |
| Wind history 30 min | Influx + Grafana | §7.16.6 | FR-54 | Planned |
| Waypoints / routes | `AI-sailing-data` YAML + `course-editor` | §7.13, §7.15 | FR-30 | Partial |
| Auto-advance route | `live-results` leg state machine | §7.16.7 | FR-55 | Planned |
| Temp waypoints | `course-editor` | §7.16.7 | FR-56 | Planned |
| GPX import/export | `course-parser` / `race-import` adapter | §7.16.8 | FR-57 | Planned |
| Polar CSV 20×360 | `polar-manager` interop import | §7.16.9 | — | Planned |
| Polar trim | `polar-certificate-extractor` post-process | §7.16.9 | FR-58 | Planned |
| SLK polar (own boat) | `polar-manager` primary | §7.12 | FR-19–23 | Specified |
| Onboard polar record | **Out of scope** — use SLK + shore prep | §7.16.9 | — | Rejected |
| NMEA 0183 Wi‑Fi | Signal K (SLA-1) — not duplicate decode | §7.1 | FR-2 | Specified |
| NMEA 2000 | PiCAN-M → Signal K | §7.1 | FR-1 | **Beyond iRegatta** |
| True wind compute | Signal K paths | §7.1 | — | Specified |
| RMB outbound | Optional `signalk-nmea-out` plugin | §7.16.10 | FR-59 | Optional |
| AIS fleet | `ais-collector` | §7.12 | FR-15–16 | **Beyond iRegatta** |
| Live corrected results | `live-results` + `handicap-manager` | §7.13–7.14 | FR-31–35 | **Beyond iRegatta** |
| GRIB / wind zones | `wind-field-analyzer` | §7.12 | FR-17–26 | **Beyond iRegatta** |
| SI PDF courses | `course-parser` | §7.13 | FR-28–29 | **Beyond iRegatta** |
| Start-boat course flags | `course-editor` + ADR-0006 | §7.13.3 | FR-36–41 | **Beyond iRegatta** |
| LLM coach | `tactical-coach` | §7.5 | FR-80–82 | **Beyond iRegatta** |

---

## Rationale

### Why iRegatta as reference?

It encodes **20+ years** of sailor UX for start timing, laylines, and polar steering — validated in club and offshore racing. Mapping explicitly avoids rebuilding features the manual already defines well.

### Why not ship iRegatta as the UI?

The AI Sailing System needs **fleet handicaps**, **AIS**, **multi-course regattas**, **Neo4j**, and **offline GRIB** — outside iRegatta's scope. Grafana + `course-editor` on `race.local` serve multi-crew displays and match our SLA-2 stack.

### Why SLK instead of onboard polar recording?

ORC **måletall SLK** is authoritative for handicap boats. Recording polars at sea (iRegatta style) is valuable for one-design but duplicates and conflicts with certificate-matched SLK for Xbox (NOR-10133).

### Why Signal K instead of direct NMEA in SLA-2?

iRegatta talks NMEA 0183 over Wi‑Fi to one phone. We centralize **0183 + N2K** on SLA-1 Signal K so SLA-2 consumers (polars, live-results, Grafana) share one normalized stream — same formulas, multiple displays.

---

## Consequences

### Positive

- Complete checklist for race UX parity reviews.
- Shared vocabulary with crew already using iRegatta.
- Clear **beyond-iRegatta** features (handicaps, fleet, GRIB) documented separately.

### Negative

- Two UX surfaces (`grafana-race` + `course-editor`) vs iRegatta's single swipe app — need consistent start/nav state in Neo4j.
- Some iRegatta features (onboard polar recording, Google Maps) need deliberate substitutes.

### Risks

| Risk | Mitigation |
|------|------------|
| Feature drift vs manual | Link ADR + §7.16 in PR template for race UX changes |
| Start-line math mismatch | Unit tests against iRegatta calculation descriptions |
| Crew expects phone app | Optional: run iRegatta in parallel consuming same NMEA Wi‑Fi bridge |

---

## Alternatives considered

### A. Use iRegatta as primary UI; AI Sailing System back-end only

**Rejected for v1.** Handicap fleet, AIS fusion, and Grafana big-screen displays are first-class requirements; iRegatta cannot show live corrected ORC standings for 50+ boats.

### B. Ignore iRegatta; design UX from scratch

**Rejected.** High risk of missing start-line burn/gain, perpendicular DTL, and other proven patterns.

### C. Build native mobile clone of iRegatta

**Deferred.** `course-editor` responsive web + Grafana covers boat LAN; native app is non-goal for v1.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial inventory and traceability from manual v2.86 |

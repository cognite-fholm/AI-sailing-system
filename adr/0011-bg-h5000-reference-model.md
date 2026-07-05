# ADR-0011: B&G H5000 as instrument and race-display reference model

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [spec.md §7.17](../spec.md#717-bg-h5000-reference-model--integration), [ADR-0001](./0001-system-architecture-and-technology-choices.md), [ADR-0010](./0010-iregatta-reference-model.md), [AI-sailing-data schema](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md)

**Reference manual:** [H5000 Operation Manual EN 988-10630-003](https://cxjdfr.files.cmp.optimizely.com/download/assets/en-us-H5000_OM_EN_988-10630-003_w.pdf/f9fdbcee044d11f0a251baecc01b2173) (B&G / Navico)

---

## Context

The **B&G H5000** is a race-proven instrument and autopilot ecosystem: CPU with tiered software (**Hydra**, **Hercules**, **Performance**), Graphic and Race displays, web-based calibration, polar/VMG targets, SailSteer laylines, StartLine with bow-position, dual wind/speed sensors, 3D motion wind correction, and a dedicated pilot computer.

The product owner sails with H5000 and expects the AI Sailing System to:

1. **Ingest** H5000/N2K/0183 data correctly via Signal K (not duplicate the CPU).
2. **Match** race-display semantics (start line bias in boat lengths, tidal layline correction, target bargraphs).
3. **Persist** calibration, polar, and display preferences in **AI-sailing-data** YAML where they are boat- or race-specific.
4. **Extend** H5000 with fleet AIS, live ORC standings, GRIB, and LLM coaching — without breaking H5000 as the helm instrument source of truth.

---

## Decision

Adopt **H5000 Operation Manual (988-10630-003)** as the **instrument integration and race-display reference**. Architecture:

| Layer | Role |
|-------|------|
| **H5000 CPU + sensors** | Primary marine data source on N2K / B&G network |
| **SLA-1 Signal K** | Decode N2K + NMEA 0183; normalize to Signal K paths; no second wind solution |
| **SLA-2 services** | Consume SK streams; mirror H5000 calculations where needed for Grafana/AIS fusion |
| **`grafana-race`** | H5000-equivalent pages (SailSteer, Start, WindPlot, Highway, …) |
| **`course-editor`** | Start-line ping, waypoint/route admin, calibration review |
| **`race-intelligence`** | Start-line math aligned with H5000 (DTL, bias°, bias boat-lengths) |
| **`polar-manager`** | SLK polars + H5000 CSV interchange + VMG targets |
| **AI-sailing-data** | `InstrumentProfile`, `LaylinePreferences`, `StartLinePreferences`, calibration backups |

**v1 non-goal:** Replacing H5000 autopilot drive — ingest pilot mode/state via N2K; do not command rudder.

---

## H5000 system inventory (manual)

### Hardware & network

| Component | Function |
|-----------|----------|
| **H5000 CPU** | Central processor; Hydra / Hercules / Performance software tiers |
| **Graphic Display** | 5″ color; configurable pages (SailSteer, Start, WindPlot, …) |
| **Race Display** | 5″ segmented; 2 data values + performance bargraph + alarms |
| **Pilot Computer** | Autopilot drive logic |
| **Pilot Controller** | Autopilot keys, modes, commissioning |
| **HV displays** | Mast 20/20 etc.; configured via CPU webserver |
| **3D Motion sensor** | Heel + trim; enables motion wind correction (Hercules+) |
| **Alarm module** | Network audible alarm |
| **H3000 sensors** | Wind, speed, heel upgrade path |
| **GPS** | Position, SOG, COG |
| **Mast rotation sensor** | Rotation correction (Performance setups) |
| **Deckman** | Offshore routing via serial (Performance) |
| **Zeus / Vulcan MFD** | Chartplotter, polar edit, calibration UI |
| **WiFi-1 router** | Wireless webserver access |
| **NMEA 0183 / 422 / 485** | Serial integration |
| **Analog module** | Boom angle, vang, loads, custom channels |

### CPU software tiers

| Tier | Capability (summary) |
|------|----------------------|
| **Hydra** | Core sailing pages, start line, polars, single sensors |
| **Hercules** | Dual sensors, 3D motion wind correction, dynamic boat-speed damping |
| **Performance** | Full pro feature set + Deckman, mast rotation, advanced variables |

Our `InstrumentProfile.spec.cpu_tier` records the boat CPU level for feature gating.

### Graphic Display — default pages

| Page | Key data |
|------|----------|
| **SailSteer** | Course/HDG, BSP, tide set/rate, waypoint, TWD, laylines, TWA, TWS |
| **Speed/Depth** | BSP, depth, acceleration bargraph |
| **WindPlot** | TWD/TWS + histograms (1/5/10/30/60 min) |
| **Start line** | DIST P/S, DIST LINE⊥, BIAS°, BIAS ADV (boat lengths), timer, tide, wind barb |
| **Depth history** | Depth + histogram (5/10/30/60 min) |
| **Highway** | WP bearing, COG, XTE, DTM, ETA, off-course limit |
| **Tide** | BSP, tide angle/rate, HDG, depth, TWA/TWS/TWD |
| **Autopilot** | Mode, set HDG/wind, rudder, performance level |

Eight user slots: replace, enable/disable, layouts (full, 2×1, 2×2, 3×3, analog).

### SailSteer & laylines

| Feature | Behavior |
|---------|----------|
| **Laylines on nav** | Shown when navigating to waypoint |
| **Tidal flow correction** | Offsets laylines for tidal set/drift |
| **Target wind angle source** | **Polar** \| **Actual** (current TWA) \| **Manual** upwind/downwind |
| **Layline limits** | Dotted min/max tack-gybe time windows: 5, 10, 15, 30 minutes |

### Start line

| Feature | Behavior |
|---------|----------|
| **Ping ends** | Port (red) / starboard (green) when bow on line |
| **Stale line** | Ends expire 23:59 same day |
| **Invalid line** | One or both ends missing |
| **Bias display** | Blue square = no bias; red/green arrow = port/starboard favored |
| **Bow offset** | Required — GPS antenna to bow |
| **Metrics** | DIST P, DIST S, DIST LINE (perpendicular), BIAS°, BIAS ADV (boat lengths) |

### Race timer

Countdown to zero; Start / Stop / Sync / Reset; returns to data page when running.

### Race Display

Two numeric fields + **bargraph** (performance target, timer, configurable variable); page key; alarm severity icons (info / warning / critical); acknowledge 2× ENTER.

### Sensor calibration (webserver + display)

| Domain | Methods |
|--------|---------|
| **Depth** | Offset to waterline or keel |
| **Boat speed** | Auto vs SOG, manual %, distance reference (multi-run) |
| **Dual speed** | Port/starboard; switch by MWA, heel, MWA+heel, fixed side |
| **Heel correction** | Speed correction table vs heel angle |
| **Wind** | MHU alignment (port/starboard tack trial), dual MHU auto-switch |
| **3D motion** | Mast height + motion correction for true wind (Hercules+) |
| **Heading** | Compass calibration, deviation table |
| **Leeway** | Calibration → **Course** = HDG + leeway |
| **Trim** | Trim angle sensor |
| **Polar tables** | Load/edit/backup via MFD; USB import |
| **VMG targets** | Separate webserver calibration section |
| **Measured sources** | Auto source priority; dual wind/speed |
| **COG as heading** | Fallback (no autopilot) |
| **SOG as boat speed** | Fallback for STW |

### Damping

Per-variable 0–9 s; **dynamic boat speed damping** (Hercules+): damping drops on acceleration, recovers in steady state.

### Alarms

Per-sensor high/low; AIS proximity; alarm groups; acknowledge + history; Race Display override on/off.

### Autopilot (reference only — ingest, not drive in v1)

Modes: **Standby**, **Auto**, **Wind**, **NoDrift**, **Navigation**, **NFU**.  
Sailing features: gust response, TWS response, heel compensation, tack time/angle, tack/gybe keys, response 1–5, recovery mode, wind mode source (Auto/Apparent/True/**Polar**).

### Webserver

Tabs: Data time plots, trip, race timer, calibration (depth, heading, BSP, wind, **polar**, **VMG targets**, heel, trim, leeway), system (units, **damping**, alarms, user data), backup/restore, diagnostics, CPU software unlock.

### Operating variables (selected — full map in `schema/h5000-variable-map.yaml`)

BSP, COG, SOG, HDG, **Course** (HDG+leeway), TWA/TWD/TWS, AWA/AWS, VMG, XTE, DTM, BTM, heel, trim, leeway, boom angle, rudder angle, set HDG/wind, performance %, bias, depth, tide set/rate, polar target BSP/angle.

---

## Traceability — H5000 → AI Sailing System

| H5000 area | Our component | Data (YAML) | Spec | FR | Status |
|------------|---------------|-------------|------|-----|--------|
| N2K / 0183 ingest | Signal K SLA-1 | `InstrumentProfile` | §7.1, §7.17 | FR-1–2 | Specified |
| SailSteer page | `grafana-race` SailSteer dashboard | `LaylinePreferences` | §7.17.2 | FR-108 | Planned |
| Start line page | `race-intelligence` + `course-editor` | `StartLinePreferences`, race `planning/` | §7.17.3 | FR-50–52, FR-109 | Partial |
| WindPlot | Grafana wind histogram | — | §7.17.2 | FR-110 | Planned |
| Highway / XTE | `live-results` + Grafana | `courses/routes/*.yaml` | §7.13 | FR-111 | Partial |
| Polar table | `polar-manager` SLK + CSV | `PolarSource`, `assets/*.slk` | §7.12 | FR-19–23 | Specified |
| VMG targets | `polar-manager` | `PolarSource.spec.vmg_targets` | §7.17.4 | FR-112 | Planned |
| Tidal layline correction | `race-intelligence` | `LaylinePreferences` | §7.17.2 | FR-113 | Planned |
| Target bargraph | Grafana gauge | — | §7.17.2 | FR-46, FR-114 | Partial |
| Bow offset | `race-intelligence` | `InstrumentProfile.spec.bow_offset_m` | §7.17.3 | FR-52 | Specified |
| Dual wind/speed | Signal K + `InstrumentProfile` | `measured_sources` | §7.17.5 | FR-115 | Planned |
| 3D motion wind corr. | Signal K plugin config | `motion_correction` | §7.17.5 | FR-116 | Planned |
| Heel speed correction | Calibration service | `InstrumentCalibration` | §7.17.5 | FR-117 | Planned |
| Leeway → Course | `race-intelligence` | `InstrumentCalibration` | §7.17.5 | FR-118 | Planned |
| Damping | Display pipeline | `InstrumentProfile.spec.damping` | §7.17.6 | FR-43, FR-119 | Partial |
| Race timer | `race-intelligence` | race `planning/start-line.yaml` | §7.17.3 | FR-49, FR-120 | Partial |
| Alarms | Grafana + optional alertmanager | `AlarmProfile` | §7.17.7 | FR-121 | Planned |
| Webserver calibration backup | `harbor-sync` | `instrumentation/backup/` | §7.17.8 | FR-122 | Planned |
| Autopilot state ingest | Signal K N2K | read-only | §7.17.9 | FR-123 | Planned |
| Zeus chart overlay | External MFD | — | — | — | Coexist |
| Fleet AIS / ORC results | `ais-collector`, `live-results` | `fleet.yaml` | §7.13–14 | — | **Beyond H5000** |
| GRIB wind zones | `wind-field-analyzer` | `grib-plan.yaml` | §7.12 | — | **Beyond H5000** |

---

## Data model (AI-sailing-data)

New YAML kinds — see [schema/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md):

| Kind | Path | Purpose |
|------|------|---------|
| `InstrumentProfile` | `boats/{sail}/instrumentation/profile.yaml` | CPU tier, bow offset, damping, measured sources |
| `InstrumentCalibration` | `boats/{sail}/instrumentation/calibration.yaml` | Depth offset, BSP %, MHU align, heel table (harbor export) |
| `LaylinePreferences` | race `planning/layline-preferences.yaml` | TWA source, tidal correction, layline limits |
| `StartLinePreferences` | race `planning/start-line.yaml` | Timer, bow offset override, bias display options |
| `AlarmProfile` | `boats/{sail}/instrumentation/alarms.yaml` | Mirror critical H5000 alarm thresholds |
| `PolarSource` (extended) | certificate `polar.yaml` | Add `h5000_export`, `vmg_targets` |

Signal K path map: [`schema/h5000-variable-map.yaml`](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/h5000-variable-map.yaml).

---

## Rationale

### Why H5000 as reference, not replacement?

H5000 remains the **helm instrument stack** with proven start-line and SailSteer UX. The Pi stack **aggregates, archives, fuses fleet/GRIB**, and coaches — it must speak H5000's data language.

### Why Signal K instead of H5000 webserver?

Webserver is configuration UI, not a race API. Signal K + N2K is the stable integration surface for SLA-2 consumers.

### Why persist calibration in git?

Harbor commissioning changes (bow offset, new MHU align after rig work) should version with the boat — same workflow as ORC certificates.

---

## Consequences

### Positive

- Clear contract for Xbox (NOR-10133) instrument setup.
- Grafana dashboards named after familiar H5000 pages reduce crew training.
- Calibration YAML enables agent-assisted harbor commissioning in Cursor.

### Negative

- Dual-sensor and motion-correction logic is complex — v1 may ingest raw SK only and defer switching to H5000 CPU.
- 19 MB operator PDF not stored in git — linked from `docs/references/`.

### Risks

| Risk | Mitigation |
|------|------------|
| SK path mismatch vs H5000 variable | Maintain `h5000-variable-map.yaml`; integration tests |
| Autopilot confusion | Document read-only; no rudder commands in v1 |
| Polar format drift | SLK canonical; H5000 CSV as export/import adapter |

---

## Alternatives considered

### A. Replace H5000 with Pi-only instruments

**Rejected.** Owner uses H5000; sunk cost and class-standard UX.

### B. Deep autopilot integration (steer from AI)

**Deferred.** Safety and class rules; ingest-only in v1.

### C. Ignore H5000; generic NMEA only

**Rejected.** Loses bias boat-lengths, tidal laylines, VMG targets, dual-sensor semantics.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial inventory from manual 988-10630-003 |

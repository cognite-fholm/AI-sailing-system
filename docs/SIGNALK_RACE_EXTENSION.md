# Signal K race extension — `race.expedition.*` and `race.tactical.*`

Normative path contract for **Expedition laptop bridge** ([ADR-0034](../adr/0034-expedition-laptop-signalk-federation.md)) and **SLA-2 tactical producers** (`race-intelligence`, `live-results`, `tactical-coach`).

**Canonical instrument paths** remain standard Signal K (`navigation.*`, `environment.wind.*`) and existing `performance.*` ([ADR-0021](../adr/0021-sla1-signalk-plugin-strategy.md)).

---

## Namespace layout

| Prefix | Producer | Writable by bridge? | Description |
|--------|----------|---------------------|-------------|
| `race.expedition.` | `expedition-bridge` (laptop) | Yes (from ExpDLL read) | Expedition-computed tactical state |
| `race.tactical.` | SLA-2 services (Pi) | Yes (from Neo4j / rules / coach) | AI-sailing value-add |
| `performance.` | `signalk-polar-performance` | Pi SLA-1 only | ORC polar % (unchanged) |

All values are **SI units** unless noted. Each update uses a dedicated `source.label` (see below).

---

## Source labels

| Label | `source.type` | Host |
|-------|---------------|------|
| `expedition-bridge` | `expedition-bridge` | Nav laptop |
| `race-intelligence` | `race-intelligence` | SLA-2 |
| `live-results` | `live-results` | SLA-2 |
| `tactical-coach` | `tactical-coach` | SLA-2 |

---

## `race.expedition.start` — start line (read from Expedition)

Mapped from Expedition `Var` / `SysVar` in `expedition-bridge`.

| Signal K path | Unit | Expedition source | Notes |
|---------------|------|-------------------|-------|
| `race.expedition.start.distToLine` | m | `StartDistToLine` | Perpendicular DTL |
| `race.expedition.start.timeToLine` | s | `StartTimeToLine` | TTL |
| `race.expedition.start.timeToBurn` | s | `StartTimeToBurn` | |
| `race.expedition.start.timeToGun` | s | `StartTimeToGun` | Countdown |
| `race.expedition.start.biasAngle` | deg | `StartLineBiasDeg` | |
| `race.expedition.start.biasBoatLengths` | — | `StartLineBiasLen` | Signed boat lengths |
| `race.expedition.start.timeToPort` | s | `StartTimeToPort` | |
| `race.expedition.start.timeToStarboard` | s | `StartTimeToStrb` | |
| `race.expedition.start.burnPort` | s | `StartTimeToPortBurn` | |
| `race.expedition.start.burnStarboard` | s | `StartTimeToStrbBurn` | |
| `race.expedition.start.distToPort` | m | `SysVar.StartDistToPort` | |
| `race.expedition.start.distToStarboard` | m | `SysVar.StartDistToStrb` | |
| `race.expedition.start.portEnd.position` | {latitude, longitude} | `StartPortEndLat/Lon` | |
| `race.expedition.start.starboardEnd.position` | {latitude, longitude} | `StartStrbEndLat/Lon` | |

---

## `race.expedition.laylines` — laylines and marks

| Signal K path | Unit | Expedition source |
|---------------|------|-------------------|
| `race.expedition.laylines.distance` | m | `LayDist` |
| `race.expedition.laylines.time` | s | `LayTime` |
| `race.expedition.laylines.bearing` | deg | `LayBear` |
| `race.expedition.laylines.port.distance` | m | `LayDistOnPort` |
| `race.expedition.laylines.port.time` | s | `LayTimeOnPort` |
| `race.expedition.laylines.port.bearing` | deg | `LayPortBear` |
| `race.expedition.laylines.starboard.distance` | m | `LayDistOnStrb` |
| `race.expedition.laylines.starboard.time` | s | `LayTimeOnStrb` |
| `race.expedition.laylines.starboard.bearing` | deg | `LayStrbBear` |
| `race.expedition.laylines.mark.bearing` | deg | `MarkBrg` |
| `race.expedition.laylines.mark.distance` | m | `MarkRng` |
| `race.expedition.laylines.nextMark.bearing` | deg | `NextMarkBrg` |
| `race.expedition.laylines.nextMark.distance` | m | `NextMarkRng` |
| `race.expedition.laylines.nextMark.timeOnPort` | s | `NextMarkTimeOnPort` |
| `race.expedition.laylines.nextMark.timeOnStarboard` | s | `NextMarkTimeOnStrb` |

---

## `race.expedition.targets` — polar targets (Expedition view)

| Signal K path | Unit | Expedition source |
|---------------|------|-------------------|
| `race.expedition.targets.trueWindAngle` | deg | `TargTwa` |
| `race.expedition.targets.boatSpeed` | m/s | `TargBsp` | knots in Exp UI; convert on publish |
| `race.expedition.targets.vmg` | m/s | `TargVmg` |
| `race.expedition.targets.polarBoatSpeed` | m/s | `PolarBsp` |
| `race.expedition.targets.polarPerformanceRatio` | ratio | `PolarBspPercent` / 100 |
| `race.expedition.targets.headingToSteer` | deg | `HeadingToSteer` |
| `race.expedition.targets.sailNow` | string | `SailNow` | sail chart label |
| `race.expedition.targets.sailAtMark` | string | `SailMark` |
| `race.expedition.targets.sailNextLeg` | string | `SailNext` |

---

## `race.expedition.routing` — routing / weather (read-only outputs)

| Signal K path | Unit | Expedition source |
|---------------|------|-------------------|
| `race.expedition.routing.predicted.trueWindDirection` | deg | `PredTwd` |
| `race.expedition.routing.predicted.trueWindSpeed` | m/s | `PredTws` |
| `race.expedition.routing.predicted.set` | deg | `PredSet` |
| `race.expedition.routing.predicted.drift` | m/s | `PredDrift` |
| `race.expedition.routing.optimal.vmc` | m/s | `OptVmc` |
| `race.expedition.routing.optimal.heading` | deg | `OptVmcHdg` |
| `race.expedition.routing.optimal.trueWindAngle` | deg | `OptVmcTwa` |
| `race.expedition.routing.wave.significantHeight` | m | `WaveSigHeight` |
| `race.expedition.routing.wave.significantPeriod` | s | `WaveSigPeriod` |

---

## `race.expedition.meta` — bridge health

| Signal K path | Type | Description |
|---------------|------|-------------|
| `race.expedition.meta.connected` | bool | ExpDLL session OK |
| `race.expedition.meta.apiVersion` | string | `legacy` or `1.2` |
| `race.expedition.meta.lastPollAt` | ISO8601 string | UTC poll timestamp |
| `race.expedition.meta.pollDurationMs` | number | Last poll latency |

---

## `race.tactical.*` — AI Sailing System (Pi SLA-2)

Reserved for producers other than Expedition. Initial paths (implemented with `race-intelligence` / `live-results`):

| Signal K path | Unit | Producer |
|---------------|------|----------|
| `race.tactical.start.distToLine` | m | `race-intelligence` | iRegatta/H5000 parity |
| `race.tactical.start.timeToLine` | s | `race-intelligence` |
| `race.tactical.start.biasBoatLengths` | — | `race-intelligence` |
| `race.tactical.standings.correctedRank` | int | `live-results` |
| `race.tactical.standings.timeBehindLeader` | s | `live-results` |
| `race.tactical.wind.activeGribModel` | string | `grib-model-scorer` |
| `race.tactical.alert.summary` | string | `insight-alerts` |

When both `race.expedition.start.*` and `race.tactical.start.*` exist, UIs should prefer **Expedition** for nav-laptop displays and **tactical** for Pi-only dashboards, or show both with source badges.

---

## Write paths (commands → Expedition)

Expedition-Python can **write** only a subset safely. The bridge exposes these as **command endpoints** (HTTP on laptop) that map to ExpDLL writes — not continuous SK paths.

| Command model | ExpDLL action | Use |
|---------------|---------------|-----|
| `ExpeditionMobCommand` | `set_mob(lat, lon)` | MOB from AI alert |
| `ExpeditionBoatPositionCommand` | `set_boat_position(boat, …)` | Inject competitor position (boat ≥ 1) |
| `ExpeditionUserChannelCommand` | `set_exp_var_value(UserN, …)` | Custom bridge tags |

**Legacy DLL only** (optional): `ping_mark`, `add_mark_to_active_route` — behind feature flag `EXPEDITION_LEGACY_ROUTE_API=1`.

Do **not** write start timer or hold-wind via SK — not exposed in Expedition-Python.

---

## Example delta (publish)

```json
{
  "context": "vessels.self",
  "updates": [
    {
      "source": { "label": "expedition-bridge", "type": "expedition-bridge" },
      "timestamp": "2026-07-13T07:30:00.000Z",
      "values": [
        { "path": "race.expedition.start.distToLine", "value": 42.5 },
        { "path": "race.expedition.start.timeToLine", "value": 38.0 },
        { "path": "race.expedition.start.biasBoatLengths", "value": -1.2 },
        { "path": "race.expedition.meta.connected", "value": true }
      ]
    }
  ]
}
```

---

## NMEA 2000 (phase 2)

v1 is **Signal K only**. Phase 2 may map a minimal subset from **SLA-1** SK → N2K for H5000 displays:

| SK path | Candidate emission | Notes |
|---------|-------------------|-------|
| `race.expedition.start.distToLine` | Proprietary / B&G PGN TBD | Verify with H5000 docs |
| `race.tactical.standings.correctedRank` | None | UI-only |

Investigation task: chart which H5000 pages can consume SK-injected values vs MFD-native StartLine.

---

## Federation checklist

1. Laptop `expedition-bridge` polls ExpDLL at 1 Hz (configurable).
2. Publishes to `http://127.0.0.1:3000` (laptop SK).
3. If `UPSTREAM_SIGNALK_URL=http://telemetry.local:3000` — repeat PUT to Pi SK.
4. Pi `signalk-influx-bridge` extended to persist `race.expedition.*` and `race.tactical.*` (future PR).
5. Grafana `grafana-race` panels use Pi SK as datasource.

---

## Pydantic package

Implementation: [`expedition-bridge/`](../expedition-bridge/) — `ExpeditionSnapshot` → `RaceExtensionDelta` via `mapping.py`.

Tests run on Linux/macOS with `MockExpeditionClient` (no ExpDLL).

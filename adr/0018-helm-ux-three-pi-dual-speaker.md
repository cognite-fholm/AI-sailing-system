# ADR-0018: Helm UX, three-Pi race deployment, and audio routing

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0002](./0002-three-tier-sla-architecture.md), [ADR-0010](./0010-iregatta-reference-model.md), [ADR-0011](./0011-bg-h5000-reference-model.md), [ADR-0015](./0015-tactical-insight-alerts-annunciation.md), [spec §5](../spec.md#5-three-tier-sla-architecture), [spec §7.4](../spec.md#74-visualization--grafana), [spec §7.4.1](../spec.md#741-race-helm-ui-grafana--signalk-plugins)

---

## Context

The platform must serve the helm during a race without replacing proven instrument UX. Decisions were needed on:

1. **Hardware topology** — one vs three Raspberry Pis
2. **Primary displays** — Grafana vs custom pages vs H5000 / phone apps
3. **Audio** — tactical voice vs safety annunciation
4. **Scope** — race optimization vs safety systems

---

## Decision

### 1. Three-Pi race profile (mandatory for this project)

Deploy **one Pi per SLA tier** in the race profile:

| Node | Tier | Hardware |
|------|------|----------|
| Telemetry Pi | SLA-1 | Pi 5 + PiCAN-M |
| Race Pi | SLA-2 | Pi 5 8 GB |
| Vision Pi | SLA-3 | Pi 5 8 GB + Coral + GoPro |

Compact and standard profiles remain documented for lab use only; **regatta deployment uses the three-node race profile**.

### 2. Grafana is not the primary helm UI

**Grafana** is used only where it excels:

- Time-series history (wind, SOG, VMG bars)
- Fleet geo map and heatmaps
- Debrief and engineering views
- Alert feed list (tactical, read-only)

**Interactive race UX** (start line, course selection, laylines, steering bars, alert ack) is implemented as **locally hosted TypeScript pages** served by a **Node.js** app (`race-ui` on SLA-2), with optional **Signal K server plugins** or embedded views that extend the Signal K instrument UX on the boat LAN.

| Surface | Role |
|---------|------|
| **B&G H5000** | Primary instrument displays; safety annunciation |
| **`race-ui` (Node/TS)** | Primary tactical/race optimization UI on helm tablet |
| **Grafana-race** | Secondary — trends, maps, fleet performance timelines |
| **iRegatta (phone)** | Optional parallel consumer of NMEA Wi‑Fi; not replaced |
| **course-editor** | Setup and waypoint editing (may merge into `race-ui` over time) |

### 3. Two speakers — separate audio paths

| Speaker | Path | Content |
|---------|------|---------|
| **Speaker A — H5000** | H5000 alarm module / instrument audio | **Safety only** — depth, collision, instrument limits |
| **Speaker B — tactical** | USB/Bluetooth on SLA-2 → Piper TTS (`insight-alerts`) | **Race optimization** — fleet rank, course, trim, wind tactics |

Tactical TTS **never** uses the H5000 speaker. No routing of AI tactical alerts through H5000 alarm groups.

### 4. H5000 is the only safety annunciator

- Safety-critical alarms stay on **H5000** (and mirrored read-only in Grafana for logging).
- **`insight-alerts`** handles **performance and tactical** notifications only.
- `insight-alerts` **rejects** `category: safety` events.
- Tactical TTS does **not** preempt or share queue with H5000 safety audio (separate hardware).

---

## Rationale

- Three Pis eliminate SLA-1 starvation from vision/LLM load during starts and mark roundings.
- Grafana is poor for interactive start-line and course workflows; React/TS on Node matches `course-editor` and Signal K plugin patterns.
- Separate speakers avoid conflating depth alarms with “you lost three places” tactical cues.
- H5000 remains authoritative for safety; our stack focuses on **winning**.

---

## Consequences

### Positive

- Clear helm UX ownership per surface
- Safety semantics unchanged from factory H5000 behavior
- Tactical voice can be tuned aggressively without safety risk

### Negative

- Additional `race-ui` service to build and maintain
- Second speaker to wire and test
- Three Pis to provision, power, and network

### Follow-up

- [ ] `race-ui` Node/TS app on SLA-2 (`race.local:3010` or dedicated port)
- [ ] Signal K plugin or `@signalk/*` integration for instrument-adjacent panels
- [ ] `InsightAlertProfile` — `channels.tts.speaker_device` for tactical speaker only
- [ ] Document H5000 vs tactical speaker wiring in `boats/.../instrumentation/`

---

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Grafana-primary helm | Weak interactivity; poor start/course workflows |
| Single speaker with priority queue | Confuses safety and tactical; user chose two speakers |
| Tactical alerts on H5000 network | Wrong abstraction; safety vs performance must not merge |
| Single-Pi race deploy | User chose three-Pi race profile |

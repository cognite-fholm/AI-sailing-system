# AI Sailing System — Specification

**Version:** 0.14.0-draft  
**Date:** 2026-07-05  
**Changelog (0.14):** Tactical insight alerts with UX feed and optional voice annunciation (ADR-0015, §7.21).  
**Changelog (0.13):** Automated ORC certificate fleet collection (ADR-0013, §7.19); dedicated Neo4j/Influx MCP endpoints; shore weather/current collection (ADR-0014, §7.20).  
**Changelog (0.12):** Race-side MCP gateway for laptop Cursor ad hoc analysis (ADR-0012, §7.18).  
**Author:** cognite-fholm  
**Status:** Draft — architecture & requirements

---

## 1. Executive summary

The **AI Sailing System** is an onboard edge platform for **competitive sailing**. It ingests marine sensor data over NMEA 0183 and NMEA 2000, normalizes it through **Signal K**, stores high-frequency telemetry in **InfluxDB**, models boats, races, courses, and tactics in **Neo4j**, visualizes performance in **Grafana**, and provides **local AI coaching** using **LLaMA** models.

The platform is organized into **three SLA tiers**, each running in **dedicated containers** and optionally on **separate Raspberry Pi devices**. Race and boat **content** lives in the companion **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** repository; **code and containers** live here.

**Reference UX / instruments:** [iRegatta](https://zifigo.com/) (race phone app — [§7.16](#716-iregatta-reference-model--feature-traceability)) and [B&G H5000](https://www.bandg.com/bg/series/h5000/) (helm instruments — [§7.17](#717-bg-h5000-reference-model--integration)) define parity targets for start line, laylines, polars, and SailSteer displays.

**Race laptop:** [§7.18](#718-race-side-mcp--laptop-cursor) — bring a laptop on boat Wi‑Fi; **Cursor** connects via **MCP** to `race-mcp-gateway` for live standings, telemetry, and ad hoc analysis.

**ORC certificates:** [§7.19](#719-orc-certificate-collection--fleet-enrichment) — automate fleet cert metadata and PDF download on shore via **orc-sailor-services** skill in AI-sailing-data ([ADR-0013](./adr/0013-orc-certificate-fleet-collection.md)).

**Weather & current:** [§7.20](#720-shore-weather--current-collection) — MET Norway GRIB, Oslofjord current plots, SMHI wind validation in **AI-sailing-data** ([ADR-0014](./adr/0014-shore-weather-current-collection.md)).

**Tactical alerts:** [§7.21](#721-tactical-insight-alerts--annunciation) — proactive insight notifications (fleet position, course, trim) on helm UX and optional speaker read-out ([ADR-0015](./adr/0015-tactical-insight-alerts-annunciation.md)).

| Tier | Domain | SLA priority |
|------|--------|----------------|
| **SLA-1** | On-boat telemetry | Critical — must never fail during a race |
| **SLA-2** | Race & competitor information | Important — tactical context; GRIB, polars, AIS, wind-on-course |
| **SLA-3** | Sail performance (vision / LLM) | Analytical — best-effort; heaviest compute |

The system is designed to:

- Run **fully offline** during a race (no internet required).
- Operate on one or more **Raspberry Pi** nodes with a **PiCAN-M HAT** on the telemetry node (NMEA buses + 3 A SMPS).
- Use a **Google Coral** accelerator on the vision node for sail-image preprocessing.
- **Isolate tiers** so image analysis and race-graph workloads cannot starve live instrument data.
- Support **remote upgrades** via **GitHub Actions → GHCR → Docker Compose** on Raspberry Pi when connectivity is available.
- Build directly on lessons learned from the existing **CogSail** repositories.

---

## 2. Problem statement

Competitive sailors need more than raw instrument readouts. They need:

1. **Unified data** — wind, speed, heading, depth, engine, autopilot, polar data, and custom sensors in one model.
2. **Race context** — marks, legs, start line, fleet position, course geometry, **GRIB wind fields**, and **polar targets** linked to live telemetry.
3. **Performance insight** — VMG, target angles, polar comparison (own boat + competitors), tack/gybe quality, and leg summaries.
4. **Tactical memory** — what worked on this course, in these conditions, against this fleet — including **runtime wind-advantage zones** derived from GRIB + AIS fleet behavior.
5. **Trustworthy edge operation** — must work at sea with intermittent or zero connectivity.

The prior CogSail stack proved that Signal K → stream buffer → structured storage works, but relied on **Cognite Data Fusion (CDF)** in the cloud. This system keeps the proven ingestion patterns and replaces CDF with **InfluxDB + Neo4j + Grafana**, adding **local LLaMA** for AI assistance.

---

## 3. Goals and non-goals

### 3.1 Goals

| ID | Goal |
|----|------|
| G1 | Win-focused analytics: start timing, laylines, wind shifts, fleet leverage, leg debrief |
| G2 | Signal K as the canonical onboard marine data model |
| G3 | Sub-second local dashboards via Grafana |
| G4 | Graph queries for race/tactic/boat relationships via Neo4j |
| G5 | Local LLM inference without cloud dependency during races |
| G6 | Containerized services with remote upgrade path |
| G7 | NMEA 0183 + NMEA 2000 via PiCAN-M HAT |
| G8 | Reuse and migrate concepts from cognite-fholm CogSail repos |
| G9 | Three isolated SLA tiers in separate containers; tiers may run on separate RPi nodes |
| G10 | SLA-1 telemetry survives failure or overload of SLA-2 / SLA-3 |
| G11 | GRIB files refreshed on a regular schedule when online; usable offline after sync |
| G12 | Polar diagrams for own boat and competitors drive VMG/target analysis |
| G13 | AIS tracks for own boat and fleet enable runtime wind-on-course analysis |
| G14 | Parse race courses from competition program PDFs (e.g. SI chapter 11) |
| G15 | Live corrected-time standings from waypoints, handicaps, and AIS progress |
| G16 | Multiple handicap numbers per boat (ORC certificate + per-race WRS TCF) |
| G17 | Multiple course variants per regatta; active course from start-boat flags |
| G18 | UX shows class flag + course signals; user confirms or overrides vision detection |
| G19 | Advisory agents consume a versioned **Google OKF** knowledge bundle for system context |
| G20 | **GitHub + Docker** end-to-end: Actions CI, GHCR images, Compose on Pi — no cloud orchestration |
| G21 | Shore **TrimTransformer** training on **own gaming PC** (SLA-S), not paid cloud GPU |
| G22 | **AI-sailing-data** repo for temporal race/boat planning onshore |
| G23 | Onboard **race-data-sync** pulls newer data from GitHub via Teltonika LTE when available |
| G24 | **iRegatta-equivalent** race UX for start, laylines, polars, and navigation — see [§7.16](#716-iregatta-reference-model--feature-traceability) and [ADR-0010](./adr/0010-iregatta-reference-model.md) |
| G25 | **B&G H5000-equivalent** instrument semantics, SailSteer/StartLine pages, calibration YAML — see [§7.17](#717-bg-h5000-reference-model--integration) and [ADR-0011](./adr/0011-bg-h5000-reference-model.md) |
| G26 | **Race-side MCP** — laptop on boat LAN runs **Cursor** with live Neo4j, Influx, standings, and YAML context for ad hoc analysis — [§7.18](#718-race-side-mcp--laptop-cursor), [ADR-0012](./adr/0012-race-side-mcp-laptop-cursor.md) |
| G27 | **Automated ORC certificate collection** for race-class fleets — metadata via `activecerts`, PDFs via authenticated download, `boats/` stubs — [§7.19](#719-orc-certificate-collection--fleet-enrichment), [ADR-0013](./adr/0013-orc-certificate-fleet-collection.md) |
| G28 | **Shore weather/current collection** for Oslofjord races — MET GRIB, current plot interpretation, SMHI validation — [§7.20](#720-shore-weather--current-collection), [ADR-0014](./adr/0014-shore-weather-current-collection.md) |
| G29 | **Tactical insight alerts** — raise and display performance alerts (trim, course, fleet rank); optional voice annunciation — [§7.21](#721-tactical-insight-alerts--annunciation), [ADR-0015](./adr/0015-tactical-insight-alerts-annunciation.md) |

### 3.2 Non-goals (v1)

- Autonomous vessel control or autopilot override.
- Class rule enforcement or protest filing automation.
- Replacing dedicated race tracking services (e.g. YB Tracking) — integration may come later.
- Replacing the **iRegatta** iOS app as a personal phone UI — our stack is boat-LAN Grafana + `course-editor`; iRegatta may run in parallel on the same NMEA Wi‑Fi feed.
- Training large models onboard — only **inference** of pre-quantized models.
- Full cloud SaaS replacement — optional sync/export may be added later.

---

## 4. Hardware platform

### 4.1 Reference bill of materials

Hardware is assigned **per SLA tier**. A single-boat deployment may use 1–3 Raspberry Pi nodes.

| Component | SLA tier | Role | Notes |
|-----------|----------|------|-------|
| **Raspberry Pi 5** (4 GB) | SLA-1 | Telemetry node | PiCAN-M HAT; runs Signal K + InfluxDB only |
| **Raspberry Pi 5** (8 GB) | SLA-2 | Race node | Neo4j, race intelligence, tactical LLM |
| **Raspberry Pi 5** (8 GB) | SLA-3 | Vision node | Cameras, Coral dongle, sail vision LLM |
| **PiCAN-M HAT + 3 A SMPS** | SLA-1 only | Marine I/O + power | NMEA 0183 + NMEA 2000; **must** live on telemetry node |
| **Google Coral accelerator** | SLA-3 | Sail image preprocessing | USB/PCIe on vision node; see [§7.5](#75-ai--llama--coral) |
| **GoPro HERO13 Black** (×3–5) | SLA-3 | Sail & boom imaging | Wireless capture via [Open GoPro](https://gopro.github.io/OpenGoPro/); see [§7.9](#79-gopro-hero13-black-fleet) |
| **USB Bluetooth 5.0 dongles** (×2, optional) | SLA-3 | Multi-GoPro BLE | One BLE central per camera; or Wi-Fi station mode on boat LAN |
| **32 GB+ industrial microSD** or **NVMe (Pi 5)** | All nodes | OS + data | Per-node persistent storage |
| **Boat LAN (Ethernet/Wi-Fi)** | All | Inter-node link | Gigabit preferred when tiers are split across Pis |
| **12 V marine supply** | All | Power | N2K SMPS on telemetry node; DC-DC for additional nodes |
| **Wi-Fi / LTE (optional)** | SLA-2 | Remote deploy & sync | Not required for race operation |
| **Teltonika LTE router** | WAN | 4G/5G + boat LAN | See [§4.4](#44-network--teltonika-lte-router) |

**Deployment profiles:**

| Profile | Nodes | When to use |
|---------|-------|-------------|
| **Compact** | 1× Pi 5 (8 GB) | Testing, day sailing; all tiers with cgroup CPU/RAM limits |
| **Standard** | 2× Pi — SLA-1 + SLA-2/3 combined | Club racing; telemetry isolated from vision |
| **Race** | 3× Pi — one per tier | Recommended for serious regatta sailing |

### 4.2 PiCAN-M integration

```
NMEA 2000 backbone ──► Micro-C (J1) ──► can0 (SocketCAN, 250 kbit/s)
NMEA 0183 talker/listener ──► RS-422 screw terminal (J3) ──► /dev/ttyS0
I²C sensors (wind, env) ──► Qwiic (J4)
12 V N2K power ──► onboard SMPS ──► 5 V for Pi + HAT
```

**Signal K configuration (reference):**

- NMEA 2000: `canboatjs` or Signal K N2K plugin reading `can0` — includes **AIS PGNs** (129038, 129039, 129809, 129810) forwarded to SLA-2.
- NMEA 0183: serial port plugin on `/dev/ttyS0` (4800/38400/115200 as appropriate).
- I²C sensors: optional plugin or custom Python reader publishing Signal K deltas.

**B&G H5000 coexistence:** On boats with H5000, N2K talkers on `can0` include wind, BSP, heel, GPS, and autopilot state. Signal K should **prefer H5000-corrected** true wind when present. See [§7.17](#717-bg-h5000-reference-model--integration) and [`h5000-variable-map.yaml`](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/h5000-variable-map.yaml).

### 4.3 Coral accelerator note

The linked [google-coral/coralnpu](https://github.com/google-coral/coralnpu) repository describes Coral's **ML accelerator core** (successor/evolution of Edge TPU). For v1:

- **LLaMA inference** runs on the **ARM CPU** via **llama.cpp** (quantized GGUF models).
- **Coral** accelerates **complementary** workloads: wake/event detection, image classification (crew/camera), custom TFLite models — not full transformer LLM inference.

This split is intentional and matches hardware capabilities.

### 4.4 Network — Teltonika LTE router

**Device class:** Teltonika industrial LTE router (4G/5G) with **RMS** (Remote Management System).

| Capability | Use in AI Sailing System |
|------------|--------------------------|
| **LTE WAN** | Internet when away from marina Wi-Fi — GitHub data sync, GRIB fetch, GHCR pull (harbor rules) |
| **Boat LAN AP** | DHCP/DNS for `telemetry.local`, `race.local`, `vision.local` |
| **RMS cloud** | Remote router health, config backup, firmware, optional VPN to home |
| **Failover** | Marina Wi-Fi as WAN when available; LTE when offshore |

```mermaid
flowchart LR
    LTE["4G/5G"]
    RMS["Teltonika RMS\n(optional VPN)"]
    RTR["Teltonika router"]
    Pi1["telemetry.local"]
    Pi2["race.local"]
    Pi3["vision.local"]
    GH["GitHub\nsystem + data repos"]
    LTE --> RTR
    RTR --> Pi1 & Pi2 & Pi3
    Pi2 -->|race-data-sync| GH
    RTR -.-> RMS
```

**Integration points:**

| Service | Uses LTE for |
|---------|--------------|
| `race-data-sync` | `git pull` on [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) when remote commit ahead |
| `grib-ingest` | Scheduled GRIB download when `ONLINE_MODE=true` |
| Watchtower | Container pull — **harbor mode only**, `RACE_MODE=false` |
| `training-export` | **Never** during race; harbor opt-in only |

**Guardrails:** Router credentials and RMS tokens are **not** stored in git. Document AP SSID/VLAN in harbor runbook only.

---

## 5. Three-tier SLA architecture

The system is partitioned into **three independent SLA tiers**. Each tier:

- Runs in its **own Docker Compose stack** (separate `docker-compose.sla-N.yml`).
- Has **dedicated containers** — no tier shares a process with another.
- Communicates over the **boat LAN** via defined APIs only (no shared databases across tiers except read replicas where noted).
- May run on the **same physical Raspberry Pi** (with resource limits) or on **dedicated Raspberry Pi hardware**.

**Golden rule:** SLA-1 must continue operating if SLA-2 or SLA-3 crash, restart, or saturate CPU/RAM.

### 5.1 Tier overview

```mermaid
flowchart TB
    subgraph SLA1["SLA-1 — Telemetry (Critical)"]
        direction TB
        T1_HW["PiCAN-M\nNMEA 0183 + 2000"]
        T1_SK["signalk-server"]
        T1_IFX["influxdb"]
        T1_BR["signalk-influx-bridge"]
        T1_GF["grafana-telemetry"]
        T1_HW --> T1_SK --> T1_BR --> T1_IFX --> T1_GF
    end

    subgraph SLA2["SLA-2 — Race & Competitors (Important)"]
        direction TB
        T2_N4J["neo4j"]
        T2_RACE["race-intelligence"]
        T2_AIS["ais-collector"]
        T2_COMP["competitor-sync"]
        T2_GRIB["grib-ingest"]
        T2_POLAR["polar-manager"]
        T2_WIND["wind-field-analyzer"]
        T2_GF["grafana-race"]
        T2_GRIB --> T2_WIND
        T2_AIS --> T2_WIND
        T2_POLAR --> T2_WIND
        T2_RACE --> T2_N4J
        T2_AIS --> T2_N4J
        T2_COMP --> T2_N4J
        T2_POLAR --> T2_N4J
        T2_WIND --> T2_N4J
        T2_N4J --> T2_GF
    end

    subgraph SLA3["SLA-3 — Sail Performance Vision (Analytical)"]
        direction TB
        T3_GOPRO["gopro-orchestrator\nHERO13 × N"]
        T3_CAM["media-ingest"]
        T3_CORAL["coral-preprocess"]
        T3_VLLM["llama-vision"]
        T3_GEO["sail-geometry"]
        T3_MATCH["condition-matcher"]
        T3_API["sail-analysis-api"]
        T3_STORE["image-store"]
        T3_GOPRO --> T3_CAM --> T3_CORAL --> T3_GEO --> T3_VLLM --> T3_API
        T3_GEO --> T3_MATCH --> T3_API
        T3_CAM --> T3_STORE
    end

    SLA1 -.->|"read-only Influx API\n+ Signal K WS fan-out"| SLA2
    SLA1 -.->|"telemetry context\n(optional)"| SLA3
    SLA2 -.->|"race_id, leg, wind sector"| SLA3
    SLA3 -.->|"sail trim insights"| SLA2
```

### 5.2 SLA definitions

#### SLA-1 — On-boat telemetry

**Purpose:** Ingest, normalize, persist, and display **live instrument data**. This is the safety-critical and race-critical path.

| Attribute | Target |
|-----------|--------|
| **Availability** | 99.99% during active race session |
| **Write latency** | Signal K delta → InfluxDB &lt; 500 ms (p95) |
| **Dashboard refresh** | &lt; 1 s for SOG, COG, AWA, AWS, depth, heel |
| **Recovery time** | &lt; 30 s after container restart |
| **Internet** | Not required |
| **PiCAN-M** | Required on this node |

**Containers (`docker-compose.sla-1.yml`):**

| Container | Image | Responsibility |
|-----------|-------|----------------|
| `signalk-server` | `ghcr.io/.../signalk` | NMEA ingest, Signal K hub; **host network** for CAN/serial |
| `signalk-influx-bridge` | `ghcr.io/.../influx-bridge` | Delta → Influx line protocol |
| `influxdb` | `influxdb:2` | Time series store (telemetry bucket only) |
| `grafana-telemetry` | `grafana/grafana` | Live instrument panels only |
| `redis` (optional) | `redis:alpine` | Write buffer if burst load |

**Does not include:** Neo4j, LLM, cameras, crawl jobs, or sail analysis.

**Hardware:** Raspberry Pi 5 (4 GB minimum) **with PiCAN-M HAT**. Dedicated node in race profile.

---

#### SLA-2 — Race and competitor information

**Purpose:** Model **races, courses, marks, fleet, and competitors**; ingest **GRIB** weather grids and **polar diagrams**; collect **AIS** for own boat and competitors; run **runtime wind-on-course analysis** to identify where favorable wind exists on the course.

| Attribute | Target |
|-----------|--------|
| **Availability** | 99.9% during race; graceful degradation acceptable |
| **Query latency** | Neo4j tactical query &lt; 3 s (p95) |
| **AIS refresh** | Own + competitor positions ≤ 10 s (from N2K AIS PGNs) |
| **GRIB refresh** | Scheduled every 6 h when online; manual pre-race upload |
| **Wind-field analysis** | Course wind map updated every 30–60 s during active race |
| **Recovery time** | &lt; 2 min; SLA-1 unaffected |
| **Internet** | Required for GRIB auto-fetch; optional for AIS (local N2K) |

**Containers (`docker-compose.sla-2.yml`):**

| Container | Image | Responsibility |
|-----------|-------|----------------|
| `neo4j` | `neo4j:5-community` | Race graph, vessels, marks, polars, wind zones |
| `race-intelligence` | `ghcr.io/.../race-intelligence` | Start line (DTL/TTL/burn-gain), lift, steering hints, leg timing |
| `ais-collector` | `ghcr.io/.../ais-collector` | Own-boat + competitor AIS from SLA-1 Signal K stream |
| `competitor-sync` | `ghcr.io/.../competitor-sync` | MMSI registry, fleet roster, polar linkage |
| `grib-ingest` | `ghcr.io/.../grib-ingest` | Scheduled download, manual upload, GRIB validation |
| `grib-parser` | `ghcr.io/.../grib-parser` | Decode GRIB2 → grid store; spatial query API |
| `polar-manager` | `ghcr.io/.../polar-manager` | Load **SLK** polar for own boat; serve canonical YAML |
| `polar-certificate-extractor` | `ghcr.io/.../polar-certificate-extractor` | Derive competitor polars from ORC certificate **PNG/PDF** |
| `handicap-manager` | `ghcr.io/.../handicap-manager` | ORC certificate handicaps + per-race WRS TCF per vessel |
| `race-data-sync` | `ghcr.io/.../race-data-sync` | Git pull **AI-sailing-data** when GitHub ahead of local |
| `race-import` | `ghcr.io/.../race-import` | Apply data repo `neo4j/*.yaml` → Neo4j MERGE |
| `course-parser` | `ghcr.io/.../course-parser` | Extract courses/waypoints from SI/NOR PDFs |
| `live-results` | `ghcr.io/.../live-results` | Corrected-time standings + VMG along course legs |
| `course-editor` | `ghcr.io/.../course-editor` | React/TS UX — waypoints + **start-line flag selection** |
| `course-flag-detector` | `ghcr.io/.../course-flag-detector` | Optional vision: read start-boat flags from GoPro photo |
| `crawl-agent` | `ghcr.io/.../crawl-agent` | NOR/SI crawl ([crawl_web](https://github.com/cognite-fholm/crawl_web) lineage) |
| `llama-tactical` | `ghcr.io/.../llama-cpp` | Text LLM — debrief, tactical Q&A |
| `tactical-coach` | `ghcr.io/.../tactical-coach` | FastAPI RAG over Neo4j + Influx + wind zones |
| `insight-alerts` | `ghcr.io/.../insight-alerts` | Tactical alert broker — UI feed, ack, optional Piper TTS |
| `grafana-race` | `grafana/grafana` | Fleet map, polars, GRIB overlay, wind-advantage heatmap, **alert feed** |

**Reads from SLA-1:** InfluxDB (telemetry + AIS-derived paths), Signal K WebSocket (`navigation`, `environment.wind`, AIS deltas). **Never writes to SLA-1 storage.**

See [§7.12](#712-grib-polars-ais--wind-on-course-analysis), [§7.13](#713-race-courses-waypoints--live-results), and [§7.14](#714-handicap-numbers--scoring).

**Hardware:** Raspberry Pi 5 (8 GB). May share a Pi with SLA-3 in compact profile; **must not share with SLA-1** in race profile.

---

#### SLA-3 — Sail performance (GoPro vision / LLM)

**Purpose:** Orchestrate a fleet of **GoPro HERO13 Black** cameras to photograph sails and boom rigging, extract **geometry** (angles, camber, twist), compare against **best-known trim in similar conditions**, and publish coaching insights.

| Attribute | Target |
|-----------|--------|
| **Availability** | 95% — best-effort; may be paused during maneuvers |
| **Capture sync** | Multi-GoPro still burst within ±200 ms (PPS via `capture_trigger`) |
| **Analysis latency** | Geometry + condition match &lt; 60 s (p95) on Pi 5 |
| **Capture rate** | 0.2–1 Hz per camera (configurable); burst on leg stable |
| **Recovery time** | &lt; 5 min; no impact on SLA-1 |
| **Internet** | Not required at sea; harbor sync for training export |

**Containers (`docker-compose.sla-3.yml`):**

| Container | Image | Responsibility |
|-----------|-------|----------------|
| `gopro-orchestrator` | `ghcr.io/.../gopro-orchestrator` | Discover, arm, and trigger HERO13 fleet via Open GoPro BLE/Wi-Fi |
| `media-ingest` | `ghcr.io/.../media-ingest` | Download photos from GoPro HTTP API; timestamp alignment |
| `coral-preprocess` | `ghcr.io/.../coral-preprocess` | Sail ROI, luff line, boom line detection (TFLite on Coral) |
| `sail-geometry` | `ghcr.io/.../sail-geometry` | Compute angles & shape metrics from ROIs + camera extrinsics |
| `condition-matcher` | `ghcr.io/.../condition-matcher` | Find best historical trim in similar wind/heel/SOG |
| `llama-vision` | `ghcr.io/.../llama-cpp-vision` | Multimodal LLM — qualitative sail shape narrative |
| `sail-analysis-api` | `ghcr.io/.../sail-analysis` | FastAPI; merge geometry + match + LLM → SLA-2 |
| `image-store` | `ghcr.io/.../image-store` | Ring buffer of frames, geometry JSON, capture metadata |
| `training-export` | `ghcr.io/.../training-export` | Harbor-only bundles for onshore ML (opt-in) |
| `grafana-sail` | `grafana/grafana` | Trim timeline, geometry gauges, best-vs-actual overlays |

**GoPro fleet (reference: 4 cameras):**

| Camera ID | Mount | Primary metrics |
|-----------|-------|-----------------|
| `gopro-mast` | Mast, above spreaders | Mainsail camber, draft %, leech twist, mast bend hint |
| `gopro-boom` | Boom gooseneck / mid-boom | **Boom angle** vs centerline, vang/kicker geometry, foot tension |
| `gopro-bow` | Bow pulpit | Genoa/jib luff, entry angle, sheet lead hint |
| `gopro-deck` (optional) | Cockpit looking up | Mainsail profile, **mast heel** visual, traveler context |

**Vision + geometry scope:**

- **Boom angle** (° off centerline / relative to TWA bucket).
- **Mast heel** (° — fused from SLA-1 `attitude.heel` + visual mast axis from `gopro-mast`).
- **Sail shape:** camber depth, draft position (% chord), leech twist (°), luff break severity.
- **Rig settings (visual proxy):** vang tension indicator, cunningham, outhaul, traveler position (where visible).
- **Condition comparison:** *"In 12–14 kt AWA 25–35° you historically carried 2° more boom angle and 15% further-aft draft with +0.3 kt VMG."*

**Reads from SLA-1:** AWA, AWS, TWS, TWD, SOG, VMG, heel, rudder, sheet/load sensors if available.  
**Reads from SLA-2:** `race_id`, leg, tack, `ConditionBucket` nodes.  
**Writes to SLA-2:** `SailAnalysis`, `SailGeometry`, `TrimDelta` nodes; links to `BestTrimSnapshot`.

**Hardware:** Raspberry Pi 5 (8 GB) + **Coral dongle** + 3–5× **GoPro HERO13 Black** + boat LAN Wi-Fi AP. **Always isolated from SLA-1.**

See [§7.9](#79-gopro-hero13-black-fleet), [§7.10](#710-sail-geometry--condition-similarity), and [§7.11](#711-onshore-transformer-training-pipeline).

---

### 5.3 SLA comparison matrix

| Dimension | SLA-1 Telemetry | SLA-2 Race & Competitors | SLA-3 Sail Vision |
|-----------|-----------------|--------------------------|-------------------|
| Priority | P0 — critical | P1 — important | P2 — analytical |
| Uptime target | 99.99% | 99.9% | 95% |
| PiCAN-M required | Yes | No | No |
| Coral required | No | No | Yes (preprocess) |
| Cameras | — | — | 3–5× GoPro HERO13 Black |
| LLM type | None | Text (llama.cpp) | Vision (llama.cpp multimodal) |
| Primary store | InfluxDB | Neo4j | Image store + metadata |
| Grafana instance | `grafana-telemetry` | `grafana-race` | `grafana-sail` |
| Survives other tier failure | — | Yes (SLA-1 up) | Yes (SLA-1 up) |
| Remote auto-update in race | **Never** | Harbor only | Harbor only |

### 5.4 Multi-node deployment topologies

```mermaid
flowchart LR
    subgraph RaceProfile["Race profile — 3× Raspberry Pi"]
        Pi1["Pi telemetry\nSLA-1 only\nPiCAN-M HAT"]
        Pi2["Pi race\nSLA-2\nNeo4j + tactical LLM"]
        Pi3["Pi vision\nSLA-3\nCoral + cameras"]
    end

    subgraph LAN["Boat LAN 192.168.42.0/24"]
        Pi1 --- Pi2
        Pi2 --- Pi3
        Pi1 --- Pi3
    end

    Tablet["Crew tablets"] --> Pi1
    Tablet --> Pi2
    Tablet --> Pi3
```

```mermaid
flowchart LR
    subgraph StandardProfile["Standard profile — 2× Raspberry Pi"]
        PiT["Pi telemetry\nSLA-1\nPiCAN-M"]
        PiAV["Pi analytics\nSLA-2 + SLA-3\ncgroup isolated"]
    end

    PiT --- PiAV
```

**DNS / hostnames (boat LAN):**

| Host | Tier | Services |
|------|------|----------|
| `telemetry.local` | SLA-1 | Signal K `:3000`, Influx `:8086`, Grafana `:3001` |
| `race.local` | SLA-2 | Neo4j `:7474`, coach `:8090`, Grafana `:3002` |
| `vision.local` | SLA-3 | sail API `:8091`, Grafana `:3003` |

### 5.5 Inter-tier communication contract

| From → To | Protocol | Data | Direction |
|-----------|----------|------|-----------|
| SLA-1 → SLA-2 | Signal K WebSocket | AIS deltas + own-boat navigation | Read-only fan-out |
| SLA-1 → SLA-2 | Influx HTTP API | Telemetry, wind, SOG/COG | Read-only |
| SLA-1 → SLA-3 | Influx HTTP API | AWA/AWS/heel window | Read-only |
| SLA-2 → SLA-3 | REST | `race_id`, active leg, target AWA | Push on leg change |
| SLA-3 → SLA-2 | REST | `SailAnalysis`, trim scores | Push on analysis complete |
| SLA-2 → SLA-1 | **None** | — | **No writes upstream** |
| SLA-3 → SLA-1 | **None** | — | **No writes upstream** |

**Failure isolation:** If `race.local` or `vision.local` is unreachable, SLA-1 continues logging and displaying instruments. Crew sees a degraded-mode banner on tactical/vision dashboards only.

### 5.6 Resource governance (same-Pi multi-tier)

When multiple tiers share one Pi (compact / standard profile), enforce:

```yaml
# Example Docker Compose deploy.resources per tier
sla-1: { cpus: "2.0", memory: 2G }   # guaranteed
sla-2: { cpus: "1.5", memory: 3G }   # burstable
sla-3: { cpus: "2.0", memory: 3G }   # lowest priority — throttled when sla-1 under load
```

A `tier-watchdog` sidecar on shared nodes pauses SLA-3 containers when SLA-1 Influx write latency exceeds 500 ms for 30 s.

### 5.7 Dual-repository architecture

The platform uses **two GitHub repositories** — see [ADR-0009](./adr/0009-dual-repository-race-data.md).

| Repository | Role | Onboard path |
|------------|------|--------------|
| **[AI-sailing-system](https://github.com/cognite-fholm/AI-sailing-system)** | Code, containers, CI/CD | `/opt/ai-sailing-system/` |
| **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | Races, boats, planning, Neo4j YAML, OKF | `/opt/ai-sailing-data/` |

```mermaid
flowchart TB
    subgraph Shore["Onshore planning"]
        HUMAN["Crew / tactician"]
        DATA["AI-sailing-data\nGitHub"]
        HUMAN -->|PR, wiki, YAML| DATA
    end

    subgraph Boat["Onboard SLA-2"]
        SYNC["race-data-sync"]
        IMP["race-import"]
        N4J["Neo4j runtime"]
        OKF["OKF loader"]
        DATA -->|git pull via LTE/Wi-Fi| SYNC
        SYNC --> IMP --> N4J
        SYNC --> OKF
    end

    subgraph Knowledge["Three layers"]
        YAML["YAML facts\nplanning"]
        OKF2["OKF concepts\nLLM bootstrap"]
        LIVE["Neo4j + Influx\nlive race"]
    end

    DATA --- YAML
    DATA --- OKF2
    N4J --- LIVE
```

**Data repo layout (summary):**

| Branch | Path pattern | Content |
|--------|--------------|---------|
| Boats | `boats/{sail_number}/{year}/` | Ratings, polar, neo4j, okf, assets |
| Races | `races/{year}/{year}-{month}-{slug}/` | Manifest, planning, courses, fleet, scoring |

**Knowledge roles:**

| Store | Holds | Does not hold |
|-------|-------|---------------|
| **AI-sailing-data** | Pre-race plans, static graph templates, SI-derived routes | Live AIS, live standings |
| **Neo4j** | Runtime graph, interconnected analysis for crew + LLM | Long-form wiki prose |
| **OKF** (data + system bundles) | Concepts — how to read Neo4j labels and YAML kinds | Telemetry samples |
| **InfluxDB** | Time series | Handicap rules, course definitions |

**Deploy rule:** Version **both** repos at race freeze — system digest lock + data git tag/ref.

---

## 6. System context and data flow

### 6.1 High-level context

```mermaid
flowchart TB
    subgraph SLA1["SLA-1 — telemetry.local"]
        N0183["NMEA 0183"]
        N2K["NMEA 2000"]
        SK["Signal K"]
        IFX["InfluxDB"]
        G1["grafana-telemetry"]
        N0183 --> SK
        N2K --> SK
        SK --> IFX --> G1
    end

    subgraph SLA2["SLA-2 — race.local"]
        N4J["Neo4j"]
        RACE["race-intelligence"]
        COACH["tactical-coach"]
        LLM2["llama-tactical"]
        G2["grafana-race"]
        RACE --> N4J
        COACH --> LLM2
        COACH --> N4J
        N4J --> G2
    end

    subgraph SLA3["SLA-3 — vision.local"]
        GOPRO["gopro-orchestrator"]
        GEO["sail-geometry"]
        MATCH["condition-matcher"]
        VLLM["llama-vision"]
        SAIL["sail-analysis-api"]
        G3["grafana-sail"]
        GOPRO --> GEO --> MATCH --> SAIL --> G3
        GEO --> VLLM --> SAIL
    end

    IFX -.->|read-only| COACH
    IFX -.->|read-only| SAIL
    N4J -.->|race context| SAIL
    SAIL -.->|trim insights| N4J
```

### 6.2 Data flow (race mode)

```mermaid
sequenceDiagram
    participant N2K as NMEA buses (SLA-1)
    participant SK as Signal K (SLA-1)
    participant IFX as InfluxDB (SLA-1)
    participant G1 as grafana-telemetry
    participant G2 as grafana-race (SLA-2)
    participant N4J as Neo4j (SLA-2)
    participant AIS as ais-collector (SLA-2)
    participant GRIB as grib-parser (SLA-2)
    participant POLAR as polar-manager (SLA-2)
    participant WIND as wind-field-analyzer (SLA-2)
    participant GOPRO as gopro-orchestrator (SLA-3)
    participant GEO as sail-geometry (SLA-3)
    participant VLLM as llama-vision (SLA-3)

    N2K->>SK: AIS PGNs + instruments
    SK->>IFX: Deltas → time series
    G1->>IFX: Live instrument panels
    SK-->>AIS: AIS target deltas (WS)
    AIS->>N4J: Own + competitor positions

    GRIB->>WIND: TWS/TWD grid on course
    IFX-->>WIND: Own AWS/TWD/SOG/COG
    AIS-->>WIND: Fleet SOG vs polar
    POLAR-->>WIND: Target BSP/VMG (own + fleet)
    WIND->>N4J: WindAdvantageZone scores
    N4J-->>G2: Wind heatmap + fleet map

    GOPRO->>GEO: Aligned GoPro JPEGs
    IFX-->>GEO: Telemetry window
    GEO->>VLLM: Sail geometry + crops
    VLLM->>N4J: SailAnalysis
```

### 6.3 Offline vs online modes

```mermaid
stateDiagram-v2
    [*] --> OfflineRace: No internet
    [*] --> OnlineHarbor: Internet available

    OfflineRace: All services local
    OfflineRace: Grafana on LAN
    OfflineRace: LLaMA local only

    OnlineHarbor: Pull container updates
    OnlineHarbor: Optional model refresh
    OnlineHarbor: Optional shore backup

    OfflineRace --> OnlineHarbor: Connectivity restored
    OnlineHarbor --> OfflineRace: Leave harbor / race start
```

---

## 7. Software components

### 7.1 Signal K Server (hub) — **SLA-1 only**

**Language:** Node.js (TypeScript for custom plugins)  
**Source:** [SignalK/signalk-server](https://github.com/SignalK/signalk-server)

Signal K is the **single source of truth** for live marine data. It:

- Reads NMEA 0183 and NMEA 2000 via PiCAN-M interfaces.
- Exposes `ws://localhost:3000/signalk/v1/stream` for subscribers.
- Hosts plugins for InfluxDB export, Neo4j event emission, and coach triggers.

**Custom plugins planned:**

| Plugin | Responsibility |
|--------|----------------|
| `signalk-to-influxdb2` | Fork/adapt existing community plugin; map Signal K paths → Influx measurements |
| `signalk-race-events` | Detect tacks, gybes, mark rounding; emit to Neo4j |
| `signalk-ai-bridge` | Forward curated context windows to coach service |

### 7.2 Time series — InfluxDB — **SLA-1 only**

**Language:** configuration + Flux/SQL queries; write path in Node.js or Python  
**Replaces:** CDF time series (previously via `push_to_cdf`)

**Schema strategy:**

- **Bucket:** `signalk` (raw, 90-day retention); `race` (downsampled, long retention); `ais_tracks` (competitor + own-boat AIS positions, 30-day retention).
- **Measurement:** derived from Signal K path (e.g. `navigation_speedOverGround`).
- **Tags:** `vessel`, `source`, `pgn` (N2K), `context`, `race_id` (when active).
- **Fields:** numeric values; store strings in Neo4j instead.

**Migration from CogSail:** The `parse_signalK()` logic in `cogsail-python/push_to_cdf/Consume stream.py` maps deltas to external IDs — reuse this path→ID mapping as Influx measurement/field conventions.

### 7.3 Knowledge graph — Neo4j — **SLA-2 only**

**Language:** Cypher; ingestion via Python (`neo4j` driver) or Node.js (`neo4j-driver`)  
**Replaces:** CDF asset hierarchy + relationships (previously `cogsail-scripts/CreateBoats.py`, CDF data models)

**Core node labels:**

| Label | Examples |
|-------|----------|
| `Vessel` | Own boat (`is_own: true`), competitors (MMSI) |
| `Polar` | Polar diagram for a vessel (TWS × TWA → target BSP/VMG) |
| `GribModel` | Imported GRIB file metadata (model run, valid time, bbox) |
| `WindGrid` | Parsed wind field reference (linked to GribModel) |
| `WindAdvantageZone` | Course sector scored for favorable wind (runtime) |
| `AisTrack` | Time-series reference for vessel movement |
| `Race` | Regatta, passage race |
| `Course` | Windward/leeward, coastal — parsed from SI |
| `CourseRoute` | Named route variant (e.g. `11.1 Tristein`, `Bane A`, `Bane B`) |
| `ClassFlag` | Fleet class signal flag (e.g. Oscar, Foxtrot) per SI §7 |
| `StartBoatSignal` | Start-boat display linking signal → course (e.g. numeral 2 → Bane A) |
| `SupplementarySignal` | Modifies rounding (e.g. flag **T** → first mark starboard) |
| `CourseSelection` | Active course for current race + selection source |
| `Waypoint` | Mark/gate with lat/lon, rounding rule, optional distance |
| `OrcCertificate` | ORC cert variant (Club/DH/NS/Intl) per year; each has matched SLK |
| `HandicapRating` | ORC ToT/ToD/APH or WRS TCF — linked to certificate |
| `LiveStanding` | Current corrected-time position in fleet |
| `Mark` | Physical or virtual marks |
| `Leg` | Between marks |
| `Tack` / `Gybe` | Maneuver events |
| `Sailor` | Crew roles |
| `Tactic` | Pre-race plan, observed pattern |
| `WindSector` | Shift / persistent pattern |
| `SailGeometry` | Per-capture metrics from GoPro analysis (SLA-3) |
| `BestTrimSnapshot` | Top performance trim in a condition cluster |
| `TrimDelta` | Current vs best/optimal gap |
| `SailAnalysis` | Vision LLM narrative + fused recommendation |

**Example relationships:**

```cypher
(v:Vessel)-[:COMPETED_IN]->(r:Race)
(v:Vessel)-[:HAS_POLAR]->(p:Polar)
(r:Race)-[:USES_GRIB]->(g:GribModel)
(r:Race)-[:ON_COURSE]->(c:Course)
(c:Course)-[:HAS_ZONE]->(z:WindAdvantageZone)
(v:Vessel)-[:AIS_POSITION]->(pos:AisTrack)
(z:WindAdvantageZone)-[:DERIVED_FROM]->(g:GribModel)
(c:Course)-[:HAS_MARK]->(m:Mark)
(v:Vessel)-[:ROUNDED]->(m:Mark)
(v:Vessel)-[:PERFORMED]->(t:Tack)
(r:Race)-[:USES_SELECTION]->(sel:CourseSelection)
(sel)-[:SELECTED_ROUTE]->(cr:CourseRoute)
(cr:CourseRoute)-[:REQUIRES_SIGNAL]->(sb:StartBoatSignal)
(r:Regatta)-[:HAS_CLASS]->(cf:ClassFlag)
(v:Vessel)-[:SAILS_IN_CLASS]->(cf:ClassFlag)
```

Neo4j holds **context** (who, what, where, why); InfluxDB holds **telemetry** (how fast, when).

### 7.4 Visualization — Grafana

**One Grafana instance per SLA tier** — avoids dashboard load on the telemetry node.

| Instance | Tier | Port (default) | Dashboards |
|----------|------|----------------|------------|
| `grafana-telemetry` | SLA-1 | 3001 | SOG, COG, AWA, AWS, depth, heel, system health |
| `grafana-race` | SLA-2 | 3002 | Fleet map, polars, wind heatmap, **live standings**, course overlay |
| `course-editor` | SLA-2 | 3010 | React/TS — waypoints + **Start Line** flag/course selection |
| `grafana-sail` | SLA-3 | 3003 | Trim timeline, sail images, vision LLM output |

### 7.5 AI — LLaMA + Coral

**Languages:** Python (orchestration), C++ runtime (llama.cpp), TFLite (Coral)

| Layer | SLA | Technology | Role |
|-------|-----|------------|------|
| Text LLM | SLA-2 | **llama.cpp** + GGUF | Tactical Q&A, debrief, start-line narration |
| Vision LLM | SLA-3 | **llama.cpp** multimodal | Sail trim analysis from camera frames |
| Text model | SLA-2 | Llama 3.2 1B–3B Instruct (Q4_K_M) | Low latency tactical coaching |
| Vision model | SLA-3 | Llama 3.2 Vision 11B or smaller quant | Sail shape / trim interpretation |
| Edge ML | SLA-3 | **Coral** + TFLite | ROI, luff detection, frame preprocessing |
| Tactical coach | SLA-2 | **Python** (FastAPI) | RAG over Neo4j + SLA-1 Influx (read-only) |
| Sail analyst | SLA-3 | **Python** (FastAPI) | Vision pipeline orchestration |

**Offline inference:** Models ship on disk per node (`/opt/models/sla-2/`, `/opt/models/sla-3/`). No cloud calls at sea.

**Recommended models:**

| Node | Model | Size |
|------|-------|------|
| SLA-2 (race) | `Llama-3.2-3B-Instruct-Q4_K_M.gguf` | ~2 GB |
| SLA-3 (vision) | `Llama-3.2-11B-Vision-Instruct-Q4_K_M.gguf` (or smaller) | 4–8 GB |

#### 7.5.1 Advisory agent context — Google OKF

**Format:** [Google Open Knowledge Format (OKF) v0.1](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md)  
**System bundle:** `/opt/knowledge/sailing-system/` — architecture, marine paths, Neo4j schema reference  
**Race/boat bundles:** `/opt/ai-sailing-data/**/okf/` — per-regatta and per-boat-year concepts from [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)  
**Consumers:** `tactical-coach`, `sail-analysis-api`, `course-flag-detector`, `okf-loader`

OKF defines the **curated system context** that advisory agents read before and during inference. It complements — but does not replace — live data from InfluxDB and Neo4j:

| Layer | Role | Update frequency |
|-------|------|------------------|
| **OKF bundle** | Stable domain + **per-race/boat** concepts | Harbor / regatta prep; `race-data-sync` |
| **Neo4j** | Live race graph (fleet, course selection, standings) | Continuous during race |
| **InfluxDB** | Live telemetry (wind, SOG, heel) | Sub-second |

**Why OKF:** Vendor-neutral, human-readable markdown with YAML frontmatter; diffable in git; traversable by agents without proprietary SDKs. Producers (humans, `course-parser`, `okf-enricher`) and consumers (`tactical-coach`, vision LLM prompts) are independent.

**Bundle layout:**

```
knowledge/sailing-system/          # OKF Knowledge Bundle
├── index.md                       # okf_version: "0.1"; directory map
├── log.md                         # Change history
├── system/
│   ├── sla-tiers.md               # type: Reference — three-tier architecture
│   └── advisory-agents.md         # type: Playbook — which agent does what
├── marine/
│   ├── signalk-paths.md           # type: Reference — key Signal K paths
│   └── nmea-sources.md            # type: Reference — PiCAN-M buses
├── graph/
│   ├── neo4j-schema.md            # type: Reference — node labels & relationships
│   └── course-selection.md        # type: Playbook — StartBoatSignal / CourseSelection
├── regatta/
│   ├── hostcup-2025.md            # type: Playbook — Bane A/B, class flags, flag T
│   └── faerderseilasen-2026.md    # type: Playbook — §11 routes, §23 scoring
├── scoring/
│   ├── orc-handicaps.md           # type: Reference — APH, triple-number, WRS TCF
│   └── live-results.md            # type: Playbook — corrected time formula
├── wind/
│   ├── grib-usage.md              # type: Playbook — stale GRIB, fusion rules
│   └── polar-interpretation.md    # type: Reference — SLK columns, ORC derived
└── sail/
    ├── trim-metrics.md            # type: Reference — boom, draft, twist definitions
    └── gopro-capture.md           # type: Playbook — burst modes, geometry pipeline
```

**Example concept** (`regatta/hostcup-2025.md`):

```markdown
---
type: Playbook
title: Høstcup 2025 — courses and start-boat signals
description: Bane A/B selection, class flags, and supplementary flag T.
tags: [regatta, hostcup, course-selection]
resource: file://../Seilingsbestemmelser Høstcup 2025 ENDELIG.pdf
timestamp: 2026-07-05T00:00:00Z
---

# Class flags (§7)

| Class | Flag |
|-------|------|
| 1 | Oscar |
| 2 | Echo |
| 3 | Foxtrot |

# Course signals (Vedlegg 1)

- Numeral **2** on start boat → [Bane A](/regatta/routes/bane-a.md)
- Numeral **3** on start boat → [Bane B](/regatta/routes/bane-b.md)
- Flag **T** present → first mark **starboard**; absent → **port**

See [course selection playbook](/graph/course-selection.md).
```

**`okf-enricher` container (SLA-2):**

| Trigger | Action |
|---------|--------|
| `POST /courses/parse` completes | Write / update `regatta/{id}.md` concepts from parsed SI |
| `handicap-manager` import | Update `scoring/orc-handicaps.md` per vessel |
| Harbor sync | Regenerate `graph/neo4j-schema.md` from live schema |
| Manual edit | Crew edits markdown; git commit in harbor |

**Advisory agent consumption pattern:**

```mermaid
flowchart LR
    OKF["OKF bundle\n/opt/knowledge/"]
    N4J["Neo4j\nlive graph"]
    IFX["InfluxDB\nlive telemetry"]
    COACH["tactical-coach"]
    SAIL["sail-analysis-api"]
    LLM2["llama-tactical"]
    VLLM["llama-vision"]

    OKF -->|playbooks + schema| COACH
    OKF -->|trim + capture refs| SAIL
    N4J -->|Cypher RAG| COACH
    IFX -->|time windows| COACH
    COACH --> LLM2
    SAIL --> VLLM
```

1. **Bootstrap:** Load bundle `index.md`; agent reads relevant concepts by `type` and `tags` (e.g. `Playbook` + `regatta`).
2. **Per query:** Merge OKF concept text with live Neo4j/Influx facts in the prompt.
3. **Citations:** Agent responses cite OKF concept IDs and live data paths (FR: no uncited tactical claims).

**`AGENTS.md` (bundle root, OKF convention):** Instructions for advisory agents — which concepts to read first, offline-only constraint, and override rules for `CourseSelection`.

**Offline:** Full bundle ships on disk with the Pi image; no network required to read context at sea.

### 7.6 Race intelligence service — **SLA-2 only**

**Language:** Python 3.11+  
**ADR:** [0010 — iRegatta reference model](./adr/0010-iregatta-reference-model.md)

Responsibilities (aligned with **iRegatta** start/race/layline logic — see [§7.16](#716-iregatta-reference-model--feature-traceability)):

- **Start sequence** — countdown sync-to-minute, pause/reset, burn-or-gain vs time-to-line, favored end from wind⊥line geometry.
- **Line metrics** — distance to line perpendicular to line and extensions; time-to-line at current COG/SOG; bow/GPS antenna offset.
- **Lift / wind shift** — heading vs 10 s rolling average; configurable threshold (iRegatta “lift indicator”).
- **Steering guidance** — optimum VMG tack/jibe angles from `polar-manager` (or manual angles in degraded mode).
- Polar comparison for **own boat and competitors** via `polar-manager` (performance %).
- Trigger `wind-field-analyzer` on leg changes.
- Debrief generation post-race (LLaMA + structured data + wind-zone summary).

Publishes computed fields to InfluxDB (`start_line`, `lift`, `steering_hint`) for `grafana-race` panels.

This replaces implicit analytics that were previously envisioned in CDF tools / future Java apps.

### 7.7 Sail vision service (SLA-3)

**Language:** Python 3.11+  
**SLA tier:** SLA-3 only

Orchestrates the GoPro fleet → geometry → condition-match → vision LLM pipeline. See [§7.9–7.11](#79-gopro-hero13-black-fleet).

**Does not** run on the telemetry node in race profile.

### 7.8 Web crawler integration (optional, online)

**Source repo:** [crawl_web](https://github.com/cognite-fholm/crawl_web)

When online, crawl race documents (NOR, SI, sailing instructions) and ingest summaries into Neo4j as `RaceDocument` nodes linked to `Race`. Not required for onboard core loop.

### 7.9 GoPro HERO13 Black fleet

**API:** [Open GoPro](https://gopro.github.io/OpenGoPro/) (BLE + Wi-Fi HTTP) via [Python SDK](https://gopro.github.io/OpenGoPro/python_sdk/)  
**Camera:** GoPro HERO13 Black (firmware ≥ v01.10.00)  
**Container:** `gopro-orchestrator` (Python 3.11+, `open-gopro` package)

#### 7.9.1 Fleet topology

```mermaid
flowchart TB
    subgraph VisionPi["vision.local — SLA-3 Pi"]
        ORCH["gopro-orchestrator"]
        INGEST["media-ingest"]
        BLE1["BLE dongle 1"]
        BLE2["BLE dongle 2"]
        WIFI["Wi-Fi client\nboat LAN"]
    end

    subgraph GoPros["GoPro HERO13 fleet"]
        G1["gopro-mast\nserial …01"]
        G2["gopro-boom\nserial …02"]
        G3["gopro-bow\nserial …03"]
        G4["gopro-deck\nserial …04"]
    end

    subgraph BoatLAN["Boat LAN Wi-Fi AP"]
        AP["vision.local AP\nor existing router"]
    end

    ORCH --> BLE1 --> G1
    ORCH --> BLE1 --> G2
    ORCH --> BLE2 --> G3
    ORCH --> BLE2 --> G4
    G1 & G2 & G3 & G4 -.->|Station mode| AP
    INGEST --> WIFI --> AP
    G1 & G2 & G3 & G4 -.->|HTTP media download| INGEST
```

**BLE constraint:** Each HERO13 accepts **one BLE central** at a time. The orchestrator uses:

1. **Round-robin BLE** across 1–2 USB dongles for shutter triggers and health polls.
2. **Wi-Fi station mode** — cameras join boat LAN (`boat-vision` SSID); `media-ingest` pulls JPEGs via HTTP (`/gopro/media/list`, `/videos/DCIM/...`).

#### 7.9.2 Capture modes

| Mode | Trigger | Use case |
|------|---------|----------|
| **Scheduled still** | Cron every N s on stable leg | Continuous trim monitoring |
| **Synchronized burst** | `capture_trigger` event (AWA/AWS stable ±2° for 10 s) | Multi-camera geometry snapshot |
| **Maneuver bracket** | Tack/gybe detected (SLA-2 webhook) | Before/after trim comparison |
| **Manual** | Crew Grafana button | Ad-hoc inspection |

**Open GoPro commands (reference flow):**

```python
# Simplified — gopro-orchestrator
async with WirelessGoPro(identifier="…01") as gopro:
    await gopro.ble_command.set_shutter(shutter=Toggle.ENABLE)   # photo mode preset
    await gopro.ble_setting.photo_output.set(PhotoOutput.MAX_27MP)
    await gopro.ble_command.set_date_time(dt=synced_utc)         # GPS/NTP aligned
    await gopro.http_command.set_photo()                          # Wi-Fi path after connect
```

#### 7.9.3 Camera configuration (HERO13)

| Setting | Value | Rationale |
|---------|-------|-----------|
| Mode | Photo (not video) | Lower storage; sharper geometry |
| Resolution | 27 MP linear | Crop flexibility for sail ROI |
| FOV | Linear | Minimize distortion for angle math |
| Protune | Flat, sharpness high | Better edge detection |
| GPS | On (camera GPS) | Secondary timestamp; fuse with boat GPS |
| Wi-Fi | Station → boat LAN | Media download without phone |
| Sleep | Disabled during race session | Avoid HERO13 BLE wake bug — power-cycle checklist in docs |

#### 7.9.4 Timestamp alignment

Every capture record carries:

| Field | Source |
|-------|--------|
| `capture_id` | UUID generated by orchestrator |
| `t_trigger` | Vision Pi monotonic clock at shutter command |
| `t_exif` | EXIF DateTimeOriginal from GoPro JPEG |
| `t_influx` | Nearest SLA-1 telemetry window (±100 ms interpolated) |
| `race_id`, `leg_id` | SLA-2 session context |
| `camera_id` | `gopro-mast` \| `gopro-boom` \| `gopro-bow` \| `gopro-deck` |

All geometry and training exports key off `capture_id` + `t_influx`.

---

### 7.10 Sail geometry & condition similarity

**Containers:** `coral-preprocess`, `sail-geometry`, `condition-matcher`

#### 7.10.1 Geometry extraction pipeline

```mermaid
flowchart LR
    IMG["GoPro JPEG\n× N cameras"]
    CORAL["Coral TFLite\nsail/boom ROI"]
    CV["sail-geometry\nOpenCV + calib"]
    METRICS["SailGeometry JSON"]
    LLM["llama-vision\nqualitative layer"]
    MATCH["condition-matcher"]

    IMG --> CORAL --> CV --> METRICS
    METRICS --> LLM
    METRICS --> MATCH
    IFX["SLA-1 Influx\nheel, AWA, AWS"] --> MATCH
    N4J["SLA-2 Neo4j\nBestTrimSnapshot"] --> MATCH
```

**`SailGeometry` metrics (per capture, per sail type):**

| Metric | Unit | Cameras | Description |
|--------|------|---------|-------------|
| `boom_angle` | ° | gopro-boom, gopro-deck | Boom angle relative to boat centerline (vision + IMU fusion) |
| `mast_heel` | ° | gopro-mast + SLA-1 heel | Mast axis angle; cross-check instrument heel |
| `draft_position` | % chord | gopro-mast | Deepest camber point from leading edge |
| `camber_depth` | % chord | gopro-mast | Max thickness / chord |
| `leech_twist` | ° | gopro-mast | Angle between upper and lower leech tangent |
| `luff_break_angle` | ° | gopro-bow | Genoa luff separation from forestay plane |
| `foot_tension_proxy` | 0–1 | gopro-boom | Visual foot shelf / wrinkle score |
| `vang_tension_proxy` | 0–1 | gopro-boom | Boom-to-leech geometry hint |

Camera extrinsics (mount position + bearing) are stored in `config/cameras.yaml` and refined per boat during calibration sail.

#### 7.10.2 Condition vector

Each capture is tagged with a **condition vector** for similarity search:

```json
{
  "tws_bucket": "12-14",
  "awa_bucket": "25-35",
  "twa_bucket": "32-42",
  "heel_bucket": "8-15",
  "sea_state": 2,
  "tack": "port",
  "sail_plan": "main+jib",
  "vmg_percentile": 0.82
}
```

Buckets derived from SLA-1 telemetry at `t_influx`. Stored on `SailGeometry` nodes in Neo4j.

#### 7.10.3 Best-trim comparison

**`BestTrimSnapshot`** nodes represent historically strong performance in a condition cluster:

```cypher
(:BestTrimSnapshot {
  condition_hash: "tws12_awa30_port",
  boom_angle: 4.2,
  mast_heel: 12.1,
  draft_position: 42,
  leech_twist: 8.5,
  vmg_avg: 5.8,
  session_id: "2025-06-regatta-3",
  rank: 1
})
```

**`condition-matcher` algorithm (onboard):**

1. Compute `condition_hash` from current telemetry.
2. Query Neo4j for `BestTrimSnapshot` within ±1 bucket on TWS, AWA, heel (Cypher + optional vector index).
3. If onshore-trained model available (see §7.11), call `trim-predictor` edge artifact for optimal targets.
4. Emit `TrimDelta` — difference between current `SailGeometry` and best/optimal.

**Crew-facing output (Grafana-sail):**

| Current | Best in conditions | Δ | Recommendation |
|---------|-------------------|---|----------------|
| Boom 6.2° | 4.0° | +2.2° | Ease boom 2° |
| Draft 38% | 45% | −7% | Move draft aft (outhaul/vang) |
| Heel 18° | 12° | +6° | Depower — traveler down / vang |

---

### 7.11 Onshore transformer training pipeline

**SLA tier:** **SLA-S (Shore)** — runs on larger onshore machines only; **not required at sea**.

**Purpose:** Train **multimodal transformer models** on aligned sensor + image data to learn optimal **boom angle**, **mast heel**, **sail shape**, and rig settings for any condition. Deploy compressed artifacts back to the boat for SLA-3 inference.

#### 7.11.1 End-to-end ML lifecycle

```mermaid
flowchart TB
    subgraph Boat["Onboard — harbor / opt-in export"]
        SLA1["SLA-1 InfluxDB\ntelemetry windows"]
        SLA3["SLA-3 image-store\nGoPro JPEG + SailGeometry"]
        EXP["training-export\nbundle builder"]
        SLA1 --> EXP
        SLA3 --> EXP
    end

    subgraph Transfer["Data transfer — harbor only"]
        USB["USB / NAS"]
        S3["Object store\nMinIO / S3"]
        EXP --> USB --> S3
        EXP -.->|LTE optional| S3
    end

    subgraph Shore["SLA-S — onshore GPU cluster"]
        CURATE["dataset-curator\nquality + label"]
        TRAIN["trim-transformer-trainer\nPyTorch / HF"]
        EVAL["model-evaluator\nVMG holdout"]
        REG["model-registry\nMLflow"]
        QUANT["quantize → ONNX / GGUF"]
        S3 --> CURATE --> TRAIN --> EVAL --> REG --> QUANT
    end

    subgraph Deploy["Back to boat"]
        GHCR["GHCR model artifacts"]
        SLA3INF["SLA-3 trim-predictor\n+ updated Neo4j snapshots"]
        QUANT --> GHCR --> SLA3INF
    end
```

#### 7.11.2 Training dataset format

Each **training sample** = one synchronized multimodal window:

```
training_bundle/
├── manifest.json
├── sessions/
│   └── {session_id}/
│       ├── telemetry.parquet      # SLA-1: 30 s window @ 10 Hz
│       ├── captures/
│       │   ├── {capture_id}_mast.jpg
│       │   ├── {capture_id}_boom.jpg
│       │   └── {capture_id}_bow.jpg
│       ├── geometry/
│       │   └── {capture_id}.json  # SailGeometry (auto or human-refined)
│       └── labels/
│           └── {capture_id}.json  # OptimalTrim targets (see below)
```

**`manifest.json` fields:** `session_id`, `vessel_id`, `race_id`, `opt_in`, `export_timestamp`, `checksum`.

**Label sources (priority order):**

| Source | Description |
|--------|-------------|
| **Performance-derived** | Top-decile VMG segments in condition cluster → `SailGeometry` becomes positive label |
| **Expert annotation** | Coach labels optimal boom/heel/shape in web UI (shore) |
| **LLM-assisted pre-label** | Vision LLM proposes labels; human confirms in curation |
| **Transformer pseudo-label** | Prior model iteration bootstraps new sessions |

**`OptimalTrim` label schema:**

```json
{
  "boom_angle_deg": 4.0,
  "mast_heel_deg": 12.0,
  "draft_position_pct": 45,
  "camber_depth_pct": 12,
  "leech_twist_deg": 8.5,
  "vang_setting": 0.65,
  "cunningham_setting": 0.40,
  "outhaul_setting": 0.55,
  "traveler_position": 0.30,
  "confidence": 0.91
}
```

#### 7.11.3 Model architecture — TrimTransformer

**Framework:** PyTorch 2.x + Hugging Face Transformers (onshore); ONNX Runtime or quantized GGUF for edge deployment.

```mermaid
flowchart LR
    subgraph Inputs
        TS["Telemetry encoder\n1D Transformer / PatchTST"]
        IMG["Vision encoder\nViT or SigLIP\nper camera view"]
    end

    subgraph Fusion
        XATTN["Cross-attention\nfusion layers"]
    end

    subgraph Outputs
        HEAD["Trim prediction head\nOptimalTrim vector"]
        CONF["Uncertainty head"]
    end

    TS --> XATTN
    IMG --> XATTN
    XATTN --> HEAD
    XATTN --> CONF
```

| Component | Specification |
|-----------|---------------|
| **Telemetry encoder** | 30 s × N channels (AWA, AWS, TWS, SOG, VMG, heel, rudder, loads); PatchTST or small Temporal Fusion Transformer |
| **Vision encoder** | One ViT-B/16 (or SigLIP) per camera view; weights optionally init from sail-pretrained checkpoint |
| **Fusion** | 4-layer cross-attention; telemetry tokens attend to image patch tokens |
| **Output head** | Regression → `OptimalTrim` (10–15 continuous targets) |
| **Auxiliary loss** | VMG prediction (helps learn performance-aligned representations) |
| **Training hardware** | 1–8× NVIDIA GPU (A100/L40S class); 32 GB+ VRAM for multi-view + long context |

**Loss function:**

```
L = λ₁ · MSE(optimal_trim, predicted_trim)
  + λ₂ · Huber(vmg, predicted_vmg)
  + λ₃ · contrastive(condition_embed, same_bucket)   # similar conditions cluster
```

#### 7.11.4 Shore infrastructure (SLA-S)

| Service | Technology | Role |
|---------|------------|------|
| `dataset-curator` | Python, Label Studio | QA, dedup, consent check, train/val/test split by **session** (no leakage) |
| `trim-transformer-trainer` | PyTorch Lightning | Distributed training |
| `model-registry` | MLflow | Versioned checkpoints |
| `model-evaluator` | Custom + W&B | Holdout by regatta; report per-condition MAE |
| `neo4j-shore` | Neo4j (optional) | Aggregate fleet learnings → publish `BestTrimSnapshot` sets to boats |

**Host:** Personal **gaming PC** with NVIDIA GPU (CUDA) — **SLA-S**, harbor/home network only  
**Containers:** `shore/docker-compose.sla-shore.yml` (not deployed on Pi; not cloud VM)

#### 7.11.5 Deployment back to boat

After training and evaluation:

1. **Quantize** model → ONNX INT8 or distil to smaller edge checkpoint.
2. Publish to `ghcr.io/cognite-fholm/trim-predictor:{version}`.
3. Harbor sync: SLA-3 pulls artifact; `condition-matcher` uses hybrid **k-NN (Neo4j) + neural predictor**.
4. Export curated `BestTrimSnapshot` Cypher → SLA-2 Neo4j import script.

**Onboard inference (no GPU required):**

| Artifact | Latency target | Runs in |
|----------|----------------|---------|
| `trim-predictor-lite.onnx` | &lt; 2 s | SLA-3 `condition-matcher` |
| `llama-vision` GGUF | &lt; 60 s | SLA-3 qualitative narrative |
| Neo4j `BestTrimSnapshot` | &lt; 500 ms | SLA-3 k-NN fallback (offline) |

#### 7.11.6 Data governance

| Rule | Implementation |
|------|----------------|
| Opt-in export | `TRAINING_EXPORT_CONSENT=true` in harbor UI; per-session toggle |
| PII / crew | No faces in training set — Coral blur pass optional |
| Competitor data | Exclude unless consented |
| Retention | Raw images on shore: 24 months; delete on request |
| Race mode | `training-export` container **stopped** when `RACE_MODE=true` |

**Shore hardware:** Use existing **gaming PC** rather than Azure/AWS GPU VMs — PyTorch + CUDA locally; publish artifacts to GHCR from harbor; see [§9.6](#96-shore-training--gaming-pc-sla-s).

---

### 7.12 GRIB, polars, AIS & wind-on-course analysis

**SLA tier:** SLA-2 (`grib-ingest`, `grib-parser`, `polar-manager`, `ais-collector`, `wind-field-analyzer`)  
**AIS source:** SLA-1 Signal K (NMEA 2000 AIS via PiCAN-M)  
**Languages:** Python 3.11+ (`cfgrib`/`xarray`, `pyais`, FastAPI)

#### 7.12.1 Data flow overview

```mermaid
flowchart TB
    subgraph SLA1["SLA-1 — telemetry.local"]
        N2K["NMEA 2000\nAIS PGNs"]
        SK["Signal K"]
        IFX["InfluxDB"]
        N2K --> SK --> IFX
    end

    subgraph SLA2["SLA-2 — race.local"]
        AIS["ais-collector"]
        GRIB_IN["grib-ingest"]
        GRIB_P["grib-parser"]
        POLAR["polar-manager"]
        WIND["wind-field-analyzer"]
        N4J["neo4j"]
        GF["grafana-race"]

        GRIB_IN --> GRIB_P --> WIND
        AIS --> WIND
        POLAR --> WIND
        AIS --> N4J
        POLAR --> N4J
        GRIB_P --> N4J
        WIND --> N4J
        N4J --> GF
    end

    SK -.->|AIS deltas WS| AIS
    IFX -.->|own-boat wind\nSOG/COG/heel| WIND
```

#### 7.12.2 GRIB ingestion — regular upload schedule

**Containers:** `grib-ingest`, `grib-parser`  
**Storage:** `/data/grib/` on SLA-2 (persistent volume `grib-store`)

| Mode | Schedule | Trigger |
|------|----------|---------|
| **Automatic fetch** | Every **6 hours** when `ONLINE_MODE=true` | `grib-ingest` cron (`0 */6 * * *`) |
| **Pre-race fetch** | Manual + 24 h before start | Grafana / API `POST /grib/fetch` |
| **Manual upload** | Anytime in harbor | `POST /grib/upload` (multipart `.grb2`) |
| **USB import** | Harbor | Copy to `/data/grib/inbox/` — file watcher ingests |
| **Shore push** | Optional | Shore server rsync/scp to `race.local` |

**Configured sources (`config/grib-sources.yaml`):**

```yaml
sources:
  - name: gfs-opendap
    url_template: "https://{host}/grib2/{run}/gfswave.t{fh}z.global.0p25.f{step}.grib2"
    model: GFS
    schedule: "0 */6 * * *"
    bbox_from: course   # auto-clip to active course + 10 NM margin
  - name: manual
    type: upload
```

**Ingest pipeline:**

1. Download or receive GRIB2 file.
2. Validate magic bytes, record `model_run`, `valid_from`, `valid_to`, `bbox`.
3. `grib-parser` extracts **U/V wind** (and optional gust, pressure) → `WindGrid` store (Zarr or GeoJSON tiles on Pi).
4. Register `GribModel` node in Neo4j; link to active `Race` when `race_id` set.
5. Prune GRIB files older than **7 days** (configurable).

**Offline use:** Latest successfully parsed GRIB remains queryable at sea without internet. Grafana shows **GRIB age** warning if valid time &gt; 12 h behind race start.

#### 7.12.3 Polar diagram management

**Containers:** `polar-manager`, `polar-certificate-extractor`

Polars define target boat speed and VMG for each **TWS × TWA** combination. The **own boat** uses a high-fidelity **SLK** performance file. **Competitors** derive polars from ORC **certificate images or PDFs** when no SLK is available.

##### Own boat — SLK file (primary source)

| Attribute | Value |
|-----------|-------|
| **Format** | **SYLK (`.slk`)** — ORC / sail-performance export |
| **Reference file (dev)** | `AI-sailing-data/boats/NOR-10133/2026/assets/7710.slk` (from `7710 (3).slk`) |
| **Certificate** | `ORC Certificate for Xbox.pdf` — CertNo **7710** matches SLK data file |
| **Deploy path (Pi)** | `/data/polars/own/7710.slk` (copy at harbor sync) |
| **Parser** | `polar-manager` SLK module (`slk_parser.py`) |
| **Required** | Yes — system will not start race mode without own-boat polar |

**SLK column mapping** (from `7710 (3).slk` header):

| SLK column | Canonical field | Unit |
|------------|-----------------|------|
| `TWS` | `tws` | knots |
| `TWA` | `twa` | degrees |
| `BTV` | `bsp` | knots (boat speed) |
| `VMG` | `vmg` | knots |
| `AWS` | `aws` | knots |
| `AWA` | `awa` | degrees |
| `Heel` | `heel` | degrees |
| `Condition` | `point_of_sail` | `beat` \| `reach` \| `run` |
| `Sail` / `Reef` / `Flat` | `sail_config` | reef / flat state |

**Example SLK rows** (TWS 6 kt):

```
Condition=beat  TWA=42.4  BTV=5.26  VMG=3.89
Condition=run   TWA=141.5 BTV=4.91  VMG=3.84
Condition=reach TWA=52.0  BTV=5.86  VMG=3.61
```

**`config/vessel.yaml` (own boat):**

```yaml
vessel:
  id: own-boat
  name: "Xbox"
  sail_number: "NOR-10133"
  mmsi: "257771000"
  orc_cert_no: "7710"
  is_own: true
polar:
  source_type: slk
  path: "../7710 (3).slk"    # relative to repo on dev machine
  # path: "/data/polars/own/7710.slk"   # on Raspberry Pi
  slk_id: "7710"
  auto_reload: true          # re-parse when file mtime changes
```

On Windows dev: `polar-manager` resolves `../7710 (3).slk` from `AI-sailing-system/` → `C:\Repositories\boat_system\7710 (3).slk`.

##### Competitors — certificate image / PDF extraction

Competitors rarely provide SLK files. Polars are **derived** from ORC rating certificate diagrams.

| Attribute | Value |
|-----------|-------|
| **Input formats** | `.png`, `.jpg`, `.pdf` (ORC sail plan / certificate) |
| **Reference file (dev)** | `C:\Repositories\boat_system\off_course.png` |
| **Example vessel** | *OFF COURSE* — sail no. **NOR 15788** |
| **Container** | `polar-certificate-extractor` |
| **Confidence** | Lower than SLK — flagged `polar_source: derived` |

**Reference certificate content** (`off_course.png`):

| Extracted data | Example value | Use |
|----------------|---------------|-----|
| Boat name | OFF COURSE | Neo4j `Vessel.name` |
| Sail number | NOR 15788 | Roster matching |
| Mainsail area | 63.99 m² | VPP input |
| Headsail area | 46.36 m² | VPP input |
| Asymmetric | 158.63 m² | Downwind model |
| LOA, P, E, J, IG | 13.69, 17.25, 6.00, 5.02, 17.17 m | Rating geometry |
| MHW, HHU, SHW, … | sail widths | Shape coefficients |

**Extraction pipeline:**

```mermaid
flowchart LR
    CERT["Certificate\nPNG / PDF"]
    OCR["OCR + layout\nTesseract / PaddleOCR"]
    VISION["Vision LLM\noptional validation"]
    VPP["VPP-lite\nORC regression"]
    YAML["polars/{mmsi}.yaml\nderived polar"]
    CERT --> OCR --> VPP
    OCR --> VISION --> VPP
    VPP --> YAML
    YAML --> PM["polar-manager"]
```

1. **`polar-certificate-extractor`** — OCR reads labelled dimensions and sail areas from diagram.
2. **Vision LLM** (optional cross-check on SLA-3 or SLA-2) validates OCR against image regions.
3. **VPP-lite** — estimates `TWS × TWA → BSP/VMG` from ORC dimensions (class-based regression or simplified velocity prediction).
4. Output saved as `polars/competitors/{mmsi}_derived.yaml` with `confidence` and `source_file` metadata.
5. Human review recommended in harbor before regatta (`polar_status: pending` → `approved`).

**`config/competitors.yaml` (example):**

```yaml
competitors:
  - name: "OFF COURSE"
    sail_number: "NOR 15788"
    mmsi: null                    # filled when AIS seen
    polar:
      source_type: certificate_image
      path: "../off_course.png"   # C:\Repositories\boat_system\off_course.png
      # path: "/data/polars/competitors/off_course.png"
      status: pending             # pending | approved | rejected
```

**API (extended):**

| Endpoint | Action |
|----------|--------|
| `POST /polars/own/reload` | Re-parse SLK from configured path |
| `POST /polars/competitor/extract` | Upload PNG/PDF → run certificate extractor |
| `POST /polars/competitor/{id}/approve` | Mark derived polar approved for race use |
| `GET /polars/{mmsi}` | Return canonical polar (`source: slk` \| `derived`) |
| `GET /polars/{mmsi}/target?tws=12&twa=42` | Interpolated target BSP/VMG |
| `GET /polars/{mmsi}/meta` | `source_type`, `confidence`, `source_file` |

##### Canonical internal format

All sources normalize to `polars/{mmsi_or_vessel_id}.yaml`:

```yaml
vessel_id: own-boat
mmsi: "257771000"
source_type: slk                    # slk | derived | manual
source_file: "7710 (3).slk"
confidence: 1.0                     # derived polars: 0.6–0.9 typical
boat_name: "7710"
points:
  - tws: 6
    twa: 42.4
    bsp: 5.262
    vmg: 3.8873
    aws: 10.5041
    awa: 22.64
    heel: 10.31
    point_of_sail: beat
```

**Neo4j:**

```cypher
MERGE (v:Vessel {mmsi: $mmsi})
MERGE (p:Polar {vessel_id: $vessel_id, season: $year})
SET p.source_type = $source_type,    // "slk" or "derived"
    p.source_file = $source_file,
    p.confidence = $confidence
MERGE (v)-[:HAS_POLAR {active: true}]->(p)
```

**Runtime use:**

- **Own boat (SLK):** `actual_VMG / target_VMG` → polar performance % — full confidence.
- **Competitors (derived):** same formula; `wind-field-analyzer` weights fleet term by `polar.confidence`.
- Low-confidence derived polars (&lt; 0.7) show warning badge on grafana-race.

**File layout on dev machine:**

```
C:\Repositories\boat_system\
├── 7710 (3).slk              ← own-boat polar (SLK)
├── off_course.png            ← competitor certificate example
└── AI-sailing-system\        ← git repo
    └── config\
        ├── vessel.yaml
        └── competitors.yaml
```

#### 7.12.4 AIS collection — own boat and competitors

**Containers:** `ais-collector` (SLA-2), Signal K (SLA-1 ingest)

AIS arrives on the **NMEA 2000 backbone** via PiCAN-M (`can0`). Signal K decodes AIS PGNs into delta paths under `sensors.ais.*`.

| Target | MMSI source | Signal K path (reference) |
|--------|-------------|---------------------------|
| **Own boat** | Transponder MMSI | `navigation.position`, `navigation.courseOverGroundTrue`, `navigation.speedOverGround` + `sensors.ais.class` |
| **Competitors** | AIS class A/B | `sensors.ais.targets.{mmsi}.position`, `.course`, `.speed`, `.name` |

**`ais-collector` pipeline:**

1. Subscribe to `ws://telemetry.local:3000/signalk/v1/stream/?subscribe=none` — filter AIS deltas.
2. Write to **SLA-2 InfluxDB** replica bucket `ais_tracks` (or SLA-1 write + SLA-2 read — prefer SLA-2 local copy to avoid SLA-1 write load):

| Measurement | Tags | Fields |
|-------------|------|--------|
| `ais_position` | `mmsi`, `name`, `is_own`, `race_id` | `lat`, `lon`, `cog`, `sog`, `heading` |

3. Upsert `Vessel` nodes in Neo4j; mark `is_own: true` for configured own MMSI.
4. `competitor-sync` maintains regatta roster — links known competitors from entry list to AIS tracks.

**Refresh rate:** ≤ 10 s for class A; class B as received (typically 30 s–3 min).

**Own-boat cross-check:** Compare AIS SOG/COG with instrument SOG/COG from SLA-1; flag calibration drift &gt; 5%.

#### 7.12.5 Runtime wind-on-course analysis

**Container:** `wind-field-analyzer`  
**Runs:** Every **30–60 s** during active `race_id`; triggered on leg change and significant wind shift (&gt; 8° TWD in 5 min).

**Purpose:** Fuse **GRIB forecast**, **own instrument wind**, **fleet AIS movement**, and **polars** to estimate **where on the course favorable wind currently exists** — including areas where competitors are outperforming their polars (proxy for better pressure).

```mermaid
flowchart LR
    GRIB["GRIB grid\nTWS/TWD per cell"]
    OWN["Own boat\nAWS/AWA/TWD"]
    AIS["Fleet AIS\ntracks × polars"]
    COURSE["Course geometry\nmarks + legs"]
    FUSE["wind-field-analyzer"]
    ZONES["WindAdvantageZone\nscores + bearing"]
    UI["grafana-race\nheatmap + advice"]

    GRIB --> FUSE
    OWN --> FUSE
    AIS --> FUSE
    COURSE --> FUSE
    FUSE --> ZONES --> UI
```

**Course discretization:**

- Divide active leg into **sectors** (default 0.25 NM grid or 500 m along-leg bins).
- For each sector center `(lat, lon)`:

| Input | Computation |
|-------|-------------|
| GRIB | Interpolate TWS/TWD at valid time nearest race now |
| Own instruments | Bias-correct GRIB with recent `AWS/TWD` residual (last 15 min) |
| Fleet AIS | For competitors in sector: `Δ = SOG_actual − SOG_polar(TWS,TWA)` |
| Own polar | `VMG_target` vs `VMG_actual` if own boat transited sector |

**Wind advantage score (0–1 per sector):**

```
score = w₁ · normalize(TWS)
      + w₂ · fleet_overperformance_mean
      + w₃ · (1 - competitor_density_penalty)
      + w₄ · vmg_potential_own_polar
```

Default weights: `w₁=0.35, w₂=0.40, w₃=0.10, w₄=0.15` (tunable per boat class).

**Outputs:**

| Artifact | Destination |
|----------|-------------|
| `WindAdvantageZone` nodes | Neo4j — sector polygon, score, TWS/TWD, timestamp |
| `wind_zone` time series | InfluxDB — sector scores for replay |
| Tactical recommendation | `tactical-coach` + grafana-race — e.g. *"Port side of beat: +1.2 kt fleet overperformance vs polars"* |
| GeoJSON layer | grafana-race geomap — green/yellow/red sectors |

**Example Cypher result:**

```cypher
(:WindAdvantageZone {
  sector_id: "leg2_bin_04",
  score: 0.82,
  tws_kn: 13.4,
  twd_deg: 245,
  fleet_delta_sog: 0.9,
  recommendation: "Favor port tack ladder — fleet gaining on polars"
})
```

**Offline behavior:** Without fresh GRIB, analyzer uses **last GRIB + instrument bias + AIS fleet deltas only** (degraded mode banner). AIS and polars work fully offline.

#### 7.12.6 Grafana-race panels (wind & fleet)

| Panel | Data source |
|-------|-------------|
| Fleet AIS map | Influx `ais_tracks` + Neo4j `Vessel` |
| GRIB wind barbs | `grib-parser` API overlay on course |
| Polar performance % | own + selected competitor MMSI |
| Wind advantage heatmap | `WindAdvantageZone` GeoJSON |
| GRIB freshness | `GribModel.valid_from` age indicator |

---

### 7.13 Race courses, waypoints & live results

**SLA tier:** SLA-2 (+ optional SLA-3 vision for flag photos)  
**Containers:** `course-parser`, `live-results`, `course-editor`, `course-flag-detector`  
**Reference SI (narrative routes):** `C:\Repositories\boat_system\Seilingsbestemmelser_Færderseilasen26_2.pdf` — §11  
**Reference SI (flag-signaled courses):** `C:\Repositories\boat_system\Seilingsbestemmelser Høstcup 2025 ENDELIG.pdf` — Vedlegg 1 & 2

#### 7.13.1 Competition program course parsing

Regatta **Sailing Instructions (SI)** and **Notice of Race (NOR)** PDFs describe race routes as narrative bullet lists — often with mixed coordinate precision. The system must parse these into structured waypoints for **VMG**, **leg geometry**, and **live results**.

**Reference — Færderseilasen 2026, §11:**

> *"Oppgitte GPS posisjoner er omtrentlige. De oppgitte distansene brukes til resultatberegning."*  
> *(Stated GPS positions are approximate. Stated distances are used for result calculation.)*

**Example routes extracted from chapter 11:**

| Route ID | Name | Coordinates in SI | Rounding notes |
|----------|------|-------------------|----------------|
| `11.1` | Tristein | Nærsnes `N59°46,3 Ø010°31,0`; lysbøye `N59°52,50' Ø010°38,76'` | Tristein stb, Bile port |
| `11.2` | Hollænderbåen | Same partial coords | Hollænderbåen stb |
| `11.3` | Mefjordbåen | Same | Mefjordbåen stb |
| `11.4` | Mølen | Same | Mølen + Bile port |
| `11.5` | Oslo–Moss | Same | Finish Moss |
| `11.6` | Tristein (Sarpsborg) | No coords — named islands | Sandøy stb, Tresteinene port |

**`course-parser` pipeline:**

```mermaid
flowchart LR
    PDF["SI/NOR PDF\nFærderseilasen…"]
    EXTRACT["PDF text + layout\nPyMuPDF"]
    NLP["Section detector\nCh. 11 Løpene"]
    COORD["Coordinate regex\nN59°52,50' Ø010°38,76'"]
    WP["Waypoint list\n+ rounding rules"]
    N4J["Neo4j CourseRoute"]
    PDF --> EXTRACT --> NLP --> COORD --> WP --> N4J
```

**Coordinate patterns parsed (WGS-84):**

| Pattern | Example | Decimal output |
|---------|---------|----------------|
| Degrees + decimal minutes | `N59°52,50' Ø010°38,76'` | `59.8750, 10.6460` |
| Degrees + decimal minutes (no prime) | `N59°46,3 Ø010°31,01` | `59.7717, 10.5168` |
| Named feature only | `Bygdøy og Nakholmen` | `coords: null` → user entry |

**Parsed waypoint schema (`waypoints/{route_id}.json`):**

```json
{
  "route_id": "11.1",
  "name": "Tristein",
  "regatta": "Færderseilasen 2026",
  "source_file": "Seilingsbestemmelser_Færderseilasen26_2.pdf",
  "source_section": "11.1",
  "distance_nm": null,
  "waypoints": [
    {"seq": 1, "name": "Startlinje Oslo havn", "lat": null, "lon": null, "type": "start"},
    {"seq": 2, "name": "Bygdøy og Nakholmen", "lat": null, "lon": null, "type": "gate", "note": "between"},
    {"seq": 3, "name": "Lysbøye Nesoddtangen", "lat": 59.875, "lon": 10.646, "type": "mark", "rounding": "pass_north_west"},
    {"seq": 4, "name": "Nærsnes", "lat": 59.7717, "lon": 10.5168, "type": "mark", "rounding": "pass_north_west"},
    {"seq": 5, "name": "Tristeingrunnen / Færder Fyr", "lat": null, "lon": null, "type": "mark", "rounding": "starboard"},
    {"seq": 6, "name": "Bile", "lat": null, "lon": null, "type": "mark", "rounding": "port"},
    {"seq": 7, "name": "Mål", "lat": null, "lon": null, "type": "finish"}
  ]
}
```

**API:**

| Endpoint | Action |
|----------|--------|
| `POST /courses/parse` | Upload SI/NOR PDF → extract all §11 routes |
| `GET /courses/{race_id}/routes` | List parsed routes for active regatta |
| `PUT /courses/{route_id}/waypoints` | Save user-edited coordinates |
| `GET /courses/{route_id}/geojson` | Course line for Grafana map |

**Parsing profiles** — `course-parser` supports two SI patterns:

| Profile | Example regatta | Course discovery |
|---------|-----------------|------------------|
| `narrative` | Færderseilasen §11 | Named sections (`11.1 Tristein`, …) |
| `flag_signaled` | Høstcup Vedlegg 1/2 | **Bane A / Bane B** + start-boat **numeral pennants** |

#### 7.13.2 Multiple courses per race & start-boat flag signaling

A single regatta often publishes **several possible courses** for the same race. The **actual course** is communicated at the start line by flags displayed on the **committee / start boat** — not known until the start sequence.

**Reference — Høstcup 2025, Vedlegg 1 (distanseseilaser):**

> *"Bane A seiles hvis tallstander 2 er vist ombord i startbåten ved start. Bane B seiles når tallstander 3 er vist ombord i startbåten ved start."*

**Supplementary signal (same appendix):**

> *"Dersom signalflagg **T** vises ombord i startbåten ved start skal første merke rundes om styrbord. Er ikke signalflagg T vist … skal første merke rundes om babord."*

**Class flags (Høstcup §7)** — identify which fleet you start with:

| Class | Description | Flag |
|-------|-------------|------|
| 1 | NOR Rating distanseseilaser | **Oscar** |
| 2 | NOR Rating shorthand distanse | **Echo** |
| 3 | NOR Rating baneseilaser | **Foxtrot** |

**Course variants per class (Høstcup):**

| Class | Appendix | Variants | Start-boat signal |
|-------|----------|----------|-------------------|
| 1–2 | Vedlegg 1 | **Bane A** (~22 nm), **Bane B** (~23 nm) | Numeral **2** → A, **3** → B |
| 3 | Vedlegg 2 | Short / medium / long windward-leeward | **None** / **2** / **3** |

**Vedlegg 2 baneseilaser sequences:**

| Signal on start boat | Mark sequence |
|---------------------|---------------|
| No numeral | Start – 1 – 1a – 2 – 1 – 1a – Mål |
| Numeral **2** | Start – 1 – 1a – Mål |
| Numeral **3** | Start – 1 – 1a – 2 – 1 – 1a – 2 – 1 – 1a – Mål |

**Data model (Neo4j):**

```cypher
(r:Regatta {id: "hostcup-2025"})-[:HAS_CLASS]->(cf:ClassFlag {
  class_no: 3,
  name: "NOR Rating baneseilaser",
  ics_flag: "Foxtrot",
  letter: "F"
})

(r)-[:OFFERS_COURSE]->(cr:CourseRoute {
  route_id: "bane-a",
  name: "Bane A",
  distance_nm: 22,
  appendix: "vedlegg-1"
})

(sb:StartBoatSignal {
  signal_type: "numeral_pennant",
  display: "2",
  maps_to_route_id: "bane-a"
})

(cr)-[:REQUIRES_SIGNAL]->(sb)

(ss:SupplementarySignal {
  ics_flag: "T",
  effect: "first_mark_rounding",
  rounding: "starboard",
  default_if_absent: "port"
})

(sel:CourseSelection {
  race_id: "hostcup-2025-race2",
  route_id: "bane-a",
  source: "user",           // user | vision | default
  vision_confidence: null,
  selected_at: datetime(),
  supplementary: ["T"]        // active modifier flags
})
```

**`course-parser` output for flag-signaled regattas (`courses/hostcup-2025.json`):**

```json
{
  "regatta_id": "hostcup-2025",
  "source_file": "Seilingsbestemmelser Høstcup 2025 ENDELIG.pdf",
  "class_flags": [
    {"class_no": 1, "ics_flag": "Oscar", "letter": "O"},
    {"class_no": 2, "ics_flag": "Echo", "letter": "E"},
    {"class_no": 3, "ics_flag": "Foxtrot", "letter": "F"}
  ],
  "start_boat_signals": [
    {"signal": "numeral_2", "display": "2", "route_id": "bane-a"},
    {"signal": "numeral_3", "display": "3", "route_id": "bane-b"},
    {"signal": "none", "display": null, "route_id": "wl-long", "classes": [3]}
  ],
  "supplementary_signals": [
    {"ics_flag": "T", "affects": "waypoint_1", "rounding_if_present": "starboard", "rounding_if_absent": "port"}
  ],
  "routes": [
    {
      "route_id": "bane-a",
      "name": "Bane A",
      "distance_nm": 22,
      "requires_signal": "numeral_2",
      "waypoints": [
        {"seq": 1, "name": "Kryssmerke", "lat": null, "lon": null, "rounding": "from_T_flag"},
        {"seq": 2, "name": "Østre Måsane", "lat": 59.8269, "lon": 10.5835, "rounding": "starboard"}
      ]
    },
    {
      "route_id": "bane-b",
      "name": "Bane B",
      "distance_nm": 23,
      "requires_signal": "numeral_3",
      "waypoints": []
    }
  ]
}
```

**Runtime behaviour:**

1. Before start: all `CourseRoute` variants for the regatta are loaded; **none** is active.
2. At start sequence: crew observes start boat (or receives GoPro capture).
3. `CourseSelection` is created — binds `race_id` + `route_id` + modifiers.
4. `live-results`, `wind-field-analyzer`, and VMG use **only the selected route**.
5. Changing selection mid-race requires user override + audit log (normally fixed at start).

#### 7.13.3 Start-line flag UX & vision detection

**Container:** `course-editor` (React/TypeScript) — **Start Line** panel  
**Optional:** `course-flag-detector` (SLA-2 or SLA-3) — Coral + vision on start-boat photo

```mermaid
flowchart TB
    subgraph UX["course-editor — Start Line panel"]
        CF["Your class flag\nFoxtrot ■"]
        SF["Course signals\n2 → Bane A | 3 → Bane B"]
        SUP["Modifiers\n□ Flag T"]
        SEL["Confirm selection"]
    end

    subgraph Vision["Optional — GoPro at start"]
        PHOTO["Photo incl. start boat"]
        DET["course-flag-detector"]
        PHOTO --> DET
    end

    DET -.->|suggested route| UX
    USER["Crew"] --> SEL
    SEL --> API["POST /courses/selection"]
    API --> N4J["CourseSelection"]
```

**UX requirements (`http://race.local:3010/start`):**

| Panel | Content |
|-------|---------|
| **Your class** | ICS flag graphic + name for own boat's fleet (from `vessel.yaml` `class_no` or user setting) — e.g. **Foxtrot** for Høstcup class 3 |
| **Course signals** | All `StartBoatSignal` options for this class — visual numeral pennants **2**, **3**, or "no numeral" with route name (**Bane A**, **Bane B**, WL short, …) |
| **Modifiers** | Toggle supplementary flags (**T**) when observed on start boat |
| **Vision suggestion** | If GoPro photo processed: *"Detected: numeral 2 → Bane A (87%)"* with **Accept** / **Override** |
| **Confirm** | Locks `CourseSelection` for active `race_id`; shows selected track on map |

**Flag visuals:** Render standard ICS racing flag shapes (numeral pennants 0–9, letter flags, **T** = red cross on white) — not text-only.

**`course-flag-detector` pipeline (optional):**

1. Trigger: manual upload, GoPro burst at start, or `capture_trigger` on preparatory signal.
2. Coral ROI: locate start boat / flag halyard region.
3. Classify visible flags: numeral pennants, **T**, class flags (CNN or small vision model).
4. Map to `StartBoatSignal` → suggested `route_id` + `SupplementarySignal[]`.
5. Return `{ suggested_route, confidence, flags_detected[] }` — **never auto-lock** without user confirm (configurable `auto_select_above_confidence: 0.95` for advanced users).

**API:**

| Endpoint | Action |
|----------|--------|
| `GET /courses/{regatta_id}/signals` | Class flags + start-boat signals + supplementary |
| `POST /courses/selection` | Set active course `{ race_id, route_id, supplementary[], source }` |
| `GET /courses/selection/{race_id}` | Current selection |
| `POST /courses/flag-detect` | Image → suggested course |
| `PUT /courses/selection/{race_id}/override` | User override with reason |

**Integration with Færderseilasen-style regattas:** Routes like `11.1`–`11.6` may also be signaled from the committee boat; parser stores optional `StartBoatSignal` mappings when SI defines them. If not defined, user picks route manually from list (same UX, no vision mapping).

#### 7.13.4 Manual waypoint entry — React/TypeScript UX

When `course-parser` cannot resolve coordinates, the crew enters them via **`course-editor`** — a lightweight **React + TypeScript** SPA served from the SLA-2 Pi.

| Attribute | Value |
|-----------|-------|
| **Stack** | React 18, TypeScript, Vite |
| **Map** | Leaflet + OpenStreetMap tiles (cached offline) |
| **Host** | `http://race.local:3010` |
| **Container** | `course-editor` (nginx + static build) |
| **Auth** | Local PIN (harbor setup) |

**UX flow:**

1. Select regatta → select route (e.g. `11.1 Tristein`).
2. List shows waypoints with **red** (missing coords) / **green** (resolved).
3. Tap waypoint → place pin on map or type `lat/lon` (decimal or DMS).
4. Optional: tap own-boat AIS position to snap nearby mark.
5. **Save** → `PUT /courses/{route_id}/waypoints` → Neo4j + JSON on disk.
6. Export GeoJSON for Grafana-race overlay.

```mermaid
flowchart TB
    USER["Crew tablet\nrace.local:3010"]
    EDITOR["course-editor\nReact/TS"]
    API["course-parser API"]
    N4J["Neo4j Waypoint nodes"]
    USER --> EDITOR --> API --> N4J
```

**Offline:** Map tiles pre-cached; editor works without internet after initial harbor setup.

#### 7.13.5 VMG and progress along course

**Container:** `live-results` (uses parsed waypoints + AIS + SLA-1 wind)

For **own boat and each competitor**, compute:

| Metric | Formula / method |
|--------|------------------|
| **Leg** | Active segment between last rounded WP and next WP |
| **DTM** | Distance to next mark (nm) |
| **BTM** | Bearing to mark (°T) |
| **VMG** | `SOG × cos(angle between COG and BTM)` — toward next mark |
| **Target VMG** | From polar at current TWS/TWA toward mark |
| **Course %** | Distance sailed along route / total route distance |
| **ETA** | `DTM / VMG` (when VMG &gt; 0) |

Coordinates from chapter 11 enable VMG **relative to the rhumb line** on each leg, not just absolute SOG.

**Influx measurements (`course_progress`):**

| Tags | Fields |
|------|--------|
| `mmsi`, `race_id`, `route_id`, `leg_seq` | `vmg`, `dtm`, `btm`, `course_pct`, `lat`, `lon` |

#### 7.13.6 Live results list (corrected time ordering)

**Reference SI §23:** *"Korrigert tid brukes til resultatberegning, korrigert tid = seilt tid × handicap"*

**`live-results`** computes **provisional standings** during the race (requires active **`CourseSelection`**):

```mermaid
flowchart LR
    AIS["AIS positions\nown + fleet"]
    WP["Waypoint route\n+ leg progress"]
    HCAP["handicap-manager\nactive TCF/APH"]
    LR["live-results"]
    STAND["LiveStanding\nranked list"]
    GF["grafana-race\nresults panel"]

    AIS --> LR
    WP --> LR
    HCAP --> LR
    LR --> STAND --> GF
```

**Per boat:**

1. **Elapsed time** — from start signal to now (or projected finish).
2. **Distance progress** — fraction of course completed (waypoint sequence + AIS projection).
3. **Projected finish time** — `elapsed / course_pct` (when &gt; 5% complete).
4. **Corrected time** — `projected_elapsed × handicap_factor` (see §7.14).
5. **Rank** — sort all vessels by corrected time ascending.

**Neo4j `LiveStanding` (refreshed every 30 s):**

```cypher
(:LiveStanding {
  mmsi: "…",
  rank: 3,
  elapsed_s: 14400,
  projected_finish_s: 28800,
  corrected_s: 34790,
  handicap_type: "aph_tot",
  handicap_value: 1.2082,
  course_pct: 0.50,
  vmg_to_mark: 4.2,
  updated_at: datetime()
})
```

**Grafana-race panel:** scratch sheet style table — rank, sail no., name, corrected time, delta to leader, leg, VMG.

---

### 7.14 Handicap numbers & scoring

**Container:** `handicap-manager`  
**Reference certificate:** `C:\Repositories\boat_system\ORC Certificate for Off Course.pdf`  
**Per-race scoring:** [ORC Weather Routing Scoring (WRS) 2026](https://orc.org/sailors/news-archive/orc-weather-routing-scoring-ready-for-2026-after-a-breakthrough-2025-season)

A single boat may carry **multiple handicap numbers** simultaneously. The active factor depends on **regatta scoring rules** and **race type**.

#### 7.14.1 Handicap types per vessel (ORC certificate)

Parsed from ORC certificate PDF (same pipeline as competitor polar extraction):

**Example — OFF COURSE (NOR 15788), CertNo 667232:**

| Type | Key | Value | Use when |
|------|-----|-------|----------|
| **APH ToD** | `aph_tod` | 496.6 s/NM | Time-on-distance, windward/leeward |
| **APH ToT** | `aph_tot` | 1.2082 | Time-on-time (single number) |
| **Cert number** | `cert_no` | 667232 | ORC database reference |
| **ORC Ref** | `orc_ref` | 03440003WLQ | Certificate ID |
| **Distanseseilas Singeltall** | `scoring_aph` | 1.2082 | Færderseilasen distance race (§23) |
| **Distanseseilas Trippeltall svak vind** | `scoring_triple_light` | 0.9544 | Light air |
| **Distanseseilas Trippeltall mellomvind** | `scoring_triple_medium` | 1.2160 | Medium wind |
| **Distanseseilas Trippeltall sterk vind** | `scoring_triple_heavy` | 1.3471 | Heavy wind |
| **Pølsebane Trippeltall** (weak/med/strong) | `scoring_wl_*` | 0.7409 / 0.9823 / 1.1070 | Windward-leeward courses |
| **Motvind Singeltall** | `scoring_upwind` | 1.1113 | Upwind-biased |
| **Medvind Singeltall** | `scoring_downwind` | 1.2015 | Downwind-biased |
| **Windward/Leeward ToD** | `tod_wl` | 615.6 s/NM | Course-specific allowance |
| **All purpose ToD** | `tod_allpurpose` | 496.6 s/NM | General |

**`config/handicaps.yaml` (OFF COURSE example):**

```yaml
vessels:
  - name: "OFF COURSE"
    sail_number: "NOR 15788"
    mmsi: null
    certificate:
      path: "../ORC Certificate for Off Course.pdf"
      cert_no: "667232"
      orc_ref: "03440003WLQ"
      valid_until: "2026-03-31"
    ratings:
      - type: aph_tot
        value: 1.2082
        source: certificate
      - type: aph_tod
        value: 496.6
        unit: sec_per_nm
        source: certificate
      - type: scoring_triple_light
        value: 0.9544
        source: certificate
      - type: scoring_triple_medium
        value: 1.2160
        source: certificate
      - type: scoring_triple_heavy
        value: 1.3471
        source: certificate
      # … additional scoring options from certificate page 2
```

**Neo4j model:**

```cypher
(v:Vessel)-[:HAS_HANDICAP]->(h:HandicapRating {
  type: "aph_tot",
  value: 1.2082,
  source: "certificate",
  valid_from: date("2025-08-11"),
  valid_to: date("2026-03-31"),
  active: false
})
```

Multiple `HandicapRating` nodes per vessel; exactly one marked `active` per race.

#### 7.14.2 Per-race handicap — ORC Weather Routing Scoring (WRS)

For regattas using **[ORC WRS](https://orc.org/sailors/news-archive/orc-weather-routing-scoring-ready-for-2026-after-a-breakthrough-2025-season)**, each boat receives a **custom Time Correction Factor (TCF)** per race — derived from:

- Predicted wind on each **leg** of the **declared course**
- Boat's **ORC polar performance curves**
- **Predicted Elapsed Time (PET)**

| Attribute | WRS behaviour |
|-----------|---------------|
| **Issued** | Few hours before start by ORC |
| **Scope** | Per race, per boat (not on certificate) |
| **Overrides** | Static APH ToT for that race only |
| **Input to system** | Manual upload, email, or `manage2sail` scrape |

**`HandicapRating` for WRS:**

```cypher
(v:Vessel)-[:HAS_HANDICAP]->(h:HandicapRating {
  type: "wrs_tcf",
  value: 1.0342,
  source: "orc_wrs",
  race_id: "faerderseilasen-2026-leg1",
  pet_seconds: 87432,
  issued_at: datetime(),
  active: true
})
```

**`handicap-manager` selection logic:**

```mermaid
flowchart TD
    START["Race session start"]
    WRS{"WRS TCF issued\nfor this race?"}
    RULES["Read SI §23\nscoring method"]
    WIND{"Triple number\nwind band?"}
    WRS_Y["Use wrs_tcf"]
    SINGLE["Use scoring_aph or aph_tot"]
    TRIPLE["Use scoring_triple_* by TWS"]
    START --> WRS
    WRS -->|yes| WRS_Y
    WRS -->|no| RULES --> WIND
    WIND -->|yes| TRIPLE
    WIND -->|no| SINGLE
```

For **Færderseilasen 2026 §23** (Racing classes): `corrected = elapsed × handicap` → use `aph_tot` / `scoring_aph` (1.2082) unless WRS or triple-number specified in SI.

#### 7.14.3 Integration with live results and polars

| Component | Handicap use |
|-----------|--------------|
| `live-results` | Active `HandicapRating` → corrected time ranking |
| `wind-field-analyzer` | Fleet overperformance vs **polar** (not handicap) |
| `polar-manager` | Speed prediction; separate from time correction |
| `tactical-coach` | Explains rank delta using handicap + VMG context |

**Own boat** — **Xbox** (NOR 10133): SLK `7710.slk` matches [ORC Certificate for Xbox.pdf](https://github.com/cognite-fholm/AI-sailing-data) (CertNo 7710). Competitor **OFF COURSE** uses separate ORC cert — both need `HandicapRating` nodes before live results activate.

#### 7.14.4 File layout (dev machine)

```
C:\Repositories\boat_system\
├── AI-sailing-system\          ← code, containers, CI
├── AI-sailing-data\            ← races, boats, planning (GitHub)
├── 7710 (3).slk                ← source polar → copied to data repo assets
├── ORC Certificate for Off Course.pdf
├── Seilingsbestemmelser_*.pdf
└── off_course.png
```

Legacy `AI-sailing-system/config/*.yaml` files are **deprecated** in favor of `AI-sailing-data` — kept as dev shortcuts until `race-import` is implemented.

### 7.15 Race & boat data repository (AI-sailing-data)

**Repository:** [github.com/cognite-fholm/AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)  
**ADR:** [0009](./adr/0009-dual-repository-race-data.md)  
**Schema:** `schema/README.md` in data repo

#### 7.15.1 Purpose — onshore planning

All regatta preparation happens in **git** before leaving harbor:

| Activity | Data repo location |
|----------|-------------------|
| GRIB strategy | `races/.../planning/grib-plan.yaml` |
| Weather insights | `planning/weather-notes.md` |
| Course preference | `planning/course-preference.yaml` |
| Waypoints & routes | `courses/routes/*.yaml` |
| Fleet & handicaps | `fleet.yaml` + `boats/{sail_number}/{year}/ratings.yaml` |
| Human strategy | `wiki/planning.md` |
| Neo4j preload | `neo4j/import-order.yaml` + nodes/relationships |
| LLM bootstrap | `okf/*.md` |

#### 7.15.2 Boat organization

One boat may hold **multiple ORC certificates per year** (Club, DH, NS, International). Each certificate has a **unique ORC Ref** and a **matched SLK** — never share polars across certificate types.

```
boats/NOR-10133/                 # Xbox
  2024/season.yaml
  2024/certificates/
    international-034400038T6/   # SLK from own boat 2024.zip
    dh-international-03440003A8L/
    ns-international-034400038UH/
  2023/certificates/club-03440002JNA/
  2021/certificates/dh-club-03440001K3L/
```

Race planning sets `active_certificate_ref` in `planning/course-preference.yaml`.

Each **year** folder captures rating changes. Competitors the own boat has raced are retained for fleet analysis across seasons.

#### 7.15.3 Race organization

```
races/
  2025/2025-10-hostcup/         # Høstcup — Bane A/B, class flags
  2026/2026-06-faerderseilasen/ # Færderseilasen §11 routes
```

Folder name: `{year}-{month}-{slug}`. Manifest: `race.yaml` (`kind: Race`).

#### 7.15.4 Neo4j YAML import format

Declarative files use `apiVersion: sailing.cognite-fholm/v1`:

```yaml
kind: Neo4jNode
metadata:
  ref: vessel-7710
spec:
  labels: [Vessel]
  merge_keys: [id]
  properties:
    id: own-boat
    sail_number: "7710"
    is_own: true
```

`race-import` resolves `from_ref` / `to_ref` in relationship files and executes idempotent `MERGE`. **Runtime-only** labels (`LiveStanding`, `CourseSelection`, `AisTrack`) are never imported from git.

#### 7.15.5 `race-data-sync` service

**Container:** `race-data-sync` (SLA-2)  
**Config:** `config/data-repo.yaml`

| Setting | Default |
|---------|---------|
| `repo_url` | `https://github.com/cognite-fholm/AI-sailing-data.git` |
| `local_path` | `/opt/ai-sailing-data` |
| `branch` | `main` or race tag |
| `poll_interval_minutes` | 60 when `ONLINE_MODE=true` |
| `auto_pull` | `true` in harbor; `false` when `RACE_MODE=true` (configurable) |

**Flow:**

1. Compare `git rev-parse HEAD` with `git ls-remote origin`.
2. If remote ahead and policy allows → `git pull --ff-only`.
3. Emit event → `race-import` (optional auto) + `okf-loader` refresh + `polar-manager` reload.
4. Log sync result to Neo4j `DataSyncEvent` node.

**LTE:** Uses Teltonika router WAN — no marina Wi-Fi required for data-only updates.

#### 7.15.6 `race-import` service

```bash
race-import apply --race faerderseilasen-2026 [--dry-run]
race-import apply --boat 7710 --year 2026
```

Loads boats referenced in `fleet.yaml`, then race `neo4j/import-order.yaml`. Validates against `schema/README.md` before MERGE.

#### 7.15.7 Dual-repo deployment

| Step | System repo | Data repo |
|------|-------------|-----------|
| Harbor clone | `git clone` → `/opt/ai-sailing-system` | `git clone` → `/opt/ai-sailing-data` |
| Version pin | `deploy/locks/current.env` digests | `git checkout` tag or commit |
| Sync script | `harbor-pull.sh` | `harbor-sync.sh` → `race-data-sync pull` |
| Race freeze | GHCR image lock | `git checkout race-faerder-2026` |

### 7.16 iRegatta reference model & feature traceability

**ADR:** [0010 — iRegatta reference model](./adr/0010-iregatta-reference-model.md)  
**Manual:** [iRegatta User Manual v2.86](https://zifigo.com/sites/default/files/iRegattaUserManual.pdf) (Let's Create / Zifigo)

**iRegatta** is the **functional reference** for crew-facing race UX: start line, laylines, polar steering, waypoint navigation, and wind presentation. The AI Sailing System **extends** iRegatta with AIS fleet, ORC handicap live results, GRIB wind zones, SI PDF course import, and Neo4j/LLM coaching — but **must not regress** the tactical features sailors expect from iRegatta.

#### 7.16.1 View mapping — iRegatta → our surfaces

| iRegatta view | Primary surface | Container / service |
|---------------|-----------------|---------------------|
| Race | `grafana-race` — Race dashboard | `grafana-race`, `polar-manager`, `race-intelligence` |
| Layline | `grafana-race` map overlay | `race-intelligence`, `polar-manager` |
| Start | `course-editor` Start panel + Grafana Start row | `race-intelligence`, `course-editor` |
| Wind | `course-editor` Wind panel (manual override) | Signal K + `race-intelligence` |
| Wind history | Grafana wind panel | InfluxDB (SLA-1 wind paths) |
| Navigation | `course-editor` Navigation tab | `live-results`, Neo4j `Waypoint` |
| Waypoints / routes | `course-editor` + `AI-sailing-data` YAML | `course-parser`, `race-import` |
| Statistics | Grafana + optional map tile | InfluxDB, `grafana-race` |
| Polar | `polar-manager` API + Grafana polar panel | `polar-manager` (SLK primary) |
| NMEA / wind instrument | Grafana instrument row | Signal K (SLA-1) |
| Settings | Grafana preferences + `deploy/env/race.env` | Compose env, user prefs store |

On **iPhone**, iRegatta uses horizontal swipe between views. On the boat we use **Grafana dashboards** (read-mostly, big screen) plus **`course-editor`** at `race.local:3010` for setup actions (line ends, waypoints, course flags, manual wind).

#### 7.16.2 Race view parity

| iRegatta feature | Implementation |
|------------------|----------------|
| Four configurable readouts | Grafana stat panels; datasource Signal K + `race-intelligence` |
| BIG-mode (focus 1–2 readouts) | Dashboard row collapse / TV mode profile |
| GPS freshness dot + accuracy | Panel from `navigation.position` timestamp + `navigation.gnss.type` / accuracy meta |
| COG/SOG damping 0/3/5/10 s | `race-intelligence` rolling window before display |
| Lift indicator | `lift_deg = heading_now − avg_heading_10s`; threshold from config |
| Speed / VMG history bars | Grafana bar gauge or custom panel; timeframe 2/4/10/20 min |
| Performance bar | `performance_pct = SOG / polar_target_bsp × 100` at current TWS/TWA |
| Steering bars (VMG optimum) | Compare COG to polar optimum upwind/downwind angles; arrow hints |

**Configurable readout catalog** (minimum): SOG, COG, STW, HDG (mag/true), AWA, AWS, TWD, TWS, VMG-to-mark, VMG-to-wind, DTM, BTM, performance %.

#### 7.16.3 Lift, damping, and steering calculations

Formulas match iRegatta manual §Calculations:

```
damped_cog = mean(COG over last N seconds)     # N ∈ {0,3,5,10}
lift_deg   = COG_now − mean(COG over 10 s)
performance_pct = SOG / polar_bsp(TWS, TWA) × 100

# Steering: when polar "tack/jibe from polar" enabled
twa_opt_up   = argmax VMG_upwind(polar, TWS)
twa_opt_down = argmax VMG_downwind(polar, TWS)
steer_hint   = signed_delta(COG, recommended_cog_for_optimum_VMG)
```

When **NMEA wind** is available (Signal K `environment.wind`), manual wind entry is disabled — same rule as iRegatta Wind view.

#### 7.16.4 Layline view parity

Requires active **navigation target** (`CourseSelection` + current `Waypoint`):

1. Determine **upwind vs downwind** from TWD vs bearing to mark.
2. Fetch optimum tack/jibe angles from `polar-manager` (`GET /polars/{id}/target?tws=&twa=`) or manual angles from Wind panel.
3. Render laylines on `grafana-race` map: red tack/jibe lines, grey bearing line, grey heading arrow.

On distance races (Færderseilasen §11), laylines apply per **leg** after `live-results` advances leg index.

#### 7.16.5 Start view parity

**Container:** `race-intelligence` + `course-editor` Start panel

| iRegatta feature | Behavior |
|------------------|----------|
| Countdown | `Start` / `Pause` / `Sync` — sync rounds to nearest minute |
| Paused + Sync | Reset to pre-sync value (not round) |
| Timer beep | Optional audio on vision/helm tablet — configurable milestones |
| Gun at 0:00 | Emit `race_started` event; switch Grafana to Race dashboard |
| Line ends | Mark **Pin** and **Boat** by position capture or select preloaded waypoints from `AI-sailing-data` |
| Favored end | Green/red ends from wind angle to line normal (assumes upwind first leg) |
| Wind arrow | Exaggerated TWD relative to line for quick visual bias |
| Distance to line (DTL) | Perpendicular from bow (with offset) to line **and extensions** |
| Time to line (TTL) | `DTL / (SOG × cos(angle(COG, line_normal)))` — `X:XX` if diverging |
| Over early | TTL &lt; countdown → red styling |
| Burn or gain bar | Early: red from top proportional to `(countdown − TTL) / countdown`; late: green from bottom; on target: yellow |

```yaml
# config/start-line.yaml (reference)
bow_offset_m: 4.5          # GPS antenna → bow, or phone → bow if no NMEA GPS
countdown_initial_s: 300
sync_rounds_to_minute: true
timer_beep: true
beep_at: [60, 30, 10, 5, 4, 3, 2, 1]
assumes_upwind_first_leg: true
```

**Note:** Høstcup-style **course flags** (ADR-0006) layer on top — favored end uses selected route’s first leg bearing when known.

#### 7.16.6 Wind view and wind history

| Mode | Source |
|------|--------|
| **NMEA / Signal K** | `environment.wind.angleApparent`, `speedApparent`, derived true wind |
| **Manual** | `course-editor` Wind panel: type direction, compass shoot, or two-tack bisection |
| **Tack/jibe angles** | From polar (`polar.use_tack_jibe_from_polar: true`) or manual |

**True wind derivation** (when only apparent available — iRegatta NMEA rules):

1. Prefer compass heading + STW from instruments.
2. Else use COG + SOG from GPS.

**Wind history:** Influx continuous query — 30 min window, 30 s `mean()` samples of TWD/TWS → Grafana time series (iRegatta Wind History graph).

#### 7.16.7 Navigation, waypoints, and routes

| iRegatta feature | Our implementation |
|------------------|-------------------|
| Start / pause nav | `CourseSelection.nav_active` in Neo4j; API `POST /navigation/start` |
| Bearing + distance to WP | `live-results` leg metrics (§7.13.5) |
| Route prev/next | `course-editor` or REST `POST /navigation/route/{id}/step` |
| Auto-advance | When `distance_to_wp < auto_advance_m` (default from env) |
| Next leg preview | Bearing, leg length, estimated TWA from GRIB or last TWD |
| Add waypoint | Editor or commit to `AI-sailing-data` `courses/routes/*.yaml` |
| Temp WP — bearing & distance | Editor dialog from current AIS/GPS position |
| Temp WP — cross-bearing | Editor: two positions + bearings; flag low confidence |
| Delete / delete all | Editor with confirm; git commit for persistent routes |

**VMG basis:** When navigating, VMG uses **bearing to mark** (iRegatta rule). When not navigating, VMG uses **wind direction** — `race-intelligence` publishes both.

#### 7.16.8 GPX interchange

| Direction | Path |
|-----------|------|
| Export | `course-editor` → `waypointExport.gpx` (USB or download) |
| Import | Append waypoints/routes to Neo4j + optional merge into data repo (no silent overwrite) |

GPX supplements — does not replace — structured YAML in `AI-sailing-data` (rounding rules, class flags).

#### 7.16.9 Polar formats and trim

| Format | Role |
|--------|------|
| **SLK** (ORC måletall) | **Primary** own-boat polar — `polar-manager` |
| **CSV 20×360** (iRegatta export) | Interop import/export via `polar-manager` `csv_polar` adapter |
| **ORC certificate image** | Competitor derived polar — `polar-certificate-extractor` |

**iRegatta Trim pipeline** (for sparse CSV or derived polars):

1. Mirror port/starboard (take max of paired angles).
2. Interpolate missing TWA columns.
3. Smooth over 10° spans.
4. Interpolate across TWS rows.
5. Smooth over 4 kt TWS spans.

**Onboard polar recording** (iRegatta Statistics → record) is **not** v1 — polars come from ORC SLK and shore preparation ([AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) certificate folders).

#### 7.16.10 NMEA and instrument presentation

iRegatta consumes **NMEA 0183 over Wi‑Fi** (TCP/UDP). This system uses **Signal K on SLA-1** as the single decoder:

| iRegatta | AI Sailing System |
|----------|-------------------|
| NMEA Wi‑Fi to phone | NMEA 0183 + N2K → PiCAN-M → Signal K |
| Ignore checksum option | Signal K plugin `strictChecksum: false` per talker |
| Magnetic vs true HDG | `environment.wind` / `navigation.headingMagnetic` paths |
| Wind instrument view | Grafana dual gauge: true vs apparent |
| Send RMB target (beta) | Optional Signal K → NMEA 0183 outbound plugin when `nav_active` |

**Compatibility:** A phone running **iRegatta** may connect to the same Wi‑Fi NMEA bridge as the Pi — both can coexist during transition.

#### 7.16.11 Global UI settings mapping

| iRegatta setting | Our config |
|------------------|------------|
| White/black theme | Grafana theme + `course-editor` CSS |
| Speed/distance units | Grafana unit prefs; Signal K meta |
| Screen lock | Kiosk mode / Grafana playlist lock (helm tablet) |
| Auto-lock idle | Browser/Grafana idle timeout |
| Waypoint format DMS vs DDM | `course-editor` display pref |
| Graph timeframe | Grafana dashboard variable `$graph_window` |
| Show performance bar | `RACE_SHOW_PERFORMANCE_BAR` |
| Show steering bars | `RACE_SHOW_STEERING_BARS` |
| Lift threshold | `RACE_LIFT_THRESHOLD_DEG` |
| COG/SOG damping | `RACE_DAMPING_SECONDS` |

#### 7.16.12 Beyond iRegatta (explicit scope expansion)

| Capability | Why outside iRegatta |
|------------|---------------------|
| AIS fleet tracks | Requires N2K AIS + `ais-collector` |
| Live ORC corrected standings | `handicap-manager` + `live-results` |
| GRIB wind zones | `wind-field-analyzer` |
| SI PDF §11 parse | `course-parser` |
| Start-boat course flags | ADR-0006 |
| Multi-certificate ORC | `AI-sailing-data` per-cert SLK |
| LLM tactical coach | SLA-2 `tactical-coach` |
| GoPro trim vision | SLA-3 |

Full traceability table: [ADR-0010](./adr/0010-iregatta-reference-model.md).

### 7.17 B&G H5000 reference model & integration

**ADR:** [0011 — B&G H5000 reference model](./adr/0011-bg-h5000-reference-model.md)  
**Manual:** [H5000 Operation Manual 988-10630-003](https://cxjdfr.files.cmp.optimizely.com/download/assets/en-us-H5000_OM_EN_988-10630-003_w.pdf/f9fdbcee044d11f0a251baecc01b2173)

The **B&G H5000** is the **primary instrument and race-display reference** for own-boat sailing (Xbox, NOR-10133). H5000 CPU + Graphic/Race displays remain the helm UI; the Pi stack **ingests**, **records**, **extends** (fleet, handicaps, GRIB, coaching), and **mirrors** key pages on `grafana-race`.

#### 7.17.1 Architecture — coexistence with H5000

```mermaid
flowchart LR
  subgraph h5000["B&G H5000 network"]
    CPU["H5000 CPU\nHydra/Hercules/Performance"]
    GD["Graphic / Race Display"]
    SENS["Wind, BSP, heel, GPS, 3D motion"]
    PILOT["Pilot Computer"]
  end

  subgraph sla1["SLA-1 telemetry Pi"]
    PICAN["PiCAN-M N2K"]
    SK["Signal K Server"]
  end

  subgraph sla2["SLA-2 race Pi"]
    RI["race-intelligence"]
    PM["polar-manager"]
    GF["grafana-race"]
    CE["course-editor"]
  end

  SENS --> CPU
  CPU -->|NMEA 2000| PICAN
  PICAN --> SK
  SK -->|WebSocket| RI
  SK --> PM
  RI --> GF
  CE --> RI
  GD -.->|helm primary| CREW["Crew"]
  GF -.->|tactical big screen| CREW
```

**Rules:**

1. **Do not recompute true wind** if H5000 already publishes corrected TWD/TWS on N2K — prefer talker data; fallback to SK derivation only when missing.
2. **Bow offset** and **start-line geometry** follow H5000 semantics (perpendicular DTL, bias in degrees and **boat lengths**).
3. **Autopilot:** ingest mode/rudder/setpoint; **no rudder commands** from Pi in v1.
4. **Polar:** ORC **SLK** in `AI-sailing-data` is canonical; export H5000-compatible CSV for MFD import when needed.

#### 7.17.2 Display page mapping (Graphic Display → Grafana)

| H5000 page | Grafana dashboard / panel | Key metrics |
|------------|---------------------------|-------------|
| **SailSteer** | `race-sailsteer` | HDG/Course, BSP, tide set/rate, WP name, TWD, laylines, TWA, TWS |
| **Speed/Depth** | `race-speed-depth` | BSP, depth, acceleration bargraph |
| **WindPlot** | `race-windplot` | TWD/TWS + histogram (1–60 min) |
| **Start line** | `race-start` + `course-editor` Start | DIST P/S, DTL⊥, BIAS°, BIAS ADV (lengths), timer, wind barb |
| **Highway** | `race-highway` | BRG, COG, XTE, DTM, ETA, off-course limit |
| **Tide** | `race-tide` | BSP, tide angle/rate vs hull, wind |
| **Depth history** | `race-depth` | Depth trend histogram |
| **Autopilot** | `race-pilot` (read-only) | Mode, set HDG/wind, rudder °, perf level |

Race Display **dual-value + bargraph** layout → Grafana row `race-display-compact` (TV mode).

#### 7.17.3 SailSteer, laylines, and tidal correction

Configured via race `planning/layline-preferences.yaml` (`kind: LaylinePreferences`):

| Setting | H5000 option | Our default |
|---------|--------------|-------------|
| `target_wind_angle_source` | Polar / Actual / Manual | `polar` (from active `PolarSource`) |
| `tidal_flow_correction` | On/off layline offset | `true` when tide data available |
| `layline_limit_minutes` | 5, 10, 15, 30 | `10` |

`race-intelligence` computes laylines using:

- Active waypoint from `CourseSelection`
- TWA targets from `polar-manager` or manual angles
- Tidal set/rate from instruments or harbor model → layline rotation

#### 7.17.4 Start line (H5000 StartLine + BowPosition)

**Containers:** `race-intelligence`, `course-editor`

| H5000 field | Description | Neo4j / runtime |
|-------------|-------------|-----------------|
| DIST P / DIST S | Distance to port/starboard end | `StartLineState.dist_port_m`, `dist_starboard_m` |
| DIST LINE | Perpendicular distance to line + extensions | `dist_line_m` (bow-adjusted) |
| BIAS | Angle wind ⊥ line | `bias_deg` |
| BIAS ADV | Advantage at favored end in **boat lengths** | `bias_boat_lengths` |
| Line ends | Ping at bow on line; stale at midnight | `StartLineEnd` nodes with `pinged_at`, `stale_after` |
| Timer | Race countdown | `RaceTimer` |

```yaml
# races/.../planning/start-line.yaml — kind: StartLinePreferences
spec:
  bow_offset_m: 4.5
  sync_countdown_to_minute: true
  show_bias_boat_lengths: true
  line_ends_stale_at_midnight: true
  assumes_upwind_first_leg: true
```

Aligns with iRegatta start metrics ([§7.16.5](#7165-start-view-parity)); H5000 adds **bias in boat lengths** and **tide direction** on start page.

#### 7.17.5 Instrument profile & calibration (boat YAML)

**Path:** `boats/{sail_number}/instrumentation/`

| File | Kind | Content |
|------|------|---------|
| `profile.yaml` | `InstrumentProfile` | `cpu_tier`, `bow_offset_m`, `damping`, `measured_sources`, `motion_correction` |
| `calibration.yaml` | `InstrumentCalibration` | Depth offset, BSP factor, MHU align, heel correction table |
| `alarms.yaml` | `AlarmProfile` | Depth, BSP, wind thresholds |

Example profile — see `AI-sailing-data/boats/NOR-10133/instrumentation/profile.yaml`.

**Dual sensors (Hercules+):** `measured_sources.boat_speed.switch_policy`: `mwa` \| `heel` \| `mwa_heel` \| `port` \| `starboard` — documented in profile; switching executed on H5000 CPU; Pi logs active source from N2K if exposed.

**3D motion wind correction:** requires `motion_correction.enabled`, `mast_height_m`, Hercules+ tier — reference only in v1; validate TWD against H5000 display in harbor.

#### 7.17.6 Polars, VMG targets, and H5000 export

| Format | Direction | Service |
|--------|-----------|---------|
| **SLK** (ORC) | Shore → Pi | `polar-manager` primary |
| **H5000 polar CSV** | Pi ↔ MFD | `polar-manager` `h5000_csv` adapter (20 TWS × 360 TWA) |
| **VMG targets** | Shore YAML → display | `PolarSource.spec.vmg_targets` |

Certificate `polar.yaml` may include:

```yaml
spec:
  h5000_export:
    enabled: true
    last_export_path: assets/h5000-polar.csv
  vmg_targets:
    upwind_source: polar
    downwind_source: polar
```

#### 7.17.7 Damping and dynamic boat speed

H5000 applies per-variable damping (0–9 s). Map to `InstrumentProfile.spec.damping`:

```yaml
damping:
  boat_speed_s: 3
  cog_s: 3
  heading_s: 2
  wind_speed_s: 3
  dynamic_boat_speed: 5   # Hercules+ only; 0 = off
```

`race-intelligence` and Grafana apply damping before display — same role as iRegatta COG/SOG damping ([§7.16.3](#7163-lift-damping-and-steering-calculations)).

#### 7.17.8 Alarms

Mirror safety-critical H5000 alarms on Grafana alert rules driven from Signal K:

| Alarm | Typical source |
|-------|----------------|
| Depth low | `environment.depth.belowTransducer` |
| BSP high/low | `navigation.speedThroughWater` |
| Wind high | `environment.wind.speedTrue` |
| AIS proximity | SLA-2 `ais-collector` |

Acknowledge flow documented for helm tablet; full network alarm groups deferred to v2.

**Tactical insight alerts** (fleet rank, course, trim, wind tactics) are a **separate system** — see [§7.21](#721-tactical-insight-alerts--annunciation). Do not route performance alerts through H5000 safety alarm groups.

#### 7.17.9 Autopilot integration (read-only v1)

Ingest via N2K / Signal K:

| Field | Use |
|-------|-----|
| Pilot mode | Auto / Wind / Nav / Standby |
| Set heading / wind angle | Coach context |
| Rudder angle | Maneuver detection |
| Performance level | Display on `race-pilot` panel |

**No** `SET_RUDDER` or pilot engage commands from Pi services.

#### 7.17.10 Signal K variable map

H5000 operating variables map to Signal K paths in  
[`AI-sailing-data/schema/h5000-variable-map.yaml`](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/h5000-variable-map.yaml).

Key variables: **BSP**, **COG**, **SOG**, **HDG**, **Course** (HDG+leeway), **TWA/TWD/TWS**, **VMG**, **XTE**, **heel**, **trim**, **leeway**, **rudder**, **setpoint**.

#### 7.17.11 Beyond H5000

| Capability | Component |
|------------|-----------|
| Live ORC fleet standings | `live-results` + `handicap-manager` |
| AIS wind-pressure map | `wind-field-analyzer` |
| SI course import | `course-parser` |
| Start-boat course flags | ADR-0006 |
| LLM coach | `tactical-coach` |
| GoPro trim | SLA-3 |

Full traceability: [ADR-0011](./adr/0011-bg-h5000-reference-model.md).

### 7.18 Race-side MCP & laptop Cursor

**ADR:** [0012 — Race-side MCP](./adr/0012-race-side-mcp-laptop-cursor.md)

At the regatta the user may bring a **laptop** with **Cursor**, join the **boat LAN** (Teltonika Wi‑Fi or Ethernet), and run the same agent-assisted analysis used on shore — but against **live** race state.

#### 7.18.1 Purpose

| Shore (GitHub) | At race (boat LAN + MCP) |
|----------------|--------------------------|
| Prepare `AI-sailing-data` in Cursor | Query **live** standings, legs, AIS |
| Static YAML + wiki | **Influx** history — VMG, wind, polars |
| Neo4j import templates | **Neo4j** runtime graph — ad hoc Cypher |
| OKF concepts | **wind-field-analyzer** recommendations |
| — | **Signal K** snapshots — current instruments |

MCP bridges Cursor’s tool protocol to onboard services without exposing raw database admin ports to the laptop.

#### 7.18.2 Service: `race-mcp-gateway`

**Container:** `race-mcp-gateway` (SLA-2)  
**Endpoint:** `http://race.local:3100` (MCP over HTTP/SSE)  
**Language:** Python 3.11+ with official MCP SDK

```mermaid
flowchart LR
  subgraph laptop [Navigator laptop]
    CUR[Cursor]
    MCPc[MCP client]
    CUR --> MCPc
  end

  subgraph sla2 [race.local SLA-2]
    GW[race-mcp-gateway :3100]
    LR[live-results]
    PM[polar-manager]
    WF[wind-field-analyzer]
    GW --> LR
    GW --> PM
    GW --> WF
  end

  subgraph backends [Read-only backends]
    NEO[Neo4j]
    IFX[InfluxDB]
    SK[Signal K]
    DATA[AI-sailing-data mount]
  end

  MCPc -->|Wi‑Fi boat LAN| GW
  GW --> NEO
  GW --> IFX
  GW --> SK
  GW --> DATA
```

#### 7.18.3 MCP server endpoints

Configured in `config/mcp-gateway.yaml`. Implementation: `race-mcp-gateway/`.

| Endpoint | Server id | Tools | Backend |
|----------|-----------|-------|---------|
| `/mcp/neo4j` | `race-neo4j` | `cypher_query`, `get_live_standings`, `get_course_selection`, `get_fleet_positions`, `get_graph_schema` | Neo4j read role |
| `/mcp/influx` | `race-influx` | `flux_query`, `get_latest_instruments`, `get_wind_history`, `list_buckets` | Influx read token (SLA-1) |
| `/mcp` | `race-boat` | All Neo4j + Influx tools above | Combined |
| *(planned)* | `race-context` | `read_yaml`, `read_wiki`, `search_okf`, `get_fleet_yaml` | `/opt/ai-sailing-data` |
| *(planned)* | `race-tactical` | `get_wind_zones`, `get_polar_target`, `get_start_line_state` | SLA-2 REST |
| *(planned)* | `signalk-snapshot` | `get_wind_now`, `get_navigation` | Signal K HTTP |

Detail: [docs/mcp-neo4j-influx.md](./docs/mcp-neo4j-influx.md)

**v1:** all tools **read-only**.  
**v2 (optional):** `append_race_note` → `wiki/race-day.md` with explicit enable flag.

#### 7.18.4 Laptop setup workflow

1. **Before race:** Clone `AI-sailing-data` on laptop; note active regatta path from `index.yaml`.
2. **On boat:** Join boat Wi‑Fi; verify `ping race.local`.
3. **Cursor MCP config** (user or project `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "race-boat": {
      "url": "http://race.local:3100/mcp",
      "headers": {
        "Authorization": "Bearer ${RACE_MCP_API_KEY}"
      }
    },
    "race-neo4j": {
      "url": "http://race.local:3100/mcp/neo4j",
      "headers": {
        "Authorization": "Bearer ${RACE_MCP_API_KEY}"
      }
    },
    "race-influx": {
      "url": "http://race.local:3100/mcp/influx",
      "headers": {
        "Authorization": "Bearer ${RACE_MCP_API_KEY}"
      }
    }
  }
}
```

4. Open `AI-sailing-data` workspace in Cursor; set `spec.active.regatta_id` context in prompts.
5. Example prompts:
   - *“Use race MCP: live standings for Doublehanded and corrected-time delta to leader.”*
   - *“Flux query: our VMG and TWA for the last 20 minutes on this beat.”*
   - *“Cypher: competitors within 0.5 nm on port side of the course.”*

See [docs/race-laptop-mcp.md](./docs/race-laptop-mcp.md).

#### 7.18.5 Security

| Control | Setting |
|---------|---------|
| Network scope | Boat LAN only — **no** LTE port forwarding |
| Authentication | `RACE_MCP_API_KEY` in `deploy/env/race.env` |
| Neo4j | Dedicated `mcp_analyst` user — read-only |
| Influx | Read token scoped to race bucket |
| Rate limits | `max_cypher_per_minute`, `max_flux_range_hours` in config |
| RACE_MODE | Gateway **stays on** — analysis does not mutate race state |
| Forbidden | Autopilot, Signal K write, `docker`, `git push` from MCP |

#### 7.18.6 Relationship to onboard LLM coach

| | `tactical-coach` (Pi LLM) | MCP + Cursor (laptop) |
|--|---------------------------|------------------------|
| Hardware | Raspberry Pi CPU | User laptop GPU/CPU |
| UI | Grafana / API | Cursor chat |
| Best for | Quick helm questions | Deep ad hoc analysis, multi-step queries |
| Offline | Yes | Yes (boat LAN only) |

Both consume OKF + live data; MCP does not replace `tactical-coach`.

#### 7.18.7 Config reference

```yaml
# config/mcp-gateway.yaml (reference)
apiVersion: sailing.cognite-fholm/v1
kind: McpGatewayConfig
spec:
  listen_port: 3100
  bind: boat_lan_only
  enabled_servers:
    - race-graph
    - race-telemetry
    - race-context
    - race-tactical
    - signalk-snapshot
  limits:
    max_cypher_per_minute: 30
    max_flux_range_hours: 48
  data_repo_path: /opt/ai-sailing-data
  signalk_url: http://telemetry.local:3000
  influx_url: http://telemetry.local:8086
  neo4j_uri: bolt://localhost:7687
```

### 7.19 ORC certificate collection & fleet enrichment

**ADR:** [0013 — ORC certificate fleet collection](./adr/0013-orc-certificate-fleet-collection.md)  
**Skill:** [AI-sailing-data `.cursor/skills/orc-sailor-services`](https://github.com/cognite-fholm/AI-sailing-data/tree/main/.cursor/skills/orc-sailor-services)  
**HAR reference:** `data.orc.org.har` — `ListCert` POST; `orc.org.har` — marketing site only

Shore agents collect ORC certificate **metadata and PDFs** for all entrants in the relevant class after `fleet.yaml` exists from Manage2Sail or SailRace System.

#### 7.19.1 Portal API (`data.orc.org/public/WPub.dll`)

| Action | Method | Auth | Output |
|--------|--------|------|--------|
| `activecerts` | GET `?CountryId={cc}&Family={n}` | None | XML — all active certs in family |
| `ListCert` | POST `SailNo`, `CountryId`, … | None | HTML — per-boat cert history |
| `CC/{dxtID}` | GET | Session cookie | PDF certificate copy |

**Family** filter for bulk fetch:

| `Family` | Use |
|----------|-----|
| `1` | ORC Standard / Club |
| `3` | Double Handed (DH Club, DH International) |
| `5` | Non Spinnaker |

Typical Norwegian Doublehanded regatta: **one** `activecerts` call matches full starter list; validate `orc_ref` from registration against live ORC.

#### 7.19.2 Shore pipeline (three scripts)

```mermaid
flowchart LR
  FLEET[fleet.yaml]
  META[fetch_fleet_certs.py]
  IDX[collected/orc/fleet-orc-index.yaml]
  PDF[download_cert_pdfs.py]
  MAT[materialize_boat_certs.py]
  BOATS[boats/sail/year/certificates/]

  FLEET --> META --> IDX
  IDX --> PDF
  IDX --> MAT
  PDF --> MAT --> BOATS
```

| Step | Script | Lands in |
|------|--------|----------|
| 1. Metadata | `fetch_fleet_certs.py` | `collected/orc/{race}/`, ref validation |
| 2. PDFs | `download_cert_pdfs.py` + cookie | `collected/orc/{race}/pdfs/` |
| 3. Stubs | `materialize_boat_certs.py` | `boats/{sail}/{year}/certificates/{type}-{orc_ref}/` |

**Provenance:** `schema/collected-sources.yaml` → `orc_sailor_services`.

#### 7.19.3 PDF authentication

`WPub.dll/CC/{id}` returns HTML without Sailor Services login. Shore workflow:

1. User logs in via browser once.
2. Export `Cookie` header to gitignored `_import/orc-cookie.txt` or `ORC_SESSION_COOKIE` env.
3. `download_cert_pdfs.py` validates `%PDF` magic bytes.

**Alternatives:** ORC måletall zip (own boat SLK), [crawl_web](https://github.com/cognite-fholm/crawl_web) bulk fetch, manual download.

#### 7.19.4 Downstream consumers (onboard)

| Service | Uses certificate assets |
|---------|-------------------------|
| `handicap-manager` | Ratings from PDF / `ratings.yaml` |
| `polar-certificate-extractor` | Competitor polars from `assets/orc-certificate.pdf` |
| `polar-manager` | Own-boat SLK from måletall |
| `race-import` | `OrcCertificate` nodes from `certificate.yaml` |
| `live-results` | Active handicap per `planning/course-preference.yaml` |

No new SLA-2 container in v1 — collection is **shore-only** via Cursor skill. Optional future: `orc-cert-sync` in harbor (Phase 2+).

#### 7.19.5 Integration with registration portals

| Source | Provides | ORC skill adds |
|--------|----------|----------------|
| Manage2Sail `regattaentry` | `orc_ref`, `Hcp`, `OrcCertificateType` | Live validation, expiry, `dxt_id`, PDF |
| SailRace System starters | Sail, name, sometimes ref | Fill missing refs via `activecerts` |

**Ref mismatch** example: registration `03440004IHD` vs live ORC `03440004TID` — index flags before race day.

---

### 7.20 Shore weather & current collection

**ADR:** [0014 — Shore weather and current collection](./adr/0014-shore-weather-current-collection.md)  
**Data repo:** [AI-sailing-data weather skills](https://github.com/cognite-fholm/AI-sailing-data/tree/main/.cursor/skills)

Oslofjord and Skagerrak regattas need **fjord-resolution** wind, wave, and tidal-current data linked to each race folder — not only coarse global models.

#### 7.20.1 Sources

| Source | API / URL | Content | Skill |
|--------|-----------|---------|-------|
| MET Norway GRIB | `api.met.no/weatherapi/gribfiles/1.1/?area=oslofjord&content={weather\|current\|waves}` | Wind, current (u/v −3 m), waves | `metno-oslofjord-weather` |
| Oslofjord varsler | [projects.met.no/~nilsmk/oslofjord](https://projects.met.no/~nilsmk/oslofjord/) | Human portal → same GRIB + current PNGs | — |
| YR GRIB help | [hjelp.yr.no GRIB article](https://hjelp.yr.no/hc/en-us/articles/360009342993-GRIB-weather-data) | Documentation for OpenCPN / local models | — |
| Oslofjord current plots | `api.met.no/weatherapi/oslofjord/0.1/?area={ferder1..4\|drammen1}&hour={0..48}` | PNG forecast maps (arrows + color bar) | `oslofjord-current-plots` |
| SMHI MetObs | `opendata-download-metobs.smhi.se/.../parameter/{3\|4\|24}/station/{id}/period/latest-hour/data.json` | Observed wind speed, gust, direction | `smhi-wind-observations` |

**Default SMHI validation station:** Väderöarna **81350** — Skagerrak boundary wind for Færder approach ([table view](https://www.smhi.se/vader/observationer/observationer/station/81350/vind/tabell)).

#### 7.20.2 Shore pipeline

```mermaid
flowchart LR
  PLAN[planning/grib-plan.yaml]
  GRIB[metno-oslofjord-weather]
  PNG[oslofjord-current-plots]
  SMHI[smhi-wind-observations]
  MAN[collected/weather/manifest.yaml]
  NOTES[planning/weather-notes.md]
  BOAT["/data/grib/ on SLA-2"]

  PLAN --> GRIB --> MAN
  PLAN --> PNG --> MAN
  PLAN --> SMHI --> MAN
  MAN --> NOTES
  GRIB --> BOAT
```

| Script | Output |
|--------|--------|
| `fetch_grib.py` | `collected/weather/grib/*.grb` + `WeatherCollection` manifest |
| `fetch_current_plots.py` | `collected/weather/current-plots/*.png` + area index |
| `fetch_smhi_wind.py` | `collected/weather/smhi-{station}.json` |

GRIB binaries are **gitignored**; manifests and `grib-plan.yaml` are committed per race.

#### 7.20.3 Current plot interpretation (agent skill)

The `oslofjord-current-plots` skill includes a **reference guide** for reading PNG maps:

- **Areas:** `ferder1`–`ferder4` (Færder approach tiers), `drammen1` (inner fjord)
- **Color bar:** m/s current speed; arrows show direction **toward** which water moves
- **Hour parameter:** forecast lead time from model run — align with race start in `Europe/Oslo`
- **Cross-check:** compare qualitative PNG with GRIB `current_oslofjord.grb` u/v at same valid time

No automated CV in v1 — agents and humans interpret images using `reference.md`, then record conclusions in `weather-notes.md`.

#### 7.20.4 Downstream consumers (onboard)

| Service | Uses weather assets |
|---------|---------------------|
| `grib-ingest` / `grib-parser` | GRIB files copied to `/data/grib/` at harbor |
| `wind-field-analyzer` | GRIB + AIS + polar fusion |
| `race-intelligence` | Start-line current bias hints from planning notes |
| `tactical-coach` | OKF + `weather-notes.md` for advisory context |

Collection is **shore-only** via Cursor skills (same pattern as ORC §7.19).

#### 7.20.5 Race linkage

Each Oslofjord race should have:

```
races/{year}/{race}/
  planning/grib-plan.yaml      # models, schedule, MET area, SMHI stations
  planning/weather-notes.md    # interpretation after collection
  collected/weather/
    manifest.yaml              # kind: WeatherCollection (merged entries)
    grib/                      # gitignored *.grb
    current-plots/
    smhi-81350.json
```

`GribPlan.spec.sources` references collector skills and validation stations; `WeatherCollection` records provenance for harbor sync.

---

### 7.21 Tactical insight alerts & annunciation

**ADR:** [0015 — Tactical insight alerts and voice annunciation](./adr/0015-tactical-insight-alerts-annunciation.md)

Analysis services produce insights continuously; the helm needs **proactive notification** when something actionable happens — not only passive Grafana panels or on-demand coach queries.

#### 7.21.1 Scope vs safety alarms

| | Safety alarms ([§7.17.8](#7178-alarms)) | Tactical insight alerts (this section) |
|---|----------------------------------------|----------------------------------------|
| Purpose | Boat/instrument limits, collision risk | Performance, tactics, fleet position |
| Source | Signal K / H5000 thresholds | SLA-2/3 analysis services |
| Severity | info / warning / **critical** | info / warning / **urgent** |
| Voice | H5000 alarm module (if fitted) | Optional Piper TTS on Pi speaker |
| Config | `AlarmProfile` (`alarms.yaml`) | `InsightAlertProfile` (`tactical-alerts.yaml`) |

#### 7.21.2 Alert broker — `insight-alerts`

Central **SLA-2** service (`:8095`) that:

1. Receives **`InsightEvent`** JSON from producers
2. Evaluates rules from active `InsightAlertProfile`
3. Deduplicates (same `rule_id` + context within cooldown)
4. Routes to enabled **channels**
5. Persists to Neo4j (`InsightAlert`) and Influx annotations

```mermaid
flowchart LR
  P[Producers] -->|POST /events| IA[insight-alerts]
  IA --> UI[Grafana + course-editor]
  IA --> TTS[Piper → speaker]
  IA --> NEO[Neo4j history]
```

#### 7.21.3 Producers and example triggers

| Producer | Category | Example trigger |
|----------|----------|-----------------|
| `live-results` | `fleet_position` | Corrected rank drops ≥ N places in T minutes |
| `live-results` | `fleet_position` | Delta to leader widens beyond threshold on leg |
| `race-intelligence` | `course` | XTE &gt; limit for &gt; 30 s while navigating |
| `race-intelligence` | `course` | Favored tack / layline side changed |
| `race-intelligence` | `start_line` | TTL &lt; burn window; bias end shift |
| `wind-field-analyzer` | `wind_tactics` | Persistent header on unfavored side (GRIB + AIS) |
| `sail-analysis-api` | `sail_trim` | Trim score below polar target for &gt; 2 min |
| `tactical-coach` | `coach` | High-confidence LLM insight (structured payload) |

Producers emit events; **thresholds live in YAML**, not hard-coded per service.

#### 7.21.4 `InsightEvent` payload (v1)

```yaml
event_id: "uuid"
timestamp: "2026-07-05T10:15:00Z"
race_id: faerderseilasen-2026
category: fleet_position
rule_id: rank_drop_15min
severity: warning
title: "Fleet position"
message: "Dropped 3 places in 15 minutes — VMG 0.4 kt below polar"
message_short: "Three places lost — check VMG"
data:
  rank_before: 5
  rank_after: 8
  vmg_delta_kt: -0.4
source_service: live-results
ttl_s: 600
```

`message_short` is used for TTS (≤ 12 words).

#### 7.21.5 Configuration — `InsightAlertProfile`

Per race: `races/{year}/{race}/planning/tactical-alerts.yaml`  
Optional boat override: `boats/{sail}/instrumentation/tactical-alerts.yaml`

```yaml
apiVersion: sailing.cognite-fholm/v1
kind: InsightAlertProfile
metadata:
  race_id: faerderseilasen-2026
spec:
  channels:
    ui: true
    grafana_panel: race-alerts
    course_editor: true
    tts:
      enabled: true
      min_severity: warning
      locale: nb-NO
      speaker_device: alsa:plughw:1,0
      max_per_10min: 6
  rules:
    - id: rank_drop_15min
      category: fleet_position
      enabled: true
      severity: warning
      params:
        places: 3
        window_min: 15
    - id: xte_off_course
      category: course
      enabled: true
      severity: warning
      params:
        xte_m: 50
        persist_s: 30
    - id: trim_under_target
      category: sail_trim
      enabled: true
      severity: info
      params:
        polar_pct_below: 85
        persist_s: 120
      channels:
        tts: false   # visual only
  ack:
    cooldown_min: 30
```

#### 7.21.6 UX channels

| Channel | Component | Behavior |
|---------|-----------|----------|
| **Grafana** | `grafana-race` → **Alert feed** panel | Scrollable list; severity color; ack button links to API |
| **course-editor** | Alert strip + history drawer | WebSocket from `insight-alerts`; toast for `warning`+ |
| **Race Display row** | Optional compact alert icon | Mirrors H5000 severity icon pattern ([§7.17.7](#7177-race-display-parity)) |

Unacknowledged `urgent` alerts pulse on UI until ack or TTL expiry.

#### 7.21.7 Voice annunciation

When `spec.channels.tts.enabled`:

1. Broker enqueues `message_short` if severity ≥ `min_severity`
2. **Piper** synthesizes WAV (offline arm64 model in harbor bundle)
3. Playback via **ALSA** to USB or Bluetooth speaker (`speaker_device`)
4. **espeak-ng** fallback if Piper model missing
5. **Safety yield:** incoming safety Grafana alert cancels current TTS and clears queue

Helm acknowledges via course-editor or Grafana → `POST /alerts/{id}/ack` → suppresses repeat voice for `ack.cooldown_min`.

**Hardware:** Standard USB speaker or marine Bluetooth receiver on boat LAN; no cloud TTS.

#### 7.21.8 API surface (v1)

| Method | Path | Purpose |
|--------|------|---------|
| `POST` | `/events` | Producers submit `InsightEvent` |
| `GET` | `/alerts/active` | Active alerts for UI |
| `GET` | `/alerts/history` | Recent alerts (query params: race_id, category) |
| `POST` | `/alerts/{id}/ack` | Acknowledge; start cooldown |
| `WS` | `/alerts/stream` | Push to course-editor / Grafana live |

`race-mcp-gateway` (planned): `get_active_alerts`, `ack_alert` tools for laptop Cursor.

#### 7.21.9 Degradation

| Condition | Behavior |
|-----------|----------|
| SLA-3 offline | No `sail_trim` events; other categories continue |
| TTS disabled / no speaker | UI channels only |
| `insight-alerts` down | Producers log locally; no alert UX (race continues) |
| `RACE_MODE=true` | Service stays up; no container updates |

---

## 8. Technology matrix

| Concern | Choice | Language | Rationale |
|---------|--------|----------|-----------|
| Marine hub | Signal K Server | Node.js / TS | Industry standard; PiCAN-M compatible; plugin ecosystem |
| Live stream | WebSocket (Signal K v1) | — | Proven in `subscribe_to_websocket` |
| Message buffer | Redis Streams (v1) | — | Lighter than RabbitMQ on Pi; optional |
| Time series DB | InfluxDB 2.x | Flux | Purpose-built; Grafana native |
| Graph DB | Neo4j 5 Community | Cypher | Replaces CDF relationships; rich tactical queries |
| Dashboards | Grafana OSS | — | De facto for InfluxDB |
| LLM runtime | llama.cpp | C++ / Python bindings | Best ARM edge performance for LLaMA |
| Edge ML | Coral libedgetpu | Python | Accelerate non-LLM models |
| GoPro control | Open GoPro Python SDK | Python | HERO13 BLE + Wi-Fi capture |
| Sail geometry | OpenCV + custom calib | Python | Angles and shape metrics |
| Onshore training | PyTorch + Hugging Face | Python | TrimTransformer on GPU servers |
| Model registry | MLflow | — | Versioned shore → edge deploy |
| GRIB parsing | cfgrib / xarray / eccodes | Python | Decode GRIB2 wind grids on SLA-2 |
| AIS decode | pyais + Signal K paths | Python | Fleet position ingest |
| Polars | NumPy interpolation | Python | Target BSP/VMG per TWS/TWA |
| Wind analysis | Custom fusion service | Python | GRIB + AIS + polar runtime |
| Course PDF parse | PyMuPDF + regex/NLP | Python | SI chapter 11 → waypoints |
| Course editor | React + TypeScript + Vite | TS/TSX | Manual waypoint entry on Pi |
| Live results | FastAPI + Neo4j | Python | Corrected-time standings |
| Handicap registry | ORC PDF parser | Python | Certificate + WRS TCF per race |
| Agent context | **Google OKF** v0.1 | Markdown/YAML | Knowledge bundle for advisory agents |
| Race/boat data | **AI-sailing-data** GitHub repo | YAML/OKF | Temporal planning; Neo4j import source |
| Data sync | `race-data-sync` | Python | Git pull data repo via LTE/Wi-Fi |
| Graph import | `race-import` | Python | MERGE neo4j YAML bundles |
| Race MCP | `race-mcp-gateway` + MCP SDK | Python | Laptop Cursor → live Neo4j/Influx/YAML on boat LAN |
| TTS (alerts) | Piper + espeak-ng | C++ / CLI | Offline voice annunciation for tactical alerts |
| API / coach | FastAPI | Python | Async, typed, small footprint |
| Containers | Docker Compose | YAML | Repeatable; works on Pi arm64 |
| CI/CD | **GitHub Actions** | YAML | Lint, test, build arm64, push GHCR |
| Container registry | **GHCR** (`ghcr.io/cognite-fholm`) | OCI | Free with GitHub; same org as repo |
| Pi orchestration | Docker Compose + systemd | — | No Kubernetes; optional Watchtower in harbor |
| Shore training host | **Gaming PC** (SLA-S) | Docker Compose | Local GPU; harbor-only TrimTransformer training |
| Remote updates | Watchtower (harbor only) | — | Pull from GHCR when `RACE_MODE=false` |
| Config | Environment + YAML | — | No cloud config dependency |

---

## 9. Deployment architecture

### 9.1 Container layout (per SLA tier)

Each tier has its own Compose file. **Never merge SLA-1 with SLA-3 on the same Pi in race profile.**

```mermaid
graph TB
    subgraph sla1["docker-compose.sla-1.yml — telemetry.local"]
        sk["signalk-server :3000\nhost network"]
        bridge["signalk-influx-bridge"]
        influx["influxdb :8086"]
        g1["grafana-telemetry :3001"]
        sk --> bridge --> influx --> g1
    end

    subgraph sla2["docker-compose.sla-2.yml — race.local"]
        neo["neo4j :7474"]
        race["race-intelligence"]
        ais["ais-collector"]
        comp["competitor-sync"]
        grib_in["grib-ingest"]
        grib_p["grib-parser"]
        polar["polar-manager"]
        wind["wind-field-analyzer"]
        course["course-parser"]
        results["live-results"]
        hcap["handicap-manager"]
        editor["course-editor :3010"]
        llm2["llama-tactical :8080"]
        coach["tactical-coach :8090"]
        g2["grafana-race :3002"]
        race --> neo
        ais --> neo
        comp --> neo
        polar --> neo
        course --> neo
        hcap --> neo
        results --> neo
        grib_in --> grib_p --> wind --> neo
        ais --> wind
        polar --> wind
        ais --> results
        course --> results
        hcap --> results
        coach --> llm2
        coach --> neo
        neo --> g2
    end

    subgraph sla3["docker-compose.sla-3.yml — vision.local"]
        gopro["gopro-orchestrator"]
        ingest["media-ingest"]
        coral["coral-preprocess"]
        geo["sail-geometry"]
        match["condition-matcher"]
        llm3["llama-vision :8081"]
        sail["sail-analysis-api :8091"]
        store["image-store"]
        export["training-export"]
        g3["grafana-sail :3003"]
        gopro --> ingest --> coral --> geo --> match --> sail
        geo --> llm3 --> sail
        ingest --> store
        sail --> g3
    end

    influx -.->|read-only| coach
    influx -.->|read-only| sail
    neo -.->|race context| sail
    sail -.->|SailAnalysis| neo
```

**Compose file mapping:**

| File | Deploy to | Watchtower in race mode |
|------|-----------|-------------------------|
| `docker-compose.sla-1.yml` | `telemetry.local` | **Disabled** |
| `docker-compose.sla-2.yml` | `race.local` | Harbor only |
| `docker-compose.sla-3.yml` | `vision.local` | Harbor only |
| `docker-compose.harbor.yml` | Overlay — enables Watchtower per tier | When `RACE_MODE=false` |

### 9.2 Platform commitment — GitHub + Docker

The project goes **all-in on GitHub and Docker**. No Azure Container Registry, Kubernetes, or cloud edge orchestration for the boat stack. Shore ML runs on **own hardware** (gaming PC), not rented cloud GPU.

| Concern | Choice | Rationale |
|---------|--------|-----------|
| Source control | **GitHub** (`cognite-fholm/AI-sailing-system`) | Single home for code, issues, releases |
| CI | **GitHub Actions** | Free tier; native GHCR push; path-filtered workflows per SLA tier |
| Registry | **GHCR** (`ghcr.io/cognite-fholm/*`) | Zero marginal cost; digest-pinned deploys |
| Edge runtime | **Docker Compose** on Raspberry Pi (`linux/arm64`) | Matches ADR-0001/0002; no k3s overhead |
| Edge updates | **Watchtower** (harbor overlay only) | Pull-based; disabled during races |
| Shore training | **Gaming PC** + `docker-compose.sla-shore.yml` | Cost-effective vs cloud GPU VMs |
| Config / knowledge | Git + bind mounts | Not baked into app images |

**Explicitly out of scope:** ACR, AKS, Argo CD, Terraform cloud state, direct Actions→SSH deploy to boat.

### 9.3 CI pipeline — GitHub Actions → GHCR

**Workflow layout** (`.github/workflows/`):

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `ci.yml` | Pull request | Lint, unit tests, compose config validate |
| `publish-sla-1.yml` | Push to `main` (path: `signalk/**`, `influxdb/**`, …) | `docker buildx` **linux/arm64** → push GHCR |
| `publish-sla-2.yml` | Push to `main` (path: `tactical-coach/**`, `course-parser/**`, …) | Same |
| `publish-sla-3.yml` | Push to `main` (path: `gopro-orchestrator/**`, `sail-geometry/**`, …) | Same |
| `release.yml` | Tag `v*` | Build all tiers; write `deploy/locks/{tag}.env`; GitHub Release notes |

**Image tagging:**

| Tag | When | Use |
|-----|------|-----|
| `sha-{git_sha}` | Every `main` build | Traceability |
| `main` | Latest successful `main` | Harbor dev pulls |
| `v0.4.0` | Git tag | Regatta freeze / production |
| `@sha256:…` | Digest | **Pinned** in `deploy/locks/*.env` |

**Build rules:**

1. **arm64 only** for Pi images (amd64 optional for local dev smoke tests).
2. **Path filters** — do not rebuild all 20+ services on every commit.
3. **No GGUF / training data in images** — see §9.7.
4. **Self-hosted arm64 runner** (optional Phase 4+) on a spare Pi at home when QEMU builds become slow.

**Secrets (GitHub repo settings):**

| Secret | Purpose |
|--------|---------|
| `GITHUB_TOKEN` (built-in) | Push to GHCR (`packages: write`) |
| None required for Pi pull | GHCR public packages or `docker login ghcr.io` once on each Pi |

### 9.4 CD on Raspberry Pi — Docker Compose

Each Pi runs **one SLA compose stack**, started by **systemd** (`ai-sailing-sla-N.service`).

```bash
# Example — race.local (SLA-2)
cd /opt/ai-sailing-system
source deploy/env/harbor.env          # or race.env during regatta
docker compose -f docker-compose.sla-2.yml \
  --env-file deploy/locks/current.env \
  up -d
```

**Compose overlays:**

| File | When |
|------|------|
| `docker-compose.sla-N.yml` | Always — service definitions |
| `deploy/locks/current.env` | Image digest pins (`POLAR_MANAGER_IMAGE=…@sha256:…`) |
| `docker-compose.harbor.yml` | `RACE_MODE=false` — enables Watchtower on SLA-2/3 |
| `deploy/compact|standard|race/*.yml` | Topology overrides (1–3 Pi) |

**Watchtower policy:**

| Tier | Watchtower | Label |
|------|------------|-------|
| SLA-1 | **Never** | `com.centurylinklabs.watchtower.enable=false` on all services |
| SLA-2 | Harbor only | Enabled via `docker-compose.harbor.yml` |
| SLA-3 | Harbor only | Same |

Watchtower updates **one container at a time**; SLA-1 is updated only via **manual** `compose pull && up` in harbor.

### 9.5 Lifecycle states and guardrails

```mermaid
stateDiagram-v2
    [*] --> Development
    Development --> Harbor: merge to main, pull on Pi
    Harbor --> RaceFreeze: pre-regatta lock digests
    RaceFreeze --> Racing: RACE_MODE=true
    Racing --> Harbor: regatta ends, RACE_MODE=false
    Harbor --> Development: local compose build
    Racing --> Offline: no internet
    Offline --> Harbor: return to marina
```

| State | `RACE_MODE` | Watchtower | SLA-1 update | Training export |
|-------|-------------|------------|--------------|-----------------|
| **Development** | `false` | off | local build OK | n/a |
| **Harbor** | `false` | SLA-2/3 on | manual only | opt-in consent |
| **Race freeze** | `false` | off | manual + checklist | stopped |
| **Racing** | `true` | **off all tiers** | **forbidden** | **stopped** |
| **Offline** | `true` | off | USB `docker load` only | stopped |

**Guardrails (non-negotiable):**

| ID | Rule |
|----|------|
| **GR-1** | `RACE_MODE=true` → Watchtower disabled on every Pi (`WATCHTOWER_NO_PULL=true` or harbor overlay not loaded) |
| **GR-2** | SLA-1 `signalk-server` never auto-restarts from Watchtower — NMEA gaps at start sequence are unacceptable |
| **GR-3** | Deploy order when upgrading: **SLA-3 → SLA-2 → SLA-1**; never all tiers simultaneously |
| **GR-4** | Production compose uses **digest pins** from `deploy/locks/` — not bare `:latest` |
| **GR-5** | `training-export` and shore push containers **stopped** when `RACE_MODE=true` |
| **GR-6** | Neo4j / InfluxDB / image-store volumes are **never** destroyed by `compose up` — migrations are explicit jobs |
| **GR-7** | Rollback = restore previous `deploy/locks/*.env` + `compose up` — keep last two lock files |
| **GR-8** | Harbor sync script runs **models + OKF + config** separately from container pulls |
| **GR-9** | GitHub Release tag required before any regatta freeze lock file is marked `production` |
| **GR-10** | No off-device data export without `TRAINING_EXPORT_CONSENT` |

**Race freeze procedure** (before regatta):

1. Tag release: `git tag v0.4.0 && git push --tags`
2. CI builds all images; `release.yml` writes `deploy/locks/v0.4.0.env`
3. Copy to Pis: `deploy/locks/current.env` (or symlink)
4. On each Pi in harbor: `scripts/harbor-sync.sh` (models, OKF, config) then `scripts/harbor-pull.sh`
5. Run pre-flight checklist (§9.3 former 9.3 → §9.9)
6. Set `RACE_MODE=true` in `deploy/env/race.env` on all nodes
7. Disable Watchtower / stop harbor overlay

### 9.6 Shore training — gaming PC (SLA-S)

**Hardware:** Personal **gaming PC** with NVIDIA GPU (CUDA). Not deployed to Raspberry Pi. Not a cloud VM.

**Location:** Home / workshop — same LAN as harbor Pis when syncing training bundles.

| Component | Runs on | Deploy |
|-----------|---------|--------|
| `dataset-curator` | Gaming PC | `docker compose -f shore/docker-compose.sla-shore.yml` |
| `trim-transformer-trainer` | Gaming PC (GPU) | Same |
| `model-evaluator` | Gaming PC | Same |
| `MLflow` (local) | Gaming PC | Volume `~/mlflow/` |

**Data flow:**

```mermaid
flowchart LR
    BOAT["SLA-3 training-export\nharbor USB or LAN"]
    BUNDLE["training bundle\n/opt/exports/"]
    PC["Gaming PC\nSLA-S Compose"]
    MLF["MLflow checkpoints"]
    GHCR["GHCR\ntrim-predictor:v*"]
    PI3["vision.local\nSLA-3"]

    BOAT -->|consent only| BUNDLE --> PC
    PC --> MLF
    PC -->|quantize + publish| GHCR
    GHCR -->|harbor pull| PI3
```

**Shore lifecycle:**

1. **Ingest** — copy harbor export bundle to PC (`rsync` / USB).
2. **Curate** — `dataset-curator` splits by **session** (no frame leakage).
3. **Train** — `trim-transformer-trainer` on GPU; log to local MLflow.
4. **Evaluate** — hold out full regatta sessions; gate release on MAE thresholds.
5. **Publish** — push `trim-predictor:{version}` to GHCR (arm64 ONNX artifact or thin inference image).
6. **Deploy to boat** — harbor: `harbor-pull.sh` on `vision.local`; import `BestTrimSnapshot` to Neo4j.

**Cost:** electricity only — no Azure/AWS GPU rental.

### 9.7 Artifact classes — what CI builds vs harbor sync

| Artifact | In GHCR image? | How it reaches the Pi |
|----------|----------------|------------------------|
| Python / Node app services | Yes | `compose pull` |
| `course-editor` static build | Yes | same |
| LLaMA GGUF (2–8 GB) | **No** | `scripts/harbor-sync.sh` → `/opt/models/sla-{2,3}/` |
| `trim-predictor` ONNX | Optional thin image | GHCR on release + harbor pull |
| OKF knowledge bundle | **No** | `git pull` or rsync → `/opt/knowledge/` |
| `config/*.yaml` | **No** | bind mount `/opt/ai-sailing-system/config/` |
| Polars (SLK / derived YAML) | **No** | `data/polars/` volume |
| GRIB files | **No** | `data/grib/` volume |
| Neo4j / InfluxDB data | **Never** | named volumes; backup via `scripts/backup-volumes.sh` |

### 9.8 Rollback and offline fallback

**Rollback (harbor, internet available):**

```bash
cp deploy/locks/v0.3.9.env deploy/locks/current.env
./scripts/harbor-pull.sh --tier 3
./scripts/harbor-pull.sh --tier 2
# SLA-1 only if required:
./scripts/harbor-pull.sh --tier 1
```

**Offline (no registry):**

```bash
# Prepared on shore before departure:
docker save ghcr.io/cognite-fholm/tactical-coach:v0.4.0 | gzip > tactical-coach.tar.gz
# On Pi:
docker load < tactical-coach.tar.gz
```

Keep a USB stick with **saved images + lock file** matching the frozen regatta stack.

### 9.9 Remote upgrade strategy (summary)

**Problem:** Upgrade containers from harbor Wi-Fi without breaking NMEA or mid-race stability.

**Approach** (unchanged principles, now under GitHub + Docker guardrails):

1. **Immutable images** on GHCR (`linux/arm64`).
2. **Watchtower** — harbor only, SLA-2/3, one service at a time.
3. **Signal K** — `network_mode: host`; manual SLA-1 updates only in harbor with `candump` pre-check.
4. **Per-tier rollout** — SLA-3 → SLA-2 → SLA-1 (GR-3).
5. **Pre-race freeze** — digest lock file + `RACE_MODE=true` (GR-1, GR-4).
6. **Rollback** — previous `deploy/locks/*.env` (GR-7).
7. **Offline** — `docker load` from USB (§9.8).

**NMEA bus consideration:** Container restarts on `signalk-server` cause brief data gaps (~seconds). Watchtower **never** targets SLA-1. A systemd timer may start Watchtower only when `RACE_MODE=false` and network is up.

### 9.10 Local-only operation checklist

- [ ] Each tier has independent `restart: unless-stopped`
- [ ] DNS not required (use `/etc/hosts` for `telemetry.local`, `race.local`, `vision.local`)
- [ ] Grafana auth enabled on all three instances
- [ ] Models pre-downloaded on SLA-2 and SLA-3 nodes
- [ ] InfluxDB volume on SLA-1; Neo4j volume on SLA-2; image-store on SLA-3
- [ ] NTP optional (GPS time from Signal K on SLA-1 preferred)
- [ ] Inter-tier firewall: SLA-2/SLA-3 read-only access to SLA-1 Influx API

---

## 10. Lineage from cognite-fholm / CogSail

### 10.1 Repository analysis

| Repository | Era | Role | Carry forward | Replace |
|------------|-----|------|-------------|---------|
| [CogSail](https://github.com/cognite-fholm/CogSail) | 2018–2021 | Java/Android client experiments | UX lessons, marine domain model | Java stack, CDF client |
| [Cogsail-raspberry-pi](https://github.com/cognite-fholm/Cogsail-raspberry-pi) | 2021 | Java on RPi | Onboard deployment concept | Java runtime |
| [cogsail-raspberry](https://github.com/cognite-fholm/cogsail-raspberry) | 2021 | RPi project skeleton | — | Empty/stale |
| [cogsail-python](https://github.com/cognite-fholm/cogsail-python) | 2024 | **SignalK → RabbitMQ → CDF** | `parse_signalK()`, stream pattern, OAuth-free local variant | CDF, RabbitMQ (optional), cloud |
| [subscribe_to_websocket](https://github.com/cognite-fholm/subscribe_to_websocket) | 2024 | WebSocket → RabbitMQ | WebSocket subscription pattern | RabbitMQ coupling |
| [push_to_cdf](https://github.com/cognite-fholm/push_to_cdf) | 2024 | RabbitMQ → CDF time series | Batching, dedup, offset tracking | CDF SDK |
| [cogsail-scripts](https://github.com/cognite-fholm/cogsail-scripts) | 2019 | CDF asset hierarchy (MMSI boats) | MMSI → vessel graph model | CDF assets API |
| [crawl_web](https://github.com/cognite-fholm/crawl_web) | 2024 | Race web crawling | NOR/SI ingestion pipeline | — |
| [3d_processing](https://github.com/cognite-fholm/3d_processing) | 2024 | 3D data processing | Future: course/spatial overlays | — |
| [Cognite-Sailing](https://github.com/cognite-fholm/Cognite-Sailing) | 2018 | Early prototype | Historical reference | Empty |

### 10.2 Architecture evolution

```mermaid
flowchart LR
    subgraph Old["CogSail (2024) — cogsail-python"]
        SKold["Signal K\nWebSocket"]
        RMQ["RabbitMQ Streams"]
        CDF["Cognite Data Fusion\ntime series + assets"]
        SKold --> RMQ --> CDF
    end

    subgraph New["AI Sailing System (2026)"]
        SKnew["Signal K\n+ PiCAN-M"]
        IFXnew["InfluxDB"]
        N4Jnew["Neo4j"]
        GRnew["Grafana"]
        LLM["LLaMA / llama.cpp"]
        SKnew --> IFXnew
        SKnew --> N4Jnew
        IFXnew --> GRnew
        N4Jnew --> GRnew
        IFXnew --> LLM
        N4Jnew --> LLM
    end

    Old -.->|migrate patterns| New
```

### 10.3 Specific code reuse

1. **`parse_signalK()`** (`cogsail-python/push_to_cdf/Consume stream.py`) — adapt to write Influx points instead of CDF `time_series.data.insert_multiple`.
2. **WebSocket subscriber** (`subscribe_to_websocket/`) — replace RabbitMQ sink with direct Influx line protocol or Redis Streams consumer.
3. **MMSI asset hierarchy** (`cogsail-scripts/CreateBoats.py`) — translate to Cypher `MERGE (v:Vessel {mmsi: $mmsi})`.
4. **RabbitMQ offset persistence** (CDF data model `RabbitMQOffset`) — replace with InfluxDB task checkpoint or Redis consumer group ID.

---

## 11. Functional requirements

### 11.1 SLA-1 — Telemetry

| ID | Requirement |
|----|-------------|
| FR-1 | Ingest NMEA 2000 PGNs from `can0` at 250 kbit/s |
| FR-2 | Ingest NMEA 0183 from `/dev/ttyS0` at configurable baud |
| FR-3 | Publish all data to Signal K v1 delta stream within 200 ms |
| FR-4 | Persist numeric telemetry to InfluxDB with &lt; 500 ms write latency (p95) |
| FR-5 | Support optional I²C environmental sensors |
| FR-6 | SLA-1 operates independently when SLA-2 and SLA-3 are offline |

### 11.2 SLA-2 — Race, competitors, GRIB, polars & wind

| ID | Requirement |
|----|-------------|
| FR-10 | User can start/stop a **race session** (tags all data with `race_id`) |
| FR-11 | System detects tacks and gybes from heading/rudder/AWA thresholds |
| FR-12 | Grafana-race shows live VMG and **polar %** for own boat and selected competitors |
| FR-13 | Neo4j stores leg boundaries, mark roundings, and competitor positions |
| FR-14 | Post-race debrief includes wind-zone summary within 5 min of session end |
| FR-15 | **AIS** collected for own boat and all visible competitors (MMSI, COG, SOG, position) |
| FR-16 | `ais-collector` refreshes fleet positions ≤ 10 s (class A) from N2K via Signal K |
| FR-17 | **GRIB** auto-fetched every 6 h when `ONLINE_MODE=true`; manual upload supported |
| FR-18 | Latest GRIB usable offline; age warning if stale &gt; 12 h at race start |
| FR-19 | **Own-boat polar** loaded from **SLK** file (`7710 (3).slk`); auto-reload on change |
| FR-20 | `polar-manager` parses SYLK columns: TWS, TWA, BTV, VMG, AWS, AWA, Heel, Condition |
| FR-21 | **Competitor polars** derived from ORC certificate **PNG/PDF** via `polar-certificate-extractor` |
| FR-22 | Derived polars require harbor **approve** before use in wind-field scoring (configurable) |
| FR-23 | `polar-manager` interpolates target BSP/VMG for any TWS/TWA |
| FR-24 | `wind-field-analyzer` updates course wind-advantage map every 30–60 s during race |
| FR-25 | Wind zones fuse GRIB, own instruments, fleet AIS overperformance vs polars |
| FR-26 | Crew sees heatmap + recommendation (e.g. favored side of beat) on grafana-race |
| FR-27 | crawl_web agent ingests NOR/SI when online |
| FR-28 | `course-parser` extracts §11 routes from SI PDF (e.g. Færderseilasen) |
| FR-29 | Coordinates parsed from `N59°52,50' Ø010°38,76'` (WGS-84) format |
| FR-30 | Waypoints without coords editable in React `course-editor` at `:3010` |
| FR-31 | `live-results` ranks fleet by corrected time (`elapsed × handicap`) |
| FR-32 | VMG to next mark computed for own boat and competitors using waypoint geometry |
| FR-33 | `handicap-manager` loads multiple ORC ratings per vessel from certificate PDF |
| FR-34 | Per-race **ORC WRS TCF** overrides static handicap when issued |
| FR-35 | Active handicap selected from SI scoring rule + wind band (single/triple/WRS) |
| FR-36 | Parser loads **multiple course variants** per regatta (e.g. Bane A / Bane B) |
| FR-37 | `StartBoatSignal` maps start-boat displays (numeral 2/3) to `CourseRoute` |
| FR-38 | `ClassFlag` linked to own boat; shown in course-editor Start Line panel |
| FR-39 | User **confirms** active course at start; stored as `CourseSelection` |
| FR-40 | Optional `course-flag-detector` suggests course from start-boat photo; user may override |
| FR-41 | Supplementary signals (e.g. flag **T**) modify waypoint rounding rules |
| FR-42 | **iRegatta parity:** Grafana race dashboard with configurable readouts (SOG, COG, VMG, wind, DTM, performance %) |
| FR-43 | **iRegatta parity:** COG/SOG damping selectable 0/3/5/10 s before display |
| FR-44 | **iRegatta parity:** Lift indicator — heading vs 10 s average; threshold configurable |
| FR-45 | **iRegatta parity:** Speed and VMG history graphs with 2/4/10/20 min window |
| FR-46 | **iRegatta parity:** Performance bar — actual vs polar BSP as percentage |
| FR-47 | **iRegatta parity:** Steering bars toward optimum VMG from polar tack/jibe angles |
| FR-48 | **iRegatta parity:** Layline overlay on map when navigating to active waypoint |
| FR-49 | **iRegatta parity:** Start countdown with sync-to-minute, pause, optional timer beeps |
| FR-50 | **iRegatta parity:** Start line pin/boat ends; favored end; DTL perpendicular to line + extensions |
| FR-51 | **iRegatta parity:** Time-to-line at current COG/SOG; burn-or-gain bar vs countdown |
| FR-52 | **iRegatta parity:** Bow/GPS antenna offset applied to distance-to-line |
| FR-53 | **iRegatta parity:** Manual wind entry (type, compass, two-tack) when instruments unavailable |
| FR-54 | **iRegatta parity:** Wind history — 30 min rolling, 30 s samples |
| FR-55 | **iRegatta parity:** Route auto-advance when within configurable distance of waypoint |
| FR-56 | **iRegatta parity:** Temporary waypoints by bearing+distance and cross-bearing |
| FR-57 | **iRegatta parity:** GPX import/export for waypoints and routes |
| FR-58 | **iRegatta parity:** Polar trim (mirror, interpolate, smooth) for CSV/derived polars |
| FR-59 | **iRegatta parity:** Optional NMEA RMB outbound when navigating (autopilot target) |

### 11.3 SLA-3 — Sail performance vision (GoPro HERO13)

| ID | Requirement |
|----|-------------|
| FR-61 | Orchestrate 3–5 GoPro HERO13 cameras via Open GoPro BLE/Wi-Fi |
| FR-62 | Synchronized multi-camera still burst within ±200 ms |
| FR-63 | Coral preprocess extracts sail/boom ROI before geometry + LLM |
| FR-64 | `sail-geometry` computes boom angle, mast heel, draft, twist, luff metrics |
| FR-65 | Each capture aligned to SLA-1 telemetry (`t_influx` ±100 ms) |
| FR-66 | `condition-matcher` finds best `BestTrimSnapshot` in similar conditions |
| FR-67 | Crew sees current vs best Δ for boom, heel, draft on grafana-sail |
| FR-68 | Vision LLM produces qualitative trim narrative per capture burst |
| FR-69 | Results published to SLA-2 Neo4j as `SailGeometry`, `TrimDelta`, `SailAnalysis` |
| FR-70 | SLA-3 pausable without affecting SLA-1 or SLA-2 |
| FR-71 | GoPro capture at start may feed `course-flag-detector` (user confirms course) |

### 11.4 Onshore training (SLA-S)

| ID | Requirement |
|----|-------------|
| FR-72 | `training-export` builds multimodal bundles (telemetry + images + geometry) in harbor |
| FR-73 | Export requires explicit `TRAINING_EXPORT_CONSENT` per session |
| FR-74 | Shore pipeline trains TrimTransformer on GPU machines (PyTorch) |
| FR-75 | Model predicts optimal boom angle, mast heel, sail shape for condition vector |
| FR-76 | Evaluator holds out full regatta sessions — no random frame leakage |
| FR-77 | Quantized `trim-predictor` artifact deployable to SLA-3 via GHCR |
| FR-78 | `BestTrimSnapshot` sets sync from shore to boat Neo4j after training round |

### 11.5 AI coaching (cross-tier)

| ID | Requirement |
|----|-------------|
| FR-80 | SLA-2 text LLM answers tactical questions in &lt; 30 s on Pi 5 |
| FR-81 | No tier sends data off-device without explicit opt-in |
| FR-82 | SLA-2 coach context: OKF bundle + telemetry + race graph + wind zones + **selected course** |
| FR-83 | SLA-3 vision LLM receives OKF trim/capture playbooks in prompt context |
| FR-84 | `okf-enricher` syncs parsed SI, handicaps, and schema into OKF concepts |
| FR-85 | Advisory agents cite OKF concept IDs and live data sources in responses |

### 11.6 Operations

| ID | Requirement |
|----|-------------|
| FR-90 | SLA-1 full stack boots in &lt; 60 s on power-on |
| FR-91 | Remote container update per tier without manual SSH (when online) |
| FR-92 | `RACE_MODE=true` disables Watchtower on all tiers; SLA-1 never auto-updates |
| FR-93 | System runs with zero internet for 72+ hours across all tiers |
| FR-94 | Each tier deployable via separate `docker compose -f docker-compose.sla-N.yml` |
| FR-95 | `grib-store` and `polars/` volumes persist across reboots on SLA-2 |
| FR-96 | All app images built by **GitHub Actions** and published to **GHCR** (`linux/arm64`) |
| FR-97 | Pi deployment uses **Docker Compose** only — no Kubernetes on boat hardware |
| FR-98 | `RACE_MODE=true` enforces guardrails GR-1–GR-5 (no Watchtower, no training export) |
| FR-99 | Regatta deploys use **digest-pinned** images from `deploy/locks/*.env` |
| FR-100 | Shore TrimTransformer training runs on **local gaming PC** (SLA-S), not cloud GPU |
| FR-101 | Harbor sync separates **container pulls** from **models / OKF / config** artifacts |
| FR-102 | **AI-sailing-data** holds races (by year/date) and boats (by sail number/year) |
| FR-103 | `race-data-sync` compares local vs GitHub and pulls when newer (policy-gated) |
| FR-104 | `race-import` applies declarative Neo4j YAML from data repo without clobbering runtime nodes |
| FR-105 | Deploy uses **both** system image lock and data repo git ref at race freeze |
| FR-106 | Teltonika LTE provides WAN for data sync and GRIB when marina Wi-Fi unavailable |

### 11.7 B&G H5000 integration & display parity

| ID | Requirement |
|----|-------------|
| FR-107 | Signal K ingests H5000 N2K wind, BSP, heel, GPS, depth without duplicate true-wind solver when CPU publishes TWD |
| FR-108 | Grafana `race-sailsteer` mirrors H5000 SailSteer fields including laylines when navigating |
| FR-109 | Start page shows DIST P/S, DTL⊥, BIAS°, BIAS ADV (boat lengths), favored end — H5000 semantics |
| FR-110 | Grafana `race-windplot` provides TWD/TWS histograms (1–60 min windows) |
| FR-111 | Grafana `race-highway` shows XTE, DTM, ETA, COG, off-course limit per active route leg |
| FR-112 | `PolarSource` supports H5000 CSV export/import and `vmg_targets` configuration |
| FR-113 | Layline computation supports tidal flow correction and 5/10/15/30 min layline limit bands |
| FR-114 | Race Display-style compact row: two primary values + performance bargraph |
| FR-115 | `InstrumentProfile` documents dual wind/BSP sensors and switch policy (read from H5000) |
| FR-116 | `InstrumentProfile` documents 3D motion wind correction and mast height when equipped |
| FR-117 | `InstrumentCalibration` persists BSP, depth, MHU align, heel correction table in data repo |
| FR-118 | **Course** (HDG + leeway) available for layline/tack logic when leeway calibrated |
| FR-119 | Per-variable damping 0–9 s configurable in `InstrumentProfile`; dynamic BSP damping when tier ≥ Hercules |
| FR-120 | Race timer matches H5000: countdown, sync, stop, reset; line ping with midnight stale rule |
| FR-121 | Critical alarms (depth, BSP, wind) configurable via `AlarmProfile` |
| FR-122 | Harbor export slot for H5000 webserver calibration backup under `instrumentation/backup/` |
| FR-123 | Autopilot mode, setpoint, rudder angle ingested read-only — no drive commands from Pi |

### 11.8 Race-side MCP (laptop Cursor)

| ID | Requirement |
|----|-------------|
| FR-124 | `race-mcp-gateway` on SLA-2 exposes MCP over boat LAN (`race.local:3100`) |
| FR-125 | MCP tools read live standings, fleet positions, and course selection from Neo4j |
| FR-126 | MCP tools run bounded Flux queries against Influx telemetry (read token) |
| FR-127 | MCP tools read active race/boat YAML and wiki from mounted `AI-sailing-data` |
| FR-128 | MCP tools return wind zones, polar targets, and start-line state from SLA-2 APIs |
| FR-129 | MCP gateway authenticated; not exposed on LTE WAN; read-only default role |
| FR-130 | Rate limits protect SLA-2 CPU during ad hoc agent queries |
| FR-131 | Gateway remains available when `RACE_MODE=true` |
| FR-132 | [docs/race-laptop-mcp.md](./docs/race-laptop-mcp.md) documents laptop + Cursor setup |
| FR-139 | Dedicated MCP endpoint `/mcp/neo4j` with read-only Cypher and curated standing queries |
| FR-140 | Dedicated MCP endpoint `/mcp/influx` with bounded Flux and instrument snapshot tools |
| FR-141 | Combined `/mcp` endpoint exposes both Neo4j and Influx tool sets |
| FR-142 | [docs/mcp-neo4j-influx.md](./docs/mcp-neo4j-influx.md) documents tools, buckets, and example queries |

### 11.9 ORC certificate collection (shore)

| ID | Requirement |
|----|-------------|
| FR-133 | Shore skill fetches ORC metadata for all `fleet.yaml` entrants via `activecerts` XML (family inferred from class) |
| FR-134 | Per-boat `ListCert` fallback when entrant absent from bulk active list |
| FR-135 | `fleet-orc-index.yaml` records ref mismatches vs registration `orc_ref` |
| FR-136 | Authenticated `download_cert_pdfs.py` stores PDFs with `%PDF` validation; cookies never in git |
| FR-137 | `materialize_boat_certs.py` creates `boats/{sail}/{year}/certificates/{type}-{orc_ref}/` with `manifest.yaml` |
| FR-138 | `collected-sources.yaml` registers `orc_sailor_services` provenance |

### 11.10 Shore weather & current collection

| ID | Requirement |
|----|-------------|
| FR-143 | `metno-oslofjord-weather` skill downloads GRIB (`weather`, `current`, `waves`) for `oslofjord` (or race bbox area) and writes `WeatherCollection` manifest |
| FR-144 | `oslofjord-current-plots` skill fetches PNG maps for race-relevant areas (`ferder4`, etc.) with interpretation guide in `reference.md` |
| FR-145 | `smhi-wind-observations` skill fetches MetObs JSON for configured validation stations (default 81350) |
| FR-146 | `grib-plan.yaml` documents MET area, refresh schedule, SMHI stations, and boat path `/data/grib/` |
| FR-147 | GRIB binaries gitignored; only manifests and planning YAML committed |
| FR-148 | `collected-sources.yaml` registers `metno_gribfiles`, `metno_oslofjord_plots`, `smhi_metobs` provenance |
| FR-149 | `planning/weather-notes.md` records agent/human interpretation after collection |

### 11.11 Tactical insight alerts & annunciation

| ID | Requirement |
|----|-------------|
| FR-150 | `insight-alerts` service on SLA-2 ingests `InsightEvent` from analysis producers and evaluates `InsightAlertProfile` rules |
| FR-151 | Alert categories: `fleet_position`, `course`, `sail_trim`, `wind_tactics`, `start_line`, `coach` — separate from safety alarms (FR-121) |
| FR-152 | Active alerts visible on `grafana-race` alert feed panel and `course-editor` WebSocket strip |
| FR-153 | Helm can acknowledge alerts; repeat annunciation suppressed for configurable cooldown |
| FR-154 | Optional TTS via Piper (espeak-ng fallback) to ALSA speaker when `channels.tts.enabled` |
| FR-155 | Voice rate limit (`max_per_10min`) and `min_severity` prevent alert fatigue |
| FR-156 | Safety Grafana critical alarms preempt tactical TTS playback |
| FR-157 | `InsightAlertProfile` in `planning/tactical-alerts.yaml` per race; optional boat override |
| FR-158 | Producers (`live-results`, `race-intelligence`, `wind-field-analyzer`, `sail-analysis-api`, `tactical-coach`) emit structured events with `message_short` for voice |
| FR-159 | Alert history in Neo4j (`InsightAlert`) and Influx annotations for debrief |
| FR-160 | `insight-alerts` remains available when `RACE_MODE=true` |
| FR-161 | Degrade gracefully when SLA-3 offline — fleet/course alerts continue without trim category |

---

## 12. Non-functional requirements

| Category | SLA-1 | SLA-2 | SLA-3 |
|----------|-------|-------|-------|
| Availability (race) | 99.99% | 99.9% | 95% |
| Latency (dashboard) | &lt; 1 s | &lt; 3 s | &lt; 60 s per analysis |
| Storage | 32 GB min; 7 days raw @ 10 Hz | Neo4j 16 GB+; GRIB 2–5 GB; polars &lt;100 MB | GoPro JPEG ring 64 GB+ |
| Power | N2K SMPS or 12 V DC | 12 V DC | 12 V DC |
| Isolation | Dedicated Pi in race profile | Separate Pi or shared with SLA-3 | Separate Pi required in race profile |
| Security | No default passwords; read token for cross-tier Influx | Neo4j auth; REST API keys | Camera data local only |
| Maintainability | Independent compose stack per tier | Same | Same |

---

## 13. Repository layout (planned)

```
AI-sailing-system/
├── spec.md
├── docs/
│   ├── ARCHITECTURE.md           # Architecture index (repos, tiers, ADRs)
│   ├── deployment-lifecycle.md
│   └── references/README.md      # iRegatta + H5000 manual links
├── adr/
├── docker-compose.sla-1.yml    # Telemetry tier
├── docker-compose.sla-2.yml    # Race & competitor tier
├── docker-compose.sla-3.yml    # Sail vision tier
├── docker-compose.harbor.yml     # Watchtower overlay (harbor mode)
├── .github/
│   └── workflows/                # CI: lint/test; CD: build arm64 → GHCR
├── deploy/
│   ├── README.md                 # Lifecycle, guardrails, race freeze
│   ├── env/
│   │   ├── harbor.env.example
│   │   └── race.env.example
│   ├── locks/                    # Digest-pinned image env files per release
│   ├── compact/                  # Single-Pi overrides
│   ├── standard/                 # 2-Pi overrides
│   └── race/                     # 3-Pi overrides (recommended)
├── scripts/
│   ├── harbor-sync.sh            # Models, OKF, config (not containers)
│   ├── harbor-pull.sh            # compose pull per tier
│   ├── install-pi-telemetry.sh
│   ├── install-pi-race.sh
│   └── install-pi-vision.sh
├── signalk/                      # SLA-1
├── influxdb/                     # SLA-1
├── grafana/
│   ├── telemetry/                # SLA-1 dashboards
│   ├── race/                     # SLA-2 dashboards
│   └── sail/                     # SLA-3 dashboards
├── neo4j/                        # SLA-2
├── race-intelligence/            # SLA-2 start line, lift, steering
├── race-data-sync/               # SLA-2 git pull AI-sailing-data
├── race-import/                  # SLA-2 Neo4j YAML MERGE
├── race-mcp-gateway/             # SLA-2 MCP for laptop Cursor (boat LAN)
├── competitor-sync/                # SLA-2 fleet roster
├── ais-collector/                  # SLA-2 AIS ingest from Signal K
├── grib-ingest/                    # SLA-2 scheduled GRIB fetch + upload
├── grib-parser/                    # SLA-2 GRIB2 → wind grid
├── polar-manager/                  # SLA-2 SLK parser + polar API
├── polar-certificate-extractor/    # SLA-2 ORC PNG/PDF → derived polar
├── wind-field-analyzer/
├── course-parser/                  # SLA-2 SI/NOR PDF → waypoints
├── course-editor/                  # SLA-2 React/TS waypoint + Start Line flag UX
├── course-flag-detector/           # Optional start-boat flag vision (Coral)
├── live-results/                   # SLA-2 corrected-time standings
├── handicap-manager/               # SLA-2 ORC + WRS handicaps
├── config/
│   ├── vessel.yaml
│   ├── competitors.yaml
│   ├── courses.yaml                # Active regatta + route selection
│   ├── handicaps.yaml              # Multi-rating per vessel
│   ├── cameras.yaml
│   └── grib-sources.yaml
├── examples/
│   └── README.md                   # Parent-dir polar files (boat_system/)
├── data/                           # gitignored — runtime volumes
│   ├── grib/
│   └── polars/                     # Canonical YAML (generated from SLK / derived)
├── tactical-coach/                 # SLA-2
├── insight-alerts/                 # SLA-2 tactical alert broker + TTS
├── gopro-orchestrator/           # SLA-3 Open GoPro fleet control
├── media-ingest/                   # SLA-3 GoPro HTTP download
├── sail-geometry/                  # SLA-3 angle & shape metrics
├── condition-matcher/              # SLA-3 best-trim comparison
├── coral-preprocess/               # SLA-3
├── sail-analysis/                  # SLA-3 API
├── training-export/                # SLA-3 harbor bundle builder
├── shore/                          # SLA-S onshore only
│   ├── dataset-curator/
│   ├── trim-transformer-trainer/
│   ├── model-evaluator/
│   └── docker-compose.sla-shore.yml
├── models/
│   ├── sla-2/                      # Text GGUF manifests
│   └── sla-3/                      # Vision GGUF manifests
├── knowledge/                      # OKF bundle (advisory agent context)
└── docs/
    ├── ARCHITECTURE.md             # Architecture index
    ├── hardware-setup.md
    ├── sla-tiers.md
    ├── deployment-lifecycle.md
    ├── race-laptop-mcp.md          # Laptop Cursor + MCP at regatta
    └── references/README.md
```

---

## 14. Implementation phases

### Phase 0 — Specification (current)

- [x] Repository created; [spec.md](./spec.md) v0.11
- [x] [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) — architecture index
- [x] ADR-0001 through ADR-0006, ADR-0008, ADR-0009, ADR-0010, ADR-0011, ADR-0012, ADR-0013
- [x] Dual-repo model ([AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)) + race prep guide
- [x] Reference models: iRegatta (§7.16), B&G H5000 (§7.17); ORC collection skill (§7.19); weather/current skills (§7.20); tactical insight alerts (§7.21)
- [x] Deploy scaffolding, workflow stubs, harbor scripts
- [ ] Runtime containers (Phase 1+)

### Phase 1 — SLA-1 telemetry (MVP)
- [ ] Signal K on Pi with PiCAN-M
- [ ] `docker-compose.sla-1.yml`
- [ ] InfluxDB bridge
- [ ] grafana-telemetry live dashboard

### Phase 2 — SLA-2 race, GRIB, polars, AIS, courses & results
- [ ] Neo4j schema (Vessel, Polar, GribModel, WindAdvantageZone, Waypoint, HandicapRating)
- [ ] `docker-compose.sla-2.yml`
- [ ] `ais-collector` + `polar-manager` (SLK + ORC PDF)
- [ ] `grib-ingest` + `grib-parser` + `wind-field-analyzer`
- [ ] `course-parser` — Færderseilasen §11 PDF
- [ ] `course-editor` — React/TS waypoint + Start Line flag/course selection UI
- [ ] `course-flag-detector` — optional start-boat flag vision
- [ ] `handicap-manager` — ORC certificate + WRS TCF
- [ ] `live-results` — corrected-time standings + VMG
- [ ] `race-intelligence` — start line, lift, steering (iRegatta + H5000 parity)
- [ ] `insight-alerts` — tactical alert broker, Grafana/course-editor UX, optional Piper TTS ([ADR-0015](./adr/0015-tactical-insight-alerts-annunciation.md))
- [ ] `race-data-sync` + `race-import` — pull [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)
- [x] `race-mcp-gateway` scaffold — Neo4j + Influx MCP (`race-mcp-gateway/`)
- [ ] Shore ORC pipeline documented — runtime uses data repo assets ([ADR-0013](./adr/0013-orc-certificate-fleet-collection.md))
- [ ] grafana-race dashboards (SailSteer, Start, WindPlot, Highway per §7.17)

### Phase 3 — SLA-3 GoPro sail vision
- [ ] `docker-compose.sla-3.yml`
- [ ] `gopro-orchestrator` — HERO13 fleet (Open GoPro)
- [ ] `sail-geometry` + `condition-matcher`
- [ ] Coral preprocess + vision LLM
- [ ] grafana-sail dashboards (current vs best trim)

### Phase 4 — GitHub CI/CD & multi-Pi ops
- [ ] `.github/workflows/ci.yml` — lint + test on PR
- [ ] `publish-sla-{1,2,3}.yml` — arm64 build → GHCR
- [ ] `release.yml` — tag → `deploy/locks/{version}.env`
- [ ] `docker-compose.harbor.yml` + Watchtower (SLA-2/3 only)
- [ ] `scripts/harbor-sync.sh` + `harbor-pull.sh`
- [ ] Race profile (3-node) deployment guide + systemd units
- [ ] Migrate `cogsail-python` mapping utilities

### Phase 5 — Shore training (gaming PC / SLA-S)
- [ ] `training-export` harbor bundles (opt-in)
- [ ] `shore/docker-compose.sla-shore.yml` on **local gaming PC** (CUDA)
- [ ] TrimTransformer train/eval → GHCR `trim-predictor`
- [ ] `trim-predictor` edge deployment to SLA-3
- [ ] `BestTrimSnapshot` shore → boat Neo4j sync

---

## 15. Open questions

| # | Question | Notes |
|---|----------|-------|
| OQ-1 | Primary GRIB model for region? | GFS global vs regional HARMONIE/AROME |
| OQ-2 | VPP-lite model for derived polars? | ORC regression table vs custom neural VPP |
| OQ-3 | AIS class B timeout handling? | Stale track grey-out after 5 min |
| OQ-4 | Wind-zone weight tuning per class? | One-design vs ORC handicap fleet |
| OQ-5 | GRIB spatial resolution on Pi? | 0.25° vs clipped high-res regional |
| OQ-6 | Include rig load cells in training labels? | If available on N2K |

---

## 16. References

- [Signal K specification](https://signalk.org/specification/)
- [Signal K server](https://github.com/SignalK/signalk-server)
- [PiCAN-M documentation](https://copperhilltech.com/content/pican-m_UGB_10.pdf)
- [Google Coral NPU](https://github.com/google-coral/coralnpu)
- [InfluxDB documentation](https://docs.influxdata.com/)
- [Neo4j documentation](https://neo4j.com/docs/)
- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [Open GoPro specification](https://gopro.github.io/OpenGoPro/)
- [Open GoPro Python SDK](https://gopro.github.io/OpenGoPro/python_sdk/)
- [cfgrib documentation](https://ecmwf.github.io/cfgrib/)
- [pyais](https://github.com/M0r13n/pyais)
- [GoPro HERO13 Black](https://gopro.com/en/us/shop/cameras/hero13-black/CHDHX-131-master.html)
- [CogSail Python (prior art)](https://github.com/cognite-fholm/cogsail-python)
- [iRegatta User Manual v2.86](https://zifigo.com/sites/default/files/iRegattaUserManual.pdf) — functional reference for race/start/layline UX ([ADR-0010](./adr/0010-iregatta-reference-model.md), [§7.16](./spec.md#716-iregatta-reference-model--feature-traceability))
- [B&G H5000 Operation Manual 988-10630-003](https://cxjdfr.files.cmp.optimizely.com/download/assets/en-us-H5000_OM_EN_988-10630-003_w.pdf/f9fdbcee044d11f0a251baecc01b2173) — instrument, SailSteer, StartLine, calibration ([ADR-0011](./adr/0011-bg-h5000-reference-model.md), [§7.17](./spec.md#717-bg-h5000-reference-model--integration))
- [Zifigo / Let's Create — iRegatta](https://zifigo.com/)

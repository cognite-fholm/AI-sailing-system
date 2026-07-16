# Complete system diagram — AI Sailing System

Single-page map of **repositories**, **hardware**, **services**, **data flows**, and **integrations** (including the Expedition nav laptop and Home Assistant domotics). Normative detail: [spec.md](../spec.md) · [ARCHITECTURE.md](./ARCHITECTURE.md) · [EQUIPMENT_LIST.md](./EQUIPMENT_LIST.md) · [adr/README.md](../adr/README.md).

**Last updated:** 2026-07-16

---

## Legend

| Symbol | Meaning |
|--------|---------|
| **Solid line** | Data path in production design |
| **Dashed line** | Optional, remote, or human workflow |
| **Green / implemented** | Service exists in repo + compose today |
| **Amber / partial** | Scaffold or library without full spec behaviour |
| **Grey / planned** | Normative in spec; not built yet |

---

## 1. System context (who talks to whom)

```mermaid
flowchart TB
  subgraph shore [Shore — before and after race]
    CURSOR[Cursor + agents]
    SKILLS[Data-repo skills\nManage2Sail · ORC · weather]
    SHACL[GitHub Actions\nYAML-LD + SHACL CI]
    CURSOR --> SKILLS
    SKILLS --> DATA_REPO
    DATA_REPO[AI-sailing-data Git] --> SHACL
  end

  subgraph cloud [Cloud]
    GH_SYS[AI-sailing-system Git]
    GHCR[GHCR container images]
    GHA[GitHub Actions CI]
    GH_SYS --> GHA --> GHCR
  end

  subgraph boat [Boat — race week]
    CREW[Crew + H5000 displays]
    N2K[NMEA 2000 bus]
    PI1[SLA-1 Pi\ntelemetry.local]
    PI2[SLA-2 Pi\nrace.local]
    PI3[SLA-3 Pi\nvision.local]
    ROUTER[Teltonika LTE + Wi‑Fi]
    N2K --> PI1
    PI1 --> PI2
    PI2 --> PI3
    ROUTER --> PI1
    ROUTER --> PI2
    ROUTER --> PI3
    CREW --> N2K
  end

  subgraph nav_laptop [Nav laptop — Windows]
    EXP[Expedition]
    EBR[expedition-bridge]
    SK_LAP[Signal K localhost]
    EXP --> EBR --> SK_LAP
  end

  DATA_REPO -->|git pull harbor| PI2
  PI2 -->|race-live-sync 5 min| DATA_REPO
  GHCR -->|harbor-pull| PI1
  GHCR -->|harbor-pull| PI2
  nav_laptop -->|Wi‑Fi boat LAN| ROUTER
  EBR -->|federate race.expedition.*| PI1
  CURSOR -.->|MCP VPN/Wi‑Fi| PI2
```

---

## 2. Physical deployment on the boat

```mermaid
flowchart TB
  subgraph deck [Deck / mast / nav station]
    H5000[B&G H5000 CPU + displays\nprimary instruments + safety audio]
    AIS_RX[AIS receiver]
    AUTOPILOT[Autopilot N2K\nread-only ingest]
    GOPRO[GoPro HERO13 fleet]
  end

  subgraph nav_table [Nav table]
    LAPTOP[Windows laptop\nExpedition + expedition-bridge + SK]
    TABLET[Helm tablet\nrace-ui planned]
    PHONE[Phone\noptional iRegatta]
  end

  subgraph rack [Below deck — Pi rack]
    PICAN[Pi 5 + PiCAN-M\nSLA-1]
    PI_RACE[Pi 5 8GB\nSLA-2 + Home Assistant]
    PI_VIS[Pi 5 + Coral\nSLA-3]
  end

  subgraph domotics [Non-NMEA — Zigbee / Wi‑Fi / Modbus]
    LIGHTS[Cabin & deck lights]
    RELAYS[Relays / pumps]
    HOUSE[House power / climate]
  end

  LIGHTS --> PI_RACE
  RELAYS --> PI_RACE
  HOUSE --> PI_RACE

  subgraph network [Teltonika RUT]
    LTE[LTE modem]
    WIFI[Wi‑Fi AP boat-race]
    DNS[DNS:\ntelemetry.local · race.local · vision.local]
  end

  H5000 -->|NMEA 2000| PICAN
  AIS_RX -->|N2K| PICAN
  AUTOPILOT -->|N2K| PICAN
  PICAN -->|Ethernet| WIFI
  PI_RACE -->|Ethernet| WIFI
  PI_VIS -->|Ethernet| WIFI
  LAPTOP -->|Wi‑Fi| WIFI
  TABLET -->|Wi‑Fi| WIFI
  PHONE -.->|Wi‑Fi NMEA| PICAN
  GOPRO -->|Wi‑Fi| PI_VIS
  LTE --> WIFI
```

**Golden rule ([ADR-0002](../adr/0002-three-tier-sla-architecture.md)):** SLA-1 telemetry keeps running if SLA-2 or SLA-3 fail.

---

## 3. Services by host

### SLA-1 — `telemetry.local` (implemented)

```mermaid
flowchart LR
  N2K[NMEA 2000 / 0183] --> SK[signalk-server :3000]
  SK --> BR[signalk-influx-bridge]
  SK --> CSP[course-sk-sync]
  SK --> SPP[signalk-polar-performance]
  BR --> IFX[(InfluxDB)]
  CSP -->|reads YAML waypoints| DATA[(AI-sailing-data mount)]
  SPP -->|GET /polars/.../target| PM_REF[polar-manager on SLA-2]
  IFX --> GF1[grafana-telemetry :3001]
```

| Service | Status | Role |
|---------|--------|------|
| `signalk-server` | Implemented | Marine hub; `@signalk/course-provider` |
| `signalk-influx-bridge` | Implemented | Telemetry → Influx `signalk` bucket |
| `course-sk-sync` | Implemented | WaypointList YAML → `navigation.course` |
| `signalk-polar-performance` | Implemented | `performance.polarSpeed*` paths |
| `grafana-telemetry` | Implemented | History / instrument panels |

### SLA-2 — `race.local` (mixed)

```mermaid
flowchart TB
  subgraph implemented [Implemented today]
    NEO[(Neo4j)]
    RIMP[race-import]
    RDS[race-data-sync]
    RLC[race-lifecycle]
    RLS[race-live-sync]
    PM[polar-manager]
    AIS[ais-collector]
    GRIB[grib-model-scorer v1]
    FPT[fleet-performance-tracker]
    GW[race-mcp-gateway :3100]
  end

  subgraph domotics [Domotics — ADR-0035]
    HA[home-assistant :8123]
    IOT[Zigbee / Shelly / Modbus]
    IOT --> HA
  end

  subgraph planned [Planned — spec normative]
    RI[race-intelligence]
    LR[live-results]
    UI[race-ui]
    GF2[grafana-race]
    COACH[tactical-coach]
    ALERTS[insight-alerts]
    GRIB_IN[grib-ingest / parser]
    WIND[wind-field-analyzer]
    CE[course-editor]
  end

  DATA[(AI-sailing-data)] --> RDS --> RIMP --> NEO
  RLS --> NEO
  RLS -->|git push| GH[(GitHub)]
  SK1[SLA-1 Signal K] --> AIS
  SK1 --> FPT
  PM --> SK1
  GW --> NEO
  GW --> IFX[(Influx SLA-1)]
  GW --> SK1
  RI -.-> SK1
  LR -.-> NEO
  LR -.-> GF2
```

| Service | Status | Role |
|---------|--------|------|
| `race-import` | Implemented | YAML-LD Neo4j bundles → graph |
| `race-data-sync` | Implemented | Git pull data repo |
| `race-lifecycle` | Implemented | Schedule-driven harbor/race mode |
| `race-live-sync` | Implemented | Neo4j + Influx → `race-live/` git |
| `polar-manager` | Partial | ORC target-speeds API (full SLK planned) |
| `ais-collector` | Implemented | AIS → Influx `ais_tracks` |
| `fleet-performance-tracker` | Implemented | Fleet polar % timeline |
| `grib-model-scorer` | Partial | Observed-wind baseline (full GRIB planned) |
| `race-mcp-gateway` | Partial | Neo4j + Influx + Signal K MCP |
| `home-assistant` | Planned | Non-NMEA domotics — lights, climate, house power ([ADR-0035](../adr/0035-home-assistant-non-nmea-domotics.md)) |
| `race-intelligence` | Planned | Start, laylines, lift |
| `live-results` | Planned | Corrected standings |
| `race-ui` | Planned | Primary helm UX |
| `grafana-race` | Planned | Tactical dashboards |
| `tactical-coach` | Planned | Onboard LLM |

### SLA-3 — `vision.local` (planned)

GoPro capture → Coral preprocess → vision LLM → `grafana-sail` ([ADR-0003](../adr/0003-gopro-capture-and-shore-training.md)).

### Nav laptop — Windows (new)

```mermaid
flowchart LR
  EXP[Expedition UI + ExpDLL] --> EBR[expedition-bridge]
  EBR -->|PUT race.expedition.*| SKL[Signal K :3000 localhost]
  EBR -->|dual_publish| SK1[telemetry.local Signal K]
  SK1 -.->|instrument mirror read| SKL
```

See [ADR-0034](../adr/0034-expedition-laptop-signalk-federation.md) · [SIGNALK_RACE_EXTENSION.md](./SIGNALK_RACE_EXTENSION.md).

### Shore — SLA-S + dev

| Host | Services | Status |
|------|----------|--------|
| **Dev laptop** | `docker-compose.sla-1.yml` + `sla-2.yml` + `dev.yml` | Local emulation |
| **Gaming PC** | TrimTransformer training (`shore/docker-compose.sla-shore.yml`) | Planned Phase 5 |
| **GitHub** | CI, SHACL (data repo), GHCR publish | Active |

---

## 4. Dual-repository data model

```mermaid
flowchart TB
  subgraph data_repo [AI-sailing-data — facts in Git]
    YAML[boats/ races/ YAML-LD]
    SHACL_SH[schema/shacl]
    NEOJ[neo4j/ import templates]
    OKF[okf/ advisory Markdown]
    LIVE[race-live/ during race]
    POST[post-race/ after finalize]
    CTX[schema/yaml-ld/context.jsonld]
  end

  subgraph shore_ci [Shore CI only]
    VAL[validate_yaml_ld.py + pySHACL]
    DQ[dq-report/]
    YAML --> VAL
    SHACL_SH --> VAL
    VAL --> DQ
  end

  subgraph runtime [Boat runtime]
  NEO[(Neo4j SLA-2)]
  end

  YAML -->|race-import MERGE| NEO
  NEO -->|race-live-sync| LIVE
  NEO -->|finalize| POST
  OKF -.->|shore export TTL| OKF_EXP[okf-export/]
```

| Layer | Artifact | Runs where |
|-------|----------|------------|
| Facts | `boats/`, `races/` YAML-LD | Git; edited on shore |
| Constraints | SHACL shapes | Shore CI only |
| Runtime graph | Neo4j | SLA-2 Pi |
| Advisory | OKF / Vault-LD | Shore; not Neo4j import |
| Temporal | `race-live/` → `post-race/` | Git via `race-live-sync` |

Detail: [DATA_SCHEMA.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md) (data repo).

---

## 5. End-to-end data flows

### 5.1 Instruments (race hour)

```mermaid
sequenceDiagram
  participant N2K as NMEA 2000 / H5000
  participant SK as SLA-1 Signal K
  participant IFX as InfluxDB
  participant PM as polar-manager
  participant SPP as signalk-polar-performance
  participant GF as Grafana telemetry

  N2K->>SK: wind, BSP, GPS, depth
  SK->>IFX: signalk-influx-bridge
  PM->>SPP: target BSP / angle
  SPP->>SK: performance.polarSpeed*
  SK->>GF: WebSocket / dashboards
```

### 5.2 Race prep → harbor → start

```mermaid
sequenceDiagram
  participant Shore as Shore Cursor
  participant Git as GitHub data repo
  participant RDS as race-data-sync
  participant RIMP as race-import
  participant NEO as Neo4j
  participant CSP as course-sk-sync
  participant SK as Signal K

  Shore->>Git: push YAML-LD fleet + race
  RDS->>Git: git pull at harbor
  RIMP->>NEO: MERGE boats / courses / fleet
  CSP->>SK: navigation.course from WaypointList
```

### 5.3 During race — live sync + Expedition

```mermaid
sequenceDiagram
  participant EXP as Expedition laptop
  participant EBR as expedition-bridge
  participant SKL as Laptop SK
  participant SK1 as Pi Signal K
  participant NEO as Neo4j
  participant RLS as race-live-sync
  participant Git as GitHub

  EXP->>EBR: ExpDLL poll 1 Hz
  EBR->>SKL: race.expedition.*
  EBR->>SK1: federate race.expedition.*
  NEO->>RLS: standings / course snapshot
  RLS->>Git: race-live/current.yaml every 5 min
```

### 5.4 After race

```mermaid
flowchart LR
  NEO[(Neo4j)] -->|finalize| RLS[race-live-sync]
  RLS --> POST[post-race/*.yaml on main]
  POST --> SHACL[SHACL CI]
  POST --> ANALYSIS[Shore debrief / agents]
```

---

## 6. Signal K namespace map

Canonical instruments stay standard Signal K. Extensions:

```mermaid
flowchart LR
  subgraph sla1_paths [SLA-1 canonical]
    NAV[navigation.*]
    ENV[environment.wind.*]
    PERF[performance.polarSpeed*]
    COURSE[navigation.course.*]
  end

  subgraph expedition_paths [Laptop → federated]
    EXP_R[race.expedition.start.*]
    EXP_L[race.expedition.laylines.*]
    EXP_T[race.expedition.targets.*]
    EXP_W[race.expedition.routing.*]
  end

  subgraph tactical_paths [SLA-2 planned]
    TAC[race.tactical.start.*]
    STAND[race.tactical.standings.*]
    ALERT[race.tactical.alert.*]
  end

  EBR[expedition-bridge] --> EXP_R
  EBR --> EXP_L
  RI[race-intelligence] -.-> TAC
  LR[live-results] -.-> STAND
```

Full path table: [SIGNALK_RACE_EXTENSION.md](./SIGNALK_RACE_EXTENSION.md).

---

## 7. Helm and UX surfaces

```mermaid
flowchart TB
  subgraph primary [Primary helm — human]
    H5000[B&G H5000 displays\ninstruments + safety audio]
    EXP_UI[Expedition laptop\nrouting + pro start]
  end

  subgraph secondary [Secondary — Pi stack]
    GF1[grafana-telemetry :3001]
    GF2[grafana-race :3002 planned]
    UI[race-ui tablet planned]
  end

  subgraph advisory [Advisory]
    MCP[Cursor + race-mcp-gateway]
    COACH[tactical-coach planned]
    TTS[Tactical speaker TTS planned]
  end

  SK[Signal K SLA-1] --> H5000
  SK --> GF1
  SK --> GF2
  SK --> UI
  EXP_UI --> EBR[expedition-bridge] --> SK
  MCP --> GW[race-mcp-gateway]
  COACH -.-> GW
```

| Surface | Reference product | Status |
|---------|-------------------|--------|
| H5000 | B&G H5000 | Hardware on boat |
| Expedition | Expedition Marine | Nav laptop |
| `race-ui` | iRegatta parity | Planned |
| Grafana race | H5000 / iRegatta pages | Planned |
| Cursor MCP | Beyond reference products | Partial |

---

## 8. Shore preparation pipeline

```mermaid
flowchart LR
  subgraph portals [Fleet portals]
    M2S[manage2sail]
    SRS[sailracesystem]
  end

  subgraph orc [ORC]
    ORC_SKILL[orc-sailor-services]
    CERTS[boats/certificates/]
  end

  subgraph wx [Weather]
    MET[metno GRIB]
    CUR[oslofjord currents]
    SMHI[SMHI validation]
  end

  subgraph out [Race bundle]
    FLEET[fleet.yaml]
    RACE[race.yaml]
    PLAN[planning/*.yaml]
    GPX[export/marine-map/]
  end

  M2S --> FLEET
  SRS --> FLEET
  FLEET --> ORC_SKILL --> CERTS
  RACE --> MET
  RACE --> CUR
  RACE --> SMHI
  FLEET --> RACE --> PLAN
  PLAN --> GPX
```

Guide: [RACE_PREPARATION_GUIDE.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md).

---

## 9. Network and remote access

```mermaid
flowchart TB
  subgraph internet [Internet]
    GH[GitHub]
    LTE_NET[LTE carrier CGNAT]
  end

  subgraph boat_lan [Boat LAN 192.168.x.x]
    RUT[Teltonika RUT]
    SK1[telemetry.local:3000]
    RACE[race.local:7474 / :3100 / :3002]
    VIS[vision.local]
    LAP[Nav laptop]
  end

  subgraph remote [Remote crew / shore]
    NAV_PC[Navigator laptop Cursor]
    VPN[Tailscale / RMS VPN optional]
  end

  LTE_NET <--> RUT
  RUT --> SK1
  RUT --> RACE
  RUT --> LAP
  RACE -->|race-live-sync| GH
  NAV_PC --> VPN --> RUT
  NAV_PC -->|boat Wi‑Fi| RACE
```

Docs: [vpn-remote-access.md](./vpn-remote-access.md) · [race-laptop-mcp.md](./race-laptop-mcp.md).

---

## 10. Implementation status summary

| Area | Today | Next |
|------|-------|------|
| SLA-1 telemetry pipeline | Signal K, Influx, polar %, course sync | PiCAN / H5000 ingest configured |
| SLA-2 data plane | Neo4j import, sync, lifecycle, live-sync, AIS, fleet polar % | `live-results`, `race-intelligence` |
| SLA-2 tactical UX | — | `race-ui`, `grafana-race` |
| Expedition integration | `expedition-bridge` scaffold + spec | Windows deploy + federation test |
| Shore data | YAML-LD, SHACL, DQ, ORC skills | Onboard GRIB ingest |
| SLA-3 vision | Spec only | GoPro + Coral stack |

Detail table: [ARCHITECTURE.md § Implementation status](./ARCHITECTURE.md).

---

## Related documents

| Document | Topic |
|----------|--------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Narrative architecture + ADR index |
| [spec.md](../spec.md) | Normative requirements |
| [USER_GUIDE.md](./USER_GUIDE.md) | Crew-facing overview |
| [SIGNALK_RACE_EXTENSION.md](./SIGNALK_RACE_EXTENSION.md) | `race.expedition.*` / `race.tactical.*` paths |
| [ADR-0034](../adr/0034-expedition-laptop-signalk-federation.md) | Expedition laptop federation |
| [deploy/README.md](../deploy/README.md) | Env files and harbor deploy |
| [DEV-SETUP.md](./DEV-SETUP.md) | Windows/WSL Docker setup |

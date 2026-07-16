# Equipment list — hardware and software to buy

What you need to purchase or license for the **AI Sailing System** regatta deployment (race profile) and shore preparation. Normative detail: [spec §4](../spec.md#4-hardware-and-deployment-profiles) · [ADR-0018](../adr/0018-helm-ux-three-pi-dual-speaker.md) · [SYSTEM_DIAGRAM.md](./SYSTEM_DIAGRAM.md). **Victron:** [ADR-0036](../adr/0036-victron-vecan-nmea2000-power.md) · **Domotics:** [ADR-0035](../adr/0035-home-assistant-non-nmea-domotics.md).

**Last updated:** 2026-07-16

---

## How to read this list

| Column | Meaning |
|--------|---------|
| **Qty** | Typical for one boat (NOR-10133 / Xbox class) |
| **Status** | `Required` · `Recommended` · `Optional` · `Phase 3+` · `Shore only` |
| **Indic. NOK** | Rough retail in Norway, **incl. VAT** unless noted — July 2026 |
| **Indic. EUR** | Same item, ex-VAT or EU retail equivalent — **not a currency conversion** |

**Prices are indicative only** — shop around (Proshop, Komplett, RS, marine chandlers, Copperhill, Teltonika partners). Exchange reference: **1 EUR ≈ 11.5 NOK** (round numbers used below).

**Already on boat:** Items you may already own are listed separately — only buy gaps.

**Software:** Many stack components are **free/open source**. Paid items are called out explicitly.

---

## 1. Already on boat (assumed — verify gaps)

Typical for a competitive ORC boat with B&G instrumentation. **Do not duplicate** unless missing.

| Item | Role in stack | Buy if missing? | Indic. NOK (if new) | Indic. EUR |
|------|---------------|-----------------|---------------------|------------|
| **B&G H5000** (CPU + displays) | Instruments, true wind, start line, **safety audio** | Core to project | 25 000–80 000+ | 2 500–7 000+ |
| **NMEA 2000 backbone** + terminators + drops | PiCAN integration | Required | 2 000–8 000 | 180–700 |
| **Wind, speed, depth, GPS** on N2K | Telemetry | Usually on H5000 fit-out | (included) | — |
| **Autopilot** (N2K) | Read-only ingest | Optional for data | 15 000–40 000 | 1 300–3 500 |
| **AIS transponder** (Class B) | Fleet tracks → `ais-collector` | Often installed | 3 000–8 000 | 260–700 |
| **12 V house / instrument battery** | Powers N2K + Pi rack | Boat standard | — | — |
| **Victron power system** (Cerbo, Lynx, Multi/Quattro) | House bank monitoring + charging | Often installed | 30 000–150 000+ | 2 600–13 000+ |
| **[VE.Can → NMEA 2000 cable](https://www.victronenergy.com/cables/ve-can-to-nmea2000-micro-c-male)** | Bridge Victron to PiCAN backbone | Required for N2K ingest | 600–1 200 | 50–100 | See [ADR-0036](../adr/0036-victron-vecan-nmea2000-power.md) |

---

## 2. Core onboard — three-Pi race profile (required)

[ADR-0018](../adr/0018-helm-ux-three-pi-dual-speaker.md) — **one Raspberry Pi per SLA tier** for regattas.

### 2.1 Computers

| Item | Qty | Status | Indic. NOK (unit) | Indic. EUR (unit) | Notes |
|------|-----|--------|-------------------|-------------------|-------|
| **Raspberry Pi 5** (4 GB) | 1 | Required | 1 100–1 700 | 95–145 | **SLA-1** telemetry only |
| **Raspberry Pi 5** (8 GB) | 2 | Required | 1 200–2 600 | 100–220 | **SLA-2** + **SLA-3** |
| **Pi 5 official 27 W USB-C PSU** | 3 | Required | 200–350 | 18–30 | Or marine 5 V DC-DC per node |
| **NVMe 128 GB + Pi 5 active cooler case** | 3 | Required | 600–1 200 | 50–100 | Preferred over microSD for Neo4j/Influx |
| **Heatsink / active cooling** | 3 | Recommended | 150–300 | 15–25 | Summer cockpit |

**Subtotal §2.1 (3 nodes):** ~**6 500–14 000 NOK** · **€560–1 200**

### 2.2 SLA-1 marine I/O (telemetry Pi only)

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **[PiCAN-M HAT](https://copperhilltech.com/product/pican-m-nmea-0183-nmea-2000-hat-for-raspberry-pi/)** + 3 A SMPS | 1 | Required | 1 400–1 800 | 120–155 | N2K + 0183; 12 V from N2K branch |
| **Micro-C male drop cable** (N2K → PiCAN) | 1 | Required | 200–400 | 18–35 | |
| **NMEA 2000 terminators** | 2 | Required | 300–600 ea. | 25–50 ea. | Only if backbone lacks them |
| **RS-422 wiring** (0183 talker) | — | Optional | 100–300 | 10–25 | Screw terminal J3 |

Reference: [validation_plan.md](./validation_plan.md) · [PiCAN-M user guide](https://copperhilltech.com/content/pican-m_UGB_10.pdf)

**Subtotal §2.2:** ~**2 200–3 600 NOK** · **€190–310**

### 2.3 Networking (required)

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **Teltonika industrial LTE router** (RUTX/RUT9xx) | 1 | Required | 4 000–8 000 | 350–700 | Boat LAN hub — [spec §4.4](../spec.md#44-network--teltonika-lte-router) |
| **LTE SIM** (data plan) | 1 | Required | 200–500 /mo | 20–45 /mo | `race-live-sync`, harbor `git pull`, GRIB |
| **Gigabit Ethernet switch** (5–8 port) | 1 | Recommended | 300–800 | 25–70 | Pis + router; wired preferred |
| **Cat6 Ethernet cables** | 3+ | Recommended | 100–200 ea. | 10–18 ea. | Short runs in dry box |
| **Wi‑Fi** | — | Included | — | — | Teltonika AP — no extra AP |

Optional: **Tailscale** on SLA-2 (software) — no extra hardware ([vpn-remote-access.md](./vpn-remote-access.md)).

**Subtotal §2.3 (excl. monthly SIM):** ~**4 700–9 400 NOK** · **€410–820**

### 2.4 Rack, power, and mounting

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **Water-resistant enclosure / dry box** | 1 | Required | 500–2 000 | 45–175 | Ventilation + cable glands |
| **12 V → 5 V DC-DC** (3× Pi + router) | 1–3 | Required | 300–800 | 25–70 | If not using per-Pi USB-C off house batt. |
| **Fused marine terminal blocks / USB** | 1 set | Recommended | 200–500 | 18–45 | |
| **Cable labels** | — | Recommended | 50–150 | 5–15 | `telemetry`, `race`, `vision`, `N2K` |

**Subtotal §2.4:** ~**1 050–3 450 NOK** · **€90–300**

### Core onboard total (§2.1–2.4)

| | NOK | EUR |
|---|-----|-----|
| **Low** | ~14 500 | ~1 250 |
| **High** | ~30 500 | ~2 630 |

---

## 3. Helm and crew displays

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **B&G H5000 displays** | — | On boat | — | — | Primary helm — safety speaker |
| **Helm tablet** (10–13″, Wi‑Fi) | 1 | Recommended | 2 500–6 000 | 220–520 | Future **`race-ui`** / Grafana (`race.local`) |
| **Tactical USB/BT speaker** | 1 | Recommended | 300–1 500 | 25–130 | Piper TTS only — **not** H5000 ([ADR-0018](../adr/0018-helm-ux-three-pi-dual-speaker.md)) |
| **USB microphone** | 1 | Optional | 300–800 | 25–70 | Not v1 |
| **iPhone + iRegatta** | 1 | Optional | (owned) | — | Parallel consumer — not replaced |
| **Large HDMI monitor** (nav station) | 1 | Optional | 2 000–5 000 | 175–435 | Harbor Grafana debrief |

**Subtotal §3 (recommended):** ~**2 800–7 500 NOK** · **€245–650**

---

## 4. Nav laptop — Expedition ([ADR-0034](../adr/0034-expedition-laptop-signalk-federation.md))

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **Windows 10/11 laptop** (64-bit, 16 GB+ RAM) | 1 | Required* | 8 000–15 000 | 700–1 300 | *Skip if you already have a suitable machine |
| **Expedition Marine license** | 1 | Required | ~15 000** | 1 250 ex VAT | [expeditionmarine.com](https://www.expeditionmarine.com/) — v12.x |
| **Expedition-Python** | — | Free | 0 | 0 | `pip install Expedition-Python` |
| **Signal K Server** on laptop | — | Recommended | 0 | 0 | Docker or native; federate to `telemetry.local` |
| **NMEA Wi‑Fi gateway for laptop** | — | **Not needed** | 0 | 0 | Use Pi Signal K over boat Wi‑Fi |

\** €1 250 ex VAT ≈ NOK 15 600 incl. 25% MVA at 11.5 NOK/EUR.

**Do not buy** a second N2K Wi‑Fi gateway for Expedition if the Pi stack is on board.

**Subtotal §4 (laptop + license, new):** ~**23 000–30 500 NOK** · **€1 950–2 550**

---

## 5. Home Assistant — non-NMEA domotics

[ADR-0035](../adr/0035-home-assistant-non-nmea-domotics.md) — **Home Assistant on SLA-2** (`homeassistant.local:8123`). Controls boat systems **not** on NMEA 2000. Marine telemetry stays on SLA-1 Signal K.

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **Zigbee 3.0 USB coordinator** (Sonoff ZBDongle-E, ConBee III) | 1 | Recommended | 400–700 | 35–60 | Plugs into SLA-2 Pi USB |
| **Shelly / ESPHome Wi‑Fi relays** | 3–10 | Recommended | 300–600 ea. | 25–50 ea. | Lights, pumps, outlets — boat LAN |
| **Z-Wave USB stick** (optional) | 1 | Optional | 500–900 | 45–80 | Only if Z-Wave devices chosen |
| **12 V relay modules** (dry contact) | 2–6 | Optional | 150–400 ea. | 15–35 ea. | Nav/anchor lights off N2K path |
| **Home Assistant** (software) | 1 | Free | 0 | 0 | Docker on SLA-2 — no extra Pi |

**Typical domains:** cabin lighting, courtesy LEDs, diesel heater, bilge float monitoring, hatch sensors, fridge temperature. **House battery monitoring** uses Victron on N2K → SLA-1 ([ADR-0036](../adr/0036-victron-vecan-nmea2000-power.md)); Cerbo **control** via HA Modbus.

**Do not buy:** N2K Wi‑Fi gateway for domotics; do not run HA on the SLA-1 PiCAN node.

**Subtotal §5 (starter kit):** ~**2 000–5 000 NOK** · **€175–435** (excluding per-circuit Shelly count)

---

## 6. Phase 3+ — sail vision (optional / later)

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **GoPro HERO13 Black** | 3–5 | Phase 3+ | 4 500–5 500 ea. | 400–480 ea. | Mast/boom imaging ([spec §7.9](../spec.md#79-gopro-hero13-black-fleet)) |
| **GoPro mounts + tethers** | 3–5 | Phase 3+ | 500–1 000 ea. | 45–90 ea. | |
| **Google Coral USB Accelerator** | 1 | Phase 3+ | 800–1 200 | 70–100 | TFLite on vision Pi |
| **USB Bluetooth 5.0 dongle** | 1–2 | Phase 3+ | 150–300 ea. | 15–25 ea. | Multi-GoPro BLE |
| **GoPro batteries + charger** | several | Phase 3+ | 1 500–3 000 | 130–260 | |

**Subtotal §6 (3-camera starter):** ~**18 000–25 000 NOK** · **€1 560–2 170**

---

## 7. Shore — development and training

| Item | Qty | Status | Indic. NOK | Indic. EUR | Notes |
|------|-----|--------|------------|------------|-------|
| **Developer laptop** | 1 | Shore only | (often owned) | — | [DEV-SETUP.md](./DEV-SETUP.md) |
| **Docker Desktop** (+ WSL2) | — | Free | 0 | 0 | Local SLA-1/2 emulation |
| **Gaming PC** (NVIDIA GPU) | 1 | Phase 5 optional | 15 000–40 000 | 1 300–3 500 | TrimTransformer training |
| **GitHub** + repos | — | Free | 0 | 0 | Public repos |
| **Cursor subscription** | — | Paid | ~250 /mo | ~20 /mo | Shore prep + boat MCP |

---

## 8. Software and services (no hardware)

### 7.1 Onboard — free / open source

| Software | SLA | License | Cost |
|----------|-----|---------|------|
| Signal K Server | 1 (+ laptop opt.) | Apache 2.0 | 0 |
| InfluxDB 2.x | 1 | OSS | 0 |
| Neo4j 5 Community | 2 | Community | 0 |
| Grafana OSS | 1–3 | AGPL | 0 |
| Docker + Compose | all Pis | Apache 2.0 | 0 |
| AI-sailing-system containers | 1–2 | Project GHCR | 0 |
| llama.cpp + models | 2 | OSS | 0 |

### 7.2 Paid or licensed software

| Software | Where | Indic. NOK | Indic. EUR | Notes |
|----------|-------|------------|------------|-------|
| **Expedition Marine** | Nav laptop | ~15 000 | 1 250 ex VAT | See §4 |
| **PredictWind** (optional) | Shore + boat | 1 000–3 000 /yr | 90–260 /yr | [ADR-0019](../adr/0019-predictwind-multi-model-grib.md) |
| **ORC certificate** | Shore | ~500–1 500 /yr | 45–130 /yr | Data in AI-sailing-data |
| **Teltonika RMS** (optional) | Cloud | 0–200 /mo | 0–18 /mo | Router remote mgmt |
| **Tailscale** (optional) | Cloud | 0 | 0 | Free tier often enough |
| **LTE data** (race week) | Boat | 200–500 /mo | 20–45 /mo | See §2.3 |

### 7.3 Explicitly not required to buy

| Item | Why |
|------|-----|
| Orca / Vakaros / chartplotter | Optional parallels; not this stack |
| Apache Jena Fuseki | Rejected for Pi ([ADR-0023](../adr/0023-shacl-neo4j-projection-no-fuseki.md)) |
| Second N2K gateway for laptop | Pi + Signal K federation |
| Cloud LLM API during race | Local-first ([spec G5](../spec.md)) |

---

## 9. Shopping checklist by phase (with budgets)

### Phase A — Minimum viable race week

| # | Item | Est. NOK | Est. EUR |
|---|------|----------|----------|
| 1 | Pi 5 (4 GB) + PiCAN-M + NVMe case + PSU | 3 500–6 500 | 300–560 |
| 2 | Pi 5 (8 GB) + NVMe case + PSU (SLA-2) | 2 000–4 000 | 175–345 |
| 3 | Teltonika router + SIM + switch + cables | 5 000–10 000 | 435–870 |
| 4 | Enclosure + DC power + labels | 1 000–3 500 | 90–300 |
| 5 | Windows laptop (if needed) + Expedition license | 23 000–30 500 | 1 950–2 550 |
| 6 | Helm tablet (recommended) | 2 500–6 000 | 220–520 |
| 7 | Tactical speaker (recommended) | 300–1 500 | 25–130 |
| 8 | Verify N2K + AIS + H5000 on boat | 0 | 0 |

| Phase A total | Low NOK | High NOK | Low EUR | High EUR |
|---------------|---------|----------|---------|----------|
| **With new laptop + Expedition** | ~37 000 | ~62 000 | ~3 200 | ~5 300 |
| **Laptop owned; buy Expedition only** | ~29 000 | ~47 000 | ~2 500 | ~4 050 |
| **All hardware; Expedition owned** | ~14 500 | ~30 500 | ~1 250 | ~2 630 |

**Runs today:** Signal K, Influx, Neo4j import, fleet AIS, polar %, live git sync, MCP, Expedition bridge (when configured).

### Phase B — Full tactical UX (software on same hardware)

- [ ] No major hardware — build `race-ui`, `grafana-race`, `race-intelligence` on existing Pis  
- [ ] Optional: defer third Pi until Phase C  

**Added hardware cost:** **0 NOK**

### Phase C — Vision (SLA-3)

- [ ] Third Pi 5 (8 GB) if deferred: **2 000–4 000 NOK** / **€175–345**  
- [ ] Coral + 3× GoPro + mounts: **~18 000–25 000 NOK** / **€1 560–2 170**

### Phase D — Shore ML (optional)

- [ ] Gaming PC: **15 000–40 000 NOK** / **€1 300–3 500**

---

## 10. Estimated bundles (indicative)

| Bundle | Contents | Est. NOK | Est. EUR |
|--------|----------|----------|----------|
| **SLA-1 kit** | Pi 5 4GB + PiCAN-M + NVMe case + PSU | 3 500–6 500 | 300–560 |
| **SLA-2 kit** | Pi 5 8GB + NVMe case + PSU | 2 000–4 000 | 175–345 |
| **SLA-3 kit** | Pi 5 8GB + NVMe case + PSU | 2 000–4 000 | 175–345 |
| **Network kit** | Teltonika + switch + 3× Ethernet + SIM (1 mo) | 5 200–10 500 | 450–910 |
| **Rack kit** | Enclosure + DC-DC + fusing + labels | 1 050–3 450 | 90–300 |
| **Nav kit** | Laptop + Expedition (if both new) | 23 000–30 500 | 1 950–2 550 |
| **Helm kit** | Tablet + tactical speaker | 2 800–7 500 | 245–650 |
| **Domotics kit** | Zigbee dongle + 4× Shelly + HA on SLA-2 | 2 000–5 000 | 175–435 |

**Rough order of spend:** Expedition + laptop (if new) → Teltonika → Pi kits + PiCAN → domotics (parallel) → GoPro/Coral (later).

---

## 11. Printable one-page checklist

*Print this section. Tick when ordered / received. Prices = Phase A mid-range estimates.*

```
AI SAILING SYSTEM — EQUIPMENT ORDER CHECKLIST          Date: ___________
Boat: _________________________   Regatta: _________________________

── CORE Pi RACK (Phase A) ──────────────────────────────────────────
[ ] Raspberry Pi 5  4 GB  (SLA-1 telemetry)          ~1 400 NOK
[ ] Raspberry Pi 5  8 GB  (SLA-2 race)               ~1 800 NOK
[ ] Raspberry Pi 5  8 GB  (SLA-3 vision — optional)  ~1 800 NOK
[ ] Pi 5 NVMe case + 128 GB NVMe  ×3                 ~2 700 NOK
[ ] Pi 5 official 27 W PSU  ×3                       ~750 NOK
[ ] PiCAN-M HAT + SMPS                               ~1 600 NOK
[ ] N2K Micro-C drop cable                           ~300 NOK
[ ] N2K terminators  ×2 (if needed)                  ~800 NOK

── NETWORK ─────────────────────────────────────────────────────────
[ ] Teltonika LTE router (RUTX/RUT9xx)                 ~6 000 NOK
[ ] LTE SIM activated (data plan)                    ~350 NOK/mo
[ ] Gigabit Ethernet switch                          ~500 NOK
[ ] Cat6 cables  ×3                                  ~450 NOK

── POWER & ENCLOSURE ───────────────────────────────────────────────
[ ] Waterproof dry box / rack enclosure              ~1 000 NOK
[ ] 12 V → 5 V DC-DC (or 3× fused USB-C)             ~500 NOK
[ ] Marine fuses / terminal blocks                   ~350 NOK
[ ] Cable labels                                     ~100 NOK

── NAV LAPTOP & SOFTWARE ───────────────────────────────────────────
[ ] Windows laptop 16 GB+ (skip if owned)            ~12 000 NOK
[ ] Expedition Marine license v12                    ~15 000 NOK
[ ] Expedition-Python installed (free)               —
[ ] Signal K on laptop (Docker, free)                —

── HELM (recommended) ──────────────────────────────────────────────
[ ] Wi-Fi tablet 10–13″                              ~4 000 NOK
[ ] Tactical BT/USB speaker (not H5000)              ~800 NOK

── VERIFY ON BOAT (do not re-buy) ──────────────────────────────────
[ ] B&G H5000 + displays
[ ] NMEA 2000 backbone + sensors
[ ] AIS transponder on N2K
[ ] 12 V instrument / house power

── HOME ASSISTANT — NON-NMEA (ADR-0035) ────────────────────────────
[ ] Zigbee 3.0 USB coordinator (SLA-2 Pi)              ~550 NOK
[ ] Shelly / ESPHome relays  ×___                        ~400 NOK ea.
[ ] Home Assistant Docker on SLA-2 (free)                —
[ ] Verify: NOT on SLA-1 / PiCAN node

── PHASE C — VISION (later) ────────────────────────────────────────
[ ] GoPro HERO13 Black  ×___                         ~5 000 NOK ea.
[ ] GoPro mounts + tethers  ×___
[ ] Google Coral USB Accelerator                     ~1 000 NOK
[ ] USB Bluetooth dongle                               ~200 NOK

── SHORE (dev machine — often owned) ─────────────────────────────────
[ ] Docker Desktop + WSL2 (free)
[ ] Cursor subscription                              ~250 NOK/mo
[ ] Gaming PC for ML training (Phase D, optional)    ~25 000 NOK

ESTIMATED PHASE A TOTAL (mid-range, new laptop):
    Hardware rack + network  ~ 22 000 NOK  (~€1 900)
    Laptop + Expedition      ~ 27 000 NOK  (~€2 350)
    Helm tablet + speaker    ~  4 800 NOK  (~€  420)
    ─────────────────────────────────────────────────
    GRAND TOTAL              ~ 54 000 NOK  (~€4 700)
    (Subtract ~12 000 NOK if laptop owned; ~15 000 if Expedition owned)

Supplier notes:
  Pi / parts:  Proshop · Komplett · RS · Kiwi Electronics
  PiCAN-M:     Copperhill Technologies (ship to NO)
  Router:      Teltonika partner / industrial supplier
  Expedition:  expeditionmarine.com or Nordic reseller

Signed off: _________________________   Budget approved: ___________
```

---

## 12. Related documents

| Document | Topic |
|----------|--------|
| [SYSTEM_DIAGRAM.md](./SYSTEM_DIAGRAM.md) | Where everything connects |
| [DEV-SETUP.md](./DEV-SETUP.md) | Shore laptop Docker setup |
| [validation_plan.md](./validation_plan.md) | PiCAN bring-up checklist |
| [deploy/README.md](../deploy/README.md) | Harbor deploy and secrets |
| [race-laptop-mcp.md](./race-laptop-mcp.md) | Laptop on boat Wi‑Fi |
| [USER_GUIDE.md](./USER_GUIDE.md) | Crew-facing overview |
| [ADR-0035](../adr/0035-home-assistant-non-nmea-domotics.md) | Home Assistant domotics boundary |
| [ADR-0036](../adr/0036-victron-vecan-nmea2000-power.md) | Victron VE.Can → N2K power ingest |

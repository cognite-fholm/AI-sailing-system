# Race decision playbook

Race-day guide for asking the right questions and turning answers into actions using `tactical-coach` and laptop Cursor + MCP.

**ADR:** [0031](../adr/0031-race-decision-intelligence-playbook.md)  
**Spec:** [§7.28](../spec.md#728-race-decision-intelligence), [§11.21](../spec.md#1121-race-decision-intelligence)

---

## Answer format to demand

For every tactical question, ask for:

1. **Recommendation now**
2. **Evidence and sources**
3. **Confidence level**
4. **Risk / invalidation trigger**
5. **Re-check timing**

This avoids generic advice and keeps decisions auditable.

---

## Core race-winning questions

### 1) Corrected-time if finished now

Prompt:

```text
If the race finished now, what are corrected-time results for our class?
Show our rank, delta to leader, and what changed in the last 15 minutes.
```

Expected evidence:

- `standings[]` / corrected seconds,
- rank delta vs previous sequence,
- course progress and VMG context.

### 2) Polar outperformers (and why)

Prompt:

```text
Who is sailing above polar right now (>105%), where are they on the course,
and what wind/current conditions are they in?
```

Expected evidence:

- `fleet_performance[]` outliers,
- position cluster / leg,
- TWS/TWA and current/wind advantage hints.

### 3) Polar underperformers (and tactical opportunity)

Prompt:

```text
Who is sailing below polar (<90%), where are they, and is this likely a lane,
current, or maneuver-cost issue?
```

### 4) Better course/speed toward mark

Prompt:

```text
Compare own boat vs top 5 competitors on VMG to next mark and course efficiency.
Who has the best mark-progress right now and why?
```

### 5) Better wind/current conditions

Prompt:

```text
Who appears to have a pressure or current advantage right now?
Separate likely wind benefit from likely current benefit.
```

### 6) Sail and trim decisions

Prompt:

```text
Given current TWS/TWA/sea state and our recent performance, what sail plan and
trim priorities should we use now: main twist/traveler/sheet, forestay tension,
jib shape? Include confidence and missing signals.
```

Use lower confidence if no direct sail-shape sensing is available.

### 7) Helm command to win (magnetic)

Prompt:

```text
Taking wind/current and next-mark geometry into account, what magnetic heading
should we steer for best true VMG and speed over next 3 minutes?
Include fallback if wind shifts by 5 degrees.
```

### 8) Start line favored end + long-tack-first

Prompt:

```text
What is the favored end now? Include bias in degrees, boat-length advantage, and
whether long-tack-first is still valid in current forecast and fleet behavior.
```

Reference concept: [thefavoredend.com long-tack-first tip](https://www.thefavoredend.com/faster/tip-of-the-day-always-sail-the-long-tack-first)

### 9) Layline and mark overshoot control

Prompt:

```text
How do we avoid overshooting the next mark? Give layline control guidance with
current drift, expected shift risk, and tack/jibe trigger margin.
```

---

## Race phase checklist

| Phase | Decision focus |
|------|-----------------|
| Pre-start | favored end, burn/gain vs line, start timing confidence |
| Upwind leg | pressure lanes, long-term shift regime, layline risk |
| Downwind leg | VMG mode, sail transitions, fleet leverage |
| Mark approach | overshoot control, current set, maneuver timing |
| Endgame | corrected-time protection vs attack mode |

---

## Tactical confidence policy

| Confidence | Meaning |
|-----------|---------|
| **High** | Multiple independent signals agree (telemetry + fleet + context, and optionally vision) |
| **Medium** | Good telemetry and fleet evidence but limited direct trim/shape evidence |
| **Low** | Sparse, stale, or contradictory data; recommendation is tentative |

Always state what data is missing when confidence is not high.

---

## Two operating modes

| Mode | Use when |
|------|----------|
| **Fast helm mode** | Need short command now (10-20 second response) |
| **Analyst mode** | Need deeper comparison and trade-off explanation |

For fast mode, ask for one command + one risk only.

---

## Post-race learning loop

After each leg, capture:

1. recommendation given,
2. action taken,
3. outcome (gain/loss),
4. likely reason.

This creates a feedback loop for sail-choice and trim heuristics in future races.

---

## Pre-race ORC optimization (winning on paper)

In ORC handicap racing, optimization starts **months before the start line**. The rating system evaluates physical measurements — so boat configuration, declared sail inventory, and certificate profile can be tuned to exploit specific rating behaviors **before** the certificate is issued.

### Certificate window and what you can still change

ORC programs and regatta **NOR/SI** state when a certificate must be issued for a target event (not the race portals — see cross-check below). **Until that deadline** you may still adjust:

| Lever | Examples |
|-------|----------|
| **Sail inventory** | Which headsails, spinnakers, and gennakers to declare and bring |
| **Declared sail areas** | e.g. reduce largest spinnaker area by a few m² before measurement submission |
| **Crew weight allocation** | Declared crew weight bands where rules allow |
| **Internal ballast / configuration** | Changes that affect CDL (Class Division Length) or time allowance |

After the deadline, the issued certificate and matched SLK polar become the rating baseline for that configuration. To race under a different profile you must **request a new certificate** reflecting the updated inventory and measurements.

### Strategic profile choice

The hardest owner/skipper decision is **which weather profile to optimize for**:

| Profile | When it wins | Trade-off |
|---------|--------------|-----------|
| **All-around** | Mixed venues and uncertain forecasts | Rarely maximizes rating advantage in any one condition band |
| **Light-air coastal** | Historical light winds, flat water, short legs | May give up heavy-air/offshore performance vs fleet |
| **Heavy-air offshore** | Strong breeze, open courses, survival-speed legs | May be over-canvassed or slow in light air |

Pick your battles: tailor the ORC certificate to the **historical reality** of your target events, not an idealized average season.

### Optimizer inputs and outputs

Manual spreadsheet work does not scale across sail combinations, fleet mixes, and forecast bands. A **`pre-race-optimizer`** (planned automation) should evaluate scenarios using:

**Inputs**

- GRIB / shore weather forecast for the regatta window ([§7.20](./spec.md#720-shore-weather--current-collection))
- Current and tidal forecast along the course
- Competitor list with ORC certificates, handicaps, and derived polars ([§7.19](./spec.md#719-orc-certificate-collection--fleet-enrichment))
- Candidate sail inventory and declared-area options
- Target event scoring mode (ToT / ToD / WRS profile)

**Outputs**

- Recommended **sail inventory to bring** and declare
- Recommended **certificate configuration** (areas, crew weight, ballast choices)
- Expected **rating impact** (CDL class, ToT/ToD, WRS TCF sensitivity)
- **Scenario comparison** — all-around vs light-air vs heavy-air profile
- Whether to **request a new certificate** before the issuance deadline

### Pre-race optimization prompts

```text
Given our target regatta, historical wind/current profile, and competitor ORC certificates,
recommend which sail inventory and declared areas to optimize for before the certificate deadline.
Compare all-around, light-air coastal, and heavy-air offshore profiles.
```

```text
Simulate corrected-time outcomes for our boat under candidate sail inventories vs the published fleet.
Which configuration maximizes expected corrected-time rank in the forecast wind band?
```

```text
We can still change declared spinnaker area and crew weight before certificate issue.
List top 3 configuration changes, expected rating delta, and certificate re-issue steps.
```

### Answer contract (pre-race)

Same five-part format as race-day decisions:

1. **Recommendation** — profile + sail inventory + certificate action (issue now / change and re-issue)
2. **Evidence** — forecast bands, fleet handicap spread, polar deltas, historical venue stats
3. **Confidence** — lower when forecast is uncertain or competitor certs are missing
4. **Risk** — wrong profile for actual race weather; measurement errors; rating protest exposure
5. **Re-check** — forecast update date, certificate deadline, fleet entry changes

### Where this lives in the data repo

Store optimization scenarios under the boat or race planning folder, e.g.:

- `boats/NOR-10133/planning/pre-race-optimization.yaml` — scenarios, candidates, chosen profile
- `races/{year}/{regatta}/planning/course-preference.yaml` — active certificate ref for the event

Link the chosen certificate to race import and polar-manager before harbor sync.

### Cross-check: Manage2Sail, SailRace System, and prep pipeline

Pre-race optimization pulls inputs from **two Norwegian regatta portals** and the **AI-sailing-data** preparation phases. Neither portal exposes certificate issuance deadlines or sail-inventory optimization — those come from ORC rules, NOR/SI, and your boat planning YAML.

| Input | Manage2Sail | SailRace System | AI-sailing-data phase / path |
|-------|-------------|-----------------|------------------------------|
| **Competitor fleet** | `regattaentry` → `fleet.yaml` (`SailNumber`, `OrcCertificateType`, `OrcDetailUrl`, `Hcp`) | Starter HTML → `fleet.yaml` (`sail_number`, `orc_ref`, `nor_rating`) | Phase **2** — skills `manage2sail` or `sailracesystem` |
| **Class / cert type** | `OrcCertificateType` per entry (e.g. `DH CL`) | Class section + `orc_ref` per boat | Must match `planning/course-preference.yaml` `certificate_type` |
| **ORC certificate PDFs** | `OrcDetailUrl` → [crawl_web](https://github.com/cognite-fholm/crawl_web) | `orc_ref` → crawl_web / ORC portal | Phase **3b** — `orc-sailor-services` |
| **Competitor polars / ratings** | Via `boats/{sail}/certificates/` after 3b/4 | Same | Phase **4** — `fleet-boat-enrichment` |
| **Weather forecast** | — | — | Phase **6** — `metno-oslofjord-weather`, GRIB plan |
| **Current forecast** | — | — | Phase **6** — `oslofjord-current-plots` |
| **SI / NOR rules** | Event/class document API + PDF download | Homepage PDF links | Phase **5** — `course-from-si`; read for **cert deadline** |
| **Certificate issue deadline** | — | — | **Manual** — record in `planning/pre-race-optimization.yaml` from NOR/SI/ORC |
| **Own sail inventory candidates** | — | — | `boats/{sail}/planning/` + `SailDecisionMatrix` YAML |
| **Scenario output / chosen profile** | — | — | `planning/pre-race-optimization.yaml` (Phase **6b**) |

**Manage2Sail example (Færder 2026):** Doublehanded class entries include `orc_certificate_type: DH CL` — optimization must use the **DH certificate and SLK** for that start, not a full-crew International cert unless you change class.

**Workflow order:**

1. Phase **2** — pull fleet from the portal that hosts the event (`race.yaml` stores `manage2sail_*` or `sailracesystem_regatta_id`).
2. Phases **3 / 3b / 4** — own boat + fleet ORC certificates and polars.
3. Phase **6** — weather and current forecasts.
4. Phase **6b** — run pre-race optimization (manual prompts now; `pre-race-optimizer` when deployed).
5. Set `planning/course-preference.yaml` `active_certificate_ref` to the **optimized certificate** before harbor import.

Portal skills: user Cursor skills **`manage2sail`** and **`sailracesystem`**. Prep orchestration: [AI-sailing-data RACE_PREPARATION_GUIDE](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md) Phase **6b**.

---

## Using your sail matrix card

A TWS/TWA card like your `NOR 10133` table is one of the best decision inputs for sail/trim calls.

How it contributes:

- Anchors recommendations to your **boat-specific** target behavior.
- Gives stable sail crossover priors when telemetry is noisy.
- Improves confidence for "wrong sail / wrong trim bucket" detection.

Operational pattern:

1. Keep the image card onboard for quick crew reference.
2. Mirror the same logic into a structured `SailDecisionMatrix` YAML in AI-sailing-data.
3. Use `config/templates/sail-decision-matrix.template.yaml` as a starter template, or the Xbox prefilled example at `config/examples/nor10133-xbox-sail-decision-matrix.yaml`.
4. Ask MCP/coach to evaluate current setup against the matrix and quantify likely gain/loss.

Quick prompt:

```text
Use our SailDecisionMatrix plus current TWS/TWA and sea state.
Confirm sail choice and top three trim actions now.
If current setup differs from matrix recommendation, estimate expected gain/loss.
```

---

## Related docs

- [race-laptop-mcp.md](./race-laptop-mcp.md)
- [race-day-command-sheet.md](./race-day-command-sheet.md)
- [mcp-neo4j-influx.md](./mcp-neo4j-influx.md)
- [USER_GUIDE.md](./USER_GUIDE.md)
- [AI-sailing-data: Race preparation guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md)
- [AI-sailing-data: Boats and certificates](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/BOATS_AND_CERTIFICATES.md)

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

## Using your sail matrix card

A TWS/TWA card like your `NOR 10133` table is one of the best decision inputs for sail/trim calls.

How it contributes:

- Anchors recommendations to your **boat-specific** target behavior.
- Gives stable sail crossover priors when telemetry is noisy.
- Improves confidence for "wrong sail / wrong trim bucket" detection.

Operational pattern:

1. Keep the image card onboard for quick crew reference.
2. Mirror the same logic into a structured `SailDecisionMatrix` YAML in AI-sailing-data.
3. Ask MCP/coach to evaluate current setup against the matrix and quantify likely gain/loss.

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

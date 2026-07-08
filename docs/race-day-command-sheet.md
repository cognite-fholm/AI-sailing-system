# Race-day command sheet

One-page prompt sheet for high-pressure racing moments.

Use with `tactical-coach` or laptop Cursor + MCP.

---

## Always require this answer format

```text
Recommendation now
Evidence
Confidence
Risk / invalidation
Re-check timing
```

---

## Start sequence

```text
What is favored end now? Include bias degrees, boat-length advantage, and if long-tack-first is still valid.
```

```text
Given current timer and speed, what is our burn-or-gain to the line and best correction in next 30 seconds?
```

---

## Upwind leg

```text
Who has best VMG/course to next mark right now (us vs top 5), and what lane should we defend or attack?
```

```text
Who is above 105% polar and below 90% polar on this leg, with likely cause (pressure/current/maneuver cost)?
```

```text
What magnetic heading should we steer for next 3 minutes for best VMG/speed, with fallback on ±5° shift?
```

---

## Mark approach

```text
How do we avoid overshooting the next mark? Give layline trigger margin, current drift impact, and no-go threshold.
```

```text
Should we tack/jibe now or hold? Quantify expected gain/loss and risk if shift/currents change.
```

---

## Sail and trim

```text
Based on TWS/TWA/sea state and our sail matrix, what sail plan and trim priorities now
(main twist, traveler, mainsheet, forestay, jib shape)?
```

```text
Is our current sail likely underpowered or overpowered for this TWS/TWA bucket? Show evidence.
```

---

## Endgame

```text
If race finished now, what are corrected-time standings, our delta to leader, and the safest/winning mode for the final leg?
```

```text
Should we protect current position or attack? Give one recommended mode and the trigger to switch.
```

---

## How your sail matrix contributes

Your attached table (TWS/TWA with sail-color bands and target values) is highly valuable:

- It is a **boat-specific prior** for sail choice and expected speed.
- It improves sail/trim recommendations when live data is noisy.
- It helps detect when you are in the wrong sail configuration for current bucket.

Best practice:

1. Keep the visual card for cockpit use.
2. Mirror the same content into structured YAML in AI-sailing-data (for MCP/coach use).

Suggested YAML shape:

```yaml
apiVersion: sailing.cognite-fholm/v1
kind: SailDecisionMatrix
metadata:
  ref: nor10133-sail-matrix-v1
spec:
  vessel_ref: nor10133
  source: "crew card"
  tws_knots: [6, 8, 10, 12, 14, 16, 20, 24]
  twa_degrees: [52, 60, 70, 75, 80, 90, 110, 120, 135, 150, 165, 180]
  sail_zone_by_twa:
    - from: 52
      to: 80
      sail: "Genoa"
    - from: 80
      to: 120
      sail: "Code55"
    - from: 120
      to: 135
      sail: "A3"
    - from: 135
      to: 180
      sail: "S2"
```

When this exists, ask:

```text
Use our SailDecisionMatrix and current TWS/TWA to confirm sail choice and trim priorities.
Flag if current setup differs from matrix recommendation and estimate gain/loss.
```

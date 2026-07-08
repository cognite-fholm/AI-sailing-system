# Race decision intelligence reference

## Full answer template

```markdown
Recommendation now:
- <action>

Evidence:
- <metric + source>
- <metric + source>

Confidence:
- <high|medium|low> because <reason>

Risk / invalidation:
- <what could make this wrong>

Re-check:
- <time/event trigger>
```

## Prompt pack

### Corrected-time projection

```text
If race finished now, show corrected-time ranking, our delta to leader,
and top 3 movers in last 15 minutes.
```

### Polar outliers

```text
List boats above 105% and below 90% polar with position cluster, leg, and TWS/TWA.
Highlight likely causes (lane/current/maneuver cost).
```

### Start favored end

```text
What is favored end now? Include bias angle, boat-length advantage, and whether
long-tack-first is still valid.
```

### Layline and mark control

```text
Give layline and mark-approach control guidance with overshoot risk, current set/drift,
and tack/jibe trigger margin.
```

### Sail and trim

```text
Recommend sail plan and trim priorities (main, traveler, mainsheet, forestay, jib shape)
for current TWS/TWA and sea state. Include confidence and missing sensors.
```

### Helm heading

```text
What magnetic heading should we steer now for best VMG/speed to next mark over 3 minutes?
Include fallback if wind shifts ±5°.
```

## Data-quality fallback phrases

Use these when evidence is weak:

- "Confidence medium: no direct sail-shape geometry in current dataset."
- "Confidence low: wind shift regime unstable; recommendation valid only for next 60-120 seconds."
- "Re-check after next tack/mark rounding or 2 minutes, whichever comes first."

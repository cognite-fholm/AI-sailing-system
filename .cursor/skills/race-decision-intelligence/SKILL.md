---
name: race-decision-intelligence
description: Converts live race telemetry and MCP outputs into actionable tactical decisions with evidence, confidence, risks, and re-check timing. Use when the user asks race-winning tactical questions about corrected-time projection, polar outliers, favored end, laylines, sail/trim, or steer heading.
disable-model-invocation: true
---

# Race Decision Intelligence

## Purpose

Answer tactical race questions in a consistent, decision-ready format.

## Required output format

For each answer, always provide:

1. Recommendation now
2. Evidence and source signals
3. Confidence (high/medium/low)
4. Risk/invalidation trigger
5. Re-check timing

Keep answers concise enough for race conditions.

## Core question families

- Corrected-time if finished now
- Polar outperformers/underperformers with position and conditions
- Mark-progress efficiency (VMG/course to next mark)
- Wind/current leverage across fleet
- Start favored end and long-tack-first implications
- Layline/mark-approach overshoot control
- Sail choice and trim priorities (main, traveler, sheet, forestay, jib shape)
- Magnetic steer heading recommendation with fallback trigger

## Confidence rules

- **High**: independent evidence aligns (telemetry + fleet + context, optionally vision)
- **Medium**: solid telemetry/fleet evidence, but missing direct trim geometry
- **Low**: sparse, stale, or conflicting data

If confidence is medium/low, explicitly say what data is missing.

## Safety and authority

- Advisory only: never imply automatic helm control.
- Explicitly mark uncertain recommendations.
- Prefer stable guidance over overfitted micro-adjustments when conditions are noisy.

## Quick prompt patterns

Use one of these compact forms:

- "If race finished now, rank + delta + last 15 min changes."
- "Who is >105% or <90% polar, where, and why?"
- "Best VMG/course to mark: us vs top competitors."
- "Favored end now, with bias degrees and boat-length advantage."
- "Layline overshoot risk and tack/jibe trigger margin."
- "Best magnetic steer heading for next 3 minutes + fallback on shift."

## Additional resources

- Decision playbook: [../../../../docs/race-decision-playbook.md](../../../../docs/race-decision-playbook.md)
- Expanded prompt and answer templates: [reference.md](./reference.md)

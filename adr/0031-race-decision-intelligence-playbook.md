# ADR-0031: Race decision intelligence playbook

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** cognite-fholm  
**Related:** [ADR-0010](./0010-iregatta-reference-model.md), [ADR-0012](./0012-race-side-mcp-laptop-cursor.md), [ADR-0015](./0015-tactical-insight-alerts-annunciation.md), [ADR-0016](./0016-fleet-polar-performance-influx.md), [ADR-0028](./0028-enriched-live-snapshot-fleet-performance-temporal.md), [docs/race-decision-playbook.md](../docs/race-decision-playbook.md)

---

## Context

The platform already computes core race data (corrected-time projections, fleet polar %, VMG leaders, wind advantage, layline/start metrics), but crews still need a repeatable way to ask high-value tactical questions and turn them into race-winning decisions.

Without a shared playbook, answers are inconsistent across:

- onboard tactical-coach,
- laptop Cursor + MCP analysis,
- post-race debrief and training loops.

---

## Decision

Standardize a **Race Decision Intelligence** layer across spec, docs, and skills.

### 1. Canonical decision question set

Define a stable, race-ready question catalog for:

- corrected-time if finished now,
- polar outperformers / underperformers and conditions,
- mark VMG/course advantage,
- wind/current advantage and leverage,
- start-line favored end and long-tack logic,
- layline and mark-approach overshoot control,
- sail and trim decisions (main, traveler, sheet, forestay, jib shape),
- steer-to-win magnetic heading recommendations with confidence and risks.

### 2. Answer contract

Each tactical answer should include:

1. **Recommendation** (what to do now),
2. **Evidence** (signals + sources),
3. **Confidence** (high/medium/low),
4. **Risk / guardrail** (what can invalidate recommendation),
5. **Next check window** (how soon to reassess).

### 3. Cross-surface parity

The same decision language and questions must be usable in:

- `race-live` 5-minute snapshots,
- MCP-driven ad hoc analysis,
- tactical-coach prompts,
- race and post-race user guides.

---

## Rationale

- Converts raw analytics into executable race actions.
- Reduces operator cognitive load under time pressure.
- Makes debrief loop measurable by comparing recommendation vs outcome.

---

## Consequences

### Positive

- Better tactical consistency during races.
- Stronger bridge between onboard decisions and post-race learning.
- Easier onboarding for crew and shore support.

### Trade-offs

- Requires disciplined prompt/answer style to stay concise.
- Some sail-trim recommendations remain confidence-limited unless SLA-3 vision and rig sensors are present.

---

## Implementation

- Spec additions:
  - `§7.28 Race decision intelligence`
  - FR coverage in `§11.21`
- Docs:
  - `docs/race-decision-playbook.md`
  - cross-links from user and laptop MCP guides
- Skills:
  - `.cursor/skills/race-decision-intelligence/SKILL.md`
  - `.cursor/skills/race-decision-intelligence/reference.md`
- BDD:
  - `tests/bdd/features/phase_02f_race_decision_intelligence.feature`

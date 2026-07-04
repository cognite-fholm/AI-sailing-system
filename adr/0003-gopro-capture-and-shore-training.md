# ADR-0003: GoPro HERO13 fleet capture and onshore TrimTransformer training

**Status:** Accepted  
**Date:** 2026-07-04  
**Deciders:** cognite-fholm  
**Related:** [ADR-0002](./0002-three-tier-sla-architecture.md), [spec.md §7.9–7.11](../spec.md#79-gopro-hero13-black-fleet)

---

## Context

SLA-3 must capture **sail and boom configuration** imagery with sufficient quality to measure **angles and shapes**, compare against **historically best trim in similar conditions**, and feed a **shore-side training pipeline** that learns optimal settings across the full condition space.

Requirements:

1. Multiple synchronized viewpoints (mast, boom, bow).
2. Programmatic trigger from the vision Pi without crew handling cameras.
3. Tight alignment between images and SLA-1 telemetry.
4. Onboard comparison without internet.
5. Periodic harbor export to train larger **transformer models** on GPU servers.
6. Deploy learned models back to the boat.

Generic USB cameras lack waterproof mounts, wide FOV options, and a documented machine API. **GoPro HERO13 Black** supports the official **Open GoPro** BLE/Wi-Fi API and is already used in marine-adjacent edge workflows.

---

## Decision

### Onboard (SLA-3)

1. Use **3–5 GoPro HERO13 Black** cameras per boat, controlled by `gopro-orchestrator` via **Open GoPro Python SDK**.
2. **BLE** for shutter trigger and health; **Wi-Fi station mode** on boat LAN for JPEG download to `media-ingest`.
3. Process images through **Coral TFLite** (ROI) → **`sail-geometry`** (angles/metrics) → **`condition-matcher`** (k-NN + neural predictor) → **vision LLM** (narrative).
4. Store **`BestTrimSnapshot`** and **`SailGeometry`** in SLA-2 Neo4j for condition-similarity lookup.
5. Harbor-only **`training-export`** builds multimodal bundles with explicit **opt-in consent**.

### Onshore (SLA-S)

1. Train **TrimTransformer** — multimodal model with telemetry encoder + multi-view vision encoder + cross-attention fusion.
2. Predict **`OptimalTrim`** vector: boom angle, mast heel, draft position, camber, twist, vang/cunningham/outhaul proxies.
3. Label from top-decile VMG segments, expert annotation, and LLM-assisted pre-labeling.
4. Quantize to **ONNX INT8** (`trim-predictor-lite`) for SLA-3 edge inference.
5. Publish **`BestTrimSnapshot`** sets back to boat Neo4j after each training round.

---

## Rationale

### Why GoPro HERO13 (not USB/CSI)?

| Factor | GoPro HERO13 | USB camera |
|--------|--------------|------------|
| API | Open GoPro (official) | V4L2 only |
| Waterproof | Native marine mounts | Requires housing |
| Resolution | 27 MP stills | Typically lower |
| Fleet BLE/Wi-Fi | Documented | Per-device USB hub |
| Known issues | BLE wake bug (mitigated by power policy) | Cable vibration |

### Why separate geometry service before LLM?

- **Angles** (boom, draft %, twist) need reproducible numeric outputs for Grafana and training labels — not LLM hallucination.
- Coral + OpenCV pipeline is fast and runs without GPU.
- Vision LLM adds qualitative narrative on top of structured metrics.

### Why condition similarity + transformer?

- **k-NN on Neo4j** works offline immediately with sparse historical data.
- **TrimTransformer** generalizes to unseen condition combinations as fleet data grows.
- Hybrid: neural predictor when artifact present; k-NN fallback when offline or low confidence.

### Why shore training (not on Pi)?

- Multi-view ViT + temporal encoder requires **GPU memory** impractical on Pi 5.
- Training is **harbor-only**; inference is quantized on SLA-3.
- Aligns with FR-31: no off-device transfer without opt-in export.

---

## Consequences

### Positive

- Repeatable, API-driven capture during races.
- Measurable trim metrics comparable across sessions.
- Clear path from logged data → shore training → edge deployment.
- Best-trim coaching grounded in own boat's historical performance.

### Negative

- **4–5 GoPros** add cost, charging, and mount maintenance.
- BLE fleet management complexity (dongles, wake bug).
- Large harbor exports (JPEG + telemetry) need storage planning.
- TrimTransformer needs sufficient labeled sessions before outperforming k-NN.

### Risks

| Risk | Mitigation |
|------|------------|
| GoPro battery dies mid-race | Pre-race checklist; scheduled stills reduce drain vs video |
| Timestamp drift | Fuse EXIF + NTP + Influx interpolation |
| Overfitting to one regatta | Train/val/test split by **session**, not frame |
| Bad auto-labels from VMG | Expert review queue in `dataset-curator` |

---

## Alternatives considered

### A. Continuous video + frame extraction

**Rejected.** Higher storage and Pi decode load; still photos sufficient for geometry at 0.2–1 Hz.

### B. Train only on Pi (no shore)

**Rejected.** Cannot fit multi-view transformer training on arm64 Pi; shore pipeline required for quality targets.

### C. Cloud SaaS vision API

**Rejected.** Offline requirement and data ownership; all inference local.

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-04 | Initial accepted decision |

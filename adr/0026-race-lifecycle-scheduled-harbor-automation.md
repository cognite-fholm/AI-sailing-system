# ADR-0026: Race lifecycle — scheduled harbor automation from active race context

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [ADR-0025](./0025-race-live-sync-github-temporal.md), [spec §7.25](../spec.md#725-race-lifecycle-automation), [spec §11.18](../spec.md#1118-race-lifecycle-automation)

---

## Context

Harbor setup today is **manual**: crew sets `index.yaml` active regatta, copies `race.env`, configures `GITHUB_TOKEN`, runs `race-import`, and flips `RACE_MODE` at the start gun. We already know **when the race starts** from shore prep (`race.yaml`, portal SI, Manage2Sail).

[ADR-0025](./0025-race-live-sync-github-temporal.md) added continuous `race-live-sync` on LTE. The missing piece is **orchestration**: tie schedule, active race context, import, race mode, live sync, and finalize into one automated state machine.

Goals:

1. **Single active race context** — boat services resolve regatta from `index.yaml` (no hand-editing three config files).
2. **Schedule-driven transitions** — warning signal, start, live sync enable, finalize from `race.yaml` `spec.schedule`.
3. **Automatic harbor deploy** — pull, active-context sync, `race-import` at `harbor_sync_at` without crew SSH.
4. **Secrets stay manual once** — `GITHUB_TOKEN` installed before the regatta; lifecycle only toggles **policy**, not credentials.

---

## Decision

### 1. Active race context (single source of truth)

| Layer | Source | Consumers |
|-------|--------|-----------|
| **Authoritative** | `AI-sailing-data/index.yaml` → `spec.active.regatta_id` + race entry `path` | Shore prep, agents |
| **Boat runtime** | `config/data-repo.yaml` → `active` (synced from index on each data pull) | `race-import`, `race-live-sync`, `race-lifecycle` |
| **Regatta facts** | `races/.../race.yaml` | Schedule, timezone, portal IDs |

On every `race-data-sync` pull (or `race-lifecycle` tick), run **`sync_active_context`**: read `index.yaml`, update `data-repo.yaml` `active.*` if changed.

Agents and crew set active regatta **only in `index.yaml`** during shore prep (Phase 9).

### 2. Schedule in `race.yaml`

Extend `Race` documents with optional `spec.schedule` (ISO 8601 with timezone offset or `spec.timezone` + local times):

```yaml
spec:
  timezone: Europe/Oslo
  start_date: "2026-06-12"
  schedule:
    harbor_sync_at: "2026-06-11T18:00:00+02:00"      # auto pull + import
    warning_signal_at: "2026-06-12T10:00:00+02:00"   # optional UI / Grafana
    start_at: "2026-06-12T11:00:00+02:00"            # race mode + live sync policy
    live_sync_lead_minutes: 30                         # enable push at start_at - 30m
    estimated_finish_at: "2026-06-13T04:00:00+02:00"   # open finalize window
    auto_race_mode: true
    auto_finalize: true
```

`live_sync_enable_at` = `start_at - live_sync_lead_minutes` (computed; may be written to lifecycle state for audit).

Portal skills (Manage2Sail, SailRace System) SHOULD populate `start_at` / `warning_signal_at` when the SI publishes them.

### 3. Service: `race-lifecycle` (SLA-2)

New container **`race-lifecycle`** polls every **60 s**:

1. Load `active` from `data-repo.yaml` + `race.yaml` for active path.
2. Compare `now` (UTC) to `spec.schedule` thresholds.
3. Emit phase transitions; write **`/var/run/ai-sailing/race-lifecycle.json`** (shared volume).

| Phase | Enter when | Actions |
|-------|------------|---------|
| `planned` | Before `harbor_sync_at` | No-op |
| `harbor_ready` | ≥ `harbor_sync_at` | `race-data-sync` pull; `sync_active_context`; `POST /import` |
| `armed` | ≥ `live_sync_enable_at` | Set lifecycle flags: `SYNC_AUTO_PULL=false`, `RACE_LIVE_SYNC_ENABLED=true`, `ONLINE_MODE` from LTE probe |
| `racing` | ≥ `start_at` | `RACE_MODE=true` (lifecycle env overlay); live sync active |
| `finalize_pending` | ≥ `estimated_finish_at` | `race-live-sync finalize` if `auto_finalize` |
| `archived` | After successful finalize | `RACE_MODE=false`; optional harbor pull |

**Peer services read lifecycle state** (not duplicate schedule logic):

| Service | Reads lifecycle | Behavior |
|---------|-----------------|----------|
| `race-data-sync` | `phase` | Pull only in `planned` / `harbor_ready` / post-race |
| `race-live-sync` | `phase`, `live_sync_enabled` | Push only in `armed` / `racing` |
| Watchtower / compose | `race_mode` | Frozen when `racing` |

### 4. Deployment automation (without baking secrets)

| Step | Automated | Manual (once per boat) |
|------|-----------|---------------------------|
| Harbor pull + import at schedule | Yes (`race-lifecycle`) | — |
| Switch to race mode at start | Yes | — |
| Enable live sync before start | Yes | — |
| Finalize after finish window | Yes (if `auto_finalize`) | — |
| Per-regatta env file swap | **No longer** ([ADR-0027](./0027-data-repo-runtime-policy-zero-pi-config.md)) | — |
| `GITHUB_TOKEN` on Pi | — | Once (long-lived PAT OK) |
| Digest lock / image freeze | — | System upgrade ([ADR-0008](./0008-github-docker-deployment-lifecycle.md)) |

Compose: `race-lifecycle` starts with SLA-2 stack; mounts data repo + `config/data-repo.yaml` + secrets volume.

Optional **systemd** on Pi (alternative to container): `ai-sailing-race-lifecycle.timer` — ADR prefers container for parity with other SLA-2 services.

### 5. Cloud / shore alignment

Shore agents read the same `race.yaml` schedule and `index.yaml` active entry — no boat VPN required to know **when** live sync should begin. GitHub branch `race-live/{regatta_id}` appears when boat phase reaches `armed`.

---

## Consequences

### Positive

- Harbor night is hands-off after token install
- Active race context consistent across import, live sync, MCP prompts
- Start time from prep flows to runtime — no duplicate clocks
- Composes with ADR-0025 git timeline

### Negative

| Risk | Mitigation |
|------|------------|
| Wrong `start_at` in YAML | Shore review in Phase 9; lifecycle logs next transition |
| Import before crew ready | `harbor_sync_at` default evening before; override in YAML |
| LTE down at start | Live sync best-effort; phase still `racing` |
| Auto-finalize too early | `estimated_finish_at` conservative; `auto_finalize: false` option |

---

## Implementation artifacts

| Artifact | Repository |
|----------|------------|
| `race-lifecycle` service | AI-sailing-system |
| `scripts/sync_active_context.py` | AI-sailing-system |
| `race.yaml` `spec.schedule` | AI-sailing-data |
| Spec §7.25, §11.18 | AI-sailing-system |
| Harbor / prep docs | Both repos |

---

## References

- [ADR-0009 Dual repository](./0009-dual-repository-race-data.md)
- [ADR-0025 Race live sync](./0025-race-live-sync-github-temporal.md)
- [ADR-0008 Deployment lifecycle](./0008-github-docker-deployment-lifecycle.md)
- [ADR-0027 Data-repo runtime policy](./0027-data-repo-runtime-policy-zero-pi-config.md)

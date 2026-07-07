# ADR-0027: Data-repo runtime policy — zero per-race Pi configuration

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [ADR-0025](./0025-race-live-sync-github-temporal.md), [ADR-0026](./0026-race-lifecycle-scheduled-harbor-automation.md), [spec §7.26](../spec.md#726-data-repo-runtime-policy), [spec §11.19](../spec.md#1119-data-repo-runtime-policy)

---

## Context

Crew want **minimal Pi work before a race** — rigging, sails, and instruments matter more than SSH and env files. Shore prep already produces everything needed in **AI-sailing-data**: active regatta (`index.yaml`), start times (`race.yaml` `spec.schedule`), fleet, courses, and Neo4j import bundles.

[ADR-0026](./0026-race-lifecycle-scheduled-harbor-automation.md) automated schedule-driven transitions but harbor docs still described a **per-regatta `race.env` switch** (`RACE_MODE=true`, `SYNC_AUTO_PULL=false`, …). That duplicates policy already implied by the schedule and forces manual steps on the boat.

`race-data-sync` **already** polls GitHub and pulls AI-sailing-data. The gap is treating the data repo as the **single source of runtime policy** (non-secret) while keeping **credentials** on the Pi once.

---

## Decision

### 1. One compose env file on the boat

| Before (ADR-0026 docs) | After (this ADR) |
|------------------------|------------------|
| `harbor.env` in harbor; switch to `race.env` before start | **`harbor.env` only** — never swap env files per regatta |
| Policy in env vars | Policy from **data repo** + lifecycle state |
| Per-race token setup | **Long-lived** fine-grained PAT in Docker secret (install once) |

`deploy/env/race.env` is **deprecated** for competition boats. It remains as an emergency override template for dev laptops only.

### 2. What lives where

| Concern | Source | On Pi? |
|---------|--------|--------|
| Active regatta | `index.yaml` → `spec.active.regatta_id` | Pulled by `race-data-sync` |
| Time-driven phases | `race.yaml` → `spec.schedule` | Read by `race-lifecycle` |
| Non-secret runtime knobs | `planning/runtime-policy.yaml` (optional) | Pulled with data repo |
| GitHub push/pull | Long-lived PAT | `deploy/secrets/github_token` once |
| DB / MCP passwords | Boat bootstrap | `harbor.env` (gitignored) once |
| Image versions | Release tag | `deploy/locks/current.env` when upgrading system |

**Never** commit token values, Neo4j passwords, or MCP API keys to AI-sailing-data ([data repo AGENTS.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/AGENTS.md)).

### 3. `planning/runtime-policy.yaml` (optional)

Per-regatta non-secret overrides under the active race folder:

```yaml
apiVersion: sailing.cognite-fholm/v1
kind: RuntimePolicy
metadata:
  regatta_id: faerderseilasen-2026
spec:
  sync:
    poll_interval_minutes: 60
    auto_import_on_change: true
  live_sync:
    interval_minutes: 5
  online_required: true
  mcp:
    enabled: true
  watchtower:
    enabled: false   # competition boats: manual harbor-pull only
```

Schedule fields (`harbor_sync_at`, `start_at`, `auto_race_mode`, …) stay in **`race.yaml`** — not duplicated here.

`race-lifecycle` merges `runtime-policy.yaml` into `/var/run/ai-sailing/race-lifecycle.json`. Peer services read lifecycle state; they do not parse the data repo independently.

### 4. Logical vs compose race mode

| Mechanism | Purpose |
|-----------|---------|
| Lifecycle `race_mode` in JSON | Gates data pull, live sync, finalize ([ADR-0026](./0026-race-lifecycle-scheduled-harbor-automation.md)) |
| `WATCHTOWER_NO_PULL=true` in `harbor.env` | Blocks container auto-updates on competition Pis (GR-1 without env swap) |
| `RACE_MODE` compose var | **Legacy** — omit or leave `false`; use lifecycle + `WATCHTOWER_NO_PULL` instead |

`harbor-pull.sh` refuses pull when lifecycle state has `race_mode: true` **or** `RACE_MODE=true`.

### 5. Per-regatta workflow (shore only)

1. Set `index.yaml` `spec.active.regatta_id`
2. Ensure `race.yaml` has `spec.schedule` (portal skills populate from SI)
3. Optional: edit `planning/runtime-policy.yaml`
4. `git push` to `main`

**On the Pi:** nothing — stacks keep running with `harbor.env` + installed secret.

### 6. One-time boat bootstrap

1. Clone `/opt/ai-sailing-system`, `/opt/ai-sailing-data` (or let `race-data-sync` clone data)
2. `copy deploy/env/harbor.env.example → deploy/env/harbor.env` — set passwords, `WATCHTOWER_NO_PULL=true`
3. `deploy/secrets/github_token` — fine-grained PAT, contents R/W on AI-sailing-data
4. Pin `deploy/locks/current.env` from release tag
5. `docker compose -f docker-compose.sla-*.yml --env-file deploy/env/harbor.env up -d`

No step 7 “switch to race.env” from [deploy/README.md](../deploy/README.md) (removed).

---

## Consequences

### Positive

- Pre-race Pi work reduced to physical artifacts (GRIB, GPX) and “is LTE up?”
- Shore agents and boat share identical policy via git
- Long-lived PAT matches user expectation; rotate on own schedule
- Composes with ADR-0025 live sync and ADR-0026 lifecycle

### Negative

| Risk | Mitigation |
|------|------------|
| Stale `runtime-policy.yaml` on branch | Same as any data — shore review in Phase 9 |
| Watchtower off-season updates forgotten | Explicit `harbor-pull.sh` when upgrading; documented |
| Token leak on stolen Pi | Fine-grained PAT scoped to one repo; rotate |

---

## Implementation artifacts

| Artifact | Repository |
|----------|------------|
| `planning/runtime-policy.yaml` example | AI-sailing-data |
| `race-lifecycle` loads runtime policy | AI-sailing-system |
| `harbor-pull.sh` checks lifecycle `race_mode` | AI-sailing-system |
| Unified `harbor.env.example` | AI-sailing-system |
| Deprecated `race.env.example` | AI-sailing-system |
| Spec §7.26, §11.19 | AI-sailing-system |
| Harbor / prep docs | Both repos |

---

## References

- [ADR-0026 Race lifecycle](./0026-race-lifecycle-scheduled-harbor-automation.md)
- [ADR-0025 Race live sync](./0025-race-live-sync-github-temporal.md)
- [ADR-0009 Dual repository](./0009-dual-repository-race-data.md)
- [RACE_LIFECYCLE.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIFECYCLE.md)

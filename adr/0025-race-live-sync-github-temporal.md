# ADR-0025: Race live sync — temporal Neo4j snapshots to GitHub via LTE

**Status:** Accepted  
**Date:** 2026-07-07  
**Deciders:** cognite-fholm  
**Related:** [ADR-0009](./0009-dual-repository-race-data.md), [ADR-0024](./0024-post-race-neo4j-export-to-data-repo.md), [ADR-0008](./0008-github-docker-deployment-lifecycle.md), [spec §7.24](../spec.md#724-race-live-sync-and-archive), [spec §11.17](../spec.md#1117-race-live-sync)

---

## Context

[ADR-0024](./0024-post-race-neo4j-export-to-data-repo.md) defined a **one-shot** export after the race. That loses two capabilities sailors need:

1. **Cloud AI during the race** — shore agents, Cursor, or automation reasoning over live standings and insights without VPN to the boat.
2. **Temporal playback** — reconstruct how the race unfolded from a versioned timeline, not only the final snapshot.

[ADR-0009](./0009-dual-repository-race-data.md) already pulls **shore → boat** via `race-data-sync` when LTE is up. The missing path is **boat → GitHub** during the race.

Constraints:

| Constraint | Implication |
|------------|-------------|
| Teltonika 4G/5G is intermittent | Push only when `ONLINE_MODE=true` and connectivity probe succeeds |
| Git history is the timeline | Each tick is a **commit**; no per-second files in the repo |
| Secrets must not ship in images | `GITHUB_TOKEN` injected at deploy via env file or Docker secret |
| `RACE_MODE=true` freezes containers | Live sync **continues**; only Watchtower auto-updates stay blocked |
| No telemetry dump | Same summaries as ADR-0024 — standings, course, insights, GRIB scores |

---

## Decision

### 1. Service: `race-live-sync` (SLA-2)

Replace the standalone `race-export` loop with **`race-live-sync`** — export Neo4j runtime summaries to YAML-LD, **commit**, and **push** to GitHub on a fixed interval when online.

| Mode | Trigger | Action |
|------|---------|--------|
| **Loop** (default) | Every `RACE_LIVE_SYNC_INTERVAL_MINUTES` (default **5**) when online | Export → commit → push |
| **Once** | `POST /sync` or CLI | Single tick |
| **Finalize** | After race | Write `post-race/*.yaml`, merge branch → `main`, set `race.yaml` archived |

**Direction:**

```text
Pre-race:   GitHub ──race-data-sync (pull)──► boat
During race: Neo4j ──race-live-sync (push)──► GitHub branch race-live/{regatta_id}
Post-race:  finalize ──► post-race/*.yaml on main + archived status
```

### 2. Temporal model — git commits as timeline

Each successful tick updates **two files** under `race-live/`:

```
races/{year}/{year}-{month}-{slug}/
  race-live/
    current.yaml         # kind: RaceLiveSnapshot
    sync-manifest.yaml   # kind: RaceLiveSyncManifest
```

| Field | Purpose |
|-------|---------|
| `spec.observed_at` | UTC instant of Neo4j read (ISO 8601) |
| `spec.sequence` | Monotonic integer per regatta (1, 2, 3, …) |
| `spec.race_phase` | `pre_start` \| `racing` \| `finished` |

**Playback:** `git log -- races/.../race-live/` on branch `race-live/{regatta_id}` — each commit is a point-in-time snapshot. Cloud agents read `HEAD` for latest; `git show {sha}:.../current.yaml` for history.

**No** per-tick duplicate files (`snapshots/2026-06-14T11-35.yaml`) — git object store already versions `current.yaml`.

### 3. `RaceLiveSnapshot` (consolidated live state)

Single document per tick (replaces separate live files during the race):

```yaml
kind: RaceLiveSnapshot
spec:
  observed_at: "2026-06-14T11:35:00Z"
  sequence: 42
  race_phase: racing
  regatta: { "@type": "sailing:Regatta", "@id": "urn:sailing:entity:regatta-faerder-2026" }
  standings: [...]           # from LiveStanding
  course_selection: {...}    # from CourseSelection
  insights: [...]            # from InsightAlert (cumulative, deduplicated)
  grib_scores: {...}         # from GribModelScore rollup
```

`post-race/*.yaml` kinds ([ADR-0024](./0024-post-race-neo4j-export-to-data-repo.md)) are produced at **finalize** by splitting the last snapshot (plus portal merge).

### 4. Git branch strategy

| Branch | Use |
|--------|-----|
| `main` | Shore prep; harbor import |
| `race-live/{regatta_id}` | Auto-push every 5 min during race |

Push targets **`race-live/{regatta_id}`** to avoid polluting `main` with hundreds of commits during a long race. Cloud AI watches this branch. **Finalize** merges into `main` (fast-forward or PR).

Commit message format:

```text
race-live: {regatta_id} seq={sequence} @ {observed_at}
```

### 5. Network and policy gating

| Env | Default (race) | Meaning |
|-----|----------------|---------|
| `RACE_MODE` | `true` | Block Watchtower; **allow** live sync |
| `ONLINE_MODE` | `true` when LTE up | Enable connectivity probe + push |
| `RACE_LIVE_SYNC_ENABLED` | `true` | Master switch |
| `RACE_LIVE_SYNC_INTERVAL_MINUTES` | `5` | Tick interval |
| `SYNC_AUTO_PULL` | `false` | No shore pull during race (avoid merge fights) |
| `SYNC_AUTO_PUSH` | `true` | Enable push loop |

Before push: `git ls-remote` (or GitHub API ping). On failure: skip tick, log `push_status: skipped_offline` in manifest.

### 6. Secrets — never in the image

Credentials are **runtime-injected only**:

| Method | Path / env | Notes |
|--------|------------|-------|
| **Docker secret** (preferred) | `/run/secrets/github_token` → `GITHUB_TOKEN` | Compose `secrets:` block; file on Pi deploy dir |
| **Deploy env file** | `deploy/env/race.env` (gitignored) | `GITHUB_TOKEN=ghp_...` sourced by compose |
| **CI/CD inject** | GitHub Actions → Pi deploy script | Token written to secret file on harbor setup |

**Requirements:**

- Fine-grained PAT or classic token with **contents: write** on `AI-sailing-data` only.
- Token **not** passed as Docker `ARG` / `ENV` at image build time.
- Rotate per regatta; document in harbor checklist.
- `git config user.email` / `user.name` set to bot identity in container entrypoint (local repo only).

Future: external secret manager (1Password, Vault) — same mount contract.

### 7. Push algorithm (each tick)

1. Probe GitHub connectivity.
2. Query Neo4j → build `RaceLiveSnapshot` + update `RaceLiveSyncManifest`.
3. Write `race-live/current.yaml`, `race-live/sync-manifest.yaml`.
4. `git fetch origin`
5. `git checkout race-live/{regatta_id}` (create from `main` if missing)
6. `git add race-live/` + `race.yaml` (`spec.live_sync_sequence`, `spec.last_live_sync_at`)
7. `git commit -m "race-live: ..."` (skip if no diff)
8. `git push origin race-live/{regatta_id}`
9. Write local `sync-push-status.json` for Grafana / health endpoint

On conflict: **boat wins** for `race-live/*` during active race (`git checkout --ours` for those paths, then commit).

### 8. Re-import safety (unchanged)

`race-live/*.yaml` and `post-race/*.yaml` are **never** MERGE'd as runtime Neo4j nodes via `race-import`.

### 9. Cloud AI consumption

| Consumer | Pattern |
|----------|---------|
| GitHub Actions / cloud agent | Poll branch `race-live/{id}`; read `current.yaml` at `HEAD` |
| Historical analysis | `git log` + `git show` per sequence |
| Shore Cursor | Clone data repo; checkout race-live branch |

---

## Amendment to ADR-0024

ADR-0024 remains valid for **archive kinds** and **finalize** workflow. ADR-0025 **extends** it:

- During race → `race-live/` + git timeline ([this ADR](./0025-race-live-sync-github-temporal.md))
- After race → `post-race/` via finalize ([ADR-0024](./0024-post-race-neo4j-export-to-data-repo.md))

The planned `race-export` service is subsumed by **`race-live-sync`** (`finalize` subcommand retains export naming in logs).

---

## Rationale

- Git commit history is a free, auditable timeline without exploding repo file count.
- LTE-gated 5-minute pushes balance cloud freshness vs bandwidth.
- Dedicated branch isolates race churn from shore prep on `main`.
- Runtime secret injection matches [ADR-0008](./0008-github-docker-deployment-lifecycle.md) — no credentials in GHCR layers.
- Consolidated `RaceLiveSnapshot` is easier for cloud agents than four files per tick.

---

## Consequences

### Positive

- Shore/cloud AI can reason during the race from GitHub
- Full playback via `git log` on `race-live/{regatta_id}`
- Same YAML-LD + SHACL stack as pre-race facts
- Symmetric bidirectional sync with ADR-0009

### Negative

| Risk | Mitigation |
|------|------------|
| Token leak on Pi | File permissions 600; rotate per regatta; fine-grained PAT |
| Hundreds of commits | Dedicated branch; squash optional at finalize |
| LTE push during rough weather fails | Best-effort; sequence gaps visible in git log |
| Merge conflict with shore | Push to race-live branch; pull disabled during race |
| CI noise on every push | CI validates branch; optional skip workflow for `race-live/*` pushes |

---

## Implementation artifacts

| Artifact | Repository |
|----------|------------|
| `race-live-sync` service | AI-sailing-system |
| `deploy/env/race.env.example` — token + sync vars | AI-sailing-system |
| `schema/neo4j-mapping.yaml` → `live_projections` | AI-sailing-data |
| `RaceLiveSnapshot`, `RaceLiveSyncManifest` in context | AI-sailing-data |
| `schema/shacl/race-live.shacl.ttl` | AI-sailing-data |
| `docs/RACE_LIVE_SYNC.md` | AI-sailing-data |
| Spec §7.24, §11.17, G35 | AI-sailing-system |

---

## References

- [ADR-0009 Dual repository](./0009-dual-repository-race-data.md)
- [ADR-0024 Post-race export](./0024-post-race-neo4j-export-to-data-repo.md)
- [ADR-0028 Enriched live snapshot](./0028-enriched-live-snapshot-fleet-performance-temporal.md) — amends snapshot content
- [ADR-0008 Deployment lifecycle](./0008-github-docker-deployment-lifecycle.md)

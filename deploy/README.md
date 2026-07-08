# Deployment — GitHub + Docker lifecycle

This directory holds **environment templates**, **digest lock files**, **runtime secret guidance**, and **topology overrides** for Raspberry Pi deployment. Full specification: [spec.md §9](../spec.md#9-deployment-architecture). ADRs: [0008](../adr/0008-github-docker-deployment-lifecycle.md), [0030](../adr/0030-simple-hybrid-secrets-model.md).

## Prerequisites (new machine)

**`git clone` does not install Docker.** Before running compose on a laptop:

| Platform | Install |
|----------|---------|
| **Windows** | [WSL2 + Ubuntu](https://learn.microsoft.com/en-us/windows/wsl/install), then [Docker Desktop](https://docs.docker.com/desktop/setup/install/windows-install/) |
| **macOS / Linux** | [Docker Desktop](https://docs.docker.com/desktop/) or Docker Engine + Compose |

Full checklist: **[docs/DEV-SETUP.md](../docs/DEV-SETUP.md)**. Clone **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** as a sibling directory for SLA-2 import.

## Platform

| Piece | Location |
|-------|----------|
| CI | GitHub Actions → `.github/workflows/` |
| Images | `ghcr.io/cognite-fholm/<service>` |
| Pi runtime | `docker-compose.sla-{1,2,3}.yml` |
| Shore training | Gaming PC — `shore/docker-compose.sla-shore.yml` |

## Lifecycle states

| State | Env file | Watchtower |
|-------|----------|------------|
| Harbor (default) | `deploy/env/harbor.env` | Off when `WATCHTOWER_NO_PULL=true` (competition default) |
| Racing | **Same** `harbor.env` — lifecycle drives policy | **No** env swap ([ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md)) |
| Dev / laptop | `deploy/env/dev.env` | **Disabled** — use `docker-compose.dev.yml` overlay |

`race.env` is **deprecated** for competition boats — see [ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md).

Copy examples:

```powershell
copy deploy\env\harbor.env.example deploy\env\harbor.env
copy deploy\env\dev.env.example deploy\env\dev.env
```

## Local dev (single machine)

```powershell
# SLA-1 telemetry stack (bridge network — no PiCAN required)
docker compose -f docker-compose.sla-1.yml -f docker-compose.dev.yml --env-file deploy/env/dev.env up -d --build

# SLA-2 graph import (mount sibling AI-sailing-data clone)
docker compose -f docker-compose.sla-2.yml -f docker-compose.dev-sla2.yml --env-file deploy/env/dev.env up -d --build
# Import graph from mounted data repo (PowerShell — curl is an alias and breaks -X)
Invoke-RestMethod -Uri http://localhost:8080/import -Method Post -ContentType "application/json" -Body "{}"
```

Grafana telemetry: `http://localhost:3001` · Signal K: `http://localhost:3000` · polar-manager: `http://localhost:8092/health` · Neo4j browser: `http://localhost:7474`

## Guardrails (summary)

| ID | Rule |
|----|------|
| GR-1 | `RACE_MODE=true` → no Watchtower on any Pi |
| GR-2 | SLA-1 never managed by Watchtower |
| GR-3 | Upgrade order: SLA-3 → SLA-2 → SLA-1 |
| GR-4 | Use `deploy/locks/current.env` digest pins in production |
| GR-5 | Stop `training-export` when `RACE_MODE=true` |
| GR-7 | Keep previous lock file for rollback |

## Secrets model (simple hybrid)

Use:

- **GitHub Actions secrets** for CI/CD only
- **On-device runtime secret files** on each Pi (`/opt/ai-sailing-system/secrets`)

Install and validate runtime files:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets
```

For RMS VPN:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets --require-rms
```

Details and required filenames: [deploy/secrets/README.md](./secrets/README.md)

## Race freeze checklist

**Shore (per regatta):**

1. Set `index.yaml` `spec.active.regatta_id` and `race.yaml` `spec.schedule` in AI-sailing-data
2. Optional: `planning/runtime-policy.yaml`
3. `git push` to `main`

**Boat (once per system upgrade, not per regatta):**

1. Tag release: `git tag v0.4.0 && git push --tags`
2. Wait for `release.yml` → `deploy/locks/v0.4.0.env`
3. On each Pi: `cp deploy/locks/v0.4.0.env deploy/locks/current.env`
4. `./scripts/harbor-sync.sh` (models, OKF, config)
5. `./scripts/harbor-pull.sh --tier 3` then `--tier 2` then `--tier 1` if needed
6. Pre-flight: Signal K `candump`, Grafana health, Neo4j auth
7. Confirm `deploy/secrets/github_token` exists (long-lived PAT — [ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md))
8. Validate runtime secrets: `python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets`
9. Stacks run with **`harbor.env` only** — `race-lifecycle` handles race mode at `start_at`

**Do not** switch to `race.env` before the start gun.

## GitHub token for race live sync

`race-live-sync` needs **write** access to **AI-sailing-data** to push `race-live/` during the race ([ADR-0025](../adr/0025-race-live-sync-github-temporal.md)).

| Method | Setup |
|--------|-------|
| **Docker secret** (preferred) | Create `deploy/secrets/github_token` on the Pi (mode `600`); reference in compose `secrets:` → `/run/secrets/github_token` |
| **harbor.env** | `GITHUB_TOKEN=ghp_...` in gitignored `deploy/env/harbor.env` (fallback) |

Install **once** per boat — long-lived fine-grained PAT is acceptable ([ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md)). `race.env` is deprecated.

**Never** pass the token as a Docker build `ARG`/`ENV`. Rotate per regatta.

Fine-grained PAT scopes: **Contents: Read and write** on `cognite-fholm/AI-sailing-data` only.

### CI cross-repo checkout (optional)

YAML-LD and SHACL validation runs in **[AI-sailing-data CI](https://github.com/cognite-fholm/AI-sailing-data/actions)**. **AI-sailing-system** CI runs system tests without checking out the private data repo.

To re-enable combined validation in system CI, add repo secret **`AI_SAILING_DATA_CHECKOUT_TOKEN`** (fine-grained PAT, **contents: read** on `AI-sailing-data`) and restore the checkout steps in `.github/workflows/ci.yml`.

User guide: [AI-sailing-data RACE_LIVE_SYNC.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIVE_SYNC.md)

## Lock files (`deploy/locks/`)

Generated by CI on release. Example entry:

```env
POLAR_MANAGER_IMAGE=ghcr.io/cognite-fholm/polar-manager@sha256:abc123...
TACTICAL_COACH_IMAGE=ghcr.io/cognite-fholm/tactical-coach@sha256:def456...
RELEASE_VERSION=v0.4.0
```

Compose files reference `${POLAR_MANAGER_IMAGE}` etc.

## Topology overrides

| Directory | Pis | Profile |
|-----------|-----|---------|
| `deploy/compact/` | 1 | All tiers stacked (not race profile) |
| `deploy/standard/` | 2 | SLA-1 isolated |
| `deploy/race/` | 3 | Recommended for regattas |

## Offline fallback

Prepare USB with `docker save` images matching `deploy/locks/current.env`. On Pi without internet: `docker load` then `compose up`.

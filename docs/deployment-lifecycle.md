# Deployment lifecycle

Operational guide for **GitHub Actions → GHCR → Docker Compose** on Raspberry Pi, with **gaming PC** shore training.

## Canonical spec

- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) — consolidated architecture index
- [spec.md §9 — Deployment architecture](../spec.md#9-deployment-architecture)
- [ADR-0008 — GitHub + Docker lifecycle](../adr/0008-github-docker-deployment-lifecycle.md)
- [ADR-0009 — Dual repository](../adr/0009-dual-repository-race-data.md) — `race-data-sync` pull on boat
- [ADR-0025 — Race live sync](../adr/0025-race-live-sync-github-temporal.md) — `race-live-sync` push every 5 min on LTE
- [ADR-0026 — Race lifecycle](../adr/0026-race-lifecycle-scheduled-harbor-automation.md) — schedule-driven harbor automation
- [ADR-0027 — Data-repo runtime policy](../adr/0027-data-repo-runtime-policy-zero-pi-config.md) — **no per-race `race.env` swap**
- [ADR-0012 — Race-side MCP](../adr/0012-race-side-mcp-laptop-cursor.md) — laptop Cursor at regatta
- [ADR-0030 — Simple hybrid secrets](../adr/0030-simple-hybrid-secrets-model.md) — GitHub CI secrets + on-device runtime secret files
- [race-laptop-mcp.md](./race-laptop-mcp.md) — setup guide
- [deploy/README.md](../deploy/README.md) — env files, lock files, race freeze checklist
- [deploy/secrets/README.md](../deploy/secrets/README.md) — required runtime secret files and permissions
- [DEV-SETUP.md](./DEV-SETUP.md) — laptop Docker/WSL prerequisites (not installed by `git clone`)

## Quick reference

| Environment | Hardware | Deploy mechanism |
|-------------|----------|------------------|
| CI | GitHub Actions | Build `linux/arm64` → push GHCR |
| Harbor | 1–3× Raspberry Pi | `harbor-sync.sh` + manual `harbor-pull.sh` (Watchtower optional) |
| Racing | Same Pis | **Same `harbor.env`** — lifecycle + data repo drive policy |
| Shore ML | Gaming PC (CUDA) | `shore/docker-compose.sla-shore.yml` |

## Guardrails

See **GR-1 – GR-10** in [spec.md §9.5](../spec.md#95-lifecycle-states-and-guardrails).

**Never** auto-update SLA-1 during a race. **`harbor-pull.sh` refuses** when lifecycle `race_mode` is true or `RACE_MODE=true`. **`race-live-sync` git push** is gated by lifecycle phase when LTE is up.

## Per regatta (shore only)

1. `index.yaml` → active regatta
2. `race.yaml` → `spec.schedule`
3. `git push`

No Pi SSH for env changes — [RACE_LIFECYCLE.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIFECYCLE.md) · [ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md).

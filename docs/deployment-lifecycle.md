# Deployment lifecycle

Operational guide for **GitHub Actions → GHCR → Docker Compose** on Raspberry Pi, with **gaming PC** shore training.

## Canonical spec

- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) — consolidated architecture index
- [spec.md §9 — Deployment architecture](../spec.md#9-deployment-architecture)
- [ADR-0008 — GitHub + Docker lifecycle](../adr/0008-github-docker-deployment-lifecycle.md)
- [ADR-0009 — Dual repository](../adr/0009-dual-repository-race-data.md) — `race-data-sync` on boat
- [deploy/README.md](../deploy/README.md) — env files, lock files, race freeze checklist

## Quick reference

| Environment | Hardware | Deploy mechanism |
|-------------|----------|------------------|
| CI | GitHub Actions | Build `linux/arm64` → push GHCR |
| Harbor | 1–3× Raspberry Pi | `harbor-sync.sh` + `harbor-pull.sh` / Watchtower |
| Racing | Same Pis | Frozen `deploy/locks/current.env`, `RACE_MODE=true` |
| Shore ML | Gaming PC (CUDA) | `shore/docker-compose.sla-shore.yml` |

## Guardrails

See **GR-1 – GR-10** in [spec.md §9.5](../spec.md#95-lifecycle-states-and-guardrails).

**Never** auto-update SLA-1 during a race. **Never** pull containers when `RACE_MODE=true`.

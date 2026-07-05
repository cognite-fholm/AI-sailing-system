# ADR-0008: GitHub + Docker deployment lifecycle and guardrails

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0001](./0001-system-architecture-and-technology-choices.md), [ADR-0002](./0002-three-tier-sla-architecture.md), [ADR-0003](./0003-gopro-capture-and-shore-training.md), [spec.md §9](../spec.md#9-deployment-architecture)

---

## Context

The AI Sailing System spans **20+ containers** across up to **three Raspberry Pi nodes**, plus an optional **shore training** pipeline. We need a deployment model that is:

- **Low cost** — no paid cloud orchestration or GPU VMs for routine ops
- **Offline-capable** — races run without internet for 72+ hours
- **Safe at sea** — telemetry (SLA-1) must not auto-restart during a start sequence
- **Reproducible** — same images in harbor dev and regatta freeze

The user has a personal Azure account but prefers **minimal cloud spend**. Prior spec work already chose **Docker Compose**, **GHCR**, and **Watchtower (harbor only)**.

---

## Decision

### All-in: GitHub + Docker

| Layer | Technology |
|-------|------------|
| Source + issues + releases | **GitHub** |
| CI | **GitHub Actions** |
| Container registry | **GHCR** (`ghcr.io/cognite-fholm/*`) |
| Edge orchestration | **Docker Compose** on Pi (`linux/arm64`) |
| Edge auto-update | **Watchtower** — SLA-2/3 only, harbor only |
| Shore ML (SLA-S) | **Own gaming PC** + `shore/docker-compose.sla-shore.yml` |

**Out of scope:** Azure ACR, AKS, Kubernetes on Pi, Terraform-managed cloud edge, Actions→SSH direct deploy to boat.

### Three deployment loops

1. **Build loop** — merge to `main` → Actions builds changed services → push arm64 images to GHCR.
2. **Deploy loop** — harbor Wi-Fi → `harbor-pull.sh` / Watchtower → digest-pinned `compose up` per Pi.
3. **Operate loop** — `harbor-sync.sh` for models, OKF bundle, config YAML; volume backups separate from images.

### Lifecycle states

| State | `RACE_MODE` | Watchtower | SLA-1 updates |
|-------|-------------|------------|---------------|
| Development | `false` | off | local build OK |
| Harbor | `false` | SLA-2/3 | manual only |
| Race freeze / Racing | `true` | **off** | **forbidden** |
| Offline | `true` | off | USB `docker load` |

### Guardrails (GR-1 – GR-10)

Documented in [spec.md §9.5](../spec.md#95-lifecycle-states-and-guardrails) and [deploy/README.md](../deploy/README.md). Non-negotiable:

- **GR-1/GR-2:** No Watchtower on SLA-1; `RACE_MODE=true` disables all auto-pull.
- **GR-3:** Upgrade order SLA-3 → SLA-2 → SLA-1.
- **GR-4:** Production uses digest pins in `deploy/locks/`, not `:latest`.
- **GR-5:** `training-export` stopped when racing.
- **GR-10:** Training data export requires explicit consent.

### CI workflows

- `ci.yml` — PR lint/test
- `publish-sla-{1,2,3}.yml` — path-filtered arm64 builds
- `release.yml` — git tag → lock file + GitHub Release

### Shore training

TrimTransformer training runs on a **home gaming PC** with NVIDIA GPU. Artifacts publish to GHCR from harbor; boat pulls in harbor. No Azure GPU VMs.

---

## Rationale

### Why GHCR over Azure ACR?

- Same org as the repo; Actions integration is one `GITHUB_TOKEN`.
- **$0** marginal cost for a personal/hobby project on GitHub free tier.
- ACR adds ~$5/month minimum with no benefit when not using Azure for compute.

### Why Compose over Kubernetes on Pi?

- ADR-0002 already rejected k3s for v1.
- Single-node Compose per tier matches hardware (1–3 Pis).
- Lower RAM/ops overhead; crew can `docker compose logs` without cluster tooling.

### Why gaming PC over cloud GPU?

- Harbor export bundles are processed infrequently (post-regatta).
- Gaming PC CUDA is sunk cost; cloud spot VMs still bill storage and egress.
- Same Docker Compose pattern as edge — one toolchain.

### Why digest lock files?

- Regatta freeze requires a known-good stack.
- Rollback is `cp deploy/locks/v0.3.9.env deploy/locks/current.env` + pull.
- USB offline images match a specific lock file.

---

## Consequences

### Positive

- Single toolchain (Git + Docker) from dev to boat to shore PC.
- Clear race-week freeze procedure.
- CI/CD cost near **$0** on GitHub free tier.
- Shore training without recurring cloud GPU bills.

### Negative

- No managed rollout dashboard — ops are scripts + Compose.
- arm64 builds on GitHub QEMU are slow until a self-hosted runner is added.
- Manual discipline required for race freeze (human sets `RACE_MODE`).

### Risks

| Risk | Mitigation |
|------|------------|
| Accidental `:latest` pull at sea | Digest locks + `RACE_MODE` |
| Signal K restart | SLA-1 excluded from Watchtower; manual harbor updates only |
| GitHub Actions minute limits | Path filters; build only changed services |
| Large GGUF in images | Excluded from CI; `harbor-sync.sh` |

---

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Azure ACR + Container Apps | Cost; complexity; boat stays offline |
| Kubernetes (k3s) on Pi | ADR-0002; resource overhead |
| Azure GPU VM for training | Gaming PC is cheaper for sporadic training |
| Direct Actions SSH deploy to Pi | Fragile; needs VPN; boat often offline |
| Docker Hub | Rate limits; weaker GitHub integration |

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial accepted decision |

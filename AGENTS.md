# Agent instructions — AI Sailing System repository

Runtime code, Docker Compose, CI/CD, and ADRs for the AI Sailing System.

**Human user guide:** [docs/USER_GUIDE.md](docs/USER_GUIDE.md)  
**New laptop / Docker setup:** [docs/DEV-SETUP.md](docs/DEV-SETUP.md) — **required before `docker compose` on Windows**  
**Race content (YAML):** [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data) — clone as sibling repo

## Read order

1. **Fresh machine or `docker` not found?** → [docs/DEV-SETUP.md](docs/DEV-SETUP.md) (WSL2 + Docker Desktop on Windows)
2. [spec.md](spec.md) — normative specification
3. [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — tiers, data flow, phase status
4. [adr/README.md](adr/README.md) — decisions and implementation order
5. [deploy/README.md](deploy/README.md) — env files, harbor vs race, local dev

## Local runtime (laptop)

Requires Docker — see [docs/DEV-SETUP.md](docs/DEV-SETUP.md). Uses `docker-compose.dev.yml` overlay + `deploy/env/dev.env`.

## Python conventions

When editing Python services, follow [.agents/skills/pydantic-first-coding/SKILL.md](.agents/skills/pydantic-first-coding/SKILL.md) — Pydantic v2 for config, HTTP, and AI-sailing-data YAML kinds. Current compliance: [ADHERENCE.md](.agents/skills/pydantic-first-coding/ADHERENCE.md).

# Developer setup — new laptop or workstation

**Read this before running `docker compose` on a fresh machine.** The runtime stacks in this repository require Docker; on Windows they also require WSL2. These are **not** installed by `git clone` — you must set them up once per computer.

Cursor agents: see also [`.cursor/rules/dev-prerequisites.mdc`](../.cursor/rules/dev-prerequisites.mdc).

---

## Required tools

| Tool | Required for | Notes |
|------|----------------|-------|
| **Git** | Clone + sync | [git-scm.com](https://git-scm.com/) |
| **WSL2 + Linux distro** | Docker on **Windows** | Ubuntu via `wsl --install` |
| **Docker Desktop** | All `docker compose` workflows | Engine must show **running** |
| **Sibling clone of [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | SLA-2 import / sync | Default mount: `../AI-sailing-data` |

**Raspberry Pi onboard:** Docker Engine (or Docker CE) on the Pi — no WSL. See [deploy/README.md](../deploy/README.md) for Pi lifecycle.

**Shore-only data prep:** You can edit **AI-sailing-data** without Docker. Docker is required when you want to run **AI-sailing-system** services locally (telemetry, Neo4j import, Grafana, MCP gateway).

---

## Windows — first-time setup

Run in **PowerShell as Administrator** (order matters):

### 1. WSL2 + Ubuntu

```powershell
wsl --install
```

- Restart if Windows asks you to.
- When Ubuntu opens, create a **Linux username and password**.
- Verify:

```powershell
wsl --list --verbose
```

`Ubuntu` should show **Running** or **Stopped** with **VERSION 2**.

### 2. Docker Desktop

```powershell
winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
```

- Approve the **Administrator** prompt when the installer requests it.
- Start **Docker Desktop** from the Start menu.
- **Settings → General** → enable **Use the WSL 2 based engine**.
- Wait until the tray icon shows **Engine running**.

### 3. Verify Docker (new PowerShell window)

```powershell
docker --version
docker info
```

If `docker` is not recognized, open a **new** terminal after install, or use:

```powershell
& "C:\Program Files\Docker\Docker\resources\bin\docker.exe" --version
```

---

## Clone both repositories (sibling layout)

```powershell
mkdir C:\Repositories\boat_system
cd C:\Repositories\boat_system

git clone https://github.com/cognite-fholm/AI-sailing-data.git
git clone https://github.com/cognite-fholm/AI-sailing-system.git
```

`deploy/env/dev.env.example` assumes data repo at `../AI-sailing-data` relative to **AI-sailing-system**.

---

## Run local dev stacks

```powershell
cd C:\Repositories\boat_system\AI-sailing-system
copy deploy\env\dev.env.example deploy\env\dev.env

# SLA-1 — Signal K, InfluxDB, bridge, Grafana telemetry
docker compose -f docker-compose.sla-1.yml -f docker-compose.dev.yml --env-file deploy/env/dev.env up -d --build

# SLA-2 — Neo4j, race-import, race-data-sync
docker compose -f docker-compose.sla-2.yml -f docker-compose.dev-sla2.yml --env-file deploy/env/dev.env up -d --build

# Import graph from mounted data repo
# Import graph from mounted data repo (PowerShell)
Invoke-RestMethod -Uri http://localhost:8080/import -Method Post -ContentType "application/json" -Body "{}"
```

| Service | URL |
|---------|-----|
| Grafana telemetry | http://localhost:3001 |
| Signal K | http://localhost:3000 |
| Neo4j browser | http://localhost:7474 |
| race-import health | http://localhost:8080/health |

---

## macOS / Linux

- Install [Docker Desktop](https://docs.docker.com/desktop/) (macOS) or Docker Engine + Compose plugin (Linux).
- Clone both repos as siblings; use the same `docker compose` commands (adjust `copy` → `cp` for env file).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `docker: command not found` | Install Docker Desktop; open a **new** terminal |
| `Cannot connect to the Docker daemon` | Start Docker Desktop; wait for engine |
| WSL provisioning hangs | Wait; or `wsl --shutdown` and retry `wsl -d Ubuntu` |
| `data repo not mounted` | Clone **AI-sailing-data** next to this repo; check `DATA_REPO_HOST_PATH` in `deploy/env/dev.env` |
| Port already in use | Change ports in `deploy/env/dev.env` |

---

## Related docs

- [deploy/README.md](../deploy/README.md) — env files, harbor vs race mode
- [docs/ARCHITECTURE.md](./ARCHITECTURE.md) — SLA tiers and compose files
- [AI-sailing-data — Getting started](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/GETTING_STARTED.md) — shore prep (no Docker required)

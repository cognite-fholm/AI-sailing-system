# User guide — AI Sailing System

Guide for **sailors and crew** using the onboard platform. Race **content** (courses, fleet, boats) is prepared in **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** — start there for shore prep.

## Two repositories

| Repo | You use it for… |
|------|-----------------|
| **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | Prepare regattas on shore (Cursor, GitHub) |
| **AI-sailing-system** (this repo) | Run on Raspberry Pi at the regatta |

Deploy **both** to the boat.

**Data format:** Race and boat facts in AI-sailing-data use **[YAML-LD](https://w3c.github.io/yaml-ld/)** (linked YAML) so boats, certificates, and courses reference each other unambiguously. See [YAML_LD.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/YAML_LD.md) · [ADR-0022](../adr/0022-yaml-ld-interconnected-data.md).

## Shore preparation (start here)

**New laptop?** Install WSL2 + Docker Desktop before running local stacks: [DEV-SETUP.md](./DEV-SETUP.md).

All detailed user guides live in the **data repo**:

| Guide | Topic |
|-------|-------|
| [docs/README.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/README.md) | **Documentation hub** |
| [Getting started](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/GETTING_STARTED.md) | Clone, Cursor, first race |
| [Cursor guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/CURSOR_GUIDE.md) | Guided `race-preparation` agent |
| [Race preparation guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md) | 12-phase workflow |
| [Boats and certificates](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/BOATS_AND_CERTIFICATES.md) | ORC, SLK, fleet |
| [Harbor and race week](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/HARBOR_AND_RACE_WEEK.md) | Sync, GPX, Grafana, MCP |
| [YAML-LD (linked data)](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/YAML_LD.md) | How boat/race YAML files link together |
| [Troubleshooting](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/TROUBLESHOOTING.md) | Common fixes |

## Onboard system overview

Three **SLA tiers** on Raspberry Pi (may be separate devices):

| Tier | What you see | Typical URL |
|------|--------------|-------------|
| **SLA-1** | Instruments, SOG, wind, depth, course VMG/XTE, polar % | Grafana telemetry `:3001`, Signal K `:3000` |
| **SLA-2** | Fleet map, standings, GRIB, polars, alerts | `race-ui` (primary helm UX), Grafana race `:3002` |
| **SLA-3** | Sail camera / trim analysis | Grafana sail (when deployed) |

Hostname examples: `telemetry.local`, `race.local` (boat LAN).

## Harbor workflow

1. **Shore:** Finish [race prep](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_PREPARATION_GUIDE.md); `git push`
2. **Boat:** `cd /opt/ai-sailing-data && git pull`
3. **Import:** confirm `config/data-repo.yaml` `active` section, then trigger `race-import` HTTP API:
   - Pi/Linux: `curl -sS -X POST http://localhost:8080/import -H "Content-Type: application/json" -d "{}"`
   - Windows laptop dev: `Invoke-RestMethod -Uri http://localhost:8080/import -Method Post -ContentType "application/json" -Body "{}"`
4. **Copy:** GRIB to `/data/grib/`; GPX zip to phone/chartplotter
5. **Verify:** Polar loads — `Invoke-RestMethod http://localhost:8092/health` (or `curl` on Pi); course sync logs in `course-sk-sync` container

Detail: [deployment-lifecycle.md](./deployment-lifecycle.md) · [data repo: Harbor guide](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/HARBOR_AND_RACE_WEEK.md)

## During the race

| Tool | Use |
|------|-----|
| **race-ui** | Primary interactive race optimization UI on boat LAN ([ADR-0018](./adr/0018-helm-ux-three-pi-dual-speaker.md)) |
| **Grafana race** | Time-series, fleet map, polar %, debrief |
| **course-editor** | Waypoints, start-line course selection (when deployed) |
| **Laptop + Cursor MCP** | Ad hoc standings, Influx, Neo4j — [race-laptop-mcp.md](./race-laptop-mcp.md) |
| **tactical-coach** | Onboard LLM advisory (Pi) |

**Race mode:** `RACE_MODE=true` — containers do not auto-update mid-regatta.

## Laptop at the regatta (Cursor + MCP)

1. Clone **AI-sailing-data** on laptop
2. Join boat Wi‑Fi
3. Configure `.cursor/mcp.json` → `http://race.local:3100`

Full setup: [race-laptop-mcp.md](./race-laptop-mcp.md) · [mcp-neo4j-influx.md](./mcp-neo4j-influx.md)

## Instrument reference

| System | Doc |
|--------|-----|
| iRegatta UX parity | [spec §7.16](./spec.md#716-iregatta-reference-model--feature-traceability), [ADR-0010](./adr/0010-iregatta-reference-model.md) |
| B&G H5000 | [spec §7.17](./spec.md#717-bg-h5000-reference-model--integration), [ADR-0011](./adr/0011-bg-h5000-reference-model.md) |
| H5000 YAML in data repo | [h5000-instrumentation skill](https://github.com/cognite-fholm/AI-sailing-data/blob/main/.cursor/skills/h5000-instrumentation/SKILL.md) |

## Technical documentation

| Doc | Audience |
|-----|----------|
| [DEV-SETUP.md](./DEV-SETUP.md) | **New laptop** — WSL2, Docker, local compose |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | Architecture index |
| [spec.md](./spec.md) | Full specification |
| [spec §7.15.8](./spec.md#7158-yaml-ld-linked-data-format) | YAML-LD normative spec section |
| [adr/README.md](../adr/README.md) | Architecture decisions |
| [deploy/README.md](../deploy/README.md) | Env files, race freeze |

## Quick troubleshooting (onboard)

| Problem | Check |
|---------|-------|
| No telemetry | SLA-1 Pi, Signal K, `can0` / NMEA |
| No fleet on map | AIS, `ais-collector`, SLA-2 running |
| Wrong handicap | `scoring.yaml` + `course-preference.yaml` on boat git pull |
| Stale GRIB | Age in Grafana; copy fresh files to `/data/grib/` |
| MCP won’t connect | Same LAN, API key, `race-mcp-gateway` logs |

More: [data repo troubleshooting](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/TROUBLESHOOTING.md)

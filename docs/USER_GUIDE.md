# User guide — AI Sailing System

Guide for **sailors and crew** using the onboard platform. Race **content** (courses, fleet, boats) is prepared in **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** — start there for shore prep.

## Two repositories

| Repo | You use it for… |
|------|-----------------|
| **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | Prepare regattas on shore (Cursor, GitHub) |
| **AI-sailing-system** (this repo) | Run on Raspberry Pi at the regatta |

Deploy **both** to the boat.

**Data format:** Race and boat facts in AI-sailing-data use **[YAML-LD](https://w3c.github.io/yaml-ld/)** (linked YAML) so boats, certificates, and courses reference each other unambiguously. Shore CI validates **SHACL** constraints before import. See [DATA_SCHEMA.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md) · [YAML_LD.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/YAML_LD.md) · [ADR-0022](../adr/0022-yaml-ld-interconnected-data.md) · [ADR-0023](../adr/0023-shacl-neo4j-projection-no-fuseki.md).

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
| [Harbor and race week](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/HARBOR_AND_RACE_WEEK.md) | Sync, GPX, Grafana, MCP, live sync |
| [Race live sync](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIVE_SYNC.md) | 5 min LTE push, GitHub token, cloud AI |
| [Post-race archive](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/POST_RACE_ANALYSIS.md) | Finalize → `post-race/` on `main` |
| [Race decision playbook](./race-decision-playbook.md) | Tactical Q&A and race-winning decision workflow |
| [Race-day command sheet](./race-day-command-sheet.md) | One-page high-pressure prompt sheet |
| [YAML-LD (linked data)](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/YAML_LD.md) | How boat/race YAML files link together |
| [**Data schema (ontology + Neo4j)**](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/DATA_SCHEMA.md) | How YAML-LD, SHACL, and Neo4j fit together |
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

**Automated harbor (optional):** Set `index.yaml` `spec.active.regatta_id` and `race.yaml` `spec.schedule` on shore. The `race-lifecycle` service on the Pi runs pull + import at `harbor_sync_at`, arms live sync before the start, and enables race mode at `start_at` — [ADR-0026](../adr/0026-race-lifecycle-scheduled-harbor-automation.md) · [ADR-0027](../adr/0027-data-repo-runtime-policy-zero-pi-config.md) · [RACE_LIFECYCLE.md](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIFECYCLE.md).

**No `race.env` swap:** Competition boats keep a single `harbor.env` + long-lived GitHub secret on the Pi.

### Runtime secrets checklist (per boat)

Install runtime credentials as files under `/opt/ai-sailing-system/secrets` (`700` dir, `600` files), then validate:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets
```

If using RMS VPN:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets --require-rms
```

Guide: [deploy/secrets/README.md](../deploy/secrets/README.md) · ADR: [0030](../adr/0030-simple-hybrid-secrets-model.md)

## During the race

| Tool | Use |
|------|-----|
| **race-ui** | Primary interactive race optimization UI on boat LAN ([ADR-0018](./adr/0018-helm-ux-three-pi-dual-speaker.md)) |
| **Grafana race** | Time-series, fleet map, polar %, debrief |
| **course-editor** | Waypoints, start-line course selection (when deployed) |
| **Laptop + Cursor MCP** | Ad hoc standings, Influx, Neo4j — [race-laptop-mcp.md](./race-laptop-mcp.md) |
| **tactical-coach** | Onboard LLM advisory (Pi) |

**Race mode:** Lifecycle sets `race_mode` at `start_at` — containers do not auto-update mid-regatta (`WATCHTOWER_NO_PULL=true` in `harbor.env`).

## After the race

Export structured insights from Neo4j to **GitHub** during and after the race ([ADR-0024](../adr/0024-post-race-neo4j-export-to-data-repo.md), [ADR-0025](../adr/0025-race-live-sync-github-temporal.md), [spec §7.24](../spec.md#724-race-live-sync-and-archive)).

### During the race (automatic on LTE)

`race-live-sync` pushes `race-live/current.yaml` to branch `race-live/{regatta_id}` **every 5 minutes** when `ONLINE_MODE=true`. Configure `GITHUB_TOKEN` via Docker secret — never in the image.

Each tick is an **enriched snapshot** ([ADR-0028](../adr/0028-enriched-live-snapshot-fleet-performance-temporal.md)) that answers five tactical questions without VPN to the boat:

| Question | Read in `current.yaml` |
|----------|------------------------|
| Results if the race finished **now**? | `spec.standings[]` — corrected seconds, rank, Δ leader |
| Who sails **above** polar? | `spec.insights[]` type `polar_outperformers` + `fleet_performance[]` |
| Who sails **below** polar? | `spec.insights[]` type `polar_underperformers` |
| Who has better **course / VMG** toward the mark? | `spec.insights[]` `vmg_leaders_leg`, `course_progress_leaders` |
| Who has **better wind** on the course? | `spec.insights[]` `wind_advantage` |

**30 s** fleet polar data stays in Influx on the boat; git stores **5 min rollups** only. Thresholds default to 105% / 90% (`planning/runtime-policy.yaml`).

Example fixture: [race-live/current.yaml.example](https://github.com/cognite-fholm/AI-sailing-data/blob/main/races/2026/2026-06-faerderseilasen/race-live/current.yaml.example)

| Guide | Topic |
|-------|-------|
| [Race live sync](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/RACE_LIVE_SYNC.md) | LTE push, secrets, cloud AI, git playback |
| [Harbor — after the race](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/HARBOR_AND_RACE_WEEK.md#after-the-race) | Finalize checklist |

### After the race

1. `race-live-sync finalize --race {id}` — writes `post-race/*.yaml`, merges to `main`
2. Add `wiki/debrief.md`; review `git diff`
3. `git push` if finalize ran on boat with pending commits

**Not exported:** Influx telemetry, AIS tracks, raw GRIB.

## Laptop at the regatta (Cursor + MCP)

1. Clone **AI-sailing-data** on laptop
2. Join boat Wi‑Fi **or** VPN ([vpn-remote-access.md](./vpn-remote-access.md))
3. Configure `.cursor/mcp.json` → `http://race.local:3100` (Neo4j, Influx, Signal K)

Full setup: [race-laptop-mcp.md](./race-laptop-mcp.md) · [mcp-neo4j-influx.md](./mcp-neo4j-influx.md)

Race-day decisions and prompt patterns: [race-decision-playbook.md](./race-decision-playbook.md)
Fast one-page prompts: [race-day-command-sheet.md](./race-day-command-sheet.md)

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
| [vpn-remote-access.md](./vpn-remote-access.md) | Tailscale / RMS VPN for remote MCP |
| [race-decision-playbook.md](./race-decision-playbook.md) | Tactical decision questions and answer format |
| [race-day-command-sheet.md](./race-day-command-sheet.md) | Fast race-day prompts and sail matrix usage |
| [config/templates/sail-decision-matrix.template.yaml](../config/templates/sail-decision-matrix.template.yaml) | Starter template for your boat sail matrix |
| [spec.md](./spec.md) | Full specification |
| [spec §7.15.8–10](./spec.md#7158-yaml-ld-linked-data-format) | YAML-LD, SHACL, Neo4j projection |
| [adr/README.md](../adr/README.md) | Architecture decisions |
| [deploy/README.md](../deploy/README.md) | Env files, race freeze |
| [deploy/secrets/README.md](../deploy/secrets/README.md) | Runtime secret files and permissions |

## Quick troubleshooting (onboard)

| Problem | Check |
|---------|-------|
| No telemetry | SLA-1 Pi, Signal K, `can0` / NMEA |
| No fleet on map | AIS, `ais-collector`, SLA-2 running |
| Wrong handicap | `scoring.yaml` + `course-preference.yaml` on boat git pull |
| Stale GRIB | Age in Grafana; copy fresh files to `/data/grib/` |
| MCP won’t connect | Same LAN or VPN, API key, `race-mcp-gateway` logs |

More: [data repo troubleshooting](https://github.com/cognite-fholm/AI-sailing-data/blob/main/docs/TROUBLESHOOTING.md)

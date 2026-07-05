# ADR-0009: Dual-repository model — system code vs race/boat data

**Status:** Accepted  
**Date:** 2026-07-05  
**Deciders:** cognite-fholm  
**Related:** [ADR-0008](./0008-github-docker-deployment-lifecycle.md), [AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)

---

## Context

Competitive sailing requires extensive **onshore planning** before each regatta: GRIB strategy, course preferences, waypoint refinement, fleet handicaps, and tactical notes. Runtime systems (Neo4j, InfluxDB) capture **live** state; they are poor places to version-plan a race across weeks of preparation.

The user needs:

1. **Temporal organization** — races by year/date; boat ratings by year (ORC certificates change).
2. **Multiple representations** — raw/collected YAML, human wiki markdown, Neo4j-import templates, OKF concepts for LLM bootstrap.
3. **GitHub workflow** — PR review, tags, history — for both own boat and competitors.
4. **Onboard sync** — boat pulls newer data from GitHub when online (Teltonika 4G/5G).
5. **Dual deploy** — system version + data version deployed together.

---

## Decision

### Two repositories

| Repository | Contents | Deploy path on Pi |
|------------|----------|-------------------|
| **[AI-sailing-system](https://github.com/cognite-fholm/AI-sailing-system)** | Code, Dockerfiles, Compose, CI, runtime config templates | `/opt/ai-sailing-system/` |
| **[AI-sailing-data](https://github.com/cognite-fholm/AI-sailing-data)** | Races, boats, planning, neo4j YAML, OKF, assets | `/opt/ai-sailing-data/` |

### Data repository layout

```
boats/{sail_number}/{year}/     # ratings, polar, neo4j, okf, assets
races/{year}/{year}-{month}-{slug}/
  race.yaml                     # manifest
  planning/                     # grib-plan, course-preference, weather notes
  courses/                      # routes & waypoints
  fleet.yaml
  scoring.yaml
  neo4j/                        # declarative import bundles
  okf/                          # per-race OKF concepts
  wiki/                         # human-refined markdown
  assets/                       # SI PDF, polars (Git LFS optional)
```

Sail number directories: `7710`, `NOR-15788` (normalize spaces to hyphens).

### Three knowledge roles

| Layer | Repo / store | Purpose |
|-------|--------------|---------|
| **Planning & facts** | AI-sailing-data YAML + wiki | Onshore preparation; versioned truth |
| **LLM concepts** | AI-sailing-data OKF + system OKF system/ | How to interpret data |
| **Runtime graph** | Neo4j on boat | Live AIS, selections, standings, maneuvers |
| **Telemetry** | InfluxDB on boat | Time series only |

Neo4j **imports** from data repo `neo4j/*.yaml` at harbor; **mutates** during race. Data repo never contains live AIS tracks.

### Onboard services (system repo)

| Container | Role |
|-----------|------|
| `race-data-sync` | Poll GitHub API; `git pull` when remote ahead (configurable branch/tag) |
| `race-import` | Apply `neo4j/import-order.yaml` → MERGE into Neo4j |
| `okf-loader` | Mount merged OKF from data repo + system bundle |

### Connectivity — Teltonika router

- **4G/5G** LTE WAN for Pis on boat LAN
- **Teltonika RMS** for remote monitoring, config backup, optional VPN to harbor
- `race-data-sync` uses LTE for GitHub pull when not in marina Wi-Fi
- Respect `RACE_MODE` — auto-pull of **data** may continue with caution (config); **container** auto-update stays disabled

### Deployment

Both repos cloned on each Pi (or NFS mount from one Pi). `harbor-sync.sh` updates both. Release tags:

- System: `v0.7.0` → GHCR images
- Data: `race-faerder-2026` or `main` → git ref for active regatta

---

## Rationale

- **Separation of concerns** — application releases ≠ regatta preparation commits.
- **Temporal model** — boat/year folders match how ORC ratings actually work.
- **Agent bootstrap** — OKF per race/boat gives LLMs structured entry points without scraping Neo4j cold.
- **GitHub already chosen** — ADR-0008; data repo is natural extension.
- **Competitor history** — fleet knowledge accumulates across years in one place.

---

## Consequences

### Positive

- Full onshore planning workflow in familiar git tools.
- Boat can refresh course/GRIB plan mid-regatta week if SI amended (with review).
- Neo4j import is idempotent from declarative YAML.
- Competitor boats reusable across races via `fleet.yaml` refs.

### Negative

- Two repos to clone and keep in sync.
- Large PDFs need LFS or harbor asset copy discipline.
- `race-import` must not clobber runtime nodes — import scope is explicit.

### Risks

| Risk | Mitigation |
|------|------------|
| Data pull breaks mid-race | Pin data ref at race freeze; optional `RACE_MODE` block on data pull |
| Schema drift | `apiVersion: sailing.cognite-fholm/v1` + schema/README |
| Secret in data repo | `.gitignore`; RMS creds only on router |

---

## Alternatives considered

| Alternative | Rejected because |
|-------------|------------------|
| Single monorepo | Mixes release cadence of code vs race prep |
| Neo4j as planning store | Poor versioning; offline editing hard |
| Cloud CMS for race data | Cost; offline; ADR-0008 GitHub commitment |
| Only YAML in system repo/config | No temporal boat history; no competitor archive |

---

## Revision history

| Version | Date | Change |
|---------|------|--------|
| 1.0 | 2026-07-05 | Initial accepted decision |

# Architecture Decision Records

This directory contains [Architecture Decision Records](https://adr.github.io/) for the AI Sailing System.

| ADR | Title | Status |
|-----|-------|--------|
| [0001](./0001-system-architecture-and-technology-choices.md) | System architecture and technology choices | Accepted |
| [0002](./0002-three-tier-sla-architecture.md) | Three-tier SLA architecture with isolated containers | Accepted |
| [0003](./0003-gopro-capture-and-shore-training.md) | GoPro HERO13 fleet capture and onshore TrimTransformer training | Accepted |
| [0004](./0004-grib-polars-ais-wind-analysis.md) | GRIB scheduling, polar fleet registry, AIS ingest, wind-on-course analysis | Accepted |
| [0005](./0005-course-parsing-handicaps-live-results.md) | Course parsing from SI PDFs, multi-handicap scoring, live results | Accepted |
| [0006](./0006-start-boat-course-flags.md) | Multiple courses per race and start-boat flag signaling | Accepted |
| [0008](./0008-github-docker-deployment-lifecycle.md) | GitHub + Docker CI/CD, lifecycle, guardrails, gaming PC shore training | Accepted |
| [0009](./0009-dual-repository-race-data.md) | Dual repo: AI-sailing-system + AI-sailing-data, Teltonika LTE sync | Accepted |
| [0010](./0010-iregatta-reference-model.md) | iRegatta v2.86 as functional reference for race UX | Accepted |
| [0011](./0011-bg-h5000-reference-model.md) | B&G H5000 instrument and race-display reference | Accepted |
| [0012](./0012-race-side-mcp-laptop-cursor.md) | Race-side MCP for laptop Cursor and ad hoc analysis | Accepted |
| [0013](./0013-orc-certificate-fleet-collection.md) | Automated ORC certificate collection for race fleets | Accepted |
| [0014](./0014-shore-weather-current-collection.md) | Shore weather and current collection (MET GRIB, Oslofjord plots, SMHI) | Accepted |

## Format

Each ADR follows the structure:

1. **Context** — what forces are at play
2. **Decision** — what we chose
3. **Rationale** — why
4. **Consequences** — positive, negative, risks
5. **Alternatives considered**

New decisions should use the next sequential number: `0015-short-title.md`.

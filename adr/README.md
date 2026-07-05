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

## Format

Each ADR follows the structure:

1. **Context** — what forces are at play
2. **Decision** — what we chose
3. **Rationale** — why
4. **Consequences** — positive, negative, risks
5. **Alternatives considered**

New decisions should use the next sequential number: `0009-short-title.md`.

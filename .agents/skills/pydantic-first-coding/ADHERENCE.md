# Pydantic adherence audit — AI-sailing-system

Snapshot: **2026-07-06** · Skill: [SKILL.md](./SKILL.md)

**Verdict: partially adherent** — new SLA-1/SLA-2 sidecars use Pydantic; legacy scaffold services still use `@dataclass`.

---

## Summary

| Area | Status |
|------|--------|
| Type hints on public APIs | **Mostly yes** |
| `pydantic` in requirements | **Partial** (`course-sk-sync`, `polar-manager`, `signalk-polar-performance`) |
| Config via `BaseSettings` | **Partial** (3× new sidecars; legacy `@dataclass`) |
| YAML kinds as Pydantic models | **No** (`dict[str, Any]`) |
| HTTP responses as models | **No** (raw dict → `JSONResponse`) |
| FastAPI services (spec) | **Not implemented** |

---

## Service-by-service

| Module | Config | Payloads / API | Gap |
|--------|--------|----------------|-----|
| `signalk-influx-bridge/config.py` | `@dataclass` `BridgeConfig` | Signal K `dict` (OK — dynamic) | Migrate config to `BaseSettings` |
| `signalk-influx-bridge/bridge.py` | — | `delta: dict[str, Any]` | Acceptable at SK boundary |
| `race-data-sync/config.py` | `@dataclass` `SyncConfig` | `dict` sync status JSON | Migrate config + `SyncStatus` model |
| `race-data-sync/sync.py` | — | untyped status dict | Add `SyncResult` model |
| `race-import/importer.py` | — | all YAML as `dict[str, Any]` | Add models per `kind` from data-repo schema |
| `race-import/api.py` | env + raw YAML | health/import dict responses | `HealthResponse`, `ImportResult`, `DataRepoConfig` |
| `race-mcp-gateway/config.py` | `@dataclass` `GatewayConfig` | YAML → dict | `McpGatewaySettings` |
| `race-mcp-gateway/influx_client.py` | — | Flux rows as `dict` | OK for query results |
| `race-mcp-gateway/neo4j_client.py` | — | Cypher rows as `dict` | OK for query results |
| `course-sk-sync/**` | `BaseSettings` | `Waypoint`, `ActiveRoute`, `SyncResult` | **Adherent** (Phase 1) |
| `signalk-polar-performance/**` | `BaseSettings` | `TelemetrySnapshot`, `PublishResult` | **Adherent** (Phase 1) |
| `polar-manager/**` | `BaseSettings` | `PolarGrid`, `TargetResponse`, API models | **Adherent** (stub) |
| `tests/bdd/**` | — | — | Exempt |

---

## Recommended migration order

1. **Shared `config/data-repo.yaml` models** — used by `race-import` + `race-data-sync` (highest duplication).
2. **`race-import`** — `ImportResult`, YAML kind models, API responses.
3. **`signalk-influx-bridge`** + **`race-data-sync`** — `BaseSettings` configs.
4. **`race-mcp-gateway`** — settings from `mcp-gateway.yaml`.
5. **New FastAPI services** — Pydantic from first commit (no dataclass debt).

---

## CI

No Pydantic lint gate yet. Optional follow-up: `ruff` + import-linter rule or a small pytest that imports settings models.

Update this file when a service is migrated.

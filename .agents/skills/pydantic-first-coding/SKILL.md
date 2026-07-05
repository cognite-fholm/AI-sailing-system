---
name: pydantic-first-coding
description: >-
  Pydantic-first patterns for AI-sailing-system Python services. Use when adding
  or modifying Python under signalk-influx-bridge/, race-import/, race-data-sync/,
  race-mcp-gateway/, or future FastAPI containers (tactical-coach, live-results, …).
---

# Pydantic-first coding — AI-sailing-system

Normative for **this repository** (`AI-sailing-system`). Shore scripts in **AI-sailing-data** may stay dataclass-based unless ported here.

Works with the workspace **cog-python** rule: type hints, `pathlib`, `ruff` — Pydantic is the **contract layer** on top.

**Schema source of truth for YAML:** [AI-sailing-data `schema/`](https://github.com/cognite-fholm/AI-sailing-data/tree/main/schema) — mirror kinds as Pydantic models in Python.

---

## Core rule

Use **Pydantic v2** (`pydantic>=2`) as the default for:

| Use | Model type |
|-----|------------|
| Service config (env + YAML) | `pydantic_settings.BaseSettings` or nested `BaseModel` + `SettingsConfigDict` |
| HTTP request/response bodies | `BaseModel` (FastAPI / Starlette JSON) |
| AI-sailing-data YAML documents | `BaseModel` per `kind` (`Neo4jNode`, `WaypointList`, …) |
| Import/sync results | `BaseModel` (e.g. `ImportResult`) |
| Internal DTOs between modules | `BaseModel` |

Add `pydantic` and `pydantic-settings` to the service `requirements.txt` when introducing models.

---

## Repository layout

| Service | Config today | Target |
|---------|--------------|--------|
| `signalk-influx-bridge` | `@dataclass` `BridgeConfig` | `BridgeSettings(BaseSettings)` |
| `race-data-sync` | `@dataclass` `SyncConfig` | `DataRepoSettings` + `SyncSettings` |
| `race-import` | raw `dict` from YAML | `DataRepoConfig`, `Neo4jNode`, … models |
| `race-mcp-gateway` | `@dataclass` `GatewayConfig` | `McpGatewaySettings` from `config/mcp-gateway.yaml` |

**New FastAPI services** (spec §7 — `tactical-coach`, `live-results`, `grib-ingest`, …): FastAPI routers + Pydantic models from day one.

---

## Required patterns

1. **Type hints** on all public function parameters and return types.
2. **Parse once at boundaries** — `Model.model_validate(raw)` or `Settings()` after loading YAML/env.
3. **Serialize at boundaries** — `model_dump(mode="json")` for JSON HTTP responses; use `by_alias=True` when matching external JSON/YAML keys.
4. **Nested structures** — nested `BaseModel`, not `dict[str, Any]`.
5. **Field metadata** — `Field(description=..., ge=..., pattern=...)` for constraints; `Field(alias="externalId")` when matching camelCase APIs.
6. **Settings** — env overrides via `Field(validation_alias="INFLUX_TOKEN")` or `pydantic-settings` env nesting.

### Example — service config (target pattern)

```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BridgeSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    signalk_ws_url: str = "ws://signalk-server:3000/signalk/v1/stream?subscribe=all"
    influx_url: str = "http://influxdb:8086"
    influx_token: str = Field(min_length=1)
    influx_org: str = "ai-sailing"
    influx_bucket: str = "signalk"
    vessel_id: str = "own-boat"
```

### Example — AI-sailing-data YAML kind

```python
from typing import Literal

from pydantic import BaseModel, Field


class Neo4jNodeSpec(BaseModel):
    labels: list[str]
    merge_keys: list[str]
    properties: dict[str, str | int | float | bool | None]


class Neo4jNodeDocument(BaseModel):
    kind: Literal["Neo4jNode"]
    metadata: dict[str, str]
    spec: Neo4jNodeSpec


def import_node(session, doc: Neo4jNodeDocument) -> None:
    ...
```

### Example — HTTP response (race-import)

```python
class ImportResult(BaseModel):
    imported: int
    files: list[str]


# return JSONResponse(import_result.model_dump(mode="json"))
```

---

## Allowed exceptions (do not force Pydantic)

| Case | Why |
|------|-----|
| **Signal K delta JSON** | Dynamic paths/values — validate only the slices you map (optional small models per path group). |
| **Influx / Neo4j query rows** | Tabular, query-dependent — `list[dict[str, object]]` OK after query; wrap in a display DTO if shaping for MCP. |
| **pytest / BDD steps** | Test fixtures — plain functions OK. |
| **One-off scripts** under `scripts/` | Prefer Pydantic if the script grows; not required for harbor shell wrappers. |

---

## Avoid

- `@dataclass` for **service config** in new or heavily touched code — use `BaseSettings`.
- `dict[str, Any]` for **known** YAML kinds from AI-sailing-data.
- Manual `raw["spec"]["merge_keys"]` chains when a model exists.
- Untyped `def import_node(session, doc)` — use typed models.

---

## Migration policy

When you **touch** a module for a feature fix (not drive-by refactors):

1. Introduce Pydantic models for that module's config and payloads.
2. Keep behaviour identical; add a thin test or BDD step if missing.
3. Remove the old `@dataclass` in the same change set when fully replaced.

Do **not** block shipping on a whole-repo migration — track gaps in [ADHERENCE.md](./ADHERENCE.md).

---

## Review checklist

- [ ] Config loaded via `BaseSettings` or validated `BaseModel`, not ad-hoc dict/`@dataclass`
- [ ] AI-sailing-data YAML parsed into typed `kind` models
- [ ] HTTP handlers return/dump Pydantic models
- [ ] `Any` only at truly dynamic boundaries (Signal K, raw DB rows)
- [ ] `pydantic>=2` in service `requirements.txt`
- [ ] `ruff` clean on touched files

## Related

- [ADHERENCE.md](./ADHERENCE.md) — current compliance snapshot
- [spec.md §7](../../spec.md) — planned FastAPI services
- [AI-sailing-data schema](https://github.com/cognite-fholm/AI-sailing-data/blob/main/schema/README.md)

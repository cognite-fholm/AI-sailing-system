# Neo4j & Influx MCP tools

Reference for **`race-mcp-gateway`** MCP servers used by Cursor on the boat LAN.

**Setup:** [race-laptop-mcp.md](./race-laptop-mcp.md)  
**Config:** `config/mcp-gateway.yaml.example`  
**Implementation:** `race-mcp-gateway/`

---

## Cursor MCP servers

| Server id | Endpoint | Use when |
|-----------|----------|----------|
| `race-boat` | `http://race.local:3100/mcp` | Combined Neo4j + Influx tools |
| `race-neo4j` | `http://race.local:3100/mcp/neo4j` | Graph / standings only |
| `race-influx` | `http://race.local:3100/mcp/influx` | Telemetry / Flux only |

Copy [`.cursor/mcp.json.example`](../.cursor/mcp.json.example) and set `RACE_MCP_API_KEY`.

**Harbor dev (stdio):** [`.cursor/mcp.harbor.json.example`](../.cursor/mcp.harbor.json.example) — local Docker Neo4j/Influx on laptop.

---

## Neo4j tools (`race-neo4j`)

| Tool | Description |
|------|-------------|
| `cypher_query` | Read-only Cypher (`MATCH`/`RETURN`). Params as JSON string. |
| `get_live_standings` | `LiveStanding` ranks and corrected times |
| `get_course_selection` | Active `CourseSelection` |
| `get_fleet_positions` | `Vessel` lat/lon/cog/sog |
| `get_graph_schema` | `SHOW LABELS` for agent orientation |

### Example prompts

```
Use race-neo4j: get live standings and explain who moved up since mark 1.
```

```
race-neo4j cypher_query: MATCH (v:Vessel {sail_number: "NOR-10133"})-[:HAS_STANDING]->(s)
RETURN v.name, s.rank, s.corrected_time_s
```

### Key graph labels (from data repo imports)

`Regatta`, `Vessel`, `Waypoint`, `CourseRoute`, `LiveStanding`, `CourseSelection`, `OrcCertificate`, `HandicapRating`, `AisTrack`, `WindAdvantageZone`

Runtime-only nodes are **not** in git YAML — they appear during the race session.

---

## Influx tools (`race-influx`)

| Tool | Description |
|------|-------------|
| `flux_query` | Arbitrary read Flux (no `to()` / `delete()`) |
| `get_latest_instruments` | Last values for twa,tws,awa,aws,sog,cog,vmg |
| `get_wind_history` | 30s-mean wind series (default 30 min) |
| `list_buckets` | Buckets visible to read token |

### Buckets (spec)

| Bucket | Content |
|--------|---------|
| `signalk` | Raw instrument deltas (90-day retention) |
| `race` | Downsampled race session series |
| `ais_tracks` | Fleet AIS positions |

### Example Flux

```flux
from(bucket: "signalk")
  |> range(start: -45m)
  |> filter(fn: (r) => r._measurement == "signalk")
  |> filter(fn: (r) => r._field == "vmg" or r._field == "twa")
  |> aggregateWindow(every: 1m, fn: mean, createEmpty: false)
```

### Example prompts

```
race-influx: get_wind_history 45 minutes. Summarize TWS trend for the last beat.
```

```
race-influx flux_query: VMG and BSP for NOR-10133 last 20 minutes from signalk bucket.
```

---

## Limits

Configured in `mcp-gateway.yaml`:

| Limit | Default |
|-------|---------|
| `max_flux_range_hours` | 48 |
| `max_cypher_per_minute` | 30 |

---

## Environment variables

| Variable | Purpose |
|----------|---------|
| `RACE_MCP_API_KEY` | Bearer auth on HTTP gateway |
| `NEO4J_URI` | `bolt://neo4j:7687` on SLA-2 |
| `NEO4J_MCP_PASSWORD` | Read-only `mcp_analyst` password |
| `INFLUX_URL` | `http://telemetry.local:8086` |
| `INFLUX_READ_TOKEN` | Read-only token (SLA-1 bucket access) |
| `INFLUX_ORG` | Default `ai-sailing` |
| `INFLUX_BUCKET` | Default `signalk` |
| `MCP_GATEWAY_CONFIG` | Path to `mcp-gateway.yaml` |

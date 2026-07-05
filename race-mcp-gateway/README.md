# race-mcp-gateway

Read-only **MCP** servers for **Neo4j** and **InfluxDB** on the boat LAN. Used by **Cursor** on a navigator laptop at the regatta.

**Spec:** [§7.18](../spec.md#718-race-side-mcp--laptop-cursor) · **ADR:** [0012](../adr/0012-race-side-mcp-laptop-cursor.md)

## Endpoints (HTTP / SSE)

| Path | MCP server | Tools |
|------|------------|-------|
| `/mcp` | `race-boat` | Neo4j + Influx (combined) |
| `/mcp/neo4j` | `race-neo4j` | Cypher, standings, fleet positions |
| `/mcp/influx` | `race-influx` | Flux, latest instruments, wind history |
| `/health` | — | Liveness |

Default port: **3100** (`race.local:3100`).

## Stdio (harbor / local dev)

```bash
cd race-mcp-gateway
pip install -r requirements.txt
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=mcp_analyst
export NEO4J_MCP_PASSWORD=...
export INFLUX_URL=http://localhost:8086
export INFLUX_READ_TOKEN=...
export INFLUX_ORG=ai-sailing
export INFLUX_BUCKET=signalk

python -m race_mcp_gateway.servers.neo4j    # stdio → Cursor "race-neo4j"
python -m race_mcp_gateway.servers.influx   # stdio → Cursor "race-influx"
```

## HTTP gateway

```bash
export MCP_GATEWAY_CONFIG=../config/mcp-gateway.yaml
python -m race_mcp_gateway.gateway
```

## Docker (SLA-2)

```bash
docker build -t race-mcp-gateway ./race-mcp-gateway
docker run --rm -p 3100:3100 \
  -e RACE_MCP_API_KEY=dev \
  -e NEO4J_URI=bolt://host.docker.internal:7687 \
  -e NEO4J_MCP_PASSWORD=... \
  -e INFLUX_URL=http://host.docker.internal:8086 \
  -e INFLUX_READ_TOKEN=... \
  race-mcp-gateway
```

## Security

- Read-only Cypher and Flux (writes rejected in code).
- Dedicated Neo4j user `mcp_analyst`.
- Influx read token scoped to `signalk` / `race` / `ais_tracks` buckets.
- Boat LAN only — do not expose on LTE WAN.

See [docs/mcp-neo4j-influx.md](../docs/mcp-neo4j-influx.md) for tool reference and example queries.

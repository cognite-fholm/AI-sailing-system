# Race laptop — Cursor + MCP

Use a **laptop** at the regatta with **Cursor** and **MCP** to query live race data on the boat LAN — the same agent workflow as shore prep, but against runtime Neo4j, Influx, and standings.

**ADR:** [0012 — Race-side MCP](../adr/0012-race-side-mcp-laptop-cursor.md)  
**Spec:** [§7.18](../spec.md#718-race-side-mcp--laptop-cursor)

---

## Prerequisites

| Item | Where |
|------|--------|
| Boat Pis running SLA-1 + SLA-2 | `race.local`, `telemetry.local` resolve on boat Wi‑Fi |
| `race-mcp-gateway` container | SLA-2, port **3100** |
| `RACE_MCP_API_KEY` | `deploy/env/race.env` on Pi (share securely with laptop) |
| Cursor on laptop | Recent Cursor with MCP support |
| `AI-sailing-data` clone | Same regatta folder as onboard (`index.yaml` → active race) |

---

## Network

1. Join the **boat Wi‑Fi** (Teltonika AP or marina net bridged to boat LAN).
2. Verify connectivity:

```bash
ping race.local
curl -s -o /dev/null -w "%{http_code}" http://race.local:3100/health
```

MCP is **not** exposed on LTE/internet — boat LAN only.

---

## Cursor MCP configuration

Add to your **user** or **project** MCP config (`.cursor/mcp.json` in the repo root, or Cursor Settings → MCP):

```json
{
  "mcpServers": {
    "race-boat": {
      "url": "http://race.local:3100/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_RACE_MCP_API_KEY"
      }
    }
  }
}
```

Replace the API key with the value from the boat’s `race.env` (navigator copy, not committed to git).

**Workspace:** Open the **`AI-sailing-data`** folder for the active regatta in Cursor so the agent has local YAML/wiki context **and** live MCP tools.

---

## Example prompts

### Live standings

```
Use the race-boat MCP server. Get live corrected-time standings for our class.
Explain who gained rank in the last 30 minutes and why (VMG, course %).
```

### Telemetry

```
Via race MCP, query Influx for NOR-10133: TWA, TWS, VMG, BSP for the last 45 minutes.
Compare average VMG to polar target from polar-manager.
```

### Graph / fleet

```
Run a Cypher query via MCP: all vessels within 2 nm on the port side of leg 2
with their corrected-time rank. Include sail numbers.
```

### Tactical context

```
Read fleet.yaml and live standings via MCP. Which competitors ahead of us
have the lowest handicap factor and are we gaining on them on corrected time?
```

### Start line (pre-start)

```
MCP: current start-line state — DTL, bias boat lengths, time to gun vs time to line.
Cross-check with start-line.yaml in planning/.
```

---

## Available MCP tool groups

| Server | What you can ask |
|--------|------------------|
| **race-graph** | Standings, course selection, fleet positions, ad hoc Cypher (read-only) |
| **race-telemetry** | Flux queries, latest instruments, time series |
| **race-context** | YAML, wiki, OKF concepts from onboard data repo |
| **race-tactical** | Wind zones, polar targets, start-line state |
| **signalk-snapshot** | Current wind, SOG, COG from Signal K |

---

## Security notes

- Treat `RACE_MCP_API_KEY` like a race password — rotate per regatta.
- MCP is **read-only** in v1; it cannot steer, write Signal K, or push git.
- Do not port-forward `:3100` on the Teltonika LTE interface.
- Prefer wired Ethernet to `race.local` in heavy Wi‑Fi traffic if available.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| MCP connection refused | `docker ps` on race Pi — is `race-mcp-gateway` running? |
| 401 Unauthorized | API key matches `race.env` |
| Empty standings | Race session started? `CourseSelection` set? |
| Slow responses | Narrow Flux time range; avoid huge Cypher |

---

## vs onboard `tactical-coach`

| | Laptop + MCP + Cursor | Pi `tactical-coach` |
|--|----------------------|---------------------|
| UI | Cursor | Grafana / API |
| Depth | Multi-step analysis, exportable chat | Quick helm answers |
| Hardware | Your laptop | Raspberry Pi |

Use both: coach for short questions; laptop for deep ad hoc work in the nav station or harbor.

# Race laptop — Cursor + MCP

Use a **laptop** at the regatta with **Cursor** and **MCP** to query live race data on the boat LAN — the same agent workflow as shore prep, but against runtime Neo4j, Influx, and standings.

**ADR:** [0012 — Race-side MCP](../adr/0012-race-side-mcp-laptop-cursor.md) · [0029 — Signal K MCP + VPN](../adr/0029-signalk-mcp-ecosystem-vpn-remote-access.md)  
**Spec:** [§7.18](../spec.md#718-race-side-mcp--laptop-cursor)

---

## Prerequisites

| Item | Where |
|------|--------|
| Boat Pis running SLA-1 + SLA-2 | `race.local`, `telemetry.local` resolve on boat Wi‑Fi |
| `race-mcp-gateway` container | SLA-2, port **3100** |
| `RACE_MCP_API_KEY` | `/opt/ai-sailing-system/secrets/race_mcp_api_key` on Pi (share securely with laptop) |
| Cursor on laptop | Recent Cursor with MCP support |
| `AI-sailing-data` clone | Same regatta folder as onboard (`index.yaml` → active race) |

---

## Network

### On boat Wi‑Fi

1. Join the **boat Wi‑Fi** (Teltonika AP or marina net bridged to boat LAN).
2. Verify connectivity:

```bash
ping race.local
curl -s -o /dev/null -w "%{http_code}" http://race.local:3100/health
```

### Remote over VPN (shore, harbor tent)

When not on boat Wi‑Fi, use **Tailscale** (recommended) or **Teltonika RMS VPN** so your laptop routes to the boat LAN. Same hostnames and MCP URLs apply.

See **[vpn-remote-access.md](./vpn-remote-access.md)** for provider comparison, Tailscale subnet-router setup on SLA-2, and security checklist.

MCP is **not** exposed on the Teltonika LTE WAN — use VPN, not port-forward.

---

## Cursor MCP configuration

Copy [`.cursor/mcp.json.example`](../.cursor/mcp.json.example) to `.cursor/mcp.json` (gitignored) or add to Cursor Settings → MCP.

**At the regatta (boat LAN HTTP):**

```json
{
  "mcpServers": {
    "race-boat": {
      "url": "http://race.local:3100/mcp",
      "headers": { "Authorization": "Bearer YOUR_RACE_MCP_API_KEY" }
    },
    "race-neo4j": {
      "url": "http://race.local:3100/mcp/neo4j",
      "headers": { "Authorization": "Bearer YOUR_RACE_MCP_API_KEY" }
    },
    "race-influx": {
      "url": "http://race.local:3100/mcp/influx",
      "headers": { "Authorization": "Bearer YOUR_RACE_MCP_API_KEY" }
    },
    "race-signalk": {
      "url": "http://race.local:3100/mcp/signalk",
      "headers": { "Authorization": "Bearer YOUR_RACE_MCP_API_KEY" }
    }
  }
}
```

| Server | Data |
|--------|------|
| **race-neo4j** | Live standings, Cypher, fleet positions, course selection |
| **race-influx** | Flux queries, instrument snapshots, wind history |
| **race-signalk** | Live vessel state, AIS targets, alarms ([signalk-mcp-server](https://signalk.org/2025/introducing-signalk-mcp-server-ai-powered-marine-data-access) compatible) |
| **race-boat** | Neo4j + Influx + key Signal K tools (combined endpoint) |

**Harbor dev (local Docker):** use [`.cursor/mcp.harbor.json.example`](../.cursor/mcp.harbor.json.example) with stdio servers against `localhost` Neo4j/Influx.

Replace the API key with the value from the boat secret store (`/opt/ai-sailing-system/secrets/race_mcp_api_key`).

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

### Signal K (live instruments)

```
Via race-signalk MCP: get_vessel_state and summarize wind, SOG, COG, and heading.
Compare to Influx wind history for the last 15 minutes.
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

### Race-winning decision pack

```text
Use race MCP and answer in this format: recommendation, evidence, confidence, risk, re-check.
1) If race finished now, what are corrected-time results and our delta?
2) Who is above 105% polar and below 90% polar, where are they, and why?
3) Who has best VMG/course toward next mark (us vs top competitors)?
4) Who likely has wind/current advantage right now?
5) What is favored end now and does long-tack-first still hold?
6) How do we avoid overshooting mark; what layline trigger margin should we use?
7) What magnetic heading should we steer for next 3 minutes, with fallback on 5° shift?
```

Playbook: [race-decision-playbook.md](./race-decision-playbook.md)

---

## Available MCP tool groups

| Server | What you can ask |
|--------|------------------|
| **race-neo4j** | `cypher_query`, live standings, course selection, fleet positions, graph schema |
| **race-influx** | `flux_query`, latest instruments, wind history, list buckets |
| **race-signalk** | `get_vessel_state`, `get_ais_targets`, `get_active_alarms`, `list_available_paths`, `get_path_value` |
| **race-boat** | All Neo4j + Influx + key Signal K tools above (combined endpoint) |
| **race-context** | YAML, wiki, OKF concepts from onboard data repo *(planned)* |
| **race-tactical** | Wind zones, polar targets, start-line state *(planned)* |

Tool reference: [mcp-neo4j-influx.md](./mcp-neo4j-influx.md)

---

## Security notes

- Treat `RACE_MCP_API_KEY` like a race password — rotate per regatta.
- MCP is **read-only** in v1; it cannot steer, write Signal K, or push git.
- Do not port-forward `:3100` on the Teltonika LTE interface — use [VPN](./vpn-remote-access.md) instead.
- Prefer wired Ethernet to `race.local` in heavy Wi‑Fi traffic if available.

---

## Troubleshooting

| Symptom | Check |
|---------|--------|
| MCP connection refused | `docker ps` on race Pi — is `race-mcp-gateway` running? |
| 401 Unauthorized | API key matches `/opt/ai-sailing-system/secrets/race_mcp_api_key` |
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

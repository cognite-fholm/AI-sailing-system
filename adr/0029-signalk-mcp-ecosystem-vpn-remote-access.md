# ADR-0029: Signal K MCP ecosystem alignment and VPN remote access

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** cognite-fholm  
**Related:** [ADR-0012](./0012-race-side-mcp-laptop-cursor.md), [ADR-0009](./0009-dual-repository-race-data.md), [docs/vpn-remote-access.md](../docs/vpn-remote-access.md), [Signal K MCP announcement](https://signalk.org/2025/introducing-signalk-mcp-server-ai-powered-marine-data-access)

---

## Context

The Signal K project published an official **signalk-mcp-server** (npm) ecosystem pattern: MCP tools over Signal K REST (`get_vessel_state`, `get_ais_targets`, `list_available_paths`, …). Community forks (e.g. [VesselSense/signalk-mcp-server](https://github.com/VesselSense/signalk-mcp-server)) extend this with code-execution helpers.

Our **`race-mcp-gateway`** ([ADR-0012](./0012-race-side-mcp-laptop-cursor.md)) already exposes Neo4j and Influx MCP tools for laptop Cursor on the boat LAN. ADR-0012 listed **`signalk-snapshot`** as planned — that gap blocked parity with the ecosystem and with common agent prompts (“what is wind and SOG right now?”).

Separately, navigators sometimes need **remote access** from shore (harbor tent, coach ashore, post-race support) when the laptop is **not** on boat Wi‑Fi. The Teltonika LTE router sits behind **CGNAT** — inbound port-forward on `:3100` is fragile and insecure.

---

## Decision

### 1. Adopt signalk-mcp-server tool contracts in `race-mcp-gateway`

Implement a **Python Signal K REST client** and mount **`/mcp/signalk`** on the existing gateway. Tool names and semantics align with **signalk-mcp-server** so Cursor prompts and third-party docs transfer directly.

| Approach | Choice |
|----------|--------|
| Run separate npm `signalk-mcp-server` container | **No** — duplicate auth, ports, and lifecycle on a constrained Pi |
| Proxy to upstream npm server | **No** — extra hop; Node runtime on SLA-2 |
| **Native Python tools on gateway** | **Yes** — same bearer auth, boat LAN bind, one container |

We do **not** adopt generic **`influxdb-mcp-server`** — our bounded Flux tools and race buckets are already tailored ([docs/mcp-neo4j-influx.md](../docs/mcp-neo4j-influx.md)).

**Endpoints after this ADR:**

| Path | Server | Tools |
|------|--------|-------|
| `/mcp/signalk` | `race-signalk` | `get_initial_context`, `get_vessel_state`, `get_ais_targets`, `get_active_alarms`, `list_available_paths`, `get_path_value` |
| `/mcp` | `race-boat` | Neo4j + Influx + subset of Signal K (`get_vessel_state`, `get_ais_targets`) |

Configuration: `SIGNALK_URL` / `upstreams.signalk_url` → `http://telemetry.local:3000` (SLA-1).

### 2. VPN for inbound access to boat LAN (MCP, Signal K, Grafana)

Use a **mesh VPN** so shore laptops join the boat LAN **without** public port-forward on LTE.

**Primary recommendation: [Tailscale](https://tailscale.com/)**

| Criterion | Tailscale |
|-----------|-----------|
| CGNAT / LTE | Works — outbound WireGuard, no inbound ports |
| Raspberry Pi | Official packages; runs on SLA-2 (or all Pis) |
| Boat LAN reachability | **Subnet router** on `race.local` Pi advertises `192.168.x.0/24` (Teltonika LAN) |
| Cost | **Free** Personal (100 devices); Teams ~$6/user/mo if org ACLs needed |
| MCP access | `http://race.local:3100` or Tailscale MagicDNS name — **still requires `RACE_MCP_API_KEY`** |

**Secondary: Teltonika RMS VPN** — choose when the fleet already pays for **RMS** and wants router-centric hub management (OpenVPN hubs, RMS push). See [docs/vpn-remote-access.md](../docs/vpn-remote-access.md).

**Not recommended:** exposing `:3100` / `:3000` on the Teltonika WAN interface.

### 3. Security model (unchanged + VPN layer)

| Layer | Rule |
|-------|------|
| Network | VPN or boat Wi‑Fi only |
| Application | Bearer token on every MCP request |
| Data | Read-only Signal K REST; no autopilot or write tools |
| LTE | Git push via `race-live-sync` remains separate (GitHub token); VPN is for interactive access |

---

## Rationale

- **Ecosystem alignment** reduces custom prompt/docs drift and lets us reference [signalk.org MCP guidance](https://signalk.org/2025/introducing-signalk-mcp-server-ai-powered-marine-data-access).
- **Single gateway container** keeps SLA-2 footprint small vs Node sidecar.
- **Tailscale** is the best cost/ease tradeoff for hobby and club fleets: free tier, Pi support, subnet routing, no static IP on LTE.
- **RMS VPN** is valid when Teltonika RMS is already the fleet console — avoids a second control plane.

---

## Consequences

### Positive

- `signalk-snapshot` gap in ADR-0012 is **implemented** as `/mcp/signalk`.
- Shore coaches can use Cursor MCP over VPN with the same `mcp.json` URLs (via subnet route).
- Documented provider comparison for Teltonika integrators.

### Negative / trade-offs

- Tailscale subnet router adds a daemon on SLA-2 — monitor CPU during races.
- Two VPN options (Tailscale vs RMS) require a fleet policy pick — document in `deploy/env`.
- Full npm signalk-mcp-server feature parity (e.g. V8 code execution) is **out of scope** unless a future ADR adds it.

---

## Implementation

| Item | Location |
|------|----------|
| Signal K client | `race-mcp-gateway/race_mcp_gateway/signalk_client.py` |
| MCP mount | `race-mcp-gateway/race_mcp_gateway/servers/signalk.py` |
| VPN guide | `docs/vpn-remote-access.md` |
| Deployment map | `docs/ARCHITECTURE.md` § Deployment topology |
| Compose env | `SIGNALK_URL` in `docker-compose.sla-2.yml` |

---

## References

- [tonybentley/signalk-mcp-server](https://github.com/tonybentley/signalk-mcp-server) — reference tool API
- [Teltonika RMS VPN Hubs](https://wiki.teltonika-networks.com/view/RMS_VPN_Hubs)
- [Teltonika WireGuard](https://wiki.teltonika-networks.com/view/WireGuard_configuration_example)
- [Tailscale subnet routers](https://tailscale.com/kb/1019/subnets)

# Runtime secrets (simple hybrid model)

This project uses a simple hybrid model:

- **GitHub Actions secrets** for CI/CD only
- **On-device secret files** on each Raspberry Pi for runtime credentials

Do not commit real secret values to git.

## Directory and permissions (on Pi)

Create once per boat:

```bash
sudo mkdir -p /opt/ai-sailing-system/secrets
sudo chown "$USER":"$USER" /opt/ai-sailing-system/secrets
chmod 700 /opt/ai-sailing-system/secrets
```

Install secrets as files (all `chmod 600`):

| File | Used by | Required |
|------|---------|----------|
| `github_token` | `race-live-sync` push to AI-sailing-data | Yes |
| `race_mcp_api_key` | `race-mcp-gateway` auth | Yes if MCP enabled |
| `neo4j_mcp_password` | MCP Neo4j read role | Yes if MCP enabled |
| `influx_read_token` | MCP Influx read queries | Yes if MCP enabled |
| `rms_client.ovpn` | OpenVPN client profile (RMS VPN) | Only for RMS mode |
| `rms_auth_user` | OpenVPN auth user (if provider requires) | Optional |
| `rms_auth_password` | OpenVPN auth password (if provider requires) | Optional |

Example:

```bash
printf '%s' 'ghp_xxx' > /opt/ai-sailing-system/secrets/github_token
printf '%s' 'mcp-race-key-xxx' > /opt/ai-sailing-system/secrets/race_mcp_api_key
printf '%s' 'neo4j-pass-xxx' > /opt/ai-sailing-system/secrets/neo4j_mcp_password
printf '%s' 'influx-token-xxx' > /opt/ai-sailing-system/secrets/influx_read_token
chmod 600 /opt/ai-sailing-system/secrets/*
```

## Validate before harbor pull

Run:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets
```

Permission checks are enforced on Linux/Pi. On Windows dev machines, mode-bit checks are skipped.

For RMS VPN mode:

```bash
python deploy/secrets/check_secrets.py --secrets-dir /opt/ai-sailing-system/secrets --require-rms
```

## Wire secrets into runtime env

Render a gitignored env include from secret files:

```bash
./scripts/render-secrets-env.sh
```

Or run one-step preparation (render + validate):

```bash
./scripts/harbor-prepare.sh
```

This writes `deploy/env/harbor.secrets.env` with:

```env
RACE_MCP_API_KEY=...
NEO4J_MCP_PASSWORD=...
INFLUX_READ_TOKEN=...
```

Then source it in your shell before compose/pull scripts:

```bash
set -a
source deploy/env/harbor.secrets.env
source deploy/env/harbor.env
set +a
```

Or copy these values into local, gitignored `deploy/env/harbor.env`:

```env
RACE_MCP_API_KEY=...
NEO4J_MCP_PASSWORD=...
INFLUX_READ_TOKEN=...
```

Recommended workflow:

1. Keep canonical secret values in files under `/opt/ai-sailing-system/secrets`.
2. Run `./scripts/harbor-prepare.sh` (or run render + validate separately).
3. Source `harbor.secrets.env` + `harbor.env` before harbor operations.

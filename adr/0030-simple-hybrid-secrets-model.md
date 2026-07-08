# ADR-0030: Simple hybrid secrets model for race operations

**Status:** Accepted  
**Date:** 2026-07-08  
**Deciders:** cognite-fholm  
**Related:** [ADR-0008](./0008-github-docker-deployment-lifecycle.md), [ADR-0027](./0027-data-repo-runtime-policy-zero-pi-config.md), [ADR-0029](./0029-signalk-mcp-ecosystem-vpn-remote-access.md), [deploy/secrets/README.md](../deploy/secrets/README.md)

---

## Context

Race operations require sensitive credentials across two planes:

1. **CI/CD plane** (GitHub Actions): image publish, optional cross-repo automation.
2. **Runtime plane** (on boat Raspberry Pis): MCP API keys, database read credentials, VPN client material, GitHub token for `race-live-sync`.

The team wants a setup that is simpler than a full cloud key vault rollout, works offline during race, and avoids committing secrets in git.

---

## Decision

Adopt a **simple hybrid model**:

- Use **GitHub Actions secrets** only for CI/CD.
- Use **on-device secret files** at `/opt/ai-sailing-system/secrets` (or `AI_SAILING_SECRETS_DIR`) for runtime.
- Validate runtime secrets before `harbor-pull` with `deploy/secrets/check_secrets.py`.

### Runtime secret files

Required baseline:

- `github_token`
- `race_mcp_api_key`
- `neo4j_mcp_password`
- `influx_read_token`

Required only when `VPN_PROVIDER=rms`:

- `rms_client.ovpn`

Permissions policy:

- Directory: `700`
- Secret files: `600`

### Guardrails

1. No secret values in tracked files (`*.env.example`, docs, compose files).
2. No secret values in image build args.
3. Harbor scripts fail early if required runtime secret files are missing or too permissive.

---

## Rationale

- Works with current single-boat operation and race-week workflow.
- Preserves offline resilience once secrets are present on Pi.
- Avoids introducing extra cloud identity/runtime dependencies before they are needed.
- Leaves room for future migration to Azure Key Vault or equivalent if team scale increases.

---

## Consequences

### Positive

- Low operational complexity and clear operator checklist.
- Better protection against accidental secret leakage in git.
- Consistent runtime checks before image pull/restart actions.

### Trade-offs

- Manual secret placement on each boat is still required.
- Rotation discipline depends on process, not central automation.
- No central audit trail for runtime secret reads.

---

## Implementation

- Policy docs: `deploy/secrets/README.md`
- Validation script: `deploy/secrets/check_secrets.py`
- Harbor integration: `scripts/harbor-pull.sh`
- Tests: `tests/unit/test_secrets_check.py`

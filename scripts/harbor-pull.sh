#!/usr/bin/env bash
# Pull digest-pinned images and restart compose stack for one SLA tier.
# Usage: ./scripts/harbor-pull.sh --tier 2
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TIER=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier) TIER="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$TIER" || ! "$TIER" =~ ^[123]$ ]]; then
  echo "Usage: $0 --tier {1|2|3}"
  exit 1
fi

if [[ -f deploy/locks/current.env ]]; then
  set -a
  # shellcheck source=/dev/null
  source deploy/locks/current.env
  set +a
fi

if [[ -f deploy/env/harbor.env ]]; then
  set -a
  # shellcheck source=/dev/null
  source deploy/env/harbor.env
  set +a
fi

if [[ -f deploy/env/harbor.secrets.env ]]; then
  set -a
  # shellcheck source=/dev/null
  source deploy/env/harbor.secrets.env
  set +a
fi

SECRETS_DIR="${AI_SAILING_SECRETS_DIR:-/opt/ai-sailing-system/secrets}"
if [[ "${SKIP_SECRETS_CHECK:-false}" != "true" ]] && [[ -f deploy/secrets/check_secrets.py ]]; then
  if command -v python3 &>/dev/null; then
    RMS_FLAG=()
    [[ "${VPN_PROVIDER:-}" == "rms" ]] && RMS_FLAG=(--require-rms)
    echo "Validating runtime secrets in $SECRETS_DIR ..."
    python3 deploy/secrets/check_secrets.py --secrets-dir "$SECRETS_DIR" "${RMS_FLAG[@]}"
  else
    echo "WARN: python3 not found; skipping deploy/secrets/check_secrets.py validation."
  fi
fi

if [[ "${RACE_MODE:-false}" == "true" ]]; then
  echo "ERROR: RACE_MODE=true — refuse pull (guardrail GR-1). Use race freeze procedure."
  exit 1
fi

LIFECYCLE_STATE="${RACE_LIFECYCLE_STATE:-/var/run/ai-sailing/race-lifecycle.json}"
if [[ -f "$LIFECYCLE_STATE" ]] && grep -q '"race_mode": true' "$LIFECYCLE_STATE" 2>/dev/null; then
  echo "ERROR: lifecycle race_mode=true — refuse pull (ADR-0027). Wait until regatta archived."
  exit 1
fi

COMPOSE_FILE="docker-compose.sla-${TIER}.yml"
if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "Missing $COMPOSE_FILE (Phase 1+)"
  exit 1
fi

EXTRA=()
if [[ "$TIER" != "1" && -f docker-compose.harbor.yml ]]; then
  EXTRA=(-f docker-compose.harbor.yml)
fi

echo "Pulling SLA-${TIER}..."
docker compose -f "$COMPOSE_FILE" "${EXTRA[@]}" pull
docker compose -f "$COMPOSE_FILE" "${EXTRA[@]}" up -d
echo "Done SLA-${TIER}"

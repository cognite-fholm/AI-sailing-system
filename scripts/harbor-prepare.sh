#!/usr/bin/env bash
# Prepare runtime secrets for harbor operations in one step.
# 1) Render deploy/env/harbor.secrets.env from on-device secret files
# 2) Validate required secret files and permissions
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SECRETS_DIR="${AI_SAILING_SECRETS_DIR:-/opt/ai-sailing-system/secrets}"
OUT_FILE="${1:-deploy/env/harbor.secrets.env}"

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required for harbor secrets preparation."
  exit 1
fi

RMS_FLAG=()
if [[ "${VPN_PROVIDER:-}" == "rms" ]]; then
  RMS_FLAG=(--require-rms)
fi

echo "Rendering env include from $SECRETS_DIR ..."
python3 deploy/secrets/render_secrets_env.py \
  --secrets-dir "$SECRETS_DIR" \
  --output "$OUT_FILE" \
  --overwrite

echo "Validating secret files in $SECRETS_DIR ..."
python3 deploy/secrets/check_secrets.py \
  --secrets-dir "$SECRETS_DIR" \
  "${RMS_FLAG[@]}"

echo "OK: harbor secrets prepared ($OUT_FILE)"

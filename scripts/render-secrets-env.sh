#!/usr/bin/env bash
# Render deploy/env/harbor.secrets.env from on-device secret files.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SECRETS_DIR="${AI_SAILING_SECRETS_DIR:-/opt/ai-sailing-system/secrets}"
OUT_FILE="${1:-deploy/env/harbor.secrets.env}"

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is required for render_secrets_env.py"
  exit 1
fi

python3 deploy/secrets/render_secrets_env.py \
  --secrets-dir "$SECRETS_DIR" \
  --output "$OUT_FILE" \
  --overwrite

echo "Wrote $OUT_FILE"

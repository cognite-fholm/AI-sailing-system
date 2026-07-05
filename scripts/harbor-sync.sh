#!/usr/bin/env bash
# Sync non-container artifacts: models, OKF knowledge, config.
# Does NOT pull GHCR images — use harbor-pull.sh for that.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

MODELS_DIR="${MODELS_DIR:-/opt/models}"
KNOWLEDGE_DIR="${KNOWLEDGE_DIR:-/opt/knowledge/sailing-system}"
CONFIG_DIR="${CONFIG_DIR:-/opt/ai-sailing-system/config}"

echo "=== Harbor sync (artifacts only) ==="

if [[ -d knowledge/sailing-system ]]; then
  echo "OKF bundle → $KNOWLEDGE_DIR"
  mkdir -p "$KNOWLEDGE_DIR"
  rsync -av --delete knowledge/sailing-system/ "$KNOWLEDGE_DIR/" 2>/dev/null || \
    cp -r knowledge/sailing-system/. "$KNOWLEDGE_DIR/" || echo "Skip OKF — bundle not yet created"
fi

if [[ -d config ]]; then
  echo "Config → $CONFIG_DIR"
  mkdir -p "$CONFIG_DIR"
  rsync -av config/ "$CONFIG_DIR/" 2>/dev/null || cp -r config/. "$CONFIG_DIR/"
fi

if [[ -d models ]]; then
  echo "Model manifests → $MODELS_DIR"
  mkdir -p "$MODELS_DIR"
  # Copy manifests only; GGUF binaries downloaded separately or via USB
  rsync -av models/ "$MODELS_DIR/" 2>/dev/null || true
fi

echo "=== Harbor sync complete ==="
echo "Next: ./scripts/harbor-pull.sh --tier {1|2|3}"

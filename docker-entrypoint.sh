#!/usr/bin/env sh
set -e

# Seed the persistent volume from the image on first boot only.
# VAULTS_ROOT lives on the mounted fly volume (/data/vaults); the bundled copy
# lives at /app/vaults-seed. If the volume has no vaults yet, copy the seed in.
: "${VAULTS_ROOT:=/data/vaults}"
SEED_DIR="/app/vaults-seed"

if [ ! -d "$VAULTS_ROOT" ] || [ -z "$(ls -A "$VAULTS_ROOT" 2>/dev/null)" ]; then
    echo "[entrypoint] Seeding vaults at $VAULTS_ROOT from $SEED_DIR"
    mkdir -p "$VAULTS_ROOT"
    cp -a "$SEED_DIR/." "$VAULTS_ROOT/"
fi

# Initialise a git repo on the data volume so the compile agent's per-vault
# auto-commit works and the vaults get a local version history.
DATA_ROOT="$(dirname "$VAULTS_ROOT")"
if [ ! -d "$DATA_ROOT/.git" ]; then
    echo "[entrypoint] Initialising git repo at $DATA_ROOT"
    git init -q "$DATA_ROOT" || true
    git -C "$DATA_ROOT" config user.email "brain@fly.local" || true
    git -C "$DATA_ROOT" config user.name "brain-mcp" || true
fi

exec "$@"

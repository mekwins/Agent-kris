#!/usr/bin/env sh
set -e

# The persistent fly volume (mounted at /data) is the live copy of the vaults.
# GitHub (brain-vaults) is the source of truth. On boot we make sure the volume
# holds a clone of that repo and is up to date; the compile agent pushes back.
: "${VAULTS_ROOT:=/data/vaults}"
: "${VAULTS_REPO:=}"   # e.g. github.com/mekwins/brain-vaults.git (no scheme/token)

# Build the authenticated remote from the token secret (never printed).
remote_url() {
    if [ -n "$GITHUB_TOKEN" ]; then
        echo "https://x-access-token:${GITHUB_TOKEN}@${VAULTS_REPO}"
    else
        echo "https://${VAULTS_REPO}"
    fi
}

if [ -n "$VAULTS_REPO" ]; then
    if [ ! -d "$VAULTS_ROOT/.git" ]; then
        echo "[entrypoint] Cloning vaults repo into $VAULTS_ROOT"
        rm -rf "$VAULTS_ROOT"
        git clone "$(remote_url)" "$VAULTS_ROOT" || echo "[entrypoint] WARNING: clone failed"
    fi
    if [ -d "$VAULTS_ROOT/.git" ]; then
        # Refresh the tokenised remote (the token may rotate between deploys),
        # set the commit identity, and pull the latest before serving.
        git -C "$VAULTS_ROOT" remote set-url origin "$(remote_url)" || true
        git -C "$VAULTS_ROOT" config user.email "brain@fly.local" || true
        git -C "$VAULTS_ROOT" config user.name "brain-mcp" || true
        git -C "$VAULTS_ROOT" config pull.rebase true || true
        git -C "$VAULTS_ROOT" pull --rebase --autostash || echo "[entrypoint] pull skipped"
    fi
else
    echo "[entrypoint] VAULTS_REPO unset — using whatever is already on the volume"
    mkdir -p "$VAULTS_ROOT"
fi

exec "$@"

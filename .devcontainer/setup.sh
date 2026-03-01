#!/usr/bin/env bash
set -euo pipefail

# ── Auto-detect workspace root (works with any repo name) ────────────
WORKSPACE_ROOT="${CODESPACE_VSCODE_FOLDER:-}"
if [ -z "$WORKSPACE_ROOT" ] || [ ! -d "$WORKSPACE_ROOT" ]; then
  WORKSPACE_ROOT="$(find /workspaces -mindepth 1 -maxdepth 1 -type d | head -1)"
fi
if [ -z "$WORKSPACE_ROOT" ]; then
  echo "[!] Cannot find workspace. Exiting."
  exit 1
fi
echo "[*] Workspace root: $WORKSPACE_ROOT"

echo "[*] Installing system dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
  gcc-multilib \
  gdb \
  nasm \
  2>/dev/null

echo "[*] Installing Python packages..."
pip install --quiet pwntools

echo "[*] Building vulnerable binaries..."
cd "$WORKSPACE_ROOT"
make clean || true
make all

echo "[*] Installing tunnel server dependencies..."
cd "$WORKSPACE_ROOT/tunnel"
npm install --production

echo "[+] Setup complete. Lab is ready."

#!/usr/bin/env bash
set -euo pipefail

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
cd /workspaces/shellcoder-lab  # codespaces default mount point
make clean || true
make all

echo "[*] Installing tunnel server dependencies..."
cd /workspaces/shellcoder-lab/tunnel
npm install --production

echo "[+] Setup complete. Lab is ready."

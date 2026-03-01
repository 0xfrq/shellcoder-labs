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

TUNNEL_DIR="$WORKSPACE_ROOT/tunnel"
LOG_FILE="/tmp/tunnel-server.log"

# ── Kill any previous tunnel instance ─────────────────────────────────
if [ -f /tmp/tunnel-server.pid ]; then
  OLD_PID=$(cat /tmp/tunnel-server.pid)
  kill "$OLD_PID" 2>/dev/null || true
  rm -f /tmp/tunnel-server.pid
fi

# ── Auto-install npm dependencies if missing ──────────────────────────
if [ ! -d "$TUNNEL_DIR/node_modules" ]; then
  echo "[*] node_modules not found — running npm install..."
  cd "$TUNNEL_DIR"
  npm install --production 2>&1 | tee -a "$LOG_FILE"
fi

# ── Start the tunnel server ──────────────────────────────────────────
echo "[*] Starting WebSocket terminal tunnel on port 7681..."
cd "$TUNNEL_DIR"
node server.js >> "$LOG_FILE" 2>&1 &
TUNNEL_PID=$!
echo "$TUNNEL_PID" > /tmp/tunnel-server.pid
echo "[+] Tunnel server started (PID: $TUNNEL_PID). Logs: $LOG_FILE"

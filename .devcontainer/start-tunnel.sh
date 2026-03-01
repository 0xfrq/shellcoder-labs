#!/usr/bin/env bash
set -euo pipefail

TUNNEL_DIR="/workspaces/shellcoder-lab/tunnel"
LOG_FILE="/tmp/tunnel-server.log"

echo "[*] Starting WebSocket terminal tunnel on port 7681..."
cd "$TUNNEL_DIR"
node server.js >> "$LOG_FILE" 2>&1 &
TUNNEL_PID=$!
echo "$TUNNEL_PID" > /tmp/tunnel-server.pid
echo "[+] Tunnel server started (PID: $TUNNEL_PID). Logs: $LOG_FILE"

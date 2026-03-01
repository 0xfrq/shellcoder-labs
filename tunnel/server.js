/**
 * WebSocket Terminal Tunnel Server
 *
 * Runs inside the GitHub Codespace and exposes a PTY shell over WebSocket.
 * Clients (browser xterm.js) connect to ws://<host>:7681/ws
 * A lightweight Express server serves the static HTML client on GET /.
 *
 * Security:  Relies on Codespace port‑visibility settings (private / org / public).
 *            An optional TUNNEL_TOKEN env‑var gates the WS upgrade if set.
 */

const http      = require("http");
const path      = require("path");
const fs        = require("fs");
const express   = require("express");
const { WebSocketServer } = require("ws");
const pty       = require("node-pty");

const PORT  = parseInt(process.env.TUNNEL_PORT || "7681", 10);
const TOKEN = process.env.TUNNEL_TOKEN || "";       // optional auth
const SHELL = process.env.SHELL || "/bin/bash";

// ── Resolve a working CWD (handles any repo name / mount point) ──────
function resolveCwd() {
  // 1. Explicit env override
  if (process.env.TUNNEL_CWD && fs.existsSync(process.env.TUNNEL_CWD)) {
    return process.env.TUNNEL_CWD;
  }
  // 2. Codespaces sets CODESPACE_VSCODE_FOLDER
  if (process.env.CODESPACE_VSCODE_FOLDER && fs.existsSync(process.env.CODESPACE_VSCODE_FOLDER)) {
    return process.env.CODESPACE_VSCODE_FOLDER;
  }
  // 3. Scan /workspaces/ for the first directory that exists
  const wsRoot = "/workspaces";
  if (fs.existsSync(wsRoot)) {
    const entries = fs.readdirSync(wsRoot, { withFileTypes: true });
    const dir = entries.find(e => e.isDirectory());
    if (dir) return path.join(wsRoot, dir.name);
  }
  // 4. Fallback: home directory (always exists)
  return process.env.HOME || "/home/vscode";
}

const CWD = resolveCwd();
console.log(`[*] Resolved CWD: ${CWD}`);

// ── Express: serve the browser client ────────────────────────────────
const app = express();
app.use(express.static(path.join(__dirname, "client")));

const server = http.createServer(app);

// ── WebSocket: terminal sessions ─────────────────────────────────────
const wss = new WebSocketServer({ server, path: "/ws" });

wss.on("connection", (ws, req) => {
  // Optional token check
  if (TOKEN) {
    const url   = new URL(req.url, `http://${req.headers.host}`);
    const token = url.searchParams.get("token");
    if (token !== TOKEN) {
      ws.close(4001, "Unauthorized");
      return;
    }
  }

  console.log(`[+] New terminal session from ${req.socket.remoteAddress}`);

  // Use CWD if it still exists, otherwise fall back to HOME
  const sessionCwd = fs.existsSync(CWD) ? CWD : (process.env.HOME || "/tmp");

  const term = pty.spawn(SHELL, [], {
    name: "xterm-256color",
    cols: 120,
    rows: 30,
    cwd: sessionCwd,
    env: {
      ...process.env,
      TERM: "xterm-256color",
    },
  });

  // PTY → WS
  term.onData((data) => {
    try { ws.send(data); } catch (_) { /* client gone */ }
  });

  // WS → PTY  (supports resize messages)
  ws.on("message", (msg) => {
    const str = msg.toString();
    // Resize message: JSON  { "type": "resize", "cols": N, "rows": N }
    if (str.startsWith("{")) {
      try {
        const obj = JSON.parse(str);
        if (obj.type === "resize" && obj.cols && obj.rows) {
          term.resize(obj.cols, obj.rows);
          return;
        }
      } catch (_) { /* not JSON, treat as input */ }
    }
    term.write(str);
  });

  ws.on("close", () => {
    console.log(`[-] Session closed`);
    term.kill();
  });

  term.onExit(() => {
    ws.close();
  });
});

// ── Health endpoint (useful for wake‑check) ──────────────────────────
app.get("/health", (_req, res) => {
  res.json({ status: "ok", uptime: process.uptime() });
});

// ── Start ────────────────────────────────────────────────────────────
server.listen(PORT, "0.0.0.0", () => {
  console.log(`[+] Tunnel server listening on 0.0.0.0:${PORT}`);
  console.log(`    Client UI : http://localhost:${PORT}`);
  console.log(`    WebSocket : ws://localhost:${PORT}/ws`);
  if (TOKEN) console.log(`    Token auth: ENABLED`);
});

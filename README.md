# Shellcoder Lab

Hands-on exploit development labs running entirely in **GitHub Codespaces** — no local setup required.

Other users don't need to clone, install, or configure anything. They just open a URL and get a live terminal in the browser.

---

## Architecture

```
┌──────────────┐        HTTPS / WSS         ┌──────────────────────────────┐
│   Browser    │ ◄─────────────────────────► │  GitHub Codespace            │
│  (xterm.js)  │   port 7681 (forwarded)     │                              │
└──────────────┘                             │  tunnel/server.js            │
                                             │    ├─ Express  → serves UI   │
       ┌──────────┐    GitHub REST API       │    └─ WS + pty → shell       │
       │ Trigger  │ ───────────────────────► │                              │
       │ (script/ │   codespaces/start       │  vuln binary (auto-built)    │
       │  action) │                          │  gdb, pwntools, etc.         │
       └──────────┘                          └──────────────────────────────┘
```

## Quick Start (for lab users)

Just open this link — everything provisions automatically:

[![Open in Codespaces](https://github.com/codespaces/badge.svg)](https://github.com/codespaces/new?repo=0xfrq/shellcoder-labs)

Once the Codespace is ready the terminal tunnel auto-starts on port **7681**.
Open the **Ports** tab in VS Code → click the forwarded URL for port 7681 → you get a browser-based shell.

## Wake a Codespace Externally

You can start/wake the Codespace from outside (CI, scripts, Slack bots, etc.) without anyone opening the Codespaces UI.

### Option A: Python script

```bash
export GITHUB_TOKEN="ghp_..."          # needs `codespace` scope

# Auto-detect or create codespace, wait for tunnel, print URL
python scripts/wake_and_tunnel.py --repo 0xfrq/shellcoder-labs --create

# Target a specific codespace by name
python scripts/wake_and_tunnel.py --name fuzzy-invention-abc123

# With optional WS auth token
python scripts/wake_and_tunnel.py --repo 0xfrq/shellcoder-labs --token mysecret
```

Output:

```
============================================================
  Terminal URL : https://<name>-7681.app.github.dev
  WebSocket    : wss://<name>-7681.app.github.dev/ws
============================================================
```

### Option B: GitHub Actions (one-click / API trigger)

Go to **Actions → Wake Lab Codespace → Run workflow**, or trigger via API:

```bash
curl -X POST \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/OWNER/REPO/actions/workflows/wake-lab.yml/dispatches \
  -d '{"ref":"main","inputs":{"tunnel_token":"optional-secret"}}'
```

The workflow wakes the Codespace and prints the terminal URL in the **job summary**.

### Option C: Raw GitHub API

```bash
# List your codespaces
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user/codespaces

# Start a stopped codespace
curl -X POST -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/user/codespaces/CODESPACE_NAME/start
```

## Setup (for repo maintainers)

1. **Make the repo a template** — Go to repo Settings → check "Template repository"
2. **Add a PAT as secret** — Settings → Secrets → Actions → add `CODESPACE_PAT` with `codespace` scope
3. Push. Done. The devcontainer config handles everything else.

### What happens on Codespace create:

1. `.devcontainer/setup.sh` runs:
   - Installs `gcc-multilib`, `gdb`, `nasm`
   - Installs `pwntools`
   - Runs `make` to compile the vulnerable binary
   - Runs `npm install` in `tunnel/`
2. `.devcontainer/start-tunnel.sh` runs on every start:
   - Launches the WebSocket terminal server on port 7681

### Environment variables

| Variable | Default | Description |
|---|---|---|
| `TUNNEL_PORT` | `7681` | Port the tunnel server listens on |
| `TUNNEL_TOKEN` | _(empty)_ | If set, clients must pass `?token=` to connect |
| `TUNNEL_CWD` | `/workspaces/shellcoder-lab` | Working directory for new terminal sessions |

## Project Structure

```
.devcontainer/
  devcontainer.json       # Codespace provisioning config
  setup.sh                # One-time setup (packages, build)
  start-tunnel.sh         # Starts tunnel on every codespace boot
.github/workflows/
  wake-lab.yml            # External trigger workflow
tunnel/
  server.js               # WebSocket terminal server (node-pty + ws)
  client/index.html       # Browser terminal UI (xterm.js)
  package.json
scripts/
  wake_and_tunnel.py      # CLI tool to wake codespace + get URL
labs/
  chapter2-stack-overflow/
    vuln.c                # Vulnerable program
    exploit.py            # pwntools exploit skeleton
    README.md             # Lab instructions
Makefile                  # Compiles vuln binaries
```

## Security Notes

- Port visibility is controlled by `.devcontainer/devcontainer.json` (`portsAttributes.visibility`). Set to `"private"` (default) or `"public"` depending on your use case.
- Optional `TUNNEL_TOKEN` adds a query-param gate to the WebSocket — lightweight but not a substitute for private port visibility.
- The vulnerable binaries are intentionally compiled without protections (`-fno-stack-protector -z execstack -no-pie -m32`). This is by design for the labs.

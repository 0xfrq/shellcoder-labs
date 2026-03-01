#!/usr/bin/env python3
"""
wake_and_tunnel.py  –  Externally wake a GitHub Codespace and return the tunnel URL.

Usage:
    # Set your GitHub PAT (needs `codespace` scope)
    export GITHUB_TOKEN="ghp_..."

    # Wake (or create) the codespace and get the terminal URL
    python scripts/wake_and_tunnel.py --repo 0xfrq/shellcoder-labs

    # With a specific codespace name (if you already have one)
    python scripts/wake_and_tunnel.py --name fuzzy-invention-abc123

    # Optionally pass a tunnel token for WS auth
    python scripts/wake_and_tunnel.py --repo 0xfrq/shellcoder-labs --token mysecret

Environment variables (alternative to flags):
    GITHUB_TOKEN        GitHub personal access token (codespace scope)
    CODESPACE_NAME      Target codespace name
    TUNNEL_TOKEN        Optional WS authentication token
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error

API = "https://api.github.com"
POLL_INTERVAL = 5       # seconds
MAX_WAIT      = 300     # 5 minutes
TUNNEL_PORT   = 7681


# ── GitHub API helpers ────────────────────────────────────────────────

def gh_headers(token: str) -> dict:
    return {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def gh_request(method: str, path: str, token: str, body: dict | None = None):
    url  = f"{API}{path}"
    data = json.dumps(body).encode() if body else None
    req  = urllib.request.Request(url, data=data, headers=gh_headers(token), method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read()) if resp.status != 204 else {}
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"[!] GitHub API {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)


# ── Codespace operations ─────────────────────────────────────────────

def list_codespaces(token: str, repo: str | None = None) -> list:
    """List codespaces for the authenticated user, optionally filtered by repo."""
    data = gh_request("GET", "/user/codespaces", token)
    spaces = data.get("codespaces", [])
    if repo:
        spaces = [c for c in spaces if c["repository"]["full_name"] == repo]
    return spaces


def get_codespace(token: str, name: str) -> dict:
    return gh_request("GET", f"/user/codespaces/{name}", token)


def create_codespace(token: str, repo: str) -> dict:
    """Create a new codespace from the repo's default branch."""
    print(f"[*] Creating new codespace for {repo}...")
    owner, repo_name = repo.split("/")
    body = {
        "repository_id": _get_repo_id(token, owner, repo_name),
        "ref": "main",
        "machine": "basicLinux32gb",          # 2‑core, cheapest
    }
    return gh_request("POST", "/user/codespaces", token, body)


def _get_repo_id(token: str, owner: str, repo_name: str) -> int:
    data = gh_request("GET", f"/repos/{owner}/{repo_name}", token)
    return data["id"]


def start_codespace(token: str, name: str) -> dict:
    """Start a stopped codespace."""
    print(f"[*] Starting codespace {name}...")
    return gh_request("POST", f"/user/codespaces/{name}/start", token)


def wait_until_available(token: str, name: str) -> dict:
    """Poll until the codespace reaches 'Available' state."""
    elapsed = 0
    while elapsed < MAX_WAIT:
        cs = get_codespace(token, name)
        state = cs.get("state", "Unknown")
        print(f"    state: {state}  ({elapsed}s)")
        if state == "Available":
            return cs
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    print("[!] Timed out waiting for codespace to become available.", file=sys.stderr)
    sys.exit(1)


# ── Port / URL helpers ───────────────────────────────────────────────

def get_tunnel_url(codespace: dict, token_param: str = "") -> str:
    """
    Codespaces forwarded ports follow the pattern:
      https://<codespace-name>-<port>.app.github.dev
    """
    name = codespace["name"]
    base = f"https://{name}-{TUNNEL_PORT}.app.github.dev"
    if token_param:
        base += f"?token={token_param}"
    return base


def wait_for_tunnel(url: str, timeout: int = 120) -> bool:
    """Poll the /health endpoint until the tunnel server is up."""
    health = url.split("?")[0] + "/health"
    elapsed = 0
    while elapsed < timeout:
        try:
            req = urllib.request.Request(health)
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(POLL_INTERVAL)
        elapsed += POLL_INTERVAL
    return False


# ── Main ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Wake a GitHub Codespace and get the terminal tunnel URL")
    parser.add_argument("--repo",  default=os.getenv("CODESPACE_REPO"),  help="owner/repo  (e.g. 0xfrq/shellcoder-labs)")
    parser.add_argument("--name",  default=os.getenv("CODESPACE_NAME"),  help="Existing codespace name")
    parser.add_argument("--token", default=os.getenv("TUNNEL_TOKEN", ""), help="Optional WS auth token")
    parser.add_argument("--create", action="store_true",                  help="Create codespace if none exists")
    args = parser.parse_args()

    gh_token = os.environ.get("GITHUB_TOKEN")
    if not gh_token:
        print("[!] GITHUB_TOKEN env var is required (needs `codespace` scope).", file=sys.stderr)
        sys.exit(1)

    # 1. Resolve codespace
    codespace = None
    if args.name:
        codespace = get_codespace(gh_token, args.name)
    elif args.repo:
        spaces = list_codespaces(gh_token, args.repo)
        if spaces:
            codespace = spaces[0]
            print(f"[*] Found existing codespace: {codespace['name']}")
        elif args.create:
            codespace = create_codespace(gh_token, args.repo)
        else:
            print("[!] No codespace found. Re‑run with --create to create one.", file=sys.stderr)
            sys.exit(1)
    else:
        print("[!] Provide --repo or --name.", file=sys.stderr)
        sys.exit(1)

    name  = codespace["name"]
    state = codespace.get("state", "Unknown")
    print(f"[*] Codespace: {name}  State: {state}")

    # 2. Start if not running
    if state != "Available":
        start_codespace(gh_token, name)
        codespace = wait_until_available(gh_token, name)

    # 3. Build tunnel URL
    tunnel_url = get_tunnel_url(codespace, args.token)
    print(f"\n[*] Waiting for tunnel server to come up...")

    if wait_for_tunnel(tunnel_url):
        print(f"\n{'='*60}")
        print(f"  Terminal URL : {tunnel_url}")
        print(f"  WebSocket    : wss://{codespace['name']}-{TUNNEL_PORT}.app.github.dev/ws")
        print(f"{'='*60}\n")
    else:
        print(f"\n[!] Tunnel server did not respond in time.")
        print(f"    The codespace IS running — the tunnel may still be starting.")
        print(f"    Try opening: {tunnel_url}")

    # 4. Output machine‑readable JSON to stdout
    result = {
        "codespace":  name,
        "state":      "Available",
        "tunnel_url": tunnel_url,
        "ws_url":     f"wss://{codespace['name']}-{TUNNEL_PORT}.app.github.dev/ws",
    }
    print(json.dumps(result))


if __name__ == "__main__":
    main()

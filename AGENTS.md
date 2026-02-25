# AGENTS.md — Rayobrowse Setup Guide for AI Agents

End-to-end setup, verification, and troubleshooting for AI agents and
automated pipelines working with the rayobrowse repository.

---

## What This Project Is

Rayobrowse is a Chromium-based stealth browser that runs inside Docker.
A lightweight Python SDK (`rayobrowse`) connects to a daemon inside the
container. You automate pages using standard Playwright, Selenium, or
Puppeteer over a CDP WebSocket — no changes to your existing scripts needed.

---

## Prerequisites

- **Docker** with Compose v2 (`docker compose` — note: no hyphen)
- **Python 3.10+**
- **~2 GB free RAM** (~300 MB per concurrent browser instance)

---

## End-to-End Setup

### Step 1 — Configure the environment

```bash
cp .env.example .env
```

Open `.env` and set `STEALTH_BROWSER_ACCEPT_TERMS=true`. This is **required**
before the daemon will create any browsers. By setting this you confirm you
have read and agree to the terms in:
- README: https://github.com/rayobyte-data/rayobrowse/blob/main/README.md
- LICENSE: https://github.com/rayobyte-data/rayobrowse/blob/main/LICENSE

The daemon will refuse all `create_browser()` calls until this is set to `true`.

To write the file non-interactively:

```bash
cat > .env << 'EOF'
STEALTH_BROWSER_API_KEY=
STEALTH_BROWSER_NOVNC=true
STEALTH_BROWSER_ACCEPT_TERMS=true
EOF
```

### Step 2 — Start the container

```bash
docker compose up -d
```

### Step 3 — Wait for the daemon to be healthy

Poll until the health endpoint returns `"success": true`:

```bash
until curl -sf http://localhost:9222/health \
  | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('success') else 1)" \
  2>/dev/null; do
  echo "Waiting for daemon..."; sleep 2
done
echo "Daemon is ready."
```

Expected healthy response:

```json
{"success": true, "data": {"status": "healthy"}}
```

If the daemon is not healthy after ~60 seconds, check logs:

```bash
docker compose logs --tail=50
```

### Step 4 — Install the Python SDK

```bash
pip install rayobrowse playwright
```

### Step 5 — Verify end-to-end

```bash
python examples/verify_setup.py
```

Expected output (exit code 0 = success):

```
INFO: Daemon healthy.
INFO: Requesting headless browser...
INFO: Browser ready: ws://localhost:9222/cdp/...
INFO: Page title: "Example Domain"
INFO: ✓ Setup verified successfully.
```

Exit code 1 means a step failed — the error line will say exactly what went
wrong and what to do.

---

## How It Works

```
.env (STEALTH_BROWSER_ACCEPT_TERMS=true)
  └─> docker compose up -d
        └─> rayobyte/rayobrowse container
              ├─ Daemon        :9222   (HTTP API + CDP WebSocket proxy)
              └─ noVNC viewer  :6080   (optional — watch sessions live)

pip install rayobrowse
  └─> create_browser() ──HTTP──> localhost:9222/browser/create
        └─> returns ws://localhost:9222/cdp/<session-id>

playwright.connect_over_cdp(ws_url)
  └─> CDP WebSocket to Chromium running inside the container
```

---

## Ports

| Port | Purpose                                          |
|------|--------------------------------------------------|
| 9222 | Daemon HTTP API + CDP WebSocket proxy            |
| 6080 | noVNC live browser viewer (optional)             |

---

## Key Files

| File                              | Purpose                                              |
|-----------------------------------|------------------------------------------------------|
| `.env`                            | Runtime config — copy from `.env.example` and edit   |
| `docker-compose.yml`              | Container definition                                 |
| `examples/verify_setup.py`        | Non-interactive E2E test — run this to confirm setup |
| `examples/playwright_example.py`  | Full Playwright walkthrough                          |
| `examples/selenium_example.py`    | Selenium example                                     |
| `examples/puppeteer_example.js`   | Puppeteer / Node.js example                          |

---

## Common Failures

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on port 9222 | Container not running | `docker compose up -d` |
| `TermsAcceptanceRequired` error | `STEALTH_BROWSER_ACCEPT_TERMS` not `true` | Set it in `.env`, then `docker compose up -d` |
| `create_browser()` hangs or times out | Container still initialising | Wait for health check to pass, then retry |
| Page title is empty | Network or fingerprint issue | Try `headless=True` first; check `docker compose logs` |
| noVNC not accessible at :6080 | `STEALTH_BROWSER_NOVNC=false` | Set to `true` in `.env`, then `docker compose up -d` |
| `docker compose` not found | Old Docker install uses `docker-compose` (hyphen) | Upgrade Docker to a version with Compose v2 |

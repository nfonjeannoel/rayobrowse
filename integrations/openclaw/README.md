# OpenClaw + rayobrowse

Run [OpenClaw](https://openclaw.ai) with a browser that doesn't get blocked.

If you want to run OpenClaw on a remote server so your personal assistant is
always on without tying up your laptop, you'll hit a wall: standard headless
Chromium gets detected as a bot and blocked by most websites. Tasks fail,
CAPTCHAs fire, and the agent becomes useless at anything involving real
web pages.

rayobrowse fixes this. It runs a stealth-fingerprinted Chromium that looks like
a real device, matching user agent, screen resolution, WebGL renderer, fonts,
and dozens of other signals that sites use to detect automation. Your OpenClaw
agent can browse and interact with sites just like you would from your
own machine.

The free tier gives you **1 concurrent browser with no time limits**, enough to
run OpenClaw as your personal cloud assistant at zero cost.

---

## How It Works

rayobrowse exposes a **`/connect` endpoint** that works with any CDP client. When
OpenClaw connects, a stealth browser is automatically created with the
fingerprint and proxy settings you specify in the URL. When the connection
closes, the browser is cleaned up automatically.

```
OpenClaw Gateway
  │
  │  ws://localhost:9222/connect?headless=true&os=windows
  ▼
rayobrowse daemon (:9222)
  │
  │  auto-create browser with fingerprint
  ▼
Chromium instance  ◄──  CDP WebSocket proxy  ──►  OpenClaw agent actions
```

No helper scripts, no manual browser creation. One static URL in your
OpenClaw config and you're done.

---

## Prerequisites

- **Docker** with Compose v2 (`docker compose`)
- **OpenClaw** installed and running ([install guide](https://docs.openclaw.ai))
- rayobrowse container running (see [main README](../../README.md))

---

## Quick Start (Local)

**1. Start rayobrowse**

If you haven't already, set up and start the container from the repo root (see main README for more info):

```bash
cp .env.example .env
# Edit .env → set STEALTH_BROWSER_ACCEPT_TERMS=true
docker compose up -d
```

Wait for the daemon to be healthy:

```bash
curl -s http://localhost:9222/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('Ready' if d.get('success') else 'Not ready')"
```

**2. Configure OpenClaw**

Add a `rayobrowse` browser profile to your OpenClaw config. Either edit
`~/.openclaw/openclaw.json` directly:

```json5
{
  browser: {
    enabled: true,
    defaultProfile: "rayobrowse",
    profiles: {
      rayobrowse: {
        cdpUrl: "ws://localhost:9222/connect?headless=true&os=windows",
      },
    },
  },
}
```

Or use the CLI (one-liner):

```bash
openclaw config set browser.enabled true
openclaw config set browser.defaultProfile rayobrowse
openclaw config set 'browser.profiles.rayobrowse.cdpUrl' 'ws://localhost:9222/connect?headless=true&os=windows'
```

OpenClaw hot-reloads config changes automatically, no restart needed.

**3. Verify**

```bash
openclaw browser --browser-profile rayobrowse status
```

That's it. OpenClaw will now use rayobrowse for all browser automation.

---

## Quick Start (Remote)

Deploy rayobrowse on a server in remote mode, then point your local OpenClaw
at it.

**1. Server setup**

On your server, configure `.env` for remote mode:

```bash
STEALTH_BROWSER_ACCEPT_TERMS=true
STEALTH_BROWSER_DAEMON_MODE=remote
STEALTH_BROWSER_API_KEY=your-secret-key #contact support@rayobyte.com for a key
RAYOBROWSE_PORT=80
```

```bash
docker compose up -d
```

**2. Configure OpenClaw locally**

```json5
// ~/.openclaw/openclaw.json
{
  browser: {
    enabled: true,
    defaultProfile: "rayobrowse",
    profiles: {
      rayobrowse: {
        cdpUrl: "ws://your-server.example.com/connect?headless=true&os=windows&api_key=your-secret-key",
      },
    },
  },
}
```

The `api_key` query param authenticates the `/connect` request. In remote
mode, all browser management endpoints require authentication; the API key in
the URL handles this transparently.

---

## Configuration Reference

The `/connect` endpoint accepts the same parameters as the
[`POST /browser` API](../../README.md#api-reference), passed as URL query
params:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `headless` | `true` | `true`, `false`, `1`, `0`, `yes`, `no` |
| `os` | `linux` | Target OS fingerprint: `windows`, `linux`, `android`, `macos` |
| `browser_name` | `chrome` | Browser fingerprint type |
| `browser_version_min` | *(latest)* | Minimum Chrome version for fingerprint |
| `browser_version_max` | *(latest)* | Maximum Chrome version for fingerprint |
| `proxy` | *(none)* | Proxy URL, e.g. `http://user:pass@host:port` |
| `browser_language` | *(auto)* | Accept-Language header, e.g. `en-US,en;q=0.9` |
| `ui_language` | *(auto)* | Browser UI locale override |
| `screen_width_min` | *(auto)* | Minimum screen width for fingerprint |
| `screen_height_min` | *(auto)* | Minimum screen height for fingerprint |
| `api_key` | *(none)* | API key (required in remote mode) |

### Example URLs

Windows fingerprint (stealth):
```
ws://localhost:9222/connect?headless=true&os=windows
```

Android fingerprint with proxy:
```
ws://localhost:9222/connect?headless=true&os=android&proxy=http://user:pass@proxy.example.com:8080
```

Specific Chrome version:
```
ws://localhost:9222/connect?headless=true&os=windows&browser_version_min=130&browser_version_max=132
```

Headful mode (visible in noVNC at `http://localhost:6080/vnc.html`):
```
ws://localhost:9222/connect?headless=false&os=windows
```

---

## Customizing Fingerprints

The `os` parameter controls the browser's fingerprint profile: user agent,
screen resolution, WebGL renderer, platform, and other signals are all
configured to match the target OS.

| `os` value | Fingerprint |
|------------|-------------|
| `windows` | Windows desktop Chrome (recommended for most sites) |
| `linux` | Linux desktop Chrome |
| `android` | Android mobile Chrome |
| `macos` | macOS desktop Chrome (experimental) |

Combine with `browser_version_min` / `browser_version_max` to pin a specific
Chrome version range if a target site checks for it.

---

## Browser Lifecycle

- **Created** when OpenClaw connects to the `/connect` WebSocket
- **Active** while the WebSocket connection is alive
- **Cleaned up** automatically after the connection closes (2-second grace
  period, then the browser process is terminated)

If OpenClaw disconnects and reconnects (e.g., between agent sessions), a
**new** browser is created automatically with the same fingerprint parameters
from the URL. Each connection gets a fresh browser instance.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on port 9222 | Container not running | `docker compose up -d` |
| `TERMS_REQUIRED` error | Terms not accepted | Set `STEALTH_BROWSER_ACCEPT_TERMS=true` in `.env`, then `docker compose up -d` |
| `CONCURRENT_LIMIT_EXCEEDED` | Too many browsers open | Close other browsers or upgrade to a paid plan |
| `UNAUTHORIZED` (remote mode) | Missing or wrong API key | Check `api_key` in URL matches `STEALTH_BROWSER_API_KEY` in `.env` |
| `FINGERPRINT_UNAVAILABLE` | Fingerprint service issue | Retry; check `docker compose logs` for details |
| OpenClaw says "browser not available" | Profile not set as default | Run `openclaw config set browser.defaultProfile rayobrowse` |
| Can't see the browser | Running in headless mode | Change `headless=false` in URL, view at `http://localhost:6080/vnc.html` |

### Checking daemon logs

```bash
docker compose logs --tail=50
```

### Testing the endpoint directly

You can test the `/connect` endpoint with any WebSocket client or Playwright:

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "ws://localhost:9222/connect?headless=true&os=windows"
    )
    page = browser.contexts[0].pages[0]
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

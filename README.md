<p align="center">
  <img src="assets/rayobrowse.png" alt="rayobrowse">
</p>

<p align="center">
  <em>Self-hosted Chromium stealth browser for web scraping and automation.</em>
</p>

## Overview

rayobrowse is a Chromium-based stealth browser for web scraping, AI agents, and automation workflows. It runs on headless Linux servers (no GPU required) and works with any tool that speaks CDP: Playwright, Puppeteer, Selenium, OpenClaw, Scrapy, and custom automation scripts.

Standard headless Chromium gets blocked immediately by modern bot detection. rayobrowse fixes this with realistic fingerprints (user agent, screen resolution, WebGL, fonts, timezone, and dozens of other signals) that make each session look like a real device.

It runs inside Docker (x86_64 and ARM64) and is actively used in production on [Rayobyte's scraping API](https://rayobyte.com/products/web-scraping-api) to scrape millions of pages per day across some of the most difficult, high-value websites.

---

## Quick Start

**1. Set up environment**

```bash
cp .env.example .env
```

Open `.env` and set `STEALTH_BROWSER_ACCEPT_TERMS=true` to confirm you agree to the [LICENSE](LICENSE). The daemon will not create browsers until this is set.

**2. Start the container**

```bash
docker compose up -d
```

Docker automatically pulls the correct image for your architecture (x86_64 or ARM64).

**3. Connect and automate**

Any CDP client can connect directly to the `/connect` endpoint. No SDK install required.

```python
# pip install playwright && playwright install
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "ws://localhost:9222/connect?headless=false&os=windows"
    )
    page = browser.new_context().new_page()
    page.goto("https://example.com")
    print(page.title())
    input("Browser open — view at http://localhost:6080/vnc.html. Press Enter to close...")
    browser.close()
```

View the browser live at [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html) (noVNC).

For more control (listing, deleting, managing multiple browsers), install the Python SDK:

```bash
pip install -r requirements.txt
python examples/playwright_example.py
```

---

## Upgrading

To upgrade to the latest version of rayobrowse:

```bash
# Pull the latest Docker image and restart the container
docker compose pull && docker compose up -d

# Upgrade the Python SDK
pip install --upgrade -r requirements.txt
```

The Docker image and Python SDK are versioned independently:

- **Docker image** (`rayobyte/rayobrowse:latest`) — contains Chromium binary, fingerprint engine, daemon server
- **Python SDK** (`rayobrowse` on PyPI) — lightweight client for `create_browser()`

Both are updated regularly. The SDK maintains backward compatibility with older daemon versions, but upgrading both together is recommended for the best experience.

---

## Requirements

- **Docker** — the browser runs inside a container
- **Python 3.10+** — for the SDK client and examples
- **2GB+ RAM** available (~300MB per browser instance)

Works on Linux, Windows (native or WSL2), and macOS. Both **x86_64 (amd64)** and **ARM64 (Apple Silicon, AWS Graviton)** are supported — the Docker image is built and tested for both architectures, and Docker automatically pulls the correct one.

### What's in the pip package vs. the Docker image

| Component | Where it lives |
| --- | --- |
| `rayobrowse` Python SDK (`create_browser()`, client) | `pip install rayobrowse` — lightweight, pure-Python |
| Chromium binary, fingerprint engine, daemon server | Docker image (`rayobyte/rayobrowse`) |

The SDK is intentionally minimal — it issues HTTP requests to the daemon and returns CDP WebSocket URLs. All browser-level logic runs inside the container.

---

## Why This Exists

Browser automation is becoming the backbone of web interaction, not just for scraping, but for AI agents, workflow automation, and any tool that needs to navigate the real web. Projects like OpenClaw, Scrapy, Firecrawl, and dozens of others all need a browser to do their job. The problem is that standard headless Chromium gets detected and blocked by most websites. Every one of these tools hits the same wall.

rayobrowse gives them a browser that actually works. It looks like a real device, with a matching fingerprint across user agent, screen resolution, WebGL, fonts, timezone, and every other signal that detection systems check. Any tool that speaks CDP (Chrome DevTools Protocol) can connect and automate without getting blocked.

We needed a browser that:

- Uses **Chromium** (71% browser market share, blending in is key)
- Runs reliably on **headless Linux servers** with no GPU
- Works with **any CDP client** (Playwright, Selenium, Puppeteer, AI agents, custom tools)
- Uses real-world, diverse fingerprints
- Can be deployed and updated at scale
- Is commercially maintained long-term

Since no existing solution met these requirements, we built rayobrowse. It's developed as part of [our scraping platform](https://rayobyte.com/products/web-scraping-api), so it'll be commercially supported and up-to-date with the latest anti-scraping techniques.

---

## Architecture

<p align="center">
  <img src="assets/architecture.png" alt="rayobrowse architecture">
</p>

rayobrowse runs as a Docker container that bundles the custom Chromium binary, fingerprint engine, and a daemon server. Your code runs on the host and connects over CDP:

There are two ways to get a browser:

| Method | How it works | Best for |
| --- | --- | --- |
| **`/connect` endpoint** | Connect to `ws://localhost:9222/connect?headless=true&os=windows`. A stealth browser is auto-created on connection and cleaned up on disconnect. | Third-party tools (OpenClaw, Scrapy, Firecrawl), quick scripts, any CDP client |
| **Python SDK** | Call `create_browser()` to get a CDP WebSocket URL, then connect with your automation library. | Fine-grained control, multiple browsers, custom lifecycle management |

The `/connect` endpoint is the simplest path. Point any CDP-capable tool at a single static URL and it just works. The Python SDK gives you more control over browser creation, listing, and deletion.

The noVNC viewer on `:6080` lets you watch browser sessions in real time, useful for debugging and demos.

Zero system dependencies on your host machine beyond Docker. No Xvfb, no font packages, no Chromium install.

---

## How It Works

### Chromium Fork

rayobrowse tracks upstream Chromium releases and applies a focused set of patches (using a [plaster approach similar to Brave](https://github.com/brave/brave-core/blob/master/tools/cr/plaster.py)):

- Normalize and harden exposed browser APIs
- Reduce fingerprint entropy leaks
- Improve automation compatibility
- Preserve native Chromium behavior where possible

Updates are continuously validated against internal test targets before release.

### Fingerprint Injection

At startup, each session is assigned a real-world device profile covering:

- User agent, platform, and OS metadata
- Screen resolution and media features
- Graphics and rendering attributes (Canvas, WebGL)
- Fonts matching the target OS
- Locale, timezone, and WebRTC configuration

Profiles are selected dynamically from a database of thousands of real-world fingerprints collected using the same techniques that major anti-bot companies use.

### Automation Layer

rayobrowse exposes standard Chromium interfaces and avoids non-standard hooks that increase detection risk. Automation connects through native CDP and operates on unmodified page contexts — your existing Playwright, Selenium, and Puppeteer scripts work as-is.

### CI & Validation

Every release passes through automated testing including fingerprint consistency checks, detection regression tests, and stability benchmarks. Releases are only published once they pass all validation stages.

---

## Features

### Fingerprint Spoofing

Use your own static fingerprint or pull from our database of thousands of real-world fingerprints. Vectors emulated include:

- OS (Windows, Android thoroughly tested; macOS and Linux experimental)
- WebRTC and DNS leak protection
- Canvas and WebGL
- Fonts (matched to target OS)
- Screen resolution
- `hardwareConcurrency`
- Timezone matching with proxy geolocation (via MaxMind GeoLite2)
- ...and much more

### Human Mouse

Optional human-like mouse movement and clicking, inspired by [HumanCursor](https://github.com/riflosnake/HumanCursor). Use Playwright's `page.click()` and `page.mouse.move()` as you normally do — our system applies natural mouse curves and realistic click timing automatically.

![Human-like mouse movement demonstration](assets/mouse.gif)

### Proxy Support

Route traffic through any HTTP proxy, just as you would with standard Playwright.

### Headless or Headful

Run headful mode on headless Linux servers via Xvfb (handled inside the container). Watch sessions live through the built-in noVNC viewer.

---

## Usage

rayobrowse works with **Playwright, Selenium, Puppeteer**, and any tool that speaks CDP. See the [`examples/`](examples/) folder for ready-to-run scripts.

### Using `/connect` (simplest)

Connect any CDP client directly to the `/connect` endpoint. No SDK needed.

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "ws://localhost:9222/connect?headless=true&os=windows"
    )
    page = browser.new_context().new_page()
    page.goto("https://example.com")
    print(page.title())
    browser.close()
```

Customize the browser via query parameters:

```
ws://localhost:9222/connect?headless=true&os=windows&proxy=http://user:pass@host:port
```

All `/connect` parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `headless` | `true` | `true` or `false` |
| `os` | `linux` | Fingerprint OS: `windows`, `linux`, `android`, `macos` |
| `browser_name` | `chrome` | Browser fingerprint type |
| `browser_version_min` | *(latest)* | Minimum Chrome version |
| `browser_version_max` | *(latest)* | Maximum Chrome version |
| `proxy` | *(none)* | Proxy URL, e.g. `http://user:pass@host:port` |
| `browser_language` | *(auto)* | Accept-Language value |
| `ui_language` | *(auto)* | Browser UI locale |
| `screen_width_min` | *(auto)* | Minimum screen width |
| `screen_height_min` | *(auto)* | Minimum screen height |
| `api_key` | *(none)* | Required in remote mode |

### Using the Python SDK

For more control over the browser lifecycle, use the Python SDK (`pip install -r requirements.txt`).

```python
from rayobrowse import create_browser
from playwright.sync_api import sync_playwright

ws_url = create_browser(headless=False, target_os="windows")

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(ws_url)
    page = browser.contexts[0].pages[0]
    page.goto("https://example.com")
    browser.close()
```

#### With Proxy

```python
ws_url = create_browser(
    headless=False,
    target_os="windows",
    proxy="http://user:pass@proxy.example.com:8000",
)
```

#### Specific Fingerprint Version

```python
ws_url = create_browser(
    headless=False,
    target_os="windows",
    browser_name="chrome",
    browser_version_min=144,
    browser_version_max=144,
)
```

#### Multiple Browsers

```python
from rayobrowse import create_browser
from playwright.sync_api import sync_playwright

urls = [create_browser(headless=False, target_os="windows") for _ in range(3)]

with sync_playwright() as p:
    for ws_url in urls:
        browser = p.chromium.connect_over_cdp(ws_url)
        browser.contexts[0].pages[0].goto("https://example.com")
    input("Press Enter to close all...")
```

#### Static Fingerprint Files

For deterministic environments, fingerprints can be loaded from disk:

```python
ws_url = create_browser(
    fingerprint_file="fingerprints/windows_chrome.json"
)
```

Due to anti-bot companies monitoring repos like ours, we don't publish fingerprint templates. Contact us at [support@rayobyte.com](mailto:support@rayobyte.com) and we'll send one over.

---

## Integrations

rayobrowse works with any tool that supports CDP. These guides walk through setup and include working examples:

| Tool | What it does | Guide |
| --- | --- | --- |
| **OpenClaw** | AI agent framework for browser automation | [`integrations/openclaw/`](integrations/openclaw/) |
| **Scrapy** | Web scraping framework with `scrapy-playwright` | [`integrations/scrapy/`](integrations/scrapy/) |
| **Playwright** | Browser automation library (Python, Node, .NET) | [`examples/playwright_example.py`](examples/playwright_example.py) |
| **Selenium** | Browser automation via WebDriver/CDP | [`examples/selenium_example.py`](examples/selenium_example.py) |
| **Puppeteer** | Node.js browser automation | [`examples/puppeteer_example.js`](examples/puppeteer_example.js) |

All integrations use the `/connect` endpoint, so there's nothing extra to install beyond the tool itself and a running rayobrowse container.

More integrations (Firecrawl, LangChain, etc.) are coming. If you have a specific tool you'd like supported, open an [issue](https://github.com/rayobyte-data/rayobrowse/issues).

---

## API Reference

### `create_browser(**kwargs) -> str`

Returns a CDP WebSocket URL. Connect to it with Playwright, Selenium, or Puppeteer.


| Parameter             | Type   | Default    | Description                                                                                                                                      |
| --------------------- | ------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `headless`            | `bool` | `False`    | Run without GUI                                                                                                                                  |
| `target_os`           | `str   | list`      | `tested: "windows", "android"; experimental: "linux", "macos"`                                                                                   |
| `browser_name`        | `str`  | `"chrome"` | Browser type                                                                                                                                     |
| `browser_version_min` | `int`  | `None`     | Min Chrome version to emulate; if you use a value that doesn't match the Chromum version (144 currently), some websites can detect the mismatch. |
| `browser_version_max` | `int`  | `None`     | Max Chrome version to emulate                                                                                                                    |
| `proxy`               | `str`  | `None`     | Proxy URL (`http://user:pass@host:port`)                                                                                                         |
| `browser_language`    | `str`  | `None`     | Language header (e.g., `"ko,en;q=0.9"`)                                                                                                          |
| `fingerprint_file`    | `str`  | `None`     | Path to a static fingerprint JSON file                                                                                                           |
| `launch_args`         | `list` | `None`     | Extra Chromium flags                                                                                                                             |
| `api_key`             | `str`  | `None`     | API key (overrides `STEALTH_BROWSER_API_KEY` env var)                                                                                            |
| `endpoint`            | `str`  | `None`     | Daemon URL (overrides `RAYOBYTE_ENDPOINT` env var, default `http://localhost:9222`)                                                              |


---

## Configuration

### Environment Variables

Set in `.env` (next to `docker-compose.yml`):


| Variable                       | Default   | Description                                                                        |
| ------------------------------ | --------- | ---------------------------------------------------------------------------------- |
| `STEALTH_BROWSER_ACCEPT_TERMS` | `false`   | **Required.** Set to `true` to accept the [LICENSE](LICENSE) and enable the daemon |
| `STEALTH_BROWSER_API_KEY`      | *(empty)* | API key for paid plans. Also used for remote mode endpoint auth                    |
| `STEALTH_BROWSER_NOVNC`        | `true`    | Enable browser viewer at [http://localhost:6080](http://localhost:6080)            |
| `STEALTH_BROWSER_DAEMON_MODE`  | `local`   | `local` or `remote`. Remote enables API key auth on management endpoints           |
| `STEALTH_BROWSER_PUBLIC_URL`   | *(empty)* | Base URL for CDP endpoints in remote mode. Auto-detects public IP if not set       |
| `RAYOBROWSE_PORT`              | `9222`    | Host port (set in `.env`, used by `docker-compose.yml`). Set to `80` for remote    |


Changes require a container restart:

```bash
docker compose up -d
```

### Viewing the Browser

With `STEALTH_BROWSER_NOVNC=true` (the default), open [http://localhost:6080](http://localhost:6080) to watch browsers in real time.

---

## Remote / Cloud Mode (*Beta*)

By default, rayobrowse runs in **local mode** — your SDK connects to the daemon on localhost. For cloud deployments where external clients need direct CDP access, switch to **remote mode**. If you need help setting up, please contact [support@rayobyte.com](mailto:support@rayobyte.com). 

### How It Works

```
┌──────────────┐      POST /browser       ┌─────────────────────────┐
│  Your Server  │ ──────────────────────► │  rayobrowse             │
│  (controller) │ ◄────── ws_endpoint ─── │  (remote mode, :80)     │
└──────────────┘                          └─────────────────────────┘
                                                    ▲
┌──────────────┐      CDP WebSocket                 │
│  End User /   │ ──────────────────────────────────┘
│  Worker       │   (direct connection, no middleman)
└──────────────┘
```

Your server requests a browser via the REST API (authenticated with your API key). The daemon returns a `ws_endpoint` URL using the server's public IP. The end user connects directly to the browser over CDP — no proxy in between.

### Setup

**1. Configure `.env`**

```bash
STEALTH_BROWSER_ACCEPT_TERMS=true
STEALTH_BROWSER_API_KEY=your_api_key_here
STEALTH_BROWSER_DAEMON_MODE=remote
RAYOBROWSE_PORT=80
# Optional: set if you have a domain, otherwise public IP is auto-detected
# STEALTH_BROWSER_PUBLIC_URL=http://browser.example.com
```

**2. Start**

```bash
docker compose up -d
```

**3. Connect (two options)**

**Option A: `/connect` with `api_key` in the URL** (simplest, works with any CDP client)

```python
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(
        "ws://your-server/connect?headless=true&os=windows&api_key=your_api_key_here"
    )
    page = browser.new_context().new_page()
    page.goto("https://example.com")
```

**Option B: REST API** (for managing multiple browsers programmatically)

```bash
curl -X POST http://your-server/browser \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{"headless": true, "os": "windows"}'
```

Response:

```json
{
  "success": true,
  "data": {
    "browser_id": "br_59245e8658532863",
    "ws_endpoint": "ws://your-server/cdp/br_59245e8658532863"
  }
}
```

Then connect to the returned `ws_endpoint` (no additional auth needed, the browser ID is the token):

```python
browser = p.chromium.connect_over_cdp("ws://your-server/cdp/br_59245e8658532863")
```

### API Authentication (Remote Mode)

In remote mode, management endpoints require your API key:


| Endpoint                | Auth Required | How to authenticate |
| ----------------------- | ------------- | --- |
| `WS /connect`           | Yes           | `api_key` query parameter in the URL |
| `POST /browser`         | Yes           | `X-API-Key: KEY` or `Authorization: Bearer KEY` header |
| `GET /browsers`         | Yes           | Same |
| `DELETE /browser/{id}`  | Yes           | Same |
| `GET /health`           | No            | |
| `WS /cdp/{browser_id}` | No            | Browser ID is the token |


Requests without a valid key receive `401 Unauthorized`.

### Public IP Auto-Detection

When `STEALTH_BROWSER_PUBLIC_URL` is not set, the daemon automatically detects the server's public IP at startup using external services (ipify.org, ifconfig.me, checkip.amazonaws.com). This works well for cloud servers that auto-scale — each instance discovers its own IP without DNS configuration.

### TLS / HTTPS

The daemon serves HTTP. For HTTPS, put a reverse proxy in front (Cloudflare, nginx, Caddy, etc.). If using Cloudflare, just point your domain at the server IP and enable the proxy — no server-side changes needed.

---

## Licensing & Usage

We can't open-source the browser itself. We saw firsthand that major anti-bot companies reverse-engineered the great [camoufox](https://github.com/daijro/camoufox). You can read more about our [reasoning and journey here](https://rayobyte.com/blog/custom-chromium-stealth-browser-web-scraping/).

Our license prohibits companies on [this list](https://cdn.sb.rayobyte.com/list-of-prohibited-companies.txt) from using our software. If you're on this list and have a legitimate scraping use case, please contact [sales@rayobyte.com](mailto:sales@rayobyte.com).

For everyone else, rayobrowse is free to download and run locally:

### Free (Default)

- Install and run immediately — no registration
- Fully self-hosted
- One concurrent browser per machine
- No proxy restrictions

### Free Unlimited (with Rayobyte Proxies)

- Unlimited concurrency when routing traffic through supported Rayobyte rotating proxies
- Fully self-hosted
- Requires [rotating residential, ISP, or data center proxies through Rayobyte](https://rayobyte.com/products/)

### Paid Threads (Bring Your Own Proxy)

For teams running their own proxy infrastructure:

- Fully self-hosted
- Unlimited concurrency
- No proxy requirements
- Pay per active browser session

### Cloud Browser

- Self-host with [remote mode](#remote--cloud-mode) for direct CDP access from external clients
- Auto-scaling friendly — each daemon detects its own public IP
- Managed cloud browser service coming soon (scaling handled by us)

For Paid or Cloud access, fill out this [form](https://share.hsforms.com/1cTZ0E4WMTWGo5QuwrKpQlA3xcyu).

---

## Limitations & Expectations

rayobrowse is currently in **Beta**. We use it to scrape millions of pages per day, but your results may vary.

For beta testers who can provide valuable feedback, we'll offer free browser threads in exchange. Contact us through this [form](https://share.hsforms.com/1cTZ0E4WMTWGo5QuwrKpQlA3xcyu) if you're interested.

Specific limitations:

- Fingerprint coverage is optimized for **Windows and Android**. macOS and Linux fingerprints are available but aren't a primary focus.
- For optimal fingerprint matching, set `browser_version_min` and `browser_version_max` to **144** (the current Chromium version). Using a fingerprint from a different version may cause detection on some sites.
- **Canvas and WebGL** fingerprinting is an ongoing research area. Major targets we scrape are unaffected, but some sites can detect our current algorithm. A new major release addressing this is expected by end of February.

---

## Troubleshooting

### Can't connect to daemon

```bash
curl http://localhost:9222/health
# Should return: {"success": true, "data": {"status": "healthy", ...}}
```

### Check daemon logs

```bash
docker compose logs -f
```

### Environment variable changes not taking effect

The container reads `.env` at startup. After editing, recreate the container:

```bash
docker compose up -d
```

### Enable debug logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## FAQ

**Why Chromium and not Chrome?**

Chrome is closed-source. Although there are slight differences between Chrome and Chromium, our experiments on the most difficult websites — and real-world scraping of millions of pages per day — show no discernible difference in detection rate. The difference yields too many false positives and would negatively impact too many users. Additionally, Chromium-based browsers (Brave, Edge, Samsung, etc.) make up a significant portion of the browser market.

**Why is it not open-source?**

We've seen great projects like camoufox get undermined by anti-bot companies reverse-engineering the source to detect it. We want to avoid that fate and continue providing a reliable scraping browser for years to come.

---

## Issues & Support

1. **Code-level bugs or feature requests** — open a [GitHub Issue](https://github.com/rayobyte/rayobrowse/issues). We'll track and resolve these publicly.
2. **Anti-scraping issues** ("detected on site X" or "fingerprint applied incorrectly on site Y") — email [support@rayobyte.com](mailto:support@rayobyte.com) with full output after enabling debug logging. We don't engage in public assistance on anti-scraping cases due to watchful eyes.
3. **Sales, partnerships, or closer collaboration** — fill in this [form](https://share.hsforms.com/1cTZ0E4WMTWGo5QuwrKpQlA3xcyu) and we'll be in touch.

---

## Legal & Ethics Notice

This project should be used only for legal and ethical web scraping of publicly available data. Rayobyte is a proud partner of the [EWDCI](https://ethicalwebdata.com/) and places a high importance on ethical web scraping.
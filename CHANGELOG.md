# Changelog

## [0.1.26] - 2026-02-21

### Added
- **`/connect` endpoint** — WebSocket endpoint that auto-creates a stealth browser on connection. Third-party tools (OpenClaw, Scrapy, Puppeteer, Selenium) can now connect via a static CDP URL like `ws://localhost:9222/connect?headless=true&os=windows` without calling the REST API. Browser is automatically cleaned up on disconnect.
- **OpenClaw integration** — full setup guide and configuration examples for running OpenClaw AI agents with rayobrowse browsers. See [`integrations/openclaw/`](integrations/openclaw/).
- **Scrapy integration** — complete tutorial and ready-to-run example project for `scrapy-playwright` + rayobrowse. Includes spiders for JS-rendered sites. See [`integrations/scrapy/`](integrations/scrapy/).

---

## [0.1.25] - 2026-02-20

### Added
- **ARM64 (Apple Silicon / AWS Graviton) support** — Docker image now ships as a multi-architecture build supporting both x86_64 (amd64) and ARM64. Docker automatically pulls the correct image for your platform. Both architectures are tested in CI/CD for each release.

---

## [0.1.24] - 2026-02-20

### Added
- **Remote / Cloud mode** — new `STEALTH_BROWSER_DAEMON_MODE=remote` option
  turns rayobrowse into a publicly accessible cloud browser backend. Your server
  creates browsers via REST API (authenticated with API key), and end users
  connect directly over CDP WebSocket with zero middleman.

### Fixed
- **Docker image cache issue** — fixed a bug where fonts and the Chromium binary
  were being downloaded twice on first startup.

---

## [0.1.11] - 2026-02-19

### Added
- **Selenium and Puppeteer support** — in addition to Playwright, rayobrowse
  now has ready-to-run examples for Selenium and Puppeteer. See the
  [`examples/`](examples/) folder.
- **`AGENTS.md`** — end-to-end setup guide for AI agents and LLM-driven
  pipelines, covering setup, verification, and common failure modes.
- **`examples/verify_setup.py`** — non-interactive E2E test script; run it
  to confirm your installation is working correctly.
- **Terms acceptance via environment variable** — `STEALTH_BROWSER_ACCEPT_TERMS=true`
  replaces the previous interactive prompt, making setup compatible with
  automated and headless environments.

---

## [0.1.11] - 2026-02-18

### Added
- **Docker-first architecture** — rayobrowse now runs entirely inside a Docker
  container. No system dependencies on the host beyond Docker and Python. This
  enables running on any x64 machine (ARM64 coming soon), while making it
  easier to develop and deploy to production.
- **Daemonized** — the system has been daemonized so that only a lightweight
  Python SDK is needed to connect to the daemon which manages the browsers. All
  connections from your automation library (Playwright, etc.) go through a
  simple CDP socket.
- **noVNC viewer** — watch live browser sessions in real time at
  `http://localhost:6080`. No VNC client required.

"""
verify_setup.py — non-interactive end-to-end setup verification.

Confirms:
  1. The rayobrowse daemon is reachable on port 9222.
  2. A headless browser can be created.
  3. A page can be loaded and returns a non-empty title.

Usage:
    python examples/verify_setup.py

Exit codes:
    0 — all checks passed
    1 — one or more checks failed (error printed, with remediation hint)

Prerequisites:
    docker compose up -d
    pip install rayobrowse playwright
"""

import json
import logging
import sys
import urllib.error
import urllib.request

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


def main() -> int:
    # ── 1. Daemon health check ───────────────────────────────────────────────
    try:
        with urllib.request.urlopen("http://localhost:9222/health", timeout=10) as r:
            data = json.loads(r.read())
        if not data.get("success"):
            log.error("Daemon health check returned success=false: %s", data)
            log.error("Check logs with: docker compose logs --tail=50")
            return 1
        log.info("Daemon healthy.")
    except urllib.error.URLError as e:
        log.error("Cannot reach daemon on port 9222: %s", e)
        log.error("Is the container running? Try: docker compose up -d")
        return 1

    # ── 2. Create a browser ──────────────────────────────────────────────────
    try:
        from rayobrowse import create_browser
    except ImportError:
        log.error("rayobrowse not installed. Run: pip install rayobrowse")
        return 1

    log.info("Requesting headless browser...")
    try:
        ws_url = create_browser(headless=True, target_os="windows")
    except Exception as e:
        msg = str(e)
        log.error("create_browser() failed: %s", msg)
        if "TermsAcceptanceRequired" in msg or "STEALTH_BROWSER_ACCEPT_TERMS" in msg:
            log.error(
                "Set STEALTH_BROWSER_ACCEPT_TERMS=true in .env, "
                "then run: docker compose up -d"
            )
        return 1

    log.info("Browser ready: %s", ws_url)

    # ── 3. Connect with Playwright and load a page ───────────────────────────
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.error("playwright not installed. Run: pip install playwright")
        return 1

    try:
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()
            page.goto("https://example.com", wait_until="domcontentloaded", timeout=30000)
            title = page.title()
            browser.close()
    except Exception as e:
        log.error("Playwright automation failed: %s", e)
        return 1

    if not title:
        log.error(
            "Page title was empty — check network connectivity and "
            "daemon logs: docker compose logs --tail=50"
        )
        return 1

    log.info('Page title: "%s"', title)
    log.info("✓ Setup verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

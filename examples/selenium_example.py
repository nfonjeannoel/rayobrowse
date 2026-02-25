"""
Selenium example for Rayobyte Stealth Browser.

This script creates a stealth browser via the daemon and controls it with
Selenium. Because the daemon uses a CDP proxy path (ws://host:port/cdp/<id>)
rather than a bare port, a lightweight local HTTP shim is started to bridge
Selenium/ChromeDriver to the daemon.

Prerequisites:
    pip install rayobrowse selenium webdriver-manager
    Docker container running: docker compose up -d

Usage:
    python selenium_example.py
"""

import http.server
import json
import logging
import socket
import sys
import threading
import urllib.request
from contextlib import contextmanager
from urllib.parse import urlparse

from rayobrowse import create_browser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# ── CDP shim ─────────────────────────────────────────────────────────────────

def _free_port() -> int:
    """Find an available TCP port on localhost."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@contextmanager
def cdp_shim(ws_url: str):
    """
    Context manager that bridges ChromeDriver to the daemon's CDP proxy.

    ChromeDriver expects CDP HTTP endpoints (like /json/version and /json/list)
    at a plain host:port address. This shim starts a minimal local HTTP server
    that proxies those requests to the daemon's per-browser endpoints.

    Yields the shim address string (e.g., "127.0.0.1:54321").
    """
    parsed = urlparse(ws_url)
    daemon_endpoint = f"http://{parsed.hostname}:{parsed.port}"
    browser_id = parsed.path.strip("/").split("/")[-1]  # br_xxxxxxxx
    base_url = f"{daemon_endpoint}/cdp/{browser_id}"

    class _ShimHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            path = self.path.lstrip("/")
            proxy_url = f"{base_url}/{path}" if path else f"{base_url}/json/version"
            try:
                with urllib.request.urlopen(proxy_url, timeout=5) as resp:
                    body = resp.read()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except Exception as exc:
                body = json.dumps({"error": str(exc)}).encode()
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        def log_message(self, *args):
            pass  # Suppress server access logs

    port = _free_port()
    server = http.server.HTTPServer(("127.0.0.1", port), _ShimHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"127.0.0.1:{port}"
    finally:
        server.shutdown()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    """
    Creates a stealth browser and controls it with Selenium.

    The browser is created via the daemon (Docker container must be running
    on port 9222). ChromeDriver is auto-downloaded to match the browser version.
    """

    # --- Define fingerprint filters ---
    target_os = "windows"  # android and windows tested; macos and linux experimental
    target_browser = "chrome"
    version_min = 144
    version_max = 144

    logging.info(f"Requesting browser: OS={target_os}, Chrome {version_min}-{version_max}")

    try:
        # Create a browser via the daemon (Docker container must be running on port 9222)
        ws_url = create_browser(
            headless=False,
            target_os=target_os,
            browser_name=target_browser,
            browser_version_min=version_min,
            browser_version_max=version_max,
            #proxy="http://username:password@host:port",
        )
        logging.info(f"Browser ready: {ws_url}")

        # Detect Chrome version to download the matching ChromeDriver
        parsed = urlparse(ws_url)
        daemon_endpoint = f"http://{parsed.hostname}:{parsed.port}"
        browser_id = parsed.path.strip("/").split("/")[-1]
        with urllib.request.urlopen(
            f"{daemon_endpoint}/cdp/{browser_id}/json/version", timeout=5
        ) as resp:
            version_info = json.loads(resp.read())
        chrome_version = version_info["Browser"].split("/")[1].split(".")[0]
        logging.info(f"Detected Chrome version: {chrome_version}")

        # Start the CDP shim and connect Selenium
        with cdp_shim(ws_url) as shim_addr:
            options = Options()
            options.debugger_address = shim_addr

            service = Service(ChromeDriverManager(driver_version=chrome_version).install())
            driver = webdriver.Chrome(service=service, options=options)
            logging.info("Selenium connected to stealth browser")

            wait = 30

            driver.set_page_load_timeout(wait)
            driver.get("https://example.com")
            logging.info(f"Page title: {driver.title}")

            try:
                if sys.stdin.isatty():
                    input("[INFO] Press Enter to close the browser...")
                else:
                    import time; time.sleep(3)
            except EOFError:
                import time; time.sleep(3)

            driver.quit()

    except Exception as e:
        logging.error(f"An error occurred: {e}")


if __name__ == "__main__":
    main()

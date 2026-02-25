import logging
import sys
from rayobrowse import create_browser
from playwright.sync_api import sync_playwright

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Example script showcasing rayobrowse with Playwright.

    This script creates a stealth browser, navigates to example.com, and waits
    for you to press Enter. You should see info logs showing the browser
    creation via the daemon.

    Prerequisites:
        pip install rayobrowse playwright
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

        # Connect to the browser via CDP WebSocket
        with sync_playwright() as p:
            browser = p.chromium.connect_over_cdp(ws_url)

            # Get the default page (or create one)
            context = browser.contexts[0] if browser.contexts else browser.new_context()
            page = context.pages[0] if context.pages else context.new_page()

            wait = 30000

            # Navigate to example.com
            page.goto("https://example.com", wait_until="commit", timeout=wait)
            page.wait_for_load_state("domcontentloaded", timeout=wait)
            page.wait_for_timeout(3000)

            logging.info(f"Page title: {page.title()}")

            try:
                if sys.stdin.isatty():
                    input("[INFO] Press Enter to close the browser...")
                else:
                    page.wait_for_timeout(3000)
            except EOFError:
                page.wait_for_timeout(3000)

            # Closing the Playwright connection triggers daemon auto-cleanup
            # (2 second grace period, then the daemon kills the browser process)
            browser.close()

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()

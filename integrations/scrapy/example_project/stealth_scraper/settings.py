BOT_NAME = "stealth_scraper"
SPIDER_MODULES = ["stealth_scraper.spiders"]
NEWSPIDER_MODULE = "stealth_scraper.spiders"

# --- rayobrowse + scrapy-playwright ----------------------------------------
# Connect to rayobrowse's /connect endpoint. A stealth browser is created
# automatically when Scrapy starts and cleaned up when it disconnects.
# Change the query params to customize the fingerprint (os, proxy, etc).
PLAYWRIGHT_CDP_URL = "ws://localhost:9222/connect?headless=true&os=windows"

# Use Playwright as the download handler for all requests.
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Let rayobrowse control the User-Agent for browser requests. Without this,
# Scrapy overrides the UA that rayobrowse set on the fingerprint, and sites
# will flag the mismatch between HTTP headers and navigator.userAgent.
PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None

# --- Scraping behaviour ----------------------------------------------------
CONCURRENT_REQUESTS = 1
DOWNLOAD_DELAY = 2
ROBOTSTXT_OBEY = True
LOG_LEVEL = "INFO"

# Scrapy + rayobrowse

Use [Scrapy](https://scrapy.org) with a stealth browser that doesn't get
detected.

Standard headless Chromium is fine for simple pages, but any site with
bot detection will block it immediately. Scrapy on its own can't render
JavaScript at all. The usual fix is `scrapy-playwright`, which adds a
real browser to Scrapy. But that browser still has a default Chromium
fingerprint that bot-detection services flag on sight.

rayobrowse gives `scrapy-playwright` a browser with a real-device fingerprint:
matching user agent, screen resolution, WebGL renderer, fonts, timezone, and
all the other signals that detection systems check. Your Scrapy spider runs
with the full power of a real browser and the stealth of a real user's machine.

The free tier gives you **1 concurrent browser with no time limits**.

---

## How It Works

[scrapy-playwright](https://github.com/scrapy-plugins/scrapy-playwright) is
the standard way to add browser rendering to Scrapy. It supports connecting to
a remote browser via CDP (Chrome DevTools Protocol) through the
`PLAYWRIGHT_CDP_URL` setting.

rayobrowse exposes a `/connect` endpoint that auto-creates a stealth browser
when Playwright connects and cleans it up when the spider finishes. You point
scrapy-playwright at that endpoint and everything works.

```
Scrapy spider
  |
  |  scrapy-playwright download handler
  |
  v
Playwright  ---CDP--->  rayobrowse /connect endpoint  --->  stealth Chromium
                         (fingerprinted, proxy-ready)
```

One line in `settings.py` is all it takes:

```python
PLAYWRIGHT_CDP_URL = "ws://localhost:9222/connect?headless=true&os=windows"
```

---

## Tutorial: Scraping Quotes with a Stealth Browser

This walkthrough takes you from zero to a working Scrapy spider that renders
JavaScript pages through a stealth-fingerprinted browser. We'll scrape
[quotes.toscrape.com/js](https://quotes.toscrape.com/js/), a practice site
that renders quotes via JavaScript (so a regular HTTP request gets an empty
page).

### Step 1: Start rayobrowse

If you haven't already, clone the repo and start the container:

```bash
git clone https://github.com/rayobyte-data/rayobrowse.git
cd rayobrowse
cp .env.example .env
```

Edit `.env` and set `STEALTH_BROWSER_ACCEPT_TERMS=true`, then:

```bash
docker compose up -d
```

Verify the daemon is healthy:

```bash
curl -s http://localhost:9222/health
# {"success": true, "data": {"status": "healthy", ...}}
```

### Step 2: Install dependencies and grab the example

```bash
pip install scrapy scrapy-playwright
```

This installs Scrapy, the `scrapy-playwright` plugin, and the Playwright
Python library (used for browser automation over CDP). You don't need to run
`playwright install` to download browser binaries since the browser itself
runs inside the rayobrowse container.

Clone or copy the [`example_project/`](example_project/) directory. It
contains a ready-to-run Scrapy project:

```
example_project/
  scrapy.cfg
  requirements.txt
  stealth_scraper/
    settings.py          # pre-configured for rayobrowse
    spiders/
      quotes.py          # JS-rendered quotes (tutorial spider)
      books.py           # book catalog with pagination
```

### How the example is configured

The key parts of [`settings.py`](example_project/stealth_scraper/settings.py):

```python
PLAYWRIGHT_CDP_URL = "ws://localhost:9222/connect?headless=true&os=windows"

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None
```

| Setting | Why |
|---------|-----|
| `PLAYWRIGHT_CDP_URL` | Points scrapy-playwright at rayobrowse's `/connect` endpoint instead of launching its own browser. A stealth browser is auto-created on connect and cleaned up when the spider finishes. |
| `DOWNLOAD_HANDLERS` | Tells Scrapy to route requests through the scrapy-playwright download handler so pages are rendered in the browser. |
| `TWISTED_REACTOR` | Required by scrapy-playwright for async support. |
| `PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None` | Stops Scrapy from overriding the User-Agent that rayobrowse set on the fingerprint. Without this, the UA in HTTP headers won't match `navigator.userAgent`, and detection systems will flag the mismatch. |

The spider in [`quotes.py`](example_project/stealth_scraper/spiders/quotes.py)
scrapes [quotes.toscrape.com/js](https://quotes.toscrape.com/js/), a practice
site that renders quotes via JavaScript (a regular HTTP request gets an empty
page). Each request uses `meta={"playwright": True}` to tell scrapy-playwright
to render it in the browser, and `playwright_include_page` gives access to the
Playwright `Page` object so it can be closed after use.

### Step 3: Run the spider

From inside `example_project/`:

```bash
scrapy crawl quotes -o quotes.json
```

You should see output like:

```
[scrapy_playwright] INFO: Connecting using CDP: ws://localhost:9222/connect?headless=true&os=windows
[scrapy_playwright] INFO: Connected using CDP: ws://localhost:9222/connect?headless=true&os=windows
...
[scrapy.statscollectors] INFO: Dumping Scrapy stats:
 'item_scraped_count': 100,
 'playwright/page_count': 10,
 ...
[scrapy.core.engine] INFO: Spider closed (finished)
```

The results are in `quotes.json`:

```json
[
  {
    "text": "\u201cThe world as we have created it is a process of our thinking...\u201d",
    "author": "Albert Einstein",
    "tags": ["change", "deep-thoughts", "thinking", "world"]
  },
  ...
]
```

There's also a `books` spider you can try: `scrapy crawl books -o books.json`.

### Step 4 (optional): Watch the browser live

Change headless to false in the URL:

```python
PLAYWRIGHT_CDP_URL = "ws://localhost:9222/connect?headless=false&os=windows"
```

Then open [http://localhost:6080/vnc.html](http://localhost:6080/vnc.html)
in your browser. You'll see the stealth Chromium navigating through the pages
as Scrapy crawls.

---

## Using a Proxy

Pass a proxy URL in the `/connect` query string:

```python
PLAYWRIGHT_CDP_URL = (
    "ws://localhost:9222/connect"
    "?headless=true"
    "&os=windows"
    "&proxy=http://user:pass@proxy.example.com:8080"
)
```

The proxy is configured at the browser level by rayobrowse. All requests from
all pages in the spider will use it. The browser fingerprint's timezone and
locale are automatically matched to the proxy's geolocation.

---

## Remote Mode

If rayobrowse is running on a remote server in remote mode, add the `api_key`:

```python
PLAYWRIGHT_CDP_URL = (
    "ws://your-server.example.com/connect"
    "?headless=true"
    "&os=windows"
    "&api_key=your-secret-key"
)
```

See the [main README](../../README.md) for remote mode setup.

---

## Configuration Reference

All `/connect` query params:

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

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `Connection refused` on 9222 | Container not running | `docker compose up -d` |
| `TERMS_REQUIRED` | Terms not accepted | Set `STEALTH_BROWSER_ACCEPT_TERMS=true` in `.env` |
| Empty page / no quotes | Missing `playwright: True` in meta | Add `meta={"playwright": True}` to the request |
| User-Agent mismatch detected | Scrapy overriding UA | Set `PLAYWRIGHT_PROCESS_REQUEST_HEADERS = None` in settings.py |
| `ReactorNotRestartable` | Wrong Twisted reactor | Add `TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"` |
| `CONCURRENT_LIMIT_EXCEEDED` | Too many browsers | Free tier allows 1 concurrent browser. Close others or upgrade. |

### Checking daemon logs

```bash
docker compose logs --tail=50
```

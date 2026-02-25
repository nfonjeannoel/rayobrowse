/**
 * Puppeteer example for Rayobyte Stealth Browser.
 *
 * This script creates a stealth browser via the daemon REST API and
 * controls it with Puppeteer over the CDP WebSocket endpoint.
 *
 * Prerequisites:
 *   npm install puppeteer-core
 *   Docker container running: docker compose up -d
 *
 * Usage:
 *   node puppeteer_example.js
 *
 * Note: puppeteer-core is used instead of puppeteer because the browser is
 * provided by the Docker daemon — no bundled Chromium download needed.
 */

'use strict';

const puppeteer = require('puppeteer-core');

// ── Config ───────────────────────────────────────────────────────────────────

const DAEMON_ENDPOINT = process.env.RAYOBYTE_ENDPOINT || 'http://localhost:9222';
const API_KEY = process.env.STEALTH_BROWSER_API_KEY || '';

// Fingerprint filters — adjust as needed
const BROWSER_CONFIG = {
  headless: false,
  os: 'windows',        // android and windows tested; macos and linux experimental
  browser_name: 'chrome',
  browser_version_min: 144,
  browser_version_max: 144,
  // proxy: 'http://username:password@host:port',
};

// ── Helpers ──────────────────────────────────────────────────────────────────

/**
 * Create a stealth browser via the daemon REST API.
 * @returns {Promise<string>} CDP WebSocket URL
 */
async function createBrowser() {
  const payload = { ...BROWSER_CONFIG };
  if (API_KEY) payload.api_key = API_KEY;

  const resp = await fetch(`${DAEMON_ENDPOINT}/browser`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });

  if (!resp.ok) {
    throw new Error(`Daemon returned HTTP ${resp.status}`);
  }

  const data = await resp.json();
  if (!data.success) {
    throw new Error(data.error?.message || 'Browser creation failed');
  }

  // Normalize 0.0.0.0 → localhost for local Docker setups
  const wsUrl = data.data.ws_endpoint.replace('0.0.0.0', 'localhost');
  return wsUrl;
}

// ── Main ─────────────────────────────────────────────────────────────────────

async function main() {
  console.log(`Creating browser (OS=${BROWSER_CONFIG.os}, Chrome ${BROWSER_CONFIG.browser_version_min}-${BROWSER_CONFIG.browser_version_max})...`);

  const wsUrl = await createBrowser();
  console.log(`Browser ready: ${wsUrl}`);

  // Connect to the browser via the CDP WebSocket
  const browser = await puppeteer.connect({ browserWSEndpoint: wsUrl });

  const pages = await browser.pages();
  const page = pages[0] || await browser.newPage();

  // Navigate to example.com
  await page.goto('https://example.com', { waitUntil: 'domcontentloaded', timeout: 30000 });
  const title = await page.title();
  console.log(`Page title: ${title}`);

  if (process.stdin.isTTY) {
    // Interactive mode — wait for Enter
    console.log('[INFO] Press Enter to close the browser...');
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
  } else {
    await new Promise(resolve => setTimeout(resolve, 3000));
  }

  // disconnect() leaves the browser running; the daemon auto-cleans up
  // after the last client disconnects (2-second grace period).
  await browser.disconnect();
  console.log('Done.');
}

main().catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});

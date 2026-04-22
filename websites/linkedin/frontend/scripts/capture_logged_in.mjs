import { chromium } from '@playwright/test'

// Usage:
//   node scripts/capture_logged_in.mjs http://127.0.0.1:12078 /path/to/output.png
const baseUrl = process.argv[2]
const outPath = process.argv[3]

if (!baseUrl || !outPath) {
  // eslint-disable-next-line no-console
  console.error('Usage: node scripts/capture_logged_in.mjs <baseUrl> <outputPath>')
  process.exit(2)
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } })

await page.goto(`${baseUrl}/login`, { waitUntil: 'domcontentloaded' })
await page.fill('input[autocomplete="email"]', 'jane.doe@example.com')
await page.fill('input[autocomplete="current-password"]', 'password123')
await page.click('button:has-text("Sign in")')

// Wait until we hit feed (header/search is a good signal).
await page.waitForURL('**/feed', { timeout: 15_000 })
await page.waitForTimeout(800)

await page.screenshot({ path: outPath, fullPage: true })
await browser.close()


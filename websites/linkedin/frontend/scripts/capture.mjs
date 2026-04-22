import { chromium } from '@playwright/test'

// Usage:
//   node scripts/capture.mjs http://localhost:12078 /path/to/output.png
const url = process.argv[2]
const outPath = process.argv[3]

if (!url || !outPath) {
  // eslint-disable-next-line no-console
  console.error('Usage: node scripts/capture.mjs <url> <outputPath>')
  process.exit(2)
}

const browser = await chromium.launch()
const page = await browser.newPage({ viewport: { width: 1200, height: 800 } })
await page.goto(url, { waitUntil: 'networkidle' })
await page.waitForTimeout(500)
await page.screenshot({ path: outPath, fullPage: true })
await browser.close()


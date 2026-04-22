import { chromium } from "playwright";

/**
 * Usage:
 *   node scripts/capture.mjs <url> <output.png>
 *
 * Notes:
 * - Waits for network idle and a short extra delay to stabilize layout.
 */
const [, , url, output] = process.argv;
if (!url || !output) {
  console.error("Usage: node scripts/capture.mjs <url> <output.png>");
  process.exit(2);
}

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

page.on("pageerror", (err) => {
  console.error("[pageerror]", err?.message || String(err));
});
page.on("console", (msg) => {
  if (msg.type() === "error") console.error("[console]", msg.text());
});

await page.goto(url, { waitUntil: "networkidle" });
await page.waitForTimeout(800);
await page.screenshot({ path: output, fullPage: true });

await browser.close();

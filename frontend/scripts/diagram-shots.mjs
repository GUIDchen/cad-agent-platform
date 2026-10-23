import { chromium } from '@playwright/test'
import path from 'node:path'
import { mkdir } from 'node:fs/promises'

const file = path.resolve('diagrams.html')
const out = path.resolve('../docs/assets/diagrams')
await mkdir(out, { recursive: true })

const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1600, height: 1200 }, deviceScaleFactor: 2 })
await page.goto('file://' + file)
await page.waitForTimeout(400)

for (const id of ['arch-overall', 'arch-layers', 'arch-deploy', 'roadmap', 'flow-approval', 'data-model', 'ai-routing']) {
  await page.locator('#' + id).screenshot({ path: out + '/' + id + '.png' })
}

await browser.close()
console.log('diagrams saved')

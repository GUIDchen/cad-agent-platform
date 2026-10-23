import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'

const out = '../docs/assets'
await mkdir(out, { recursive: true })
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, baseURL: 'http://127.0.0.1:8000' })

await page.goto('/login')
await page.waitForTimeout(700)
await page.screenshot({ path: out + '/platform-login.png', fullPage: true })

await page.getByRole('button', { name: /设计员/ }).click()
await page.waitForURL(/\/drawings/)
await page.waitForTimeout(700)
await page.screenshot({ path: out + '/platform-drawings.png', fullPage: true })

await page.goto('/dashboard')
await page.locator('canvas').first().waitFor({ state: 'visible', timeout: 20000 }).catch(() => {})
await page.waitForTimeout(900)
await page.screenshot({ path: out + '/platform-dashboard.png', fullPage: true })

await page.goto('/drawings')
await page.getByText('SW-2026-001').click()
await page.waitForURL(/\/drawings\/\d+/)
await page.locator('img.preview').waitFor({ state: 'visible', timeout: 30000 })
await page.waitForTimeout(600)
await page.screenshot({ path: out + '/platform-detail.png', fullPage: true })

await browser.close()
console.log('ui shots saved')

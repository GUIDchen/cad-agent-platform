import { chromium } from '@playwright/test'

const out = '../docs/assets'
const browser = await chromium.launch({ channel: 'chrome', headless: true })

const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, baseURL: 'http://127.0.0.1:8000' })
await page.goto('/login')
await page.getByRole('button', { name: /设计员/ }).click()
await page.waitForURL(/\/drawings/)
await page.goto('/images')
await page.getByRole('button', { name: '生成' }).click()
await page.locator('img.result').waitFor({ state: 'visible', timeout: 30000 })
await page.waitForTimeout(600)
await page.screenshot({ path: out + '/platform-images.png', fullPage: true })

const admin = await browser.newPage({ viewport: { width: 1440, height: 1000 }, baseURL: 'http://127.0.0.1:8000' })
await admin.goto('/login')
await admin.getByRole('button', { name: /管理员/ }).click()
await admin.waitForURL(/\/drawings/)
await admin.goto('/audit')
await admin.waitForTimeout(800)
await admin.screenshot({ path: out + '/platform-audit.png', fullPage: true })

await browser.close()
console.log('screenshots2 saved')

import { chromium } from '@playwright/test'
import { mkdir } from 'node:fs/promises'

const out = '../docs/assets/interview'
await mkdir(out, { recursive: true })
const browser = await chromium.launch({ channel: 'chrome', headless: true })
const base = 'http://127.0.0.1:8000'

const designer = await browser.newPage({ viewport: { width: 1440, height: 1000 }, baseURL: base })
await designer.goto('/login')
await designer.waitForTimeout(500)
await designer.screenshot({ path: out + '/01-login.png', fullPage: true })

await designer.getByRole('button', { name: /设计员/ }).click()
await designer.waitForURL(/\/drawings/)
await designer.waitForTimeout(500)
await designer.screenshot({ path: out + '/03-drawings.png', fullPage: true })

await designer.goto('/dashboard')
await designer.locator('canvas').first().waitFor({ state: 'visible', timeout: 20000 }).catch(() => {})
await designer.waitForTimeout(700)
await designer.screenshot({ path: out + '/02-dashboard.png', fullPage: true })

await designer.goto('/drawings')
await designer.getByText('SW-2026-001').click()
await designer.waitForURL(/\/drawings\/\d+/)
await designer.locator('img.preview').waitFor({ state: 'visible', timeout: 30000 })
await designer.waitForTimeout(500)
await designer.screenshot({ path: out + '/04-detail.png', fullPage: true })

await designer.goto('/projects')
await designer.waitForTimeout(500)
await designer.screenshot({ path: out + '/05-projects.png', fullPage: true })
await designer.getByRole('button', { name: '成员' }).first().click()
await designer.waitForTimeout(500)
await designer.screenshot({ path: out + '/06-members.png', fullPage: true })

await designer.goto('/images')
await designer.getByRole('button', { name: '生成' }).click()
await designer.locator('img.result').waitFor({ state: 'visible', timeout: 30000 })
await designer.waitForTimeout(400)
await designer.screenshot({ path: out + '/09-images.png', fullPage: true })

await designer.goto('/assistant')
await designer.getByRole('button', { name: '执行' }).click()
await designer.locator('.card').waitFor({ state: 'visible', timeout: 30000 })
await designer.waitForTimeout(400)
await designer.screenshot({ path: out + '/10-assistant.png', fullPage: true })

await designer.goto('/nope')
await designer.waitForTimeout(400)
await designer.screenshot({ path: out + '/11-notfound.png', fullPage: true })

const admin = await browser.newPage({ viewport: { width: 1440, height: 1000 }, baseURL: base })
await admin.goto('/login')
await admin.getByRole('button', { name: /管理员/ }).click()
await admin.waitForURL(/\/drawings/)
await admin.goto('/users')
await admin.waitForTimeout(500)
await admin.screenshot({ path: out + '/07-users.png', fullPage: true })

await admin.goto('/audit')
await admin.waitForTimeout(500)
await admin.screenshot({ path: out + '/08-audit.png', fullPage: true })

await browser.close()
console.log('interview screenshots saved')

import { expect, test } from '@playwright/test'

test('login page has basic accessible structure', async ({ page }) => {
  await page.goto('/login')
  await expect(page.locator('html')).toHaveAttribute('lang', 'zh-CN')
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  await expect(page.getByRole('button').first()).toBeVisible()
})

test('workspace exposes navigation and main landmarks', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: /设计员/ }).click()
  await expect(page).toHaveURL(/\/drawings/)
  await expect(page.getByRole('navigation')).toBeVisible()
  await expect(page.getByRole('main')).toBeVisible()
  await expect(page.getByRole('link', { name: '图纸' })).toBeVisible()
})

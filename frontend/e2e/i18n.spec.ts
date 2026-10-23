import { expect, test } from '@playwright/test'

test('language switch updates navigation', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: /设计员/ }).click()
  await expect(page).toHaveURL(/\/drawings/)

  await page.locator('.lang').click()
  await expect(page.getByRole('link', { name: 'Drawings' })).toBeVisible()

  await page.locator('.lang').click()
  await expect(page.getByRole('link', { name: '图纸' })).toBeVisible()
})

import { expect, test } from '@playwright/test'

test('command palette navigates to a page', async ({ page }) => {
  await page.goto('/login')
  await page.getByRole('button', { name: /设计员/ }).click()
  await expect(page).toHaveURL(/\/drawings/)

  await page.keyboard.press('Control+K')
  const input = page.getByPlaceholder(/搜索页面/)
  await expect(input).toBeVisible()
  await input.fill('看板')
  await page.keyboard.press('Enter')
  await expect(page).toHaveURL(/\/dashboard/)
})

import { expect, test } from '@playwright/test'

test('designer generates and reviewer approves', async ({ page, browser }, testInfo) => {
  const suffix = testInfo.project.name.includes('webkit') ? '303' : testInfo.project.name.startsWith('mobile') ? '202' : '101'
  const drawingNo = 'SW-2026-' + suffix
  await page.addInitScript(() => localStorage.setItem('locale', 'zh'))
  await page.goto('/login')
  await page.getByRole('button', { name: /设计员/ }).click()
  await expect(page).toHaveURL(/\/drawings/)

  await page.getByRole('button', { name: '新建图纸' }).click()
  const dialog = page.locator('.el-dialog').last()
  await dialog.locator('.el-form-item', { hasText: '图号' }).locator('input').fill(drawingNo)
  await dialog.locator('.el-form-item', { hasText: '名称' }).locator('input').fill('E2E 安装板')
  await dialog.getByRole('button', { name: '创建' }).click()
  await expect(page.getByText(drawingNo)).toBeVisible()

  await page.getByText(drawingNo).click()
  await expect(page).toHaveURL(/\/drawings\/\d+/)
  await page.getByRole('button', { name: '生成' }).click()
  await expect(page.locator('img.preview')).toBeVisible({ timeout: 30_000 })

  const reviewer = await browser.newPage({ baseURL: 'http://127.0.0.1:8000' })
  await reviewer.addInitScript(() => localStorage.setItem('locale', 'zh'))
  await reviewer.goto('/login')
  await reviewer.getByRole('button', { name: /审批人/ }).click()
  await expect(reviewer).toHaveURL(/\/drawings/)
  await reviewer.getByText(drawingNo).click()
  await reviewer.getByRole('button', { name: '通过' }).click()
  const confirm = reviewer.locator('.el-message-box__btns .el-button--primary')
  await confirm.waitFor()
  await confirm.dispatchEvent('click')
  await expect(reviewer.locator('.el-descriptions__content', { hasText: '已通过' })).toBeVisible()
  await reviewer.close()
})

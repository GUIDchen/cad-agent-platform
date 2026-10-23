import { defineConfig, devices } from '@playwright/test'

const channel = process.env.CI ? undefined : 'chrome'

export default defineConfig({
  testDir: './e2e',
  timeout: 90_000,
  expect: { timeout: 15_000 },
  fullyParallel: false,
  workers: 1,
  reporter: [['list']],
  use: {
    baseURL: 'http://127.0.0.1:8000',
    headless: true,
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: [
    { name: 'desktop-chrome', use: { ...devices['Desktop Chrome'], channel } },
    { name: 'mobile-chrome', use: { ...devices['Pixel 7'], channel } },
    { name: 'desktop-webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: {
    command: 'bash ../scripts/e2e-server.sh',
    url: 'http://127.0.0.1:8000/api/health',
    reuseExistingServer: false,
    timeout: 60_000,
  },
})

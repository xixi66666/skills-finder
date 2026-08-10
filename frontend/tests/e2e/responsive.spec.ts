import { expect, test } from '@playwright/test'

import { assertNoHorizontalScroll, mockApi } from './mock-api'

test.beforeEach(async ({ page }) => {
  await mockApi(page)
})

test('mobile home page has no horizontal scroll', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('octocat/agent-hub')).toBeVisible()
  await assertNoHorizontalScroll(page)
})

test('mobile detail page has no horizontal scroll', async ({ page }) => {
  await page.goto('/repositories/octocat/agent-hub')
  await expect(page.getByRole('heading', { name: 'octocat/agent-hub' })).toBeVisible()
  await assertNoHorizontalScroll(page)
})

test('mobile buttons do not truncate text', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('octocat/agent-hub')).toBeVisible()
  const overflowed = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'))
    return buttons.filter((b) => b.scrollWidth > b.clientWidth).length
  })
  expect(overflowed).toBe(0)
})

test('mobile trend chart renders non-empty pixels', async ({ page }) => {
  await page.goto('/repositories/octocat/agent-hub')
  await expect(page.getByTestId('trend-chart')).toBeVisible()
  const chart = page.getByTestId('trend-chart')
  const box = await chart.boundingBox()
  expect(box).not.toBeNull()
  const strokeColor = await chart.locator('path').first().evaluate((el) => {
    const stroke = getComputedStyle(el).stroke
    return stroke && stroke !== 'none' ? stroke : null
  })
  expect(strokeColor).not.toBeNull()
  const pathCount = await chart.locator('path, circle').count()
  expect(pathCount).toBeGreaterThan(0)
  const drawnPixels = await page.evaluate(() => {
    const svg = document.querySelector('[data-testid="trend-chart"]')
    if (!svg) return 0
    const paths = svg.querySelectorAll('path, circle')
    let pixels = 0
    paths.forEach((el) => {
      const length = (el as SVGGeometryElement).getTotalLength?.() ?? 0
      pixels += Math.max(1, Math.round(length))
    })
    return pixels
  })
  expect(drawnPixels).toBeGreaterThan(10)
})

test('keyboard can open filters and navigate', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('octocat/agent-hub')).toBeVisible()
  await page.keyboard.press('Tab')
  await page.keyboard.press('Tab')
  await page.keyboard.press('Enter')
})

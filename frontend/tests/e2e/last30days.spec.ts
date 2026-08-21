import { expect, test } from '@playwright/test'

import { mockApi } from './mock-api'

test.beforeEach(async ({ page }) => {
  await mockApi(page)
  await page.route('**/api/v1/last30days/status', async (route) => {
    await route.fulfill({
      json: {
        status: 'working',
        sources: ['reddit', 'hackernews', 'polymarket', 'github', 'grounding'],
      },
    })
  })
  await page.route('**/api/v1/last30days', async (route) => {
    await route.fulfill({
      json: {
        status: 'working',
        items: [],
        sources: ['reddit', 'hackernews', 'polymarket', 'github', 'grounding'],
        source_status: {},
        fetched_at: '2026-08-21T00:00:00Z',
      },
    })
  })
})

test('opens recent research from the primary navigation', async ({ page }) => {
  await page.goto('/')

  const researchLink = page.getByRole('link', { name: '近 30 天研究' })
  await expect(researchLink).toBeVisible()
  await researchLink.click()

  await expect(page).toHaveURL(/\/last30days$/)
  await expect(page.getByRole('heading', { name: '近 30 天研究' })).toBeVisible()
})

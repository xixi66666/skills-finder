import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import HomeView from '@/views/HomeView.vue'

import type { RepositoryListResponse } from '@/types/api'

vi.mock('@/api/repositories', () => ({
  fetchRepositories: vi.fn(),
  fetchLanguages: vi.fn(),
  fetchStats: vi.fn(),
}))

import { fetchLanguages, fetchRepositories, fetchStats } from '@/api/repositories'

const mockFetchRepositories = vi.mocked(fetchRepositories)
const mockFetchLanguages = vi.mocked(fetchLanguages)
const mockFetchStats = vi.mocked(fetchStats)

const mockRoute = { query: {} as Record<string, string> }
const mockRouter = {
  replace: vi.fn(),
  push: vi.fn(),
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => mockRouter,
}))

function makeResponse(overrides: Partial<RepositoryListResponse> = {}): RepositoryListResponse {
  return {
    items: [
      {
        id: 1,
        owner: 'octocat',
        name: 'agent-hub',
        description: 'An agent framework',
        html_url: 'https://github.com/octocat/agent-hub',
        language: 'Python',
        topics: ['ai-agent'],
        categories: ['AGENT'],
        stars_count: 1500,
        daily_stars: 20,
        weekly_stars: 100,
        last_synced_at: '2026-08-10T00:00:00Z',
        trend: [],
      },
    ],
    page: 1,
    page_size: 20,
    total: 1,
    last_successful_collection_at: '2026-08-10T00:00:00Z',
    ...overrides,
  }
}

async function mountHome() {
  const wrapper = mount(HomeView, {
    global: {
      plugins: [createPinia()],
      stubs: {
        RouterLink: { template: '<a><slot /></a>' },
        RouterView: true,
      },
    },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
  mockRoute.query = {}
  mockFetchLanguages.mockResolvedValue([])
  mockFetchStats.mockResolvedValue({
    total_repositories: 1,
    positive_growth_today: 1,
    last_successful_collection_at: null,
    last_run_status: 'SUCCESS',
  })
})

describe('HomeView', () => {
  it('shows skeleton on first load', () => {
    mockFetchRepositories.mockReturnValue(new Promise(() => {}))
    const wrapper = mount(HomeView, {
      global: { plugins: [createPinia()], stubs: { RouterLink: true, RouterView: true } },
    })
    expect(wrapper.find('[data-testid="skeleton"]').exists()).toBe(true)
  })

  it('renders repositories on success', async () => {
    mockFetchRepositories.mockResolvedValue(makeResponse())
    const wrapper = await mountHome()
    expect(wrapper.text()).toContain('agent-hub')
    expect(wrapper.text()).toContain('1,500')
  })

  it('renders empty state with reset action', async () => {
    mockFetchRepositories.mockResolvedValue(makeResponse({ items: [], total: 0 }))
    const wrapper = await mountHome()
    expect(wrapper.find('[data-testid="empty-state"]').exists()).toBe(true)
    await wrapper.find('[data-testid="reset-filters"]').trigger('click')
    expect(mockFetchRepositories).toHaveBeenCalled()
  })

  it('renders error state with retry', async () => {
    mockFetchRepositories.mockRejectedValueOnce(new Error('boom'))
    mockFetchRepositories.mockResolvedValueOnce(makeResponse())
    const wrapper = await mountHome()
    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
    await wrapper.find('[data-testid="retry"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('agent-hub')
  })

  it('re-fetches first page when sort changes', async () => {
    mockFetchRepositories.mockResolvedValue(makeResponse())
    const wrapper = await mountHome()
    vi.clearAllMocks()
    mockFetchRepositories.mockResolvedValue(makeResponse())
    const callsBefore = mockFetchRepositories.mock.calls.length
    await wrapper.find('[data-testid="sort-weekly_stars"]').trigger('click')
    await flushPromises()
    expect(mockFetchRepositories.mock.calls.length).toBe(callsBefore + 1)
    expect(mockFetchRepositories.mock.calls.at(-1)?.[0]?.page).toBe(1)
    expect(mockFetchRepositories.mock.calls.at(-1)?.[0]?.sort).toBe('weekly_stars')
  })
})

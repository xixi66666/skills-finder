import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import RepositoryDetailView from '@/views/RepositoryDetailView.vue'

import type { RepositoryDetail } from '@/types/api'

vi.mock('@/api/repositories', () => ({
  fetchRepositoryDetail: vi.fn(),
}))

import { fetchRepositoryDetail } from '@/api/repositories'

const mockFetchDetail = vi.mocked(fetchRepositoryDetail)

const mockRoute = {
  params: { owner: 'octocat', name: 'agent-hub' },
}

vi.mock('vue-router', () => ({
  useRoute: () => mockRoute,
  useRouter: () => ({ back: vi.fn() }),
}))

function makeDetail(overrides: Partial<RepositoryDetail> = {}): RepositoryDetail {
  return {
    id: 1,
    owner: 'octocat',
    name: 'agent-hub',
    description: 'An agent framework',
    introduction: null,
    html_url: 'https://github.com/octocat/agent-hub',
    homepage: null,
    language: 'Python',
    topics: ['ai-agent', 'agentic'],
    categories: ['AGENT', 'MCP'],
    matched_rules: ['topic:ai-agent', 'topic:mcp-server'],
    stars_count: 1500,
    forks_count: 50,
    open_issues_count: 3,
    daily_stars: 20,
    weekly_stars: 100,
    last_synced_at: '2026-08-10T00:00:00Z',
    github_created_at: '2026-01-01T00:00:00Z',
    trend: [
      { snapshot_date: '2026-07-12', stars_count: 1200 },
      { snapshot_date: '2026-07-20', stars_count: 1300 },
      { snapshot_date: '2026-08-10', stars_count: 1500 },
    ],
    ...overrides,
  }
}

async function mountDetail() {
  const wrapper = mount(RepositoryDetailView, {
    global: { plugins: [createPinia()], stubs: { RouterLink: true, RouterView: true } },
  })
  await flushPromises()
  return wrapper
}

beforeEach(() => {
  setActivePinia(createPinia())
  vi.clearAllMocks()
})

describe('RepositoryDetailView', () => {
  it('renders repository info on success', async () => {
    mockFetchDetail.mockResolvedValue(makeDetail())
    const wrapper = await mountDetail()
    expect(wrapper.text()).toContain('octocat/agent-hub')
    expect(wrapper.text()).toContain('An agent framework')
    expect(wrapper.text()).toContain('1,500')
  })

  it('renders introduction sections when present', async () => {
    mockFetchDetail.mockResolvedValue(
      makeDetail({
        introduction: {
          introduction: '这是项目介绍。',
          usage: '直接运行 npm install。',
          domains: ['AI Agent', '自动化'],
        },
      }),
    )
    const wrapper = await mountDetail()
    expect(wrapper.find('[data-testid="introduction"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('这是项目介绍。')
    expect(wrapper.text()).toContain('直接运行 npm install。')
    expect(wrapper.text()).toContain('AI Agent')
    expect(wrapper.text()).toContain('自动化')
  })

  it('hides introduction section when absent', async () => {
    mockFetchDetail.mockResolvedValue(makeDetail({ introduction: null }))
    const wrapper = await mountDetail()
    expect(wrapper.find('[data-testid="introduction"]').exists()).toBe(false)
  })

  it('renders not-found state on 404', async () => {
    mockFetchDetail.mockRejectedValue(
      Object.assign(new Error('not found'), {
        isAxiosError: true,
        response: { status: 404, data: { code: 'REPOSITORY_NOT_FOUND' } },
      }),
    )
    const wrapper = await mountDetail()
    expect(wrapper.find('[data-testid="not-found"]').exists()).toBe(true)
  })

  it('renders error state with retry on network error', async () => {
    mockFetchDetail.mockRejectedValueOnce(
      Object.assign(new Error('network'), { isAxiosError: true, response: undefined }),
    )
    mockFetchDetail.mockResolvedValueOnce(makeDetail())
    const wrapper = await mountDetail()
    expect(wrapper.find('[data-testid="error-state"]').exists()).toBe(true)
    await wrapper.find('[data-testid="retry"]').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('octocat/agent-hub')
  })

  it('does not render the removed 30-day trend section', async () => {
    mockFetchDetail.mockResolvedValue(makeDetail())
    const wrapper = await mountDetail()
    expect(wrapper.text()).not.toContain('最近 30 天趋势')
    expect(wrapper.find('[data-testid="trend-chart"]').exists()).toBe(false)
  })
})

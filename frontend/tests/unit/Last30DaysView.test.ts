import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import Last30DaysView from '@/views/Last30DaysView.vue'

vi.mock('@/api/last30days', () => ({
  fetchLast30daysStatus: vi.fn(),
  postLast30days: vi.fn(),
}))

import { fetchLast30daysStatus, postLast30days } from '@/api/last30days'

const mockedStatus = vi.mocked(fetchLast30daysStatus)
const mockedPost = vi.mocked(postLast30days)

describe('Last30DaysView', () => {
  beforeEach(() => {
    mockedStatus.mockReset()
    mockedPost.mockReset()
    mockedStatus.mockResolvedValue({
      status: 'working',
      sources: ['reddit', 'hackernews', 'github'],
    })
  })

  it('renders the research form and available sources', async () => {
    const wrapper = mount(Last30DaysView)
    await flushPromises()

    expect(wrapper.get('h1').text()).toBe('近 30 天研究')
    expect(wrapper.get('input').attributes('required')).toBeDefined()
    expect(wrapper.text()).toContain('Reddit')
    expect(wrapper.text()).toContain('Hacker News')
  })

  it('displays clusters and multisource results', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'working',
      query: 'OpenAI',
      sources: ['reddit', 'github'],
      source_status: { reddit: 'working', github: 'working' },
      clusters: [
        {
          title: 'Developer reactions',
          summary: 'Developers discussed the latest changes.',
          sources: ['reddit', 'github'],
          engagement_total: 320,
        },
      ],
      items: [
        {
          candidate_id: 'reddit-1',
          title: 'What developers are saying',
          source: 'reddit',
          url: 'https://www.reddit.com/r/example/1',
          published_at: '2026-08-20T00:00:00Z',
          summary: 'A grounded community summary.',
          engagement: { score: 210, comments: 42 },
          relevance_score: 0.95,
          cluster: 0,
        },
      ],
      fetched_at: '2026-08-21T00:00:00Z',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.get('input').setValue('OpenAI')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(mockedPost).toHaveBeenCalledWith('OpenAI')
    expect(wrapper.text()).toContain('Developer reactions')
    expect(wrapper.text()).toContain('What developers are saying')
    expect(wrapper.text()).toContain('相关度 95%')
  })

  it('shows an empty state when no recent signals are found', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'no-results',
      query: 'unlikely topic',
      sources: ['reddit'],
      source_status: { reddit: 'no-results' },
      clusters: [],
      items: [],
      fetched_at: '2026-08-21T00:00:00Z',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.get('input').setValue('unlikely topic')
    await wrapper.get('form').trigger('submit')
    await flushPromises()

    expect(wrapper.text()).toContain('最近 30 天没有找到相关结果')
  })

  it('shows engine setup failures without hiding the form', async () => {
    mockedStatus.mockResolvedValueOnce({
      status: 'unconfigured',
      sources: [],
      message: '未找到用户级 last30days skill。',
    })
    const wrapper = mount(Last30DaysView)
    await flushPromises()

    expect(wrapper.text()).toContain('需要配置')
    expect(wrapper.text()).toContain('未找到用户级 last30days skill。')
    expect(wrapper.get('form').element).toBeInstanceOf(HTMLFormElement)
  })
})

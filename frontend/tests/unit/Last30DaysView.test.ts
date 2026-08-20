import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import Last30DaysView from '@/views/Last30DaysView.vue'

vi.mock('@/api/last30days', () => ({
  postLast30days: vi.fn(),
}))

import { postLast30days } from '@/api/last30days'
const mockedPost = vi.mocked(postLast30days)

describe('Last30DaysView', () => {
  beforeEach(() => {
    mockedPost.mockReset()
  })

  it('renders form with input and button', () => {
    const wrapper = mount(Last30DaysView)
    expect(wrapper.find('input').exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
    expect(wrapper.find('h1').text()).toContain('Last 30 Days')
  })

  it('displays working status with results', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'working',
      items: [
        { object_id: '1', created_at: '2025-08-01', title: 'Test Story', url: 'https://example.com', author: 'user1', points: 100, num_comments: 20, story_text: '', citation_url: 'https://example.com' },
      ],
      fetched_at: '2025-08-20T00:00:00Z',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => {
      expect(wrapper.find('.source-status').text()).toContain('working')
    })
    expect(wrapper.findAll('.result-item')).toHaveLength(1)
    expect(wrapper.find('.result-title').text()).toBe('Test Story')
  })

  it('displays no-results status', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'no-results',
      items: [],
      fetched_at: '2025-08-20T00:00:00Z',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => {
      expect(wrapper.find('.source-status').text()).toContain('no-results')
    })
    expect(wrapper.findAll('.result-item')).toHaveLength(0)
  })

  it('displays error status on API failure', async () => {
    mockedPost.mockRejectedValueOnce(new Error('Network error'))
    const wrapper = mount(Last30DaysView)
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => {
      expect(wrapper.find('.source-status').text()).toContain('error')
    })
    expect(wrapper.find('.error-message').text()).toContain('Network error')
  })

  it('displays skipped status', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'skipped',
      items: [],
      fetched_at: '2025-08-20T00:00:00Z',
      message: 'Module disabled',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => {
      expect(wrapper.find('.source-status').text()).toContain('skipped')
    })
  })

  it('displays partial status with message', async () => {
    mockedPost.mockResolvedValueOnce({
      status: 'partial',
      items: [
        { object_id: '1', created_at: '2025-08-01', title: 'A', url: '', author: 'u', points: 10, num_comments: 0, story_text: '', citation_url: 'https://news.ycombinator.com/item?id=1' },
      ],
      fetched_at: '2025-08-20T00:00:00Z',
      message: 'Some items dropped',
    })
    const wrapper = mount(Last30DaysView)
    await wrapper.find('form').trigger('submit')
    await vi.waitFor(() => {
      expect(wrapper.find('.source-status').text()).toContain('partial')
      expect(wrapper.find('.source-status').text()).toContain('Some items dropped')
    })
    expect(wrapper.findAll('.result-item')).toHaveLength(1)
  })
})

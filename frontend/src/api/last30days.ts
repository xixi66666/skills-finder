import { http } from '@/api/client'

export type Last30DaysStatus =
  | 'working'
  | 'no-results'
  | 'partial'
  | 'error'
  | 'skipped'
  | 'unconfigured'

export interface Last30DaysCluster {
  title: string
  summary: string
  sources: string[]
  engagement_total: number
}

export interface Last30DaysItem {
  candidate_id: string
  title: string
  source: string
  url: string
  published_at: string
  summary: string
  engagement: Record<string, unknown>
  relevance_score: number | null
  cluster: number | null
}

export interface Last30DaysResponse {
  status: Last30DaysStatus
  query: string
  items: Last30DaysItem[]
  clusters: Last30DaysCluster[]
  sources: string[]
  source_status: Record<string, unknown>
  fetched_at: string
  message?: string | null
}

export interface Last30DaysStatusResponse {
  status: Last30DaysStatus
  sources: string[]
  message?: string | null
}

export async function fetchLast30daysStatus(): Promise<Last30DaysStatusResponse> {
  const { data } = await http.get<Last30DaysStatusResponse>('/last30days/status')
  return data
}

export async function postLast30days(query: string, limit = 50): Promise<Last30DaysResponse> {
  const { data } = await http.post<Last30DaysResponse>('/last30days', {
    query: query.trim(),
    limit,
  })
  return data
}

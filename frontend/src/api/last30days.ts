import { http } from '@/api/client'

export interface Last30DaysItem {
  object_id: string
  created_at: string
  title: string
  url: string | null
  author: string
  points: number
  num_comments: number
  story_text: string | null
  citation_url: string
}

export interface Last30DaysResponse {
  status: string
  items: Last30DaysItem[]
  fetched_at: string
  message?: string
}

export async function postLast30days(query?: string, limit?: number): Promise<Last30DaysResponse> {
  const body: Record<string, unknown> = {}
  if (query && query.trim()) body.query = query.trim()
  if (limit != null) body.limit = limit
  const { data } = await http.post<Last30DaysResponse>('/last30days', body)
  return data
}

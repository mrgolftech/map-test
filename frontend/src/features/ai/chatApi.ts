import { apiRequest } from '../../api/client'

export type ChatCitation = {
  id: string
  label: string
  value: string
  analysis_id: string | null
}

export type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations: ChatCitation[]
  limitations: string[]
  insufficient_evidence: boolean
  model: string | null
  created_at: string
}

export type ChatThreadData = {
  thread_id: string | null
  scope: 'analysis' | 'comparison'
  context_ids: string[]
  messages: ChatMessage[]
}

export type ChatThreadResponse = {
  data: ChatThreadData
  meta: Record<string, unknown>
}

export function getAnalysisChat(analysisId: string) {
  return apiRequest<ChatThreadResponse>(
    `/api/v1/ai/chat/analyses/${encodeURIComponent(analysisId)}`,
  )
}

export function askAnalysisChat(analysisId: string, question: string) {
  return apiRequest<ChatThreadResponse>(
    `/api/v1/ai/chat/analyses/${encodeURIComponent(analysisId)}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    },
  )
}

export function getComparisonChat(analysisIds: string[]) {
  const params = new URLSearchParams()
  analysisIds.forEach((id) => params.append('analysis_ids', id))
  return apiRequest<ChatThreadResponse>(
    `/api/v1/ai/chat/comparison?${params.toString()}`,
  )
}

export function askComparisonChat(analysisIds: string[], question: string) {
  return apiRequest<ChatThreadResponse>('/api/v1/ai/chat/comparison', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ analysis_ids: analysisIds, question }),
  })
}

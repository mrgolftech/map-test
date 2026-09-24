import { apiRequest } from '../../api/client'
import type {
  AIAnalyzeResponse,
  LLMConfigResponse,
  LLMConnectionResponse,
  LLMModelListResponse,
  LLMCandidate,
  LLMSelectedCandidate,
} from '../../types/ai'

export function getLLMConfig(): Promise<LLMConfigResponse> {
  return apiRequest<LLMConfigResponse>('/api/v1/settings/llm')
}

function jsonHeaders(): HeadersInit {
  return { 'Content-Type': 'application/json' }
}

export function fetchLLMModels(candidate: LLMCandidate): Promise<LLMModelListResponse> {
  return apiRequest<LLMModelListResponse>('/api/v1/settings/llm/models', {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(candidate),
  })
}

export function saveLLMConfig(candidate: LLMSelectedCandidate): Promise<LLMConfigResponse> {
  return apiRequest<LLMConfigResponse>('/api/v1/settings/llm', {
    method: 'PUT',
    headers: jsonHeaders(),
    body: JSON.stringify({ provider_type: 'openai_compatible', ...candidate }),
  })
}

export function testLLMConnection(candidate: LLMSelectedCandidate): Promise<LLMConnectionResponse> {
  return apiRequest<LLMConnectionResponse>('/api/v1/settings/llm/test', {
    method: 'POST',
    headers: jsonHeaders(),
    body: JSON.stringify(candidate),
  })
}

export function analyzeWithAI(
  analysisId: string,
): Promise<AIAnalyzeResponse> {
  return apiRequest<AIAnalyzeResponse>(
    `/api/v1/analyses/${encodeURIComponent(analysisId)}/ai`,
    { method: 'POST' },
  )
}

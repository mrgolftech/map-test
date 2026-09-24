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

function settingsHeaders(adminToken: string): HeadersInit {
  return { 'Content-Type': 'application/json', 'X-LLM-Settings-Token': adminToken }
}

export function fetchLLMModels(candidate: LLMCandidate, adminToken: string): Promise<LLMModelListResponse> {
  return apiRequest<LLMModelListResponse>('/api/v1/settings/llm/models', {
    method: 'POST', headers: settingsHeaders(adminToken), body: JSON.stringify(candidate),
  })
}

export function saveLLMConfig(candidate: LLMSelectedCandidate, adminToken: string): Promise<LLMConfigResponse> {
  return apiRequest<LLMConfigResponse>('/api/v1/settings/llm', {
    method: 'PUT', headers: settingsHeaders(adminToken),
    body: JSON.stringify({ provider_type: 'openai_compatible', ...candidate }),
  })
}

export function testLLMConnection(candidate: LLMSelectedCandidate, adminToken: string): Promise<LLMConnectionResponse> {
  return apiRequest<LLMConnectionResponse>('/api/v1/settings/llm/test', {
    method: 'POST',
    headers: settingsHeaders(adminToken), body: JSON.stringify(candidate),
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

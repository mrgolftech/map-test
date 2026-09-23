import { apiRequest } from '../../api/client'
import type {
  AIAnalyzeResponse,
  LLMConfigResponse,
  LLMConnectionResponse,
} from '../../types/ai'

export function getLLMConfig(): Promise<LLMConfigResponse> {
  return apiRequest<LLMConfigResponse>('/api/v1/settings/llm')
}

export function testLLMConnection(): Promise<LLMConnectionResponse> {
  return apiRequest<LLMConnectionResponse>('/api/v1/settings/llm/test', {
    method: 'POST',
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

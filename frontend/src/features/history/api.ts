import { apiRequest } from '../../api/client'
import type {
  AnalysisDetailResponse,
  AnalysisHistoryFilters,
  AnalysisListResponse,
} from '../../types/history'
import type {
  SourceDescriptor,
  ValidationIssue,
  WaferDataset,
} from '../../types/wafer'

export type CreateAnalysisInput = {
  dataset: WaferDataset
  sources: SourceDescriptor[]
  validation_issues: ValidationIssue[]
}

export function createAnalysis(
  input: CreateAnalysisInput,
): Promise<AnalysisDetailResponse> {
  return apiRequest<AnalysisDetailResponse>('/api/v1/analyses', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(input),
  })
}

export function getAnalysis(
  analysisId: string,
): Promise<AnalysisDetailResponse> {
  return apiRequest<AnalysisDetailResponse>(
    `/api/v1/analyses/${encodeURIComponent(analysisId)}`,
  )
}

export function listAnalyses(
  filters: AnalysisHistoryFilters,
): Promise<AnalysisListResponse> {
  const params = new URLSearchParams()
  for (const [key, value] of Object.entries(filters)) {
    if (value === undefined || value === '') continue
    params.set(key, String(value))
  }
  const query = params.toString()
  return apiRequest<AnalysisListResponse>(
    `/api/v1/analyses${query ? `?${query}` : ''}`,
  )
}

export function deleteAnalysis(analysisId: string) {
  return apiRequest<{
    data: { id: string; deleted: boolean }
    meta: Record<string, unknown>
  }>(`/api/v1/analyses/${encodeURIComponent(analysisId)}`, {
    method: 'DELETE',
  })
}

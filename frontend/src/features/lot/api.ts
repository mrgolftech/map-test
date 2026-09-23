import { apiRequest } from '../../api/client'
import type {
  ComparisonResponse,
  LotListResponse,
} from '../../types/comparison'

export function listLots(): Promise<LotListResponse> {
  return apiRequest<LotListResponse>('/api/v1/lots')
}

export function getLotSummary(
  lotId: string,
  productId?: string,
): Promise<ComparisonResponse> {
  const params = new URLSearchParams()
  if (productId) params.set('product_id', productId)
  const suffix = params.toString() ? `?${params.toString()}` : ''
  return apiRequest<ComparisonResponse>(
    `/api/v1/lots/${encodeURIComponent(lotId)}/summary${suffix}`,
  )
}

export function compareAnalyses(
  analysisIds: string[],
): Promise<ComparisonResponse> {
  return apiRequest<ComparisonResponse>('/api/v1/analyses/compare', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ analysis_ids: analysisIds }),
  })
}

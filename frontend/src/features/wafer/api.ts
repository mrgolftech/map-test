import { apiRequest } from '../../api/client'
import type { AnalysisSummary } from '../../types/analysis'
import type { WaferDataset } from '../../types/wafer'

export function analyzeWafer(dataset: WaferDataset): Promise<AnalysisSummary> {
  return apiRequest<AnalysisSummary>('/api/v1/analysis', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ dataset }),
  })
}

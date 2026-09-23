import { apiRequest } from '../../api/client'

export type DashboardSummaryResponse = {
  data: {
    analysis_count: number
    lot_count: number
    average_yield: number | null
    minimum_yield: number | null
    maximum_yield: number | null
    latest_created_at: string | null
  }
  meta: Record<string, unknown>
}

export function getDashboardSummary(): Promise<DashboardSummaryResponse> {
  return apiRequest<DashboardSummaryResponse>('/api/v1/dashboard/summary')
}

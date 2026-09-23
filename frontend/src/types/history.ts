import type { AIReport } from './ai'
import type { AnalysisSummary } from './analysis'
import type {
  SourceDescriptor,
  ValidationIssue,
  WaferDataset,
} from './wafer'

export type AnalysisListItem = {
  id: string
  created_at: string
  product_id: string | null
  lot_id: string | null
  wafer_id: string | null
  flow_id: string | null
  yield: number | null
  tested_die: number
  pass_die: number
  fail_die: number
  main_fail_bin: number | null
  main_pattern: string | null
  validation_status: string
}

export type AnalysisDetail = AnalysisListItem & {
  dataset: WaferDataset
  analysis: AnalysisSummary
  sources: SourceDescriptor[]
  validation_issues: ValidationIssue[]
  ai_report: AIReport | null
  ai_model: string | null
  ai_generated_at: string | null
}

export type AnalysisDetailResponse = {
  data: AnalysisDetail
  meta: Record<string, unknown>
}

export type AnalysisListResponse = {
  data: AnalysisListItem[]
  meta: {
    page: number
    page_size: number
    total: number
  }
}

export type AnalysisHistoryFilters = {
  product_id?: string
  lot_id?: string
  wafer_id?: string
  created_from?: string
  created_to?: string
  yield_min?: number
  yield_max?: number
  main_fail_bin?: number
  pattern?: string
  page?: number
  page_size?: number
}

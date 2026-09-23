export type CompatibilitySeverity = 'INFO' | 'WARNING' | 'ERROR'

export type CompatibilityIssue = {
  severity: CompatibilitySeverity
  code: string
  message: string
  details: Record<string, unknown> | null
}

export type YieldAggregate = {
  wafer_count: number
  valid_yield_count: number
  average: number | null
  median: number | null
  std_dev: number | null
  minimum: number | null
  maximum: number | null
  q1: number | null
  q3: number | null
  iqr: number | null
  outlier_lower_bound: number | null
  outlier_upper_bound: number | null
}

export type YieldTrendPoint = {
  analysis_id: string
  wafer_id: string | null
  test_time: string
  yield: number | null
  is_outlier: boolean
  outlier_reason: string | null
}

export type YieldExtremum = {
  analysis_id: string
  wafer_id: string | null
  yield: number
}

export type BinTrendPoint = {
  analysis_id: string
  wafer_id: string | null
  test_time: string
  wafer_rate: number
  fail_share: number | null
  edge_enrichment: number | null
  center_enrichment: number | null
}

export type BinAggregate = {
  soft_bin: number
  char: string | null
  description: string | null
  wafer_count: number
  mean_wafer_rate: number
  std_wafer_rate: number
  mean_fail_share: number | null
  mean_edge_enrichment: number | null
  mean_center_enrichment: number | null
  trend: BinTrendPoint[]
}

export type PatternDistributionItem = {
  pattern: string
  count: number
  percentage: number
}

export type PreviewBin = {
  soft_bin: number
  char: string | null
  description: string | null
}

export type WaferMapPreview = {
  rows: number
  columns: number
  notch: string | null
  map_rows: string[]
  bins: PreviewBin[]
}

export type WaferComparisonRow = {
  analysis_id: string
  product_id: string | null
  lot_id: string | null
  wafer_id: string | null
  flow_id: string | null
  test_time: string
  yield: number | null
  tested_die: number
  pass_die: number
  fail_die: number
  main_fail_bin: number | null
  main_fail_rate: number | null
  edge_enrichment: number | null
  center_enrichment: number | null
  cluster_ratio: number | null
  main_pattern: string | null
  tester: string | null
  test_program: string | null
  probe_card: string | null
  is_outlier: boolean
  preview: WaferMapPreview | null
}

export type ComparisonData = {
  product_id: string | null
  lot_id: string | null
  compatibility: {
    compatible: boolean
    issues: CompatibilityIssue[]
  }
  yield_stats: YieldAggregate
  yield_trend: YieldTrendPoint[]
  highest_yield_wafers: YieldExtremum[]
  lowest_yield_wafers: YieldExtremum[]
  bin_aggregates: BinAggregate[]
  pattern_distribution: PatternDistributionItem[]
  wafers: WaferComparisonRow[]
  limitations: string[]
}

export type ComparisonResponse = {
  data: ComparisonData
  meta: Record<string, unknown>
}

export type LotListItem = {
  product_id: string | null
  lot_id: string
  wafer_count: number
  average_yield: number | null
  minimum_yield: number | null
  maximum_yield: number | null
  last_created_at: string
}

export type LotListResponse = {
  data: LotListItem[]
  meta: Record<string, unknown>
}

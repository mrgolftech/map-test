import type { ValidationIssue, WaferDataset, WaferMetadata, WaferSummary } from './wafer'

export type AnalysisConfig = {
  center_radius: number
  edge_radius: number
  neighbor_mode: 4 | 8
  enrichment_threshold: number
  cluster_ratio_threshold: number
  min_cluster_size: number
  directional_enrichment_threshold: number
  line_concentration_threshold: number
}

export type BinStat = {
  soft_bin: number
  char: string | null
  description: string | null
  count: number
  wafer_rate: number
  fail_share: number | null
}

export type RegionMetric = {
  tested_die: number
  pass_die: number
  fail_die: number
  fail_rate: number | null
}

export type BinRegionMetric = {
  tested_die: number
  bin_die: number
  region_rate: number | null
  whole_rate: number | null
  enrichment: number | null
}

export type ClusterStats = {
  component_count: number
  largest_component: number
  average_component_size: number | null
  cluster_ratio: number | null
  component_sizes: number[]
}

export type SpatialBinStat = {
  soft_bin: number
  count: number
  center: BinRegionMetric
  mid: BinRegionMetric
  edge: BinRegionMetric
  top: BinRegionMetric
  bottom: BinRegionMetric
  left: BinRegionMetric
  right: BinRegionMetric
  q1: BinRegionMetric
  q2: BinRegionMetric
  q3: BinRegionMetric
  q4: BinRegionMetric
  cluster: ClusterStats
  max_row_fraction: number | null
  max_column_fraction: number | null
}

export type PatternResult = {
  pattern: string
  soft_bin: number | null
  score: number
  evidence: string[]
  thresholds: Record<string, number | string>
  limitations: string[]
}

export type AnalysisSummary = {
  schema_version: '1.0'
  metadata: WaferMetadata
  summary: WaferSummary
  validation: ValidationIssue[]
  config: AnalysisConfig
  bin_stats: BinStat[]
  region_stats: Record<string, RegionMetric>
  spatial_by_bin: SpatialBinStat[]
  patterns: PatternResult[]
  top_findings: string[]
  limitations: string[]
}

export type WaferWorkspace = {
  dataset: WaferDataset
  analysis: AnalysisSummary
}

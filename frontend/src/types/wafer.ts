export type ParseStatus = 'VALID' | 'WARNING' | 'INVALID'
export type ValidationSeverity = 'INFO' | 'WARNING' | 'ERROR'
export type ValidationStage = 'DETECT' | 'PARSE' | 'ASSEMBLE' | 'CANONICAL'

export type ValidationIssue = {
  severity: ValidationSeverity
  stage: ValidationStage
  code: string
  message: string
  source_file: string | null
  line: number | null
  row: number | null
  column: number | null
  details: Record<string, unknown> | null
}

export type SourceDescriptor = {
  filename: string
  size: number
  sha256: string
  detected_format: 'PAT' | 'CP1' | 'UNKNOWN'
  parser_id: string
  role: 'metadata' | 'map' | 'combined' | 'unknown'
  detection_evidence: string[]
}

export type WaferMetadata = {
  product_id: string | null
  lot_id: string | null
  wafer_id: string | null
  flow_id: string | null
  subcon: string | null
  tester: string | null
  test_program: string | null
  probe_card: string | null
  start_time: string | null
  stop_time: string | null
  notch: string | null
  rows: number
  columns: number
}

export type WaferSummary = {
  tested_die: number
  pass_die: number
  fail_die: number
  yield: number | null
}

export type BinRecord = {
  bin: number
  char: string | null
  description: string | null
  count: number
  percentage: number
}

export type DieRecord = {
  row: number
  column: number
  source_char: string
  soft_bin: number | null
  hard_bin: number | null
  result: 'PASS' | 'FAIL' | 'UNKNOWN'
  description: string | null
  test_values: Record<string, number | string | null> | null
}

export type WaferDataset = {
  metadata: WaferMetadata
  dies: DieRecord[]
  bins: BinRecord[]
  summary: WaferSummary
}

export type ParseResult = {
  dataset: WaferDataset | null
  sources: SourceDescriptor[]
  validation_issues: ValidationIssue[]
  status: ParseStatus
}

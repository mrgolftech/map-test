export type AIKeyFinding = {
  kind: 'FACT' | 'JUDGMENT'
  title: string
  detail: string
  evidence: string[]
}

export type AISpatialPattern = {
  kind: 'JUDGMENT'
  title: string
  detail: string
  evidence: string[]
}

export type AIPossibleCause = {
  kind: 'HYPOTHESIS'
  title: string
  detail: string
  rationale: string
}

export type AIRecommendedCheck = {
  kind: 'RECOMMENDATION'
  title: string
  action: string
  expected_evidence: string | null
}

export type AIReport = {
  executive_summary: string
  key_findings: AIKeyFinding[]
  spatial_patterns: AISpatialPattern[]
  possible_causes: AIPossibleCause[]
  recommended_checks: AIRecommendedCheck[]
  confidence: number
  limitations: string[]
}

export type AIAnalyzeResponse = {
  data: {
    analysis_id: string
    model: string
    report: AIReport
  }
  meta: Record<string, unknown>
}

export type LLMConfigResponse = {
  data: {
    configured: boolean
    base_url: string | null
    model: string | null
    api_key_configured: boolean
  }
  meta: Record<string, unknown>
}

export type LLMConnectionResponse = {
  data: {
    ok: boolean
    model: string
    message: string
  }
  meta: Record<string, unknown>
}

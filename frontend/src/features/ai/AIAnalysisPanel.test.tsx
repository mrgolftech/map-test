import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import type { AIReport } from '../../types/ai'
import { AIAnalysisPanel } from './AIAnalysisPanel'

vi.mock('./api', () => ({
  getLLMConfig: vi.fn().mockResolvedValue({
    data: {
      configured: false,
      base_url: null,
      model: null,
      api_key_configured: false,
    },
    meta: {},
  }),
  analyzeWithAI: vi.fn(),
}))

const persistedReport: AIReport = {
  executive_summary: '历史 AI 结论',
  key_findings: [],
  spatial_patterns: [],
  possible_causes: [],
  recommended_checks: [],
  confidence: 0.72,
  limitations: ['仅用于回归测试'],
}

describe('AIAnalysisPanel', () => {
  it('degrades cleanly when LLM is not configured', async () => {
    render(
      <AppProviders>
        <AIAnalysisPanel analysisId="analysis-1" />
      </AppProviders>,
    )

    expect(await screen.findByText('AI 尚未配置')).toBeInTheDocument()
    expect(
      screen.getByText(/核心 Wafer 分析不受影响/),
    ).toBeInTheDocument()
  })

  it('shows persisted report even when LLM is unavailable', async () => {
    render(
      <AppProviders>
        <AIAnalysisPanel
          analysisId="analysis-2"
          initialReport={persistedReport}
          initialModel="saved-model"
          initialGeneratedAt="2026-09-24T00:00:00Z"
        />
      </AppProviders>,
    )

    expect(await screen.findByText('历史 AI 结论')).toBeInTheDocument()
    expect(screen.getByText('当前 LLM 未配置')).toBeInTheDocument()
    expect(screen.getByText('模型：saved-model')).toBeInTheDocument()
  })
})

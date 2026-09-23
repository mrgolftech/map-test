import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
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
})

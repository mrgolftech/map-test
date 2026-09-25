import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { AIChatPanel } from './AIChatPanel'
import type { ChatThreadResponse } from './chatApi'

const { askAnalysisChat, askComparisonChat, getAnalysisChat, getComparisonChat } = vi.hoisted(() => ({
  askAnalysisChat: vi.fn(),
  askComparisonChat: vi.fn(),
  getAnalysisChat: vi.fn(),
  getComparisonChat: vi.fn(),
}))

vi.mock('./api', () => ({
  getLLMConfig: vi.fn().mockResolvedValue({
    data: {
      configured: true,
      base_url: 'https://example.test/v1',
      model: 'demo-model',
      api_key_configured: true,
    },
    meta: {},
  }),
}))

vi.mock('./chatApi', () => ({
  askAnalysisChat,
  askComparisonChat,
  getAnalysisChat,
  getComparisonChat,
}))

function thread(messages: ChatThreadResponse['data']['messages'] = []): ChatThreadResponse {
  return {
    data: {
      thread_id: messages.length ? 'thread-1' : null,
      scope: 'analysis',
      context_ids: ['analysis-1'],
      messages,
    },
    meta: {},
  }
}

describe('AIChatPanel', () => {
  afterEach(() => cleanup())

  beforeEach(() => {
    vi.clearAllMocks()
    getAnalysisChat.mockResolvedValue(thread())
    getComparisonChat.mockResolvedValue({
      ...thread(),
      data: { ...thread().data, scope: 'comparison', context_ids: ['a', 'b'] },
    })
  })

  it('requires a saved report before enabling single-wafer follow-up', () => {
    render(
      <AppProviders>
        <AIChatPanel analysisId="analysis-1" reportReady={false} />
      </AppProviders>,
    )

    expect(screen.getByText('请先生成 AI 分析报告')).toBeInTheDocument()
    expect(getAnalysisChat).not.toHaveBeenCalled()
  })

  it('shows persisted answers and their metric citations', async () => {
    const messages: ChatThreadResponse['data']['messages'] = [
      {
        id: 'q1',
        role: 'user',
        content: '良率是多少？',
        citations: [],
        limitations: [],
        insufficient_evidence: false,
        model: null,
        created_at: '2026-09-24T10:00:00Z',
      },
      {
        id: 'a1',
        role: 'assistant',
        content: '良率为 37.11%。',
        citations: [{
          id: 'summary.yield',
          label: 'Yield',
          value: '37.11%',
          analysis_id: null,
        }],
        limitations: [],
        insufficient_evidence: false,
        model: 'demo-model',
        created_at: '2026-09-24T10:00:00Z',
      },
    ]
    getAnalysisChat.mockResolvedValue(thread(messages))
    render(
      <AppProviders>
        <AIChatPanel analysisId="analysis-1" reportReady />
      </AppProviders>,
    )

    expect(await screen.findByText('良率是多少？')).toBeInTheDocument()
    expect(screen.getByText('良率为 37.11%。')).toBeInTheDocument()
    expect(screen.getByText('Yield：37.11%')).toBeInTheDocument()
  })

  it('sends comparison questions against the selected wafers', async () => {
    askComparisonChat.mockResolvedValue(thread())
    render(
      <AppProviders>
        <AIChatPanel analysisIds={['wafer-a', 'wafer-b']} />
      </AppProviders>,
    )

    fireEvent.change(await screen.findByPlaceholderText(
      '例如：良率下降主要发生在哪几片？Bin18 是否持续增加？',
    ), {
      target: { value: '哪片晶圆良率最低？' },
    })
    fireEvent.click(screen.getByRole('button', { name: '发送' }))

    await waitFor(() => {
      expect(askComparisonChat).toHaveBeenCalledWith(
        ['wafer-a', 'wafer-b'],
        '哪片晶圆良率最低？',
      )
    })
  })
})

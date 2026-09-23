import { afterEach, describe, expect, it, vi } from 'vitest'
import { analyzeWithAI, getLLMConfig, testLLMConnection } from './api'

describe('AI API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('reads server-side LLM config without client secrets', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        data: {
          configured: true,
          base_url: 'https://example.test/v1',
          model: 'demo',
          api_key_configured: true,
        },
        meta: {},
      }), { status: 200 }),
    )

    await getLLMConfig()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/settings/llm', undefined)
  })

  it('tests LLM connection via POST', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({
        data: { ok: true, model: 'demo', message: 'ok' },
        meta: {},
      }), { status: 200 }),
    )

    await testLLMConnection()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/settings/llm/test',
      { method: 'POST' },
    )
  })

  it('analyzes a persisted record by id', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await analyzeWithAI('id / 1')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/analyses/id%20%2F%201/ai',
      { method: 'POST' },
    )
  })
})

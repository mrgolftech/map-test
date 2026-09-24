import { afterEach, describe, expect, it, vi } from 'vitest'
import { analyzeWithAI, fetchLLMModels, getLLMConfig, saveLLMConfig, testLLMConnection } from './api'

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

    await testLLMConnection({ base_url: 'https://example.test/v1', model: 'demo', api_key: 'temporary-key' }, 'admin-token')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/settings/llm/test',
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-LLM-Settings-Token': 'admin-token' },
        body: JSON.stringify({ base_url: 'https://example.test/v1', model: 'demo', api_key: 'temporary-key' }),
      },
    )
  })

  it('fetches models and saves settings with credentials only in request bodies and headers', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async () =>
      new Response(JSON.stringify({ data: ['demo'], meta: {} }), { status: 200 }),
    )
    await fetchLLMModels({ base_url: 'https://example.test/v1', api_key: 'secret' }, 'admin-token')
    await saveLLMConfig({ base_url: 'https://example.test/v1', model: 'demo', api_key: 'secret' }, 'admin-token')
    expect(fetchMock.mock.calls.map(([url]) => url)).toEqual(['/api/v1/settings/llm/models', '/api/v1/settings/llm'])
    expect(fetchMock.mock.calls[0][1]?.method).toBe('POST')
    expect(fetchMock.mock.calls[1][1]?.method).toBe('PUT')
    expect(fetchMock.mock.calls[1][1]?.body).toContain('openai_compatible')
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

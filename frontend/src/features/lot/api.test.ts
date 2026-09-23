import { afterEach, describe, expect, it, vi } from 'vitest'
import { compareAnalyses, getLotSummary, listLots } from './api'

describe('lot API', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('loads lot list', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: [], meta: {} }), { status: 200 }),
    )

    await listLots()

    expect(fetchMock).toHaveBeenCalledWith('/api/v1/lots', undefined)
  })

  it('encodes lot and product in summary request', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await getLotSummary('LOT / A', 'PRODUCT A')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/lots/LOT%20%2F%20A/summary?product_id=PRODUCT+A',
      undefined,
    )
  })

  it('posts selected analysis ids', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await compareAnalyses(['a', 'b'])

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/analyses/compare',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ analysis_ids: ['a', 'b'] }),
      }),
    )
  })
})

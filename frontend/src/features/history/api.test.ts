import { afterEach, describe, expect, it, vi } from 'vitest'
import { listAnalyses } from './api'

describe('history api', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('serializes history filters without undefined values', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        data: [],
        meta: { page: 2, page_size: 50, total: 0 },
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await listAnalyses({
      product_id: 'DEMO',
      lot_id: 'LOT1',
      yield_min: 0.8,
      main_fail_bin: 18,
      page: 2,
      page_size: 50,
    })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url] = fetchMock.mock.calls[0] as [string]
    const params = new URL(url, 'http://localhost').searchParams

    expect(params.get('product_id')).toBe('DEMO')
    expect(params.get('lot_id')).toBe('LOT1')
    expect(params.get('yield_min')).toBe('0.8')
    expect(params.get('main_fail_bin')).toBe('18')
    expect(params.get('page')).toBe('2')
    expect(params.get('page_size')).toBe('50')
    expect(params.has('wafer_id')).toBe(false)
  })
})

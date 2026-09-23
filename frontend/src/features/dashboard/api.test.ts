import { afterEach, describe, expect, it, vi } from 'vitest'
import { getDashboardSummary } from './api'

describe('dashboard API', () => {
  afterEach(() => vi.restoreAllMocks())

  it('loads persisted analysis summary', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await getDashboardSummary()

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/dashboard/summary',
      undefined,
    )
  })
})

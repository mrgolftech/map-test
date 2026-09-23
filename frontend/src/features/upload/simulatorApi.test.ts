import { afterEach, describe, expect, it, vi } from 'vitest'
import { generateDemoLot, generateDemoWafer } from './simulatorApi'

describe('simulator API client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('requests a synthetic wafer', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await generateDemoWafer({ pattern: 'EDGE', fail_count: 48 })

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/simulator/wafer',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ pattern: 'EDGE', fail_count: 48 }),
      }),
    )
  })

  it('requests a demo lot scenario', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify({ data: {}, meta: {} }), { status: 200 }),
    )

    await generateDemoLot('EDGE_DRIFT')

    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/simulator/lot',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ scenario: 'EDGE_DRIFT' }),
      }),
    )
  })
})

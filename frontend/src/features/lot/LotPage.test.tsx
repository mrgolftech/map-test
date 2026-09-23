import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { LotPage } from './LotPage'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearch: () => ({}),
  }
})

vi.mock('./api', () => ({
  listLots: vi.fn().mockResolvedValue({
    data: [{
      product_id: 'DEMO',
      lot_id: 'LOT-001',
      wafer_count: 5,
      average_yield: 0.95,
      minimum_yield: 0.90,
      maximum_yield: 0.98,
      last_created_at: '2026-09-24T00:00:00Z',
    }],
    meta: {},
  }),
  getLotSummary: vi.fn(),
  compareAnalyses: vi.fn(),
}))

describe('LotPage', () => {
  it('renders persisted lot list before selection', async () => {
    render(
      <AppProviders>
        <LotPage />
      </AppProviders>,
    )

    expect(
      screen.getByRole('heading', { name: 'Lot / 多 Wafer' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('LOT-001')).toBeInTheDocument()
    expect(screen.getByText('5')).toBeInTheDocument()
  })
})

import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { DashboardPage } from './DashboardPage'

vi.mock('./api', () => ({
  getDashboardSummary: vi.fn().mockResolvedValue({
    data: {
      analysis_count: 2,
      lot_count: 1,
      average_yield: 0.95,
      minimum_yield: 0.90,
      maximum_yield: 0.98,
      latest_created_at: '2026-09-24T00:00:00Z',
    },
    meta: {},
  }),
}))

describe('DashboardPage', () => {
  it('renders persisted wafer and lot summary', async () => {
    render(
      <AppProviders>
        <DashboardPage />
      </AppProviders>,
    )

    expect(
      screen.getByRole('heading', { name: '总览' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('95.00%')).toBeInTheDocument()
    expect(screen.getByText('90.00% – 98.00%')).toBeInTheDocument()
    expect(screen.getByText('分析历史已就绪')).toBeInTheDocument()
  })
})

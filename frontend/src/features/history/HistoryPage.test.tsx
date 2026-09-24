import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { HistoryPage } from './HistoryPage'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearch: () => ({
      page: 1,
      page_size: 20,
    }),
  }
})

vi.mock('./api', () => ({
  listAnalyses: vi.fn().mockResolvedValue({
    data: [],
    meta: {
      page: 1,
      page_size: 20,
      total: 0,
    },
  }),
  deleteAnalysis: vi.fn(),
}))

describe('HistoryPage', () => {
  it('renders filters and empty history state', async () => {
    render(
      <AppProviders>
        <HistoryPage />
      </AppProviders>,
    )

    expect(screen.getByRole('heading', { name: '分析历史' })).toBeInTheDocument()
    expect(await screen.findByText('暂无符合条件的分析记录')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /筛选/ })).toBeInTheDocument()
  }, 15_000)
})

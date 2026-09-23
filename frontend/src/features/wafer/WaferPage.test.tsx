import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { WaferPage } from './WaferPage'

vi.mock('@tanstack/react-router', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@tanstack/react-router')>()
  return {
    ...actual,
    useNavigate: () => vi.fn(),
  }
})

describe('WaferPage', () => {
  beforeEach(() => {
    window.sessionStorage.clear()
  })

  it('shows an empty state when no current wafer workspace exists', () => {
    render(
      <AppProviders>
        <WaferPage />
      </AppProviders>,
    )

    expect(screen.getByRole('heading', { name: '单片分析' })).toBeInTheDocument()
    expect(screen.getByText('请先上传并解析 PAT / CP 文件')).toBeInTheDocument()
  })
})

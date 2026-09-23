import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { AppProviders } from '../../app/providers'
import { UploadPage } from './UploadPage'

describe('UploadPage', () => {
  it('renders the Phase 1 parse entry with parse disabled before file selection', () => {
    render(
      <AppProviders>
        <UploadPage />
      </AppProviders>,
    )

    expect(
      screen.getByText('拖拽或选择 PAT / CP 测试文件'),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /解析文件/ }),
    ).toBeDisabled()
  })
})

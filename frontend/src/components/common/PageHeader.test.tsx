import { render, screen } from '@testing-library/react'
import { PageHeader } from './PageHeader'

describe('PageHeader', () => {
  it('renders title and description', () => {
    render(<PageHeader title="总览" description="测试描述" />)
    expect(screen.getByRole('heading', { name: '总览' })).toBeInTheDocument()
    expect(screen.getByText('测试描述')).toBeInTheDocument()
  })
})

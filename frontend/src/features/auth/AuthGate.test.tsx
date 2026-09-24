import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthGate } from './AuthGate'
import { getAdminSession, loginAdmin } from './api'

vi.mock('./api', () => ({
  getAdminSession: vi.fn(),
  loginAdmin: vi.fn(),
}))

function renderGate() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={client}>
      <AuthGate>
        <div>protected-workspace</div>
      </AuthGate>
    </QueryClientProvider>,
  )
}

describe('AuthGate', () => {
  beforeEach(() => vi.clearAllMocks())

  it('shows login and enters the workspace after authentication', async () => {
    vi.mocked(getAdminSession).mockResolvedValue({
      data: { authenticated: false, configured: true, username: null },
      meta: {},
    })
    vi.mocked(loginAdmin).mockResolvedValue({
      data: { authenticated: true, configured: true, username: 'admin' },
      meta: {},
    })

    renderGate()
    expect(await screen.findByRole('heading', { name: '管理员登录' })).toBeInTheDocument()

    fireEvent.change(screen.getByLabelText('密码'), {
      target: { value: 'secret-password' },
    })
    fireEvent.click(screen.getByRole('button', { name: /登\s*录/ }))

    await waitFor(() => expect(loginAdmin).toHaveBeenCalledWith({
      username: 'admin',
      password: 'secret-password',
    }))
    expect(await screen.findByText('protected-workspace')).toBeInTheDocument()
  })

  it('explains server setup when admin login is not configured', async () => {
    vi.mocked(getAdminSession).mockResolvedValue({
      data: { authenticated: false, configured: false, username: null },
      meta: {},
    })
    renderGate()
    expect(await screen.findByText('管理员登录尚未配置')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /登\s*录/ })).toBeDisabled()
  })
})

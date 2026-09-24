import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AppProviders } from '../../app/providers'
import { SettingsPage } from './SettingsPage'
import { fetchLLMModels, getLLMConfig, saveLLMConfig, testLLMConnection } from '../ai/api'

vi.mock('../ai/api', () => ({
  getLLMConfig: vi.fn().mockResolvedValue({
    data: { configured: false, base_url: 'https://example.test/v1', model: 'demo-model', api_key_configured: false }, meta: {},
  }),
  fetchLLMModels: vi.fn().mockResolvedValue({ data: ['demo-model'], meta: {} }),
  testLLMConnection: vi.fn().mockResolvedValue({
    data: { ok: true, model: 'demo-model', message: 'ok' }, meta: {},
  }),
  saveLLMConfig: vi.fn().mockResolvedValue({
    data: { configured: true, base_url: 'https://example.test/v1', model: 'demo-model', api_key_configured: true },
    meta: {},
  }),
}))

describe('SettingsPage', () => {
  beforeEach(() => vi.clearAllMocks())

  function renderSettings() {
    render(<AppProviders><QueryClientProvider client={new QueryClient()}><SettingsPage /></QueryClientProvider></AppProviders>)
  }

  it('uses the entered key for model discovery and selected-model connectivity', async () => {
    renderSettings()
    await screen.findByDisplayValue('https://example.test/v1')

    fireEvent.change(screen.getByLabelText('管理员令牌'), { target: { value: 'admin-token' } })
    fireEvent.change(screen.getByLabelText('API Base URL'), { target: { value: 'https://example.test/v1' } })
    fireEvent.change(screen.getByLabelText('API Key'), { target: { value: 'temporary-key' } })
    fireEvent.click(screen.getByRole('button', { name: '拉取 /v1/models' }))
    await waitFor(() => expect(fetchLLMModels).toHaveBeenCalledWith(
      { base_url: 'https://example.test/v1', api_key: 'temporary-key' }, 'admin-token',
    ))

    fireEvent.click(screen.getByRole('button', { name: /测试选定模型/ }))
    await waitFor(() => expect(testLLMConnection).toHaveBeenCalledWith(
      { base_url: 'https://example.test/v1', model: 'demo-model', api_key: 'temporary-key' },
      'admin-token',
    ))

    fireEvent.click(screen.getByRole('button', { name: '保存配置' }))
    await waitFor(() => expect(saveLLMConfig).toHaveBeenCalledWith(
      { base_url: 'https://example.test/v1', model: 'demo-model', api_key: 'temporary-key' },
      'admin-token',
    ))
    expect(screen.getByLabelText('API Key')).toHaveValue('')
  })

  it('preserves an URL typed before the initial config request resolves', async () => {
    let resolveConfig: (value: Awaited<ReturnType<typeof getLLMConfig>>) => void = () => undefined
    vi.mocked(getLLMConfig).mockImplementationOnce(() => new Promise((resolve) => { resolveConfig = resolve }))
    renderSettings()
    fireEvent.change(screen.getByLabelText('API Base URL'), {
      target: { value: 'https://new.example.test/v1' },
    })
    resolveConfig({
      data: { configured: true, base_url: 'https://old.example.test/v1', model: 'previous', api_key_configured: true },
      meta: {},
    })
    await screen.findByDisplayValue('previous')
    expect(screen.getByLabelText('API Base URL')).toHaveValue('https://new.example.test/v1')
  })
})

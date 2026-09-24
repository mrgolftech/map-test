import { apiRequest } from '../../api/client'

export type AdminSession = {
  authenticated: boolean
  configured: boolean
  username: string | null
}

type AdminSessionResponse = {
  data: AdminSession
  meta: Record<string, unknown>
}

export function getAdminSession(): Promise<AdminSessionResponse> {
  return apiRequest<AdminSessionResponse>('/api/v1/auth/session')
}

export function loginAdmin(credentials: {
  username: string
  password: string
}): Promise<AdminSessionResponse> {
  return apiRequest<AdminSessionResponse>('/api/v1/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })
}

export function logoutAdmin(): Promise<AdminSessionResponse> {
  return apiRequest<AdminSessionResponse>('/api/v1/auth/logout', {
    method: 'POST',
  })
}

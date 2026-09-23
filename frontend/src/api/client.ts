export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly details: unknown

  constructor(
    message: string,
    options: { status: number; code: string; details?: unknown },
  ) {
    super(message)
    this.name = 'ApiError'
    this.status = options.status
    this.code = options.code
    this.details = options.details
  }
}

type ErrorPayload = {
  error?: {
    code?: string
    message?: string
    details?: unknown
  }
}

export async function apiRequest<T>(
  input: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(input, init)

  if (!response.ok) {
    let payload: ErrorPayload = {}
    try {
      payload = (await response.json()) as ErrorPayload
    } catch {
      // Keep the transport fallback below.
    }
    throw new ApiError(
      payload.error?.message ?? `Request failed with status ${response.status}.`,
      {
        status: response.status,
        code: payload.error?.code ?? `HTTP_${response.status}`,
        details: payload.error?.details,
      },
    )
  }

  return (await response.json()) as T
}

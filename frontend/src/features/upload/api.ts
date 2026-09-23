import { apiRequest } from '../../api/client'
import type { ParseResult } from '../../types/wafer'

export function parseWaferFiles(files: File[]): Promise<ParseResult> {
  const body = new FormData()
  for (const file of files) {
    body.append('files', file, file.name)
  }
  return apiRequest<ParseResult>('/api/v1/files/parse', {
    method: 'POST',
    body,
  })
}

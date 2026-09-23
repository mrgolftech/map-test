import type { WaferWorkspace } from '../../types/analysis'

const KEY = 'map-test-current-wafer-v1'

export function saveWaferWorkspace(workspace: WaferWorkspace) {
  window.sessionStorage.setItem(KEY, JSON.stringify(workspace))
}

export function loadWaferWorkspace(): WaferWorkspace | null {
  const raw = window.sessionStorage.getItem(KEY)
  if (!raw) return null

  try {
    return JSON.parse(raw) as WaferWorkspace
  } catch {
    window.sessionStorage.removeItem(KEY)
    return null
  }
}

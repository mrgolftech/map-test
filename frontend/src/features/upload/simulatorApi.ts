import { apiRequest } from '../../api/client'
import type { WaferDataset } from '../../types/wafer'

export type SyntheticPattern =
  | 'RANDOM'
  | 'EDGE'
  | 'CENTER'
  | 'RING'
  | 'QUADRANT'
  | 'CLUSTER'
  | 'LINE'

export type DemoLotScenario =
  | 'EDGE_DRIFT'
  | 'MIXED_PATTERNS'
  | 'STABLE_RANDOM'

export type SyntheticWaferInput = {
  pattern: SyntheticPattern
  fail_count?: number
  seed?: number
  product_id?: string
  lot_id?: string
  wafer_id?: string
  rows?: number
  columns?: number
}

export type SyntheticWaferResponse = {
  data: WaferDataset
  meta: {
    synthetic: boolean
    pattern: string
    seed: number
  }
}

export type DemoLotResponse = {
  data: {
    scenario: DemoLotScenario
    description: string
    datasets: WaferDataset[]
  }
  meta: {
    synthetic: boolean
    seed: number
  }
}

export function generateDemoWafer(
  input: SyntheticWaferInput,
): Promise<SyntheticWaferResponse> {
  return apiRequest<SyntheticWaferResponse>('/api/v1/simulator/wafer', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
}

export function generateDemoLot(
  scenario: DemoLotScenario,
): Promise<DemoLotResponse> {
  return apiRequest<DemoLotResponse>('/api/v1/simulator/lot', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ scenario }),
  })
}

import type { WaferDataset } from '../../types/wafer'
import { WaferMap } from './WaferMap'

type MiniWaferMapProps = {
  dataset: WaferDataset
  softBin: number
}

export function MiniWaferMap({ dataset, softBin }: MiniWaferMapProps) {
  return (
    <WaferMap
      dataset={dataset}
      filterMode="fail"
      selectedBins={[softBin]}
      showCoordinates={false}
      compact
    />
  )
}

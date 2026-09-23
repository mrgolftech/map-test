import { useEffect, useMemo, useRef } from 'react'
import type { WaferMapPreview } from '../../types/comparison'
import { binColor } from '../wafer/binColors'

type LotMiniMapProps = {
  preview: WaferMapPreview
  label: string
}

export function LotMiniMap({ preview, label }: LotMiniMapProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const binByChar = useMemo(
    () => new Map(
      preview.bins
        .filter((item) => item.char)
        .map((item) => [item.char as string, item.soft_bin]),
    ),
    [preview.bins],
  )

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const context = canvas.getContext('2d')
    if (!context) return

    const scale = Math.max(2, Math.floor(180 / Math.max(preview.rows, preview.columns)))
    canvas.width = preview.columns * scale
    canvas.height = preview.rows * scale
    context.clearRect(0, 0, canvas.width, canvas.height)

    preview.map_rows.forEach((row, rowIndex) => {
      Array.from(row).forEach((char, columnIndex) => {
        if (char === '.') return
        const softBin = binByChar.get(char) ?? null
        context.fillStyle = binColor(softBin, false)
        context.fillRect(columnIndex * scale, rowIndex * scale, scale, scale)
      })
    })
  }, [binByChar, preview])

  return (
    <canvas
      ref={canvasRef}
      className="lot-mini-map"
      role="img"
      aria-label={label}
    />
  )
}

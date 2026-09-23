import { useEffect, useRef } from 'react'
import * as echarts from 'echarts'
import { useAppTheme } from '../../app/theme'

type EChartProps = {
  option: echarts.EChartsOption
  height?: number
  ariaLabel: string
}

export function EChart({ option, height = 300, ariaLabel }: EChartProps) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const chartRef = useRef<echarts.EChartsType | null>(null)
  const { mode } = useAppTheme()

  useEffect(() => {
    const container = containerRef.current
    if (!container) return

    const chart = echarts.init(container, undefined, { renderer: 'canvas' })
    chartRef.current = chart
    const observer = new ResizeObserver(() => chart.resize())
    observer.observe(container)

    return () => {
      observer.disconnect()
      chart.dispose()
      chartRef.current = null
    }
  }, [])

  useEffect(() => {
    const chart = chartRef.current
    if (!chart) return
    chart.setOption(
      {
        backgroundColor: 'transparent',
        textStyle: {
          color: mode === 'dark' ? '#dbe5ef' : '#344054',
        },
        ...option,
      },
      { notMerge: true, lazyUpdate: true },
    )
  }, [mode, option])

  return (
    <div
      ref={containerRef}
      role="img"
      aria-label={ariaLabel}
      style={{ width: '100%', height }}
    />
  )
}

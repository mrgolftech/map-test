import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useMemo,
  useRef,
} from 'react'
import * as echarts from 'echarts'
import { useAppTheme } from '../../app/theme'
import type { DieRecord, WaferDataset } from '../../types/wafer'
import { binColor } from './binColors'

export type WaferFilterMode = 'all' | 'pass' | 'fail'

export type WaferMapHandle = {
  exportPng: () => string | null
  resetView: () => void
}

type WaferMapProps = {
  dataset: WaferDataset
  filterMode: WaferFilterMode
  selectedBins: number[]
  showCoordinates: boolean
  compact?: boolean
  onDieClick?: (die: DieRecord) => void
}

type MapDatum = {
  name: string
  value: [number, number, number, number]
  dieIndex: number
  itemStyle: {
    color: string
    opacity: number
    borderColor: string
    borderWidth: number
  }
}

type RenderApi = {
  value: (dimension: number) => unknown
  coord: (data: number[]) => number[]
  size: (data: number[]) => number[]
  style: () => Record<string, unknown>
}

function notchClass(notch: string | null) {
  switch ((notch ?? '').toUpperCase()) {
    case 'UP':
      return 'wafer-notch wafer-notch-up'
    case 'LEFT':
      return 'wafer-notch wafer-notch-left'
    case 'RIGHT':
      return 'wafer-notch wafer-notch-right'
    default:
      return 'wafer-notch wafer-notch-down'
  }
}

export const WaferMap = forwardRef<WaferMapHandle, WaferMapProps>(
  function WaferMap(
    {
      dataset,
      filterMode,
      selectedBins,
      showCoordinates,
      compact = false,
      onDieClick,
    },
    ref,
  ) {
    const containerRef = useRef<HTMLDivElement | null>(null)
    const chartRef = useRef<echarts.EChartsType | null>(null)
    const { mode } = useAppTheme()

    const selected = useMemo(() => new Set(selectedBins), [selectedBins])

    useImperativeHandle(ref, () => ({
      exportPng: () =>
        chartRef.current?.getDataURL({
          type: 'png',
          pixelRatio: 2,
          backgroundColor: mode === 'dark' ? '#17212c' : '#ffffff',
        }) ?? null,
      resetView: () => {
        const chart = chartRef.current
        if (!chart) return
        chart.dispatchAction({ type: 'dataZoom', start: 0, end: 100 })
      },
    }), [mode])

    useEffect(() => {
      const container = containerRef.current
      if (!container) return

      const chart = echarts.init(container, undefined, { renderer: 'canvas' })
      chartRef.current = chart

      const resizeObserver = new ResizeObserver(() => chart.resize())
      resizeObserver.observe(container)

      return () => {
        resizeObserver.disconnect()
        chart.dispose()
        chartRef.current = null
      }
    }, [])

    useEffect(() => {
      const chart = chartRef.current
      if (!chart) return

      const axisColor = mode === 'dark' ? '#aab8c7' : '#667085'
      const gridColor = mode === 'dark' ? '#334155' : '#e5e7eb'
      const selectedActive = selected.size > 0

      const data: MapDatum[] = dataset.dies
        .map((die, dieIndex) => ({ die, dieIndex }))
        .filter(({ die }) => {
          if (filterMode === 'pass') return die.result === 'PASS'
          if (filterMode === 'fail') return die.result === 'FAIL'
          return true
        })
        .map(({ die, dieIndex }) => {
          const isPass = die.result === 'PASS'
          const highlighted = !selectedActive || (
            die.soft_bin !== null && selected.has(die.soft_bin)
          )
          const color = highlighted
            ? binColor(die.soft_bin, isPass)
            : mode === 'dark'
              ? '#475569'
              : '#bfbfbf'
          return {
            name: [
              `Row: ${die.row}`,
              `Column: ${die.column}`,
              `Char: ${die.source_char}`,
              `Bin: ${die.soft_bin ?? '—'}`,
              `Description: ${die.description ?? '—'}`,
              `Result: ${die.result}`,
            ].join('<br/>'),
            value: [
              die.column,
              die.row,
              die.soft_bin ?? -1,
              die.result === 'PASS' ? 1 : 0,
            ],
            dieIndex,
            itemStyle: {
              color,
              opacity: highlighted ? 1 : 0.28,
              borderColor: mode === 'dark' ? '#0f1720' : '#ffffff',
              borderWidth: 0.45,
            },
          }
        })

      const option = {
        animation: false,
        grid: {
          left: showCoordinates ? 52 : 18,
          right: 18,
          top: 18,
          bottom: showCoordinates ? 48 : 18,
          containLabel: false,
        },
        tooltip: {
          trigger: 'item',
          confine: true,
          formatter: '{b}',
        },
        xAxis: {
          type: 'value',
          min: -0.5,
          max: dataset.metadata.columns - 0.5,
          interval: 1,
          axisLabel: {
            show: showCoordinates,
            color: axisColor,
            formatter: (value: number) => Number.isInteger(value) ? String(value) : '',
          },
          axisLine: { show: showCoordinates, lineStyle: { color: gridColor } },
          axisTick: { show: showCoordinates },
          splitLine: { show: false },
        },
        yAxis: {
          type: 'value',
          inverse: true,
          min: -0.5,
          max: dataset.metadata.rows - 0.5,
          interval: 1,
          axisLabel: {
            show: showCoordinates,
            color: axisColor,
            formatter: (value: number) => Number.isInteger(value) ? String(value) : '',
          },
          axisLine: { show: showCoordinates, lineStyle: { color: gridColor } },
          axisTick: { show: showCoordinates },
          splitLine: { show: false },
        },
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: 0,
            filterMode: 'none',
            zoomOnMouseWheel: true,
            moveOnMouseMove: true,
            moveOnMouseWheel: false,
          },
          {
            type: 'inside',
            yAxisIndex: 0,
            filterMode: 'none',
            zoomOnMouseWheel: true,
            moveOnMouseMove: true,
            moveOnMouseWheel: false,
          },
        ],
        series: [
          {
            type: 'custom',
            coordinateSystem: 'cartesian2d',
            silent: false,
            progressive: 4000,
            progressiveThreshold: 8000,
            renderItem: (
              _params: unknown,
              api: RenderApi,
            ) => {
              const column = Number(api.value(0))
              const row = Number(api.value(1))
              const point = api.coord([column, row])
              const size = api.size([1, 1])
              const width = Math.max(size[0] - 0.6, 1)
              const height = Math.max(size[1] - 0.6, 1)
              return {
                type: 'rect',
                shape: {
                  x: point[0] - width / 2,
                  y: point[1] - height / 2,
                  width,
                  height,
                },
                style: api.style(),
              }
            },
            data,
          },
        ],
      }

      chart.setOption(option, true)

      const clickHandler = (params: unknown) => {
        if (!onDieClick || typeof params !== 'object' || params === null) return
        const dataValue = (params as { data?: MapDatum }).data
        if (!dataValue) return
        const die = dataset.dies[dataValue.dieIndex]
        if (die) onDieClick(die)
      }

      chart.on('click', clickHandler)
      return () => {
        chart.off('click', clickHandler)
      }
    }, [
      dataset,
      filterMode,
      mode,
      onDieClick,
      selected,
      showCoordinates,
    ])

    return (
      <div
        className={compact ? 'wafer-map-frame wafer-map-frame-compact' : 'wafer-map-frame'}
        style={{
          aspectRatio: `${dataset.metadata.columns} / ${dataset.metadata.rows}`,
        }}
      >
        <div
          ref={containerRef}
          className={compact ? 'wafer-map-canvas wafer-map-canvas-compact' : 'wafer-map-canvas'}
          role="img"
          aria-label={`Wafer map ${dataset.metadata.lot_id ?? ''} ${dataset.metadata.wafer_id ?? ''}`}
        />
        <div className={notchClass(dataset.metadata.notch)}>
          <span>Notch {dataset.metadata.notch ?? '—'}</span>
        </div>
      </div>
    )
  },
)

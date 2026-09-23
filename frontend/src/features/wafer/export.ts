import type { WaferDataset } from '../../types/wafer'

export function waferCsv(dataset: WaferDataset) {
  const header = [
    'row',
    'column',
    'source_char',
    'soft_bin',
    'hard_bin',
    'result',
    'description',
  ]
  const escape = (value: string | number | null) => {
    const text = value === null ? '' : String(value)
    return `"${text.replaceAll('"', '""')}"`
  }
  const rows = dataset.dies.map((die) =>
    [
      die.row,
      die.column,
      die.source_char,
      die.soft_bin,
      die.hard_bin,
      die.result,
      die.description,
    ].map(escape).join(','),
  )
  return [header.join(','), ...rows].join('\n')
}

export function downloadText(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type })
  const url = URL.createObjectURL(blob)
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

export function downloadDataUrl(filename: string, dataUrl: string) {
  const anchor = document.createElement('a')
  anchor.href = dataUrl
  anchor.download = filename
  anchor.click()
}

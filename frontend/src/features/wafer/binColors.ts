const FAIL_COLORS = [
  '#d4380d',
  '#d46b08',
  '#d4b106',
  '#7cb305',
  '#08979c',
  '#0958d9',
  '#1d39c4',
  '#531dab',
  '#c41d7f',
  '#ad4e00',
  '#5b8c00',
  '#006d75',
  '#003eb3',
  '#391085',
]

export function binColor(softBin: number | null, isPass: boolean) {
  if (isPass) return '#389e0d'
  if (softBin === null) return '#8c8c8c'
  const index = Math.abs(softBin * 17 + 7) % FAIL_COLORS.length
  return FAIL_COLORS[index]
}

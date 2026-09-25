const FAIL_COLORS = [
  '#d73027',
  '#fc8d59',
  '#fdae61',
  '#fee08b',
  '#a6d96a',
  '#66bd63',
  '#1a9850',
  '#006837',
  '#1b9e77',
  '#66c2a5',
  '#3288bd',
  '#5e4fa2',
  '#7b3294',
  '#c51b7d',
  '#e7298a',
  '#a6761d',
  '#8c510a',
  '#bf812d',
  '#543005',
  '#7570b3',
  '#e6ab02',
  '#d95f02',
  '#1f78b4',
  '#fb9a99',
  '#1d6996',
]

export function binColor(softBin: number | null, isPass: boolean) {
  if (isPass) return '#389e0d'
  if (softBin === null) return '#8c8c8c'
  // 17 is coprime with 25, so consecutive Bin IDs map to distinct colors
  // across the 25-ID range used by the production-profile demo scenarios.
  const index = Math.abs(softBin * 17 + 7) % FAIL_COLORS.length
  return FAIL_COLORS[index]
}

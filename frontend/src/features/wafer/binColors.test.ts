import { describe, expect, it } from 'vitest'
import { binColor } from './binColors'

const compactFailBins = [16, 18, 20, 22, 27, 28, 32, 36]
const scaleFailBins = [12, 16, 18, 19, 20, 21, 22, 23, 26, 27, 28, 30, 32, 33, 35, 36]

describe('wafer Bin colors', () => {
  it('uses distinct colors for all Compact fail bins', () => {
    const colors = compactFailBins.map((softBin) => binColor(softBin, false))

    expect(new Set(colors).size).toBe(compactFailBins.length)
  })

  it('uses distinct colors for all Scale fail bins', () => {
    const colors = scaleFailBins.map((softBin) => binColor(softBin, false))

    expect(new Set(colors).size).toBe(scaleFailBins.length)
  })

  it('keeps pass and missing Bin colors separate from fail bins', () => {
    const failColors = new Set(scaleFailBins.map((softBin) => binColor(softBin, false)))

    expect(binColor(1, true)).not.toBe(binColor(1, false))
    expect(binColor(null, false)).not.toBe(binColor(1, false))
    expect(failColors.has(binColor(1, true))).toBe(false)
  })
})

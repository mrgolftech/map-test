import { describe, expect, it } from 'vitest'
import type { AnalysisSummary } from '../../types/analysis'
import type { WaferDataset } from '../../types/wafer'
import { waferReportHtml } from './report'

const dataset: WaferDataset = {
  metadata: {
    product_id: '<DEMO>',
    lot_id: 'LOT&1',
    wafer_id: '01',
    flow_id: 'CP1',
    subcon: null,
    tester: 'SIM',
    test_program: 'TEST',
    probe_card: 'PC',
    start_time: null,
    stop_time: null,
    notch: 'DOWN',
    rows: 1,
    columns: 1,
  },
  dies: [],
  bins: [],
  summary: {
    tested_die: 1,
    pass_die: 0,
    fail_die: 1,
    yield: 0,
  },
}

const analysis: AnalysisSummary = {
  schema_version: '1.0',
  metadata: dataset.metadata,
  summary: dataset.summary,
  validation: [],
  config: {
    center_radius: 0.35,
    edge_radius: 0.75,
    neighbor_mode: 8,
    enrichment_threshold: 1.5,
    cluster_ratio_threshold: 0.5,
    min_cluster_size: 4,
    directional_enrichment_threshold: 1.5,
    line_concentration_threshold: 0.45,
  },
  bin_stats: [],
  region_stats: {},
  spatial_by_bin: [],
  patterns: [],
  top_findings: [{ kind: 'FACT', text: 'tested=1' }],
  limitations: ['demo only'],
}

describe('waferReportHtml', () => {
  it('creates standalone escaped HTML report', () => {
    const html = waferReportHtml(
      dataset,
      analysis,
      'data:image/png;base64,AAAA',
    )

    expect(html).toContain('<!doctype html>')
    expect(html).toContain('&lt;DEMO&gt;')
    expect(html).toContain('LOT&amp;1')
    expect(html).toContain('data:image/png;base64,AAAA')
    expect(html).toContain('[FACT]')
    expect(html).not.toContain('<DEMO>')
  })

  it('does not embed non-image data URLs', () => {
    const html = waferReportHtml(
      dataset,
      analysis,
      'data:text/html;base64,PHNjcmlwdD4=',
    )

    expect(html).not.toContain('data:text/html')
  })
})

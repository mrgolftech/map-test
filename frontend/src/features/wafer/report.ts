import type { AIReport } from '../../types/ai'
import type { AnalysisSummary } from '../../types/analysis'
import type { WaferDataset } from '../../types/wafer'

function escapeHtml(value: unknown) {
  return String(value ?? '—')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;')
}

function percent(value: number | null | undefined) {
  return value === null || value === undefined
    ? '—'
    : `${(value * 100).toFixed(2)}%`
}

function ratio(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : value.toFixed(3)
}

function rows(values: string[][]) {
  return values
    .map(
      (cells) =>
        `<tr>${cells.map((cell) => `<td>${cell}</td>`).join('')}</tr>`,
    )
    .join('')
}

function aiSection(
  report: AIReport | null | undefined,
  model: string | null | undefined,
  generatedAt: string | null | undefined,
) {
  if (!report) return ''

  const keyFindings = report.key_findings.map((item) => [
    escapeHtml(item.kind),
    escapeHtml(item.title),
    escapeHtml(item.detail),
    escapeHtml(item.evidence.join('；')),
  ])
  const spatialPatterns = report.spatial_patterns.map((item) => [
    escapeHtml(item.kind),
    escapeHtml(item.title),
    escapeHtml(item.detail),
    escapeHtml(item.evidence.join('；')),
  ])
  const causes = report.possible_causes.map((item) => [
    escapeHtml(item.kind),
    escapeHtml(item.title),
    escapeHtml(item.detail),
    escapeHtml(item.rationale),
  ])
  const checks = report.recommended_checks.map((item) => [
    escapeHtml(item.kind),
    escapeHtml(item.title),
    escapeHtml(item.action),
    escapeHtml(item.expected_evidence),
  ])
  const limitations = report.limitations
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join('')

  return `
<h2>AI Assisted Diagnosis</h2>
<p class="notice">
  AI 内容是基于确定性 AnalysisSummary 的解释层；可能原因属于待验证假设，不等同于已确认根因。
</p>
<table><tbody>
${rows([
  ['Model', escapeHtml(model), 'Generated At', escapeHtml(generatedAt)],
  ['Confidence', escapeHtml(percent(report.confidence)), '', ''],
])}
</tbody></table>

<h3>Executive Summary</h3>
<p>${escapeHtml(report.executive_summary)}</p>

<h3>Key Findings</h3>
<table>
<thead><tr><th>Kind</th><th>Title</th><th>Detail</th><th>Evidence</th></tr></thead>
<tbody>${rows(keyFindings)}</tbody>
</table>

<h3>Spatial Pattern Interpretation</h3>
<table>
<thead><tr><th>Kind</th><th>Title</th><th>Detail</th><th>Evidence</th></tr></thead>
<tbody>${rows(spatialPatterns)}</tbody>
</table>

<h3>Possible Causes</h3>
<table>
<thead><tr><th>Kind</th><th>Title</th><th>Hypothesis</th><th>Rationale</th></tr></thead>
<tbody>${rows(causes)}</tbody>
</table>

<h3>Recommended Checks</h3>
<table>
<thead><tr><th>Kind</th><th>Title</th><th>Action</th><th>Expected Evidence</th></tr></thead>
<tbody>${rows(checks)}</tbody>
</table>

<h3>AI Limitations</h3>
<ul>${limitations}</ul>
`
}

export function waferReportHtml(
  dataset: WaferDataset,
  analysis: AnalysisSummary,
  mapPngDataUrl?: string | null,
  aiReport?: AIReport | null,
  aiModel?: string | null,
  aiGeneratedAt?: string | null,
) {
  const metadata = dataset.metadata
  const safeMap =
    mapPngDataUrl?.startsWith('data:image/png;') ? mapPngDataUrl : null

  const binRows = analysis.bin_stats.map((item) => [
    escapeHtml(item.soft_bin),
    escapeHtml(item.description),
    escapeHtml(item.count),
    escapeHtml(percent(item.wafer_rate)),
    escapeHtml(percent(item.fail_share)),
  ])

  const patternRows = analysis.patterns.map((item) => [
    escapeHtml(item.pattern),
    escapeHtml(item.soft_bin),
    escapeHtml(item.score.toFixed(3)),
    escapeHtml(item.evidence.join('；')),
  ])

  const regionRows = Object.entries(analysis.region_stats).map(
    ([name, item]) => [
      escapeHtml(name),
      escapeHtml(item.tested_die),
      escapeHtml(item.pass_die),
      escapeHtml(item.fail_die),
      escapeHtml(percent(item.fail_rate)),
    ],
  )

  const spatialRows = analysis.spatial_by_bin.map((item) => [
    escapeHtml(item.soft_bin),
    escapeHtml(ratio(item.edge.enrichment)),
    escapeHtml(ratio(item.center.enrichment)),
    escapeHtml(ratio(item.cluster.cluster_ratio)),
    escapeHtml(item.cluster.largest_component),
  ])

  const findings = analysis.top_findings
    .map(
      (item) =>
        `<li><strong>[${escapeHtml(item.kind)}]</strong> ${escapeHtml(item.text)}</li>`,
    )
    .join('')

  const limitations = analysis.limitations
    .map((item) => `<li>${escapeHtml(item)}</li>`)
    .join('')

  return `<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Wafer Analysis Report - ${escapeHtml(metadata.wafer_id)}</title>
<style>
  :root { font-family: Arial, "Microsoft YaHei", sans-serif; color: #172033; }
  body { max-width: 1120px; margin: 0 auto; padding: 28px; line-height: 1.5; }
  h1 { margin: 0 0 6px; font-size: 26px; }
  h2 { margin-top: 28px; font-size: 18px; border-bottom: 1px solid #d9d9d9; padding-bottom: 6px; }
  h3 { margin-top: 20px; font-size: 15px; }
  .muted { color: #667085; }
  .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
  .metric { border: 1px solid #d9d9d9; border-radius: 8px; padding: 12px; }
  .metric b { display: block; font-size: 20px; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { border: 1px solid #d9d9d9; padding: 7px 8px; text-align: left; vertical-align: top; }
  th { background: #f5f7fa; }
  .map { display: block; max-width: 720px; width: 100%; margin: 12px auto; border: 1px solid #d9d9d9; }
  .notice { padding: 10px 12px; border-left: 4px solid #1677ff; background: #f0f7ff; }
  @media (max-width: 720px) { .grid { grid-template-columns: repeat(2, 1fr); } body { padding: 14px; } }
  @media print { body { max-width: none; padding: 0; } .no-print { display: none; } }
</style>
</head>
<body>
<h1>Wafer Analysis Report</h1>
<div class="muted">
  Product ${escapeHtml(metadata.product_id)} · Lot ${escapeHtml(metadata.lot_id)}
  · Wafer ${escapeHtml(metadata.wafer_id)} · Flow ${escapeHtml(metadata.flow_id)}
</div>
<p class="notice">
  本报告的事实与空间模式来自确定性算法。空间 Pattern 是统计判断，不等同于已确认根因。
</p>

<h2>Summary</h2>
<div class="grid">
  <div class="metric">Yield<b>${escapeHtml(percent(dataset.summary.yield))}</b></div>
  <div class="metric">Tested<b>${escapeHtml(dataset.summary.tested_die)}</b></div>
  <div class="metric">Pass<b>${escapeHtml(dataset.summary.pass_die)}</b></div>
  <div class="metric">Fail<b>${escapeHtml(dataset.summary.fail_die)}</b></div>
</div>

<h2>Metadata</h2>
<table><tbody>
${rows([
  ['Product', escapeHtml(metadata.product_id), 'Lot', escapeHtml(metadata.lot_id)],
  ['Wafer', escapeHtml(metadata.wafer_id), 'Flow', escapeHtml(metadata.flow_id)],
  ['Tester', escapeHtml(metadata.tester), 'Program', escapeHtml(metadata.test_program)],
  ['Probe Card', escapeHtml(metadata.probe_card), 'Notch', escapeHtml(metadata.notch)],
  ['Geometry', escapeHtml(`${metadata.rows} × ${metadata.columns}`), 'Stop Time', escapeHtml(metadata.stop_time)],
])}
</tbody></table>

${safeMap ? `<h2>Wafer Map</h2><img class="map" src="${safeMap}" alt="Wafer map" />` : ''}

<h2>Deterministic Findings</h2>
<ul>${findings}</ul>

<h2>Soft Bin Statistics</h2>
<table>
<thead><tr><th>Bin</th><th>Description</th><th>Count</th><th>Wafer %</th><th>Fail %</th></tr></thead>
<tbody>${rows(binRows)}</tbody>
</table>

<h2>Spatial Patterns</h2>
<table>
<thead><tr><th>Pattern</th><th>Bin</th><th>Score</th><th>Evidence</th></tr></thead>
<tbody>${rows(patternRows)}</tbody>
</table>

<h2>Region Statistics</h2>
<table>
<thead><tr><th>Region</th><th>Tested</th><th>Pass</th><th>Fail</th><th>Fail Rate</th></tr></thead>
<tbody>${rows(regionRows)}</tbody>
</table>

<h2>Spatial Metrics by Bin</h2>
<table>
<thead><tr><th>Bin</th><th>Edge Enr.</th><th>Center Enr.</th><th>Cluster Ratio</th><th>Largest CC</th></tr></thead>
<tbody>${rows(spatialRows)}</tbody>
</table>

<h2>Limitations</h2>
<ul>${limitations}</ul>

${aiSection(aiReport, aiModel, aiGeneratedAt)}

<p class="muted">
  Generated by Wafer Intelligence. 可使用浏览器“打印 / 另存为 PDF”生成归档版报告。
</p>
</body>
</html>`
}

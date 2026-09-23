import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate, useSearch } from '@tanstack/react-router'
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from 'antd'
import type { EChartsOption } from 'echarts'
import { ArrowLeft, Eye } from 'lucide-react'
import { PageHeader } from '../../components/common/PageHeader'
import type {
  BinAggregate,
  LotListItem,
  WaferComparisonRow,
} from '../../types/comparison'
import { compareAnalyses, getLotSummary, listLots } from './api'
import { EChart } from './EChart'
import { LotMiniMap } from './LotMiniMap'

function percent(value: number | null, digits = 2) {
  return value === null ? '—' : `${(value * 100).toFixed(digits)}%`
}

function ratio(value: number | null, digits = 2) {
  return value === null ? '—' : value.toFixed(digits)
}

function selectedIds(value?: string) {
  return (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)
}

function issueType(severity: string) {
  if (severity === 'ERROR') return 'error' as const
  if (severity === 'WARNING') return 'warning' as const
  return 'info' as const
}

export function LotPage() {
  const search = useSearch({ from: '/lots' })
  const navigate = useNavigate({ from: '/lots' })
  const analysisIds = useMemo(
    () => selectedIds(search.analysis_ids),
    [search.analysis_ids],
  )

  const lotsQuery = useQuery({
    queryKey: ['lots'],
    queryFn: listLots,
  })

  const comparisonQuery = useQuery({
    queryKey: [
      'lot-comparison',
      search.lot_id,
      search.product_id,
      analysisIds.join(','),
    ],
    queryFn: () => {
      if (analysisIds.length >= 2) return compareAnalyses(analysisIds)
      if (!search.lot_id) throw new Error('Lot ID is required.')
      return getLotSummary(search.lot_id, search.product_id)
    },
    enabled: analysisIds.length >= 2 || Boolean(search.lot_id),
  })

  const data = comparisonQuery.data?.data
  const topBins = useMemo(
    () =>
      [...(data?.bin_aggregates ?? [])]
        .filter((item) => (item.mean_fail_share ?? 0) > 0)
        .sort((a, b) => (b.mean_fail_share ?? 0) - (a.mean_fail_share ?? 0))
        .slice(0, 5),
    [data?.bin_aggregates],
  )

  const yieldOption = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' },
    grid: { left: 52, right: 20, top: 28, bottom: 48 },
    xAxis: {
      type: 'category',
      data: data?.yield_trend.map((item) => item.wafer_id ?? item.analysis_id.slice(0, 8)) ?? [],
      axisLabel: { rotate: 25 },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 100,
      axisLabel: { formatter: '{value}%' },
    },
    series: [{
      name: 'Yield',
      type: 'line',
      smooth: false,
      symbolSize: 8,
      data: data?.yield_trend.map((item) => ({
        value: item.yield === null ? null : item.yield * 100,
        itemStyle: item.is_outlier ? { borderWidth: 3 } : undefined,
      })) ?? [],
      markPoint: {
        data: data?.yield_trend
          .map((item, index) => ({ item, index }))
          .filter(({ item }) => item.is_outlier && item.yield !== null)
          .map(({ item, index }) => ({
            name: 'Outlier',
            coord: [index, (item.yield ?? 0) * 100],
            value: '异常',
          })) ?? [],
      },
    }],
  }), [data?.yield_trend])

  const binOption = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' },
    legend: { type: 'scroll', top: 0 },
    grid: { left: 52, right: 20, top: 52, bottom: 48 },
    xAxis: {
      type: 'category',
      data: data?.yield_trend.map((item) => item.wafer_id ?? item.analysis_id.slice(0, 8)) ?? [],
      axisLabel: { rotate: 25 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: '{value}%' },
    },
    series: topBins.map((bin) => ({
      name: `Bin ${bin.soft_bin}`,
      type: 'line',
      symbolSize: 6,
      data: bin.trend.map((item) => item.wafer_rate * 100),
    })),
  }), [data?.yield_trend, topBins])

  const enrichmentBin: BinAggregate | undefined = topBins[0]
  const enrichmentOption = useMemo<EChartsOption>(() => ({
    tooltip: { trigger: 'axis' },
    legend: { top: 0 },
    grid: { left: 52, right: 20, top: 52, bottom: 48 },
    xAxis: {
      type: 'category',
      data: enrichmentBin?.trend.map((item) => item.wafer_id ?? item.analysis_id.slice(0, 8)) ?? [],
      axisLabel: { rotate: 25 },
    },
    yAxis: { type: 'value', name: 'Enrichment' },
    series: [
      {
        name: 'Edge',
        type: 'line',
        data: enrichmentBin?.trend.map((item) => item.edge_enrichment) ?? [],
      },
      {
        name: 'Center',
        type: 'line',
        data: enrichmentBin?.trend.map((item) => item.center_enrichment) ?? [],
      },
    ],
  }), [enrichmentBin])

  const lotColumns = [
    { title: 'Product', dataIndex: 'product_id', key: 'product_id' },
    { title: 'Lot', dataIndex: 'lot_id', key: 'lot_id' },
    { title: 'Wafer 数', dataIndex: 'wafer_count', key: 'wafer_count', align: 'right' as const },
    {
      title: '平均 Yield',
      dataIndex: 'average_yield',
      key: 'average_yield',
      align: 'right' as const,
      render: (value: number | null) => percent(value),
    },
    {
      title: '范围',
      key: 'range',
      render: (_: unknown, record: LotListItem) =>
        `${percent(record.minimum_yield)} ～ ${percent(record.maximum_yield)}`,
    },
    {
      title: '最近分析',
      dataIndex: 'last_created_at',
      key: 'last_created_at',
      render: (value: string) => new Date(value).toLocaleString(),
    },
  ]

  const waferColumns = [
    { title: 'Wafer', dataIndex: 'wafer_id', key: 'wafer_id', width: 90 },
    {
      title: 'Yield',
      dataIndex: 'yield',
      key: 'yield',
      align: 'right' as const,
      width: 100,
      render: (value: number | null, record: WaferComparisonRow) => (
        <Space size={4}>
          <span>{percent(value)}</span>
          {record.is_outlier && <Tag color="error">异常</Tag>}
        </Space>
      ),
    },
    {
      title: 'Main Fail',
      dataIndex: 'main_fail_bin',
      key: 'main_fail_bin',
      width: 100,
      render: (value: number | null) => value === null ? '—' : `Bin ${value}`,
    },
    {
      title: 'Fail Rate',
      dataIndex: 'main_fail_rate',
      key: 'main_fail_rate',
      align: 'right' as const,
      width: 100,
      render: (value: number | null) => percent(value),
    },
    {
      title: 'Edge',
      dataIndex: 'edge_enrichment',
      key: 'edge_enrichment',
      align: 'right' as const,
      width: 90,
      render: (value: number | null) => ratio(value),
    },
    {
      title: 'Center',
      dataIndex: 'center_enrichment',
      key: 'center_enrichment',
      align: 'right' as const,
      width: 90,
      render: (value: number | null) => ratio(value),
    },
    {
      title: 'Cluster',
      dataIndex: 'cluster_ratio',
      key: 'cluster_ratio',
      align: 'right' as const,
      width: 90,
      render: (value: number | null) => percent(value),
    },
    {
      title: 'Pattern',
      dataIndex: 'main_pattern',
      key: 'main_pattern',
      width: 150,
      render: (value: string | null) => value ? <Tag>{value}</Tag> : '—',
    },
    { title: 'Tester', dataIndex: 'tester', key: 'tester', width: 120 },
    {
      title: '',
      key: 'open',
      width: 56,
      fixed: 'right' as const,
      render: (_: unknown, record: WaferComparisonRow) => (
        <Button
          type="text"
          aria-label={`查看 Wafer ${record.wafer_id ?? record.analysis_id}`}
          icon={<Eye size={16} />}
          onClick={() => navigate({
            to: '/analyses/$analysisId',
            params: { analysisId: record.analysis_id },
          })}
        />
      ),
    },
  ]

  const hasSelection = Boolean(search.lot_id) || analysisIds.length >= 2

  return (
    <div className="page-container">
      <PageHeader
        title="Lot / 多 Wafer"
        description="基于历史分析进行良率、Fail Bin、空间富集与异常 Wafer 的确定性对比。"
      />

      {!hasSelection && (
        <Card className="section-card" title="Lot 列表">
          <Table<LotListItem>
            rowKey={(record) => `${record.product_id ?? ''}:${record.lot_id}`}
            dataSource={lotsQuery.data?.data ?? []}
            columns={lotColumns}
            loading={lotsQuery.isFetching}
            pagination={false}
            locale={{ emptyText: <Empty description="暂无可汇总的 Lot" /> }}
            onRow={(record) => ({
              onClick: () => navigate({
                search: {
                  lot_id: record.lot_id,
                  product_id: record.product_id ?? undefined,
                },
              }),
            })}
          />
          <Typography.Text type="secondary" className="history-note">
            点击任一 Lot 进入汇总；也可在“分析历史”勾选 2–25 片 Wafer 做临时对比。
          </Typography.Text>
        </Card>
      )}

      {hasSelection && (
        <>
          <Button
            className="lot-back-button"
            icon={<ArrowLeft size={16} />}
            onClick={() => navigate({ search: {} })}
          >
            返回 Lot 列表
          </Button>

          {comparisonQuery.isError && (
            <Alert
              type="error"
              showIcon
              className="section-block"
              message="多 Wafer 分析加载失败"
              description={comparisonQuery.error instanceof Error
                ? comparisonQuery.error.message
                : '无法读取对比数据。'}
            />
          )}

          {data && (
            <>
              <Row gutter={[12, 12]} className="wafer-kpi-row">
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic title="Wafer 数" value={data.yield_stats.wafer_count} />
                  </Card>
                </Col>
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic title="平均 Yield" value={percent(data.yield_stats.average)} />
                  </Card>
                </Col>
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic title="Yield 中位数" value={percent(data.yield_stats.median)} />
                  </Card>
                </Col>
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic title="Yield σ" value={percent(data.yield_stats.std_dev)} />
                  </Card>
                </Col>
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic
                      title="异常 Wafer"
                      value={data.yield_trend.filter((item) => item.is_outlier).length}
                    />
                  </Card>
                </Col>
                <Col xs={12} md={8} xl={4}>
                  <Card size="small" className="metric-card">
                    <Statistic
                      title="兼容性"
                      value={data.compatibility.compatible ? '可比较' : '需复核'}
                    />
                  </Card>
                </Col>
                <Col xs={24} md={12} xl={6}>
                  <Card size="small" className="metric-card">
                    <Statistic
                      title="最高 Yield Wafer"
                      value={
                        data.highest_yield_wafers
                          .map((item) => item.wafer_id ?? item.analysis_id.slice(0, 8))
                          .join(', ') || '—'
                      }
                    />
                    <Typography.Text type="secondary">
                      {data.highest_yield_wafers[0]
                        ? percent(data.highest_yield_wafers[0].yield)
                        : '无有效 Yield'}
                    </Typography.Text>
                  </Card>
                </Col>
                <Col xs={24} md={12} xl={6}>
                  <Card size="small" className="metric-card">
                    <Statistic
                      title="最低 Yield Wafer"
                      value={
                        data.lowest_yield_wafers
                          .map((item) => item.wafer_id ?? item.analysis_id.slice(0, 8))
                          .join(', ') || '—'
                      }
                    />
                    <Typography.Text type="secondary">
                      {data.lowest_yield_wafers[0]
                        ? percent(data.lowest_yield_wafers[0].yield)
                        : '无有效 Yield'}
                    </Typography.Text>
                  </Card>
                </Col>
              </Row>

              {data.compatibility.issues.map((issue) => (
                <Alert
                  key={issue.code}
                  className="section-block"
                  type={issueType(issue.severity)}
                  showIcon
                  message={issue.code}
                  description={issue.message}
                />
              ))}

              <Row gutter={[16, 16]} className="section-block">
                <Col xs={24} xl={12}>
                  <Card title="Yield Trend" className="metric-card">
                    <EChart option={yieldOption} ariaLabel="Yield trend chart" />
                  </Card>
                </Col>
                <Col xs={24} xl={12}>
                  <Card title="Top Fail Bin Trend" className="metric-card">
                    {topBins.length > 0 ? (
                      <EChart option={binOption} ariaLabel="Fail bin trend chart" />
                    ) : (
                      <Empty description="暂无 Fail Bin 趋势" />
                    )}
                  </Card>
                </Col>
                <Col xs={24} xl={12}>
                  <Card
                    title={enrichmentBin
                      ? `Bin ${enrichmentBin.soft_bin} 空间富集趋势`
                      : '空间富集趋势'}
                    className="metric-card"
                  >
                    {enrichmentBin ? (
                      <EChart option={enrichmentOption} ariaLabel="Spatial enrichment trend chart" />
                    ) : (
                      <Empty description="暂无空间富集数据" />
                    )}
                  </Card>
                </Col>
                <Col xs={24} xl={12}>
                  <Card title="Pattern 分布" className="metric-card">
                    <Space wrap>
                      {data.pattern_distribution.map((item) => (
                        <Tag key={item.pattern}>
                          {item.pattern}: {item.count} ({percent(item.percentage, 1)})
                        </Tag>
                      ))}
                    </Space>
                  </Card>
                </Col>
              </Row>

              <Card title="Wafer Matrix" className="section-card">
                <Table<WaferComparisonRow>
                  rowKey="analysis_id"
                  dataSource={data.wafers}
                  columns={waferColumns}
                  pagination={false}
                  scroll={{ x: 1180 }}
                />
              </Card>

              <Card title="Mini Wafer Map Grid" className="section-card">
                <Row gutter={[12, 12]}>
                  {data.wafers
                    .filter((item) => item.preview)
                    .map((item) => (
                      <Col xs={12} md={8} xl={6} xxl={4} key={item.analysis_id}>
                        <div className="lot-mini-map-card">
                          <Space className="lot-mini-map-title">
                            <Typography.Text strong>
                              Wafer {item.wafer_id ?? '—'}
                            </Typography.Text>
                            {item.is_outlier && <Tag color="error">异常</Tag>}
                          </Space>
                          {item.preview && (
                            <LotMiniMap
                              preview={item.preview}
                              label={`Wafer ${item.wafer_id ?? item.analysis_id} mini map`}
                            />
                          )}
                          <Typography.Text type="secondary">
                            Yield {percent(item.yield)}
                          </Typography.Text>
                        </div>
                      </Col>
                    ))}
                </Row>
              </Card>

              {data.limitations.length > 0 && (
                <Alert
                  className="section-block"
                  type="info"
                  showIcon
                  message="分析边界与限制"
                  description={
                    <ul className="lot-limitations">
                      {data.limitations.map((item) => <li key={item}>{item}</li>)}
                    </ul>
                  }
                />
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}

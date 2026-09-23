import { useRef, useState, type ReactNode } from 'react'
import { useNavigate } from '@tanstack/react-router'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Row,
  Segmented,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Tabs,
  Tag,
  Typography,
} from 'antd'
import { Download, FileText, RotateCcw } from 'lucide-react'
import { PageHeader } from '../../components/common/PageHeader'
import type {
  BinStat,
  PatternResult,
  RegionMetric,
  SpatialBinStat,
} from '../../types/analysis'
import type { WaferWorkspace } from '../../types/analysis'
import type { DieRecord } from '../../types/wafer'
import { binColor } from './binColors'
import { MiniWaferMap } from './MiniWaferMap'
import { downloadDataUrl, downloadText, waferCsv } from './export'
import { waferReportHtml } from './report'
import {
  WaferMap,
  type WaferFilterMode,
  type WaferMapHandle,
} from './WaferMap'

function percent(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : `${(value * 100).toFixed(2)}%`
}

function ratio(value: number | null | undefined) {
  return value === null || value === undefined ? '—' : value.toFixed(2)
}

function safeName(value: string | null | undefined) {
  return (value ?? 'wafer').replaceAll(/[^a-zA-Z0-9._-]+/g, '_')
}

type WaferExtraTab = {
  key: string
  label: ReactNode
  children: ReactNode
}

type WaferPageProps = {
  workspace?: WaferWorkspace
  extraActions?: ReactNode
  extraTabs?: WaferExtraTab[]
}

export function WaferPage({
  workspace,
  extraActions,
  extraTabs,
}: WaferPageProps = {}) {
  const navigate = useNavigate()
  const mapRef = useRef<WaferMapHandle | null>(null)
  const [filterMode, setFilterMode] = useState<WaferFilterMode>('all')
  const [selectedBins, setSelectedBins] = useState<number[]>([])
  const [showCoordinates, setShowCoordinates] = useState(true)
  const [selectedDie, setSelectedDie] = useState<DieRecord | null>(null)

  if (!workspace) {
    return (
      <div className="page-container">
        <PageHeader title="单片分析" description="当前没有可用的 Wafer 工作区。" />
        <div className="section-card">
          <Empty
            description="请先上传并解析 PAT / CP 文件"
          >
            <Button type="primary" onClick={() => navigate({ to: '/upload' })}>
              返回新建分析
            </Button>
          </Empty>
        </div>
      </div>
    )
  }

  const { dataset, analysis } = workspace
  const metadata = dataset.metadata
  const filenameBase = `${safeName(metadata.lot_id)}-${safeName(metadata.wafer_id)}`

  const describedPassBins = dataset.bins
    .filter((item) => (item.description ?? '').toUpperCase().includes('PASS'))
    .map((item) => item.bin)
  const passBins = new Set(describedPassBins.length > 0 ? describedPassBins : [1])

  const mainFailBins = analysis.bin_stats
    .filter((item) => !passBins.has(item.soft_bin) && item.count > 0)
    .sort((left, right) => right.count - left.count)
    .slice(0, 3)

  const binOptions = dataset.bins
    .filter((item) => item.count > 0)
    .map((item) => ({
      value: item.bin,
      label: `Bin ${item.bin} · ${item.description ?? 'N/A'} (${item.count})`,
    }))

  const binColumns = [
    {
      title: '',
      key: 'color',
      width: 38,
      render: (_: unknown, record: BinStat) => (
        <span
          className="bin-color-dot"
          style={{
            background: binColor(record.soft_bin, passBins.has(record.soft_bin)),
          }}
        />
      ),
    },
    {
      title: 'Bin',
      dataIndex: 'soft_bin',
      key: 'soft_bin',
      width: 70,
      render: (value: number) => <strong>{value}</strong>,
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Count',
      dataIndex: 'count',
      key: 'count',
      width: 90,
      align: 'right' as const,
    },
    {
      title: 'Wafer %',
      dataIndex: 'wafer_rate',
      key: 'wafer_rate',
      width: 100,
      align: 'right' as const,
      render: (value: number) => percent(value),
    },
    {
      title: 'Fail %',
      dataIndex: 'fail_share',
      key: 'fail_share',
      width: 100,
      align: 'right' as const,
      render: (value: number | null) => percent(value),
    },
  ]

  const patternColumns = [
    {
      title: 'Pattern',
      dataIndex: 'pattern',
      key: 'pattern',
      width: 150,
      render: (value: string) => <Tag>{value}</Tag>,
    },
    {
      title: 'Bin',
      dataIndex: 'soft_bin',
      key: 'soft_bin',
      width: 70,
    },
    {
      title: 'Score',
      dataIndex: 'score',
      key: 'score',
      width: 90,
      align: 'right' as const,
      render: (value: number) => value.toFixed(3),
    },
    {
      title: 'Evidence',
      dataIndex: 'evidence',
      key: 'evidence',
      render: (value: string[]) => value.join('；'),
    },
  ]

  const spatialColumns = [
    {
      title: 'Bin',
      dataIndex: 'soft_bin',
      key: 'soft_bin',
      width: 70,
    },
    {
      title: 'Edge Enr.',
      key: 'edge',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => ratio(record.edge.enrichment),
    },
    {
      title: 'Center Enr.',
      key: 'center',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => ratio(record.center.enrichment),
    },
    {
      title: 'Cluster Ratio',
      key: 'cluster',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => ratio(record.cluster.cluster_ratio),
    },
    {
      title: 'Largest CC',
      key: 'largest',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => record.cluster.largest_component,
    },
    {
      title: 'Max Row %',
      key: 'row',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => percent(record.max_row_fraction),
    },
    {
      title: 'Max Col %',
      key: 'column',
      align: 'right' as const,
      render: (_: unknown, record: SpatialBinStat) => percent(record.max_column_fraction),
    },
  ]

  const regionRows = Object.entries(analysis.region_stats).map(([name, metric]) => ({
    name,
    ...metric,
  }))

  const regionColumns = [
    { title: 'Region', dataIndex: 'name', key: 'name' },
    {
      title: 'Tested',
      dataIndex: 'tested_die',
      key: 'tested_die',
      align: 'right' as const,
    },
    {
      title: 'Pass',
      dataIndex: 'pass_die',
      key: 'pass_die',
      align: 'right' as const,
    },
    {
      title: 'Fail',
      dataIndex: 'fail_die',
      key: 'fail_die',
      align: 'right' as const,
    },
    {
      title: 'Fail Rate',
      dataIndex: 'fail_rate',
      key: 'fail_rate',
      align: 'right' as const,
      render: (value: RegionMetric['fail_rate']) => percent(value),
    },
  ]

  const exportPng = () => {
    const dataUrl = mapRef.current?.exportPng()
    if (dataUrl) downloadDataUrl(`${filenameBase}-wafer-map.png`, dataUrl)
  }

  const exportCsv = () => {
    downloadText(
      `${filenameBase}-dies.csv`,
      waferCsv(dataset),
      'text/csv;charset=utf-8',
    )
  }

  const exportReport = () => {
    const mapPng = mapRef.current?.exportPng()
    downloadText(
      `${filenameBase}-analysis-report.html`,
      waferReportHtml(dataset, analysis, mapPng),
      'text/html;charset=utf-8',
    )
  }

  const overview = (
    <Space direction="vertical" size={12} className="wafer-tab-stack">
      <Row gutter={[12, 12]}>
        <Col xs={24} xl={14}>
          <Card title="确定性结论" size="small">
            <Space direction="vertical" size={8}>
              {analysis.top_findings.map((item) => (
                <Flex key={`${item.kind}-${item.text}`} gap={8} align="flex-start">
                  <Tag color={item.kind === 'FACT' ? 'blue' : 'purple'}>
                    {item.kind === 'FACT' ? '事实' : '判断'}
                  </Tag>
                  <Typography.Text>{item.text}</Typography.Text>
                </Flex>
              ))}
            </Space>
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card title="分析限制" size="small">
            <Space direction="vertical" size={8}>
              {analysis.limitations.map((item) => (
                <Typography.Text type="secondary" key={item}>
                  {item}
                </Typography.Text>
              ))}
            </Space>
          </Card>
        </Col>
      </Row>

      {mainFailBins.length > 0 && (
        <Card title="主要 Fail Bin 分布" size="small">
          <Row gutter={[12, 12]}>
            {mainFailBins.map((item) => (
              <Col xs={24} md={8} key={item.soft_bin}>
                <Card
                  size="small"
                  title={`Bin ${item.soft_bin} · ${item.description ?? 'N/A'}`}
                  extra={<Tag>{item.count}</Tag>}
                >
                  <MiniWaferMap dataset={dataset} softBin={item.soft_bin} />
                </Card>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </Space>
  )

  const spatial = (
    <Space direction="vertical" size={12} className="wafer-tab-stack">
      <Card title="Pattern v1" size="small">
        <Table<PatternResult>
          rowKey={(item) => `${item.soft_bin}-${item.pattern}-${item.evidence.join('|')}`}
          columns={patternColumns}
          dataSource={analysis.patterns}
          pagination={false}
          size="small"
          scroll={{ x: 760 }}
        />
      </Card>
      <Card title="区域统计" size="small">
        <Table
          rowKey="name"
          columns={regionColumns}
          dataSource={regionRows}
          pagination={false}
          size="small"
          scroll={{ x: 640 }}
        />
      </Card>
      <Card title="各 Bin 空间特征" size="small">
        <Table<SpatialBinStat>
          rowKey="soft_bin"
          columns={spatialColumns}
          dataSource={analysis.spatial_by_bin}
          pagination={false}
          size="small"
          scroll={{ x: 760 }}
        />
      </Card>
    </Space>
  )

  const bins = (
    <Card title="Soft Bin 统计" size="small">
      <Table<BinStat>
        rowKey="soft_bin"
        columns={binColumns}
        dataSource={analysis.bin_stats}
        pagination={false}
        size="small"
        scroll={{ x: 720 }}
      />
    </Card>
  )

  return (
    <div className="page-container">
      <PageHeader
        title={`Wafer ${metadata.wafer_id ?? '—'}`}
        description={`${metadata.product_id ?? 'Unknown Product'} · Lot ${metadata.lot_id ?? '—'} · ${metadata.flow_id ?? '—'}`}
        actions={(
          <Space wrap>
            <Button icon={<Download size={16} />} onClick={exportCsv}>
              导出 CSV
            </Button>
            <Button icon={<FileText size={16} />} onClick={exportReport}>
              导出报告
            </Button>
            <Button type="primary" icon={<Download size={16} />} onClick={exportPng}>
              导出 PNG
            </Button>
            {extraActions}
          </Space>
        )}
      />

      <Row gutter={[12, 12]} className="wafer-kpi-row">
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Yield" value={(dataset.summary.yield ?? 0) * 100} precision={2} suffix="%" /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Tested" value={dataset.summary.tested_die} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Pass" value={dataset.summary.pass_die} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Fail" value={dataset.summary.fail_die} /></Card>
        </Col>
      </Row>

      <Row gutter={[12, 12]} className="wafer-main-grid">
        <Col xs={24} xl={16}>
          <Card
            title="Wafer Map"
            size="small"
            extra={(
              <Space wrap>
                <Segmented
                  value={filterMode}
                  options={[
                    { label: '全部', value: 'all' },
                    { label: 'PASS', value: 'pass' },
                    { label: 'FAIL', value: 'fail' },
                  ]}
                  onChange={(value) => setFilterMode(value as WaferFilterMode)}
                />
                <Button
                  icon={<RotateCcw size={16} />}
                  onClick={() => mapRef.current?.resetView()}
                >
                  重置视图
                </Button>
              </Space>
            )}
          >
            <Flex gap={12} wrap className="wafer-map-controls">
              <Select
                mode="multiple"
                allowClear
                maxTagCount="responsive"
                placeholder="选择 Bin，其他 Bin 灰化"
                value={selectedBins}
                options={binOptions}
                onChange={setSelectedBins}
                className="wafer-bin-select"
              />
              <Space>
                <Switch checked={showCoordinates} onChange={setShowCoordinates} />
                <Typography.Text>Row / Column</Typography.Text>
              </Space>
            </Flex>
            <WaferMap
              ref={mapRef}
              dataset={dataset}
              filterMode={filterMode}
              selectedBins={selectedBins}
              showCoordinates={showCoordinates}
              onDieClick={setSelectedDie}
            />
          </Card>
        </Col>

        <Col xs={24} xl={8}>
          <Card title="Bin 图例与筛选" size="small">
            <Table<BinStat>
              rowKey="soft_bin"
              columns={binColumns.slice(0, 5)}
              dataSource={analysis.bin_stats}
              pagination={false}
              size="small"
              scroll={{ x: 520 }}
              onRow={(record) => ({
                onClick: () => {
                  setSelectedBins((current) =>
                    current.includes(record.soft_bin)
                      ? current.filter((item) => item !== record.soft_bin)
                      : [...current, record.soft_bin],
                  )
                },
              })}
            />
          </Card>

          <Alert
            className="section-block"
            type="info"
            showIcon
            message={`Notch: ${metadata.notch ?? '—'}`}
            description="算法保持源 Row / Column，不因 Notch 方向偷偷旋转坐标。"
          />
        </Col>
      </Row>

      <div className="section-card">
        <Tabs
          items={[
            { key: 'overview', label: 'Overview', children: overview },
            { key: 'spatial', label: 'Spatial', children: spatial },
            { key: 'bin', label: 'Bin', children: bins },
            ...(extraTabs ?? []),
          ]}
        />
      </div>

      <Drawer
        title="Die 详情"
        open={selectedDie !== null}
        onClose={() => setSelectedDie(null)}
        width={380}
      >
        {selectedDie && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="Row">{selectedDie.row}</Descriptions.Item>
            <Descriptions.Item label="Column">{selectedDie.column}</Descriptions.Item>
            <Descriptions.Item label="Char">{selectedDie.source_char}</Descriptions.Item>
            <Descriptions.Item label="Soft Bin">{selectedDie.soft_bin ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Hard Bin">{selectedDie.hard_bin ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Description">{selectedDie.description ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Result">
              <Tag color={selectedDie.result === 'PASS' ? 'success' : 'error'}>
                {selectedDie.result}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Drawer>
    </div>
  )
}

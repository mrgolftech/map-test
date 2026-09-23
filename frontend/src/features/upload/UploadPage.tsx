import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Flex,
  Result,
  Row,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
  Upload,
  type UploadFile,
  type UploadProps,
} from 'antd'
import { BarChart3, FileSearch, FlaskConical, Layers3, UploadCloud } from 'lucide-react'
import { ApiError } from '../../api/client'
import { PageHeader } from '../../components/common/PageHeader'
import type { SourceDescriptor, ValidationIssue } from '../../types/wafer'
import { createAnalysis } from '../history/api'
import { parseWaferFiles } from './api'
import {
  generateDemoLot,
  generateDemoWafer,
  type DemoLotScenario,
  type SyntheticPattern,
} from './simulatorApi'

const demoPatterns: SyntheticPattern[] = [
  'EDGE',
  'CENTER',
  'RING',
  'TOP',
  'BOTTOM',
  'LEFT',
  'RIGHT',
  'QUADRANT',
  'CLUSTER',
  'LINE',
  'MULTI_PATTERN',
  'RANDOM',
]

const statusColor = {
  VALID: 'success',
  WARNING: 'warning',
  INVALID: 'error',
} as const

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`
  return `${(value / 1024).toFixed(1)} KB`
}

export function UploadPage() {
  const navigate = useNavigate()
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const mutation = useMutation({
    mutationFn: parseWaferFiles,
  })

  const analysisMutation = useMutation({
    mutationFn: createAnalysis,
    onSuccess: (response) => {
      navigate({
        to: '/analyses/$analysisId',
        params: { analysisId: response.data.id },
      })
    },
  })

  const demoMutation = useMutation({
    mutationFn: async (pattern: SyntheticPattern) => {
      const generated = await generateDemoWafer({
        pattern,
        fail_count: pattern === 'MIXED_FAILURES' ? 300 : pattern === 'RANDOM' ? 36 : 48,
        product_id: 'DEMO_WAFER_PRODUCT',
        lot_id: `DEMO-${pattern}`,
        wafer_id: '01',
      })
      return createAnalysis({
        dataset: generated.data,
        sources: [],
        validation_issues: [],
      })
    },
    onSuccess: (response) => {
      navigate({
        to: '/analyses/$analysisId',
        params: { analysisId: response.data.id },
      })
    },
  })

  const demoLotMutation = useMutation({
    mutationFn: async (scenario: DemoLotScenario) => {
      const generated = await generateDemoLot(scenario)
      const lotId = `${generated.data.datasets[0]?.metadata.lot_id ?? `DEMO-${scenario}`}-${crypto.randomUUID().slice(0, 8).toUpperCase()}`
      const datasets = generated.data.datasets.map((dataset) => ({
        ...dataset,
        metadata: { ...dataset.metadata, lot_id: lotId },
      }))
      for (const dataset of datasets) {
        await createAnalysis({
          dataset,
          sources: [],
          validation_issues: [],
        })
      }
      return { ...generated, data: { ...generated.data, datasets } }
    },
    onSuccess: (response) => {
      const first = response.data.datasets[0]
      navigate({
        to: '/lots',
        search: {
          product_id: first?.metadata.product_id ?? undefined,
          lot_id: first?.metadata.lot_id ?? undefined,
        },
      })
    },
  })

  const uploadProps: UploadProps = {
    accept: '.pat,.cp1,.cp,.map,.txt',
    multiple: true,
    maxCount: 2,
    fileList,
    beforeUpload: () => false,
    onChange: ({ fileList: next }) => {
      setFileList(next.slice(-2))
      mutation.reset()
      analysisMutation.reset()
    },
    onRemove: () => {
      mutation.reset()
      analysisMutation.reset()
      return true
    },
  }

  const selectedFiles = useMemo(
    () =>
      fileList.flatMap((file) =>
        file.originFileObj ? [file.originFileObj] : [],
      ),
    [fileList],
  )

  const result = mutation.data
  const dataset = result?.dataset
  const error = mutation.error instanceof ApiError ? mutation.error : null

  const sourceColumns = [
    {
      title: '文件',
      dataIndex: 'filename',
      key: 'filename',
    },
    {
      title: '格式',
      dataIndex: 'detected_format',
      key: 'detected_format',
      width: 90,
      render: (value: SourceDescriptor['detected_format']) => <Tag>{value}</Tag>,
    },
    {
      title: 'Parser',
      dataIndex: 'parser_id',
      key: 'parser_id',
      width: 120,
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      align: 'right' as const,
      render: (value: number) => formatBytes(value),
    },
    {
      title: '识别依据',
      dataIndex: 'detection_evidence',
      key: 'detection_evidence',
      render: (value: string[]) => value.join('；'),
    },
  ]

  const issueColumns = [
    {
      title: '级别',
      dataIndex: 'severity',
      key: 'severity',
      width: 90,
      render: (value: ValidationIssue['severity']) => (
        <Tag color={value === 'ERROR' ? 'error' : value === 'WARNING' ? 'warning' : 'default'}>
          {value}
        </Tag>
      ),
    },
    {
      title: '阶段',
      dataIndex: 'stage',
      key: 'stage',
      width: 110,
    },
    {
      title: '错误码',
      dataIndex: 'code',
      key: 'code',
      width: 220,
    },
    {
      title: '说明',
      dataIndex: 'message',
      key: 'message',
    },
  ]

  return (
    <div className="page-container">
      <PageHeader
        title="新建分析"
        description="上传 PAT / CP 文件，或使用脱敏 Simulator 一键生成可验收的典型 Wafer / Lot。"
      />

      <Card
        className="section-card"
        title="一键演示数据"
        extra={<Tag color="blue">Synthetic · 不含生产数据</Tag>}
      >
        <Space direction="vertical" size={12} className="demo-generator">
          <Typography.Text>
            一张晶圆可同时有多种 Fail Bin，每个 Bin 可能呈现不同空间分布。下面的多失效场景展示这种情况；其余单片场景用于验证指定 Pattern，演示 Lot 用于验证跨片趋势。
          </Typography.Text>
          <Button
            type="primary"
            icon={<FlaskConical size={16} />}
            disabled={demoLotMutation.isPending}
            loading={demoMutation.isPending && demoMutation.variables === 'MIXED_FAILURES'}
            onClick={() => demoMutation.mutate('MIXED_FAILURES')}
          >
            生成单片多失效演示（6 个 Fail Bin）
          </Button>
          <Typography.Text type="secondary">
            合成示例：边缘、中心、局部聚集、环形和离散失效共存；数据与生产样例无对应关系。
          </Typography.Text>
          <Space wrap>
            {demoPatterns.map((pattern) => (
              <Button
                key={pattern}
                icon={<FlaskConical size={16} />}
                disabled={demoLotMutation.isPending}
                loading={demoMutation.isPending && demoMutation.variables === pattern}
                onClick={() => demoMutation.mutate(pattern)}
              >
                {pattern}
              </Button>
            ))}
          </Space>
          <Space wrap>
            <Button
              type="primary"
              icon={<Layers3 size={16} />}
              loading={
                demoLotMutation.isPending
                && demoLotMutation.variables === 'EDGE_DRIFT'
              }
              disabled={demoMutation.isPending}
              onClick={() => demoLotMutation.mutate('EDGE_DRIFT')}
            >
              生成 5 片 EDGE_DRIFT 演示 Lot
            </Button>
            <Button
              icon={<Layers3 size={16} />}
              loading={
                demoLotMutation.isPending
                && demoLotMutation.variables === 'MIXED_PATTERNS'
              }
              disabled={demoMutation.isPending}
              onClick={() => demoLotMutation.mutate('MIXED_PATTERNS')}
            >
              生成 MIXED_PATTERNS 演示 Lot
            </Button>
          </Space>
          {(demoMutation.isError || demoLotMutation.isError) && (
            <Alert
              type="error"
              showIcon
              message="演示数据生成失败"
              description={
                (demoMutation.error ?? demoLotMutation.error) instanceof Error
                  ? (demoMutation.error ?? demoLotMutation.error as Error).message
                  : '无法生成或保存演示数据。'
              }
            />
          )}
        </Space>
      </Card>

      <div className="section-card">
        <Upload.Dragger {...uploadProps}>
          <p className="ant-upload-drag-icon">
            <UploadCloud size={42} />
          </p>
          <p className="ant-upload-text">拖拽或选择 PAT / CP 测试文件</p>
          <p className="ant-upload-hint">
            最多 2 个文件。PAT + CP 会自动关联并交叉校验；未知或冲突数据不会静默修正。
          </p>
        </Upload.Dragger>

        <Flex justify="flex-end" className="upload-actions">
          <Button
            type="primary"
            icon={<FileSearch size={17} />}
            disabled={selectedFiles.length === 0}
            loading={mutation.isPending}
            onClick={() => mutation.mutate(selectedFiles)}
          >
            解析文件
          </Button>
        </Flex>
      </div>

      {error && (
        <Alert
          className="section-block"
          type="error"
          showIcon
          message={error.code}
          description={error.message}
        />
      )}

      {analysisMutation.error instanceof ApiError && (
        <Alert
          className="section-block"
          type="error"
          showIcon
          message={analysisMutation.error.code}
          description={analysisMutation.error.message}
        />
      )}

      {result && (
        <>
          <div className="section-card">
            <Result
              status={
                result.status === 'VALID'
                  ? 'success'
                  : result.status === 'WARNING'
                    ? 'warning'
                    : 'error'
              }
              title={
                <Space>
                  <span>解析状态</span>
                  <Tag color={statusColor[result.status]}>{result.status}</Tag>
                </Space>
              }
              subTitle={
                result.status === 'INVALID'
                  ? '检测到阻断性数据问题，当前结果不会进入正式分析。'
                  : '已完成源文件探测、解析、组装与 canonical validation。'
              }
              extra={
                dataset && result.status !== 'INVALID'
                  ? (
                    <Button
                      type="primary"
                      icon={<BarChart3 size={17} />}
                      loading={analysisMutation.isPending}
                      onClick={() =>
                        analysisMutation.mutate({
                          dataset,
                          sources: result.sources,
                          validation_issues: result.validation_issues,
                        })
                      }
                    >
                      保存并进入分析
                    </Button>
                  )
                  : undefined
              }
            />
          </div>

          <div className="section-card">
            <Typography.Title level={4}>源文件识别</Typography.Title>
            <Table<SourceDescriptor>
              rowKey="sha256"
              columns={sourceColumns}
              dataSource={result.sources}
              pagination={false}
              size="small"
              scroll={{ x: 760 }}
            />
          </div>

          {dataset && (
            <div className="section-card">
              <Typography.Title level={4}>标准 WaferDataset 摘要</Typography.Title>
              <Row gutter={[12, 12]}>
                <Col xs={12} lg={6}>
                  <Statistic title="Tested" value={dataset.summary.tested_die} />
                </Col>
                <Col xs={12} lg={6}>
                  <Statistic title="Pass" value={dataset.summary.pass_die} />
                </Col>
                <Col xs={12} lg={6}>
                  <Statistic title="Fail" value={dataset.summary.fail_die} />
                </Col>
                <Col xs={12} lg={6}>
                  <Statistic
                    title="Yield"
                    value={(dataset.summary.yield ?? 0) * 100}
                    precision={2}
                    suffix="%"
                  />
                </Col>
              </Row>
              <Descriptions
                className="upload-summary"
                size="small"
                bordered
                column={{ xs: 1, md: 2, xl: 4 }}
              >
                <Descriptions.Item label="Product">
                  {dataset.metadata.product_id ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Lot">
                  {dataset.metadata.lot_id ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Wafer">
                  {dataset.metadata.wafer_id ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Flow">
                  {dataset.metadata.flow_id ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Geometry">
                  {dataset.metadata.rows} × {dataset.metadata.columns}
                </Descriptions.Item>
                <Descriptions.Item label="Notch">
                  {dataset.metadata.notch ?? '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Soft Bins">
                  {dataset.bins.length}
                </Descriptions.Item>
                <Descriptions.Item label="Die Records">
                  {dataset.dies.length}
                </Descriptions.Item>
              </Descriptions>
            </div>
          )}

          {result.validation_issues.length > 0 && (
            <div className="section-card">
              <Typography.Title level={4}>数据校验</Typography.Title>
              <Table<ValidationIssue>
                rowKey={(issue) =>
                  `${issue.stage}-${issue.code}-${issue.source_file ?? ''}-${issue.row ?? ''}-${issue.column ?? ''}`
                }
                columns={issueColumns}
                dataSource={result.validation_issues}
                pagination={false}
                size="small"
                scroll={{ x: 760 }}
              />
            </div>
          )}
        </>
      )}
    </div>
  )
}

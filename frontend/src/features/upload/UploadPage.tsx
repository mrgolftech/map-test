import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import {
  Alert,
  Button,
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
import { FileSearch, UploadCloud } from 'lucide-react'
import { ApiError } from '../../api/client'
import { PageHeader } from '../../components/common/PageHeader'
import type { SourceDescriptor, ValidationIssue } from '../../types/wafer'
import { parseWaferFiles } from './api'

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
  const [fileList, setFileList] = useState<UploadFile[]>([])

  const mutation = useMutation({
    mutationFn: parseWaferFiles,
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
    },
    onRemove: () => {
      mutation.reset()
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
        description="上传 PAT / CP 文件，完成格式探测、严格解析、跨文件校验与标准 WaferDataset 组装。"
      />

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

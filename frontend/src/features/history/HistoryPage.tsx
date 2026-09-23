import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate, useSearch } from '@tanstack/react-router'
import {
  Alert,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  InputNumber,
  Popconfirm,
  Row,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from 'antd'
import { Eye, Filter, RotateCcw, Trash2 } from 'lucide-react'
import { PageHeader } from '../../components/common/PageHeader'
import type { AnalysisListItem } from '../../types/history'
import { deleteAnalysis, listAnalyses } from './api'

type FilterForm = {
  product_id?: string
  lot_id?: string
  wafer_id?: string
  created_from?: string
  created_to?: string
  yield_min_percent?: number
  yield_max_percent?: number
  main_fail_bin?: number
  pattern?: string
}

const patternOptions = [
  'EDGE',
  'CENTER',
  'RING',
  'TOP',
  'BOTTOM',
  'LEFT',
  'RIGHT',
  'QUADRANT',
  'LOCALIZED_CLUSTER',
  'LINE',
  'RANDOM',
].map((value) => ({ value, label: value }))

function displayPercent(value: number | null) {
  return value === null ? '—' : `${(value * 100).toFixed(2)}%`
}

function startOfDay(value?: string) {
  return value ? `${value}T00:00:00` : undefined
}

function endOfDay(value?: string) {
  return value ? `${value}T23:59:59` : undefined
}

function dateOnly(value?: string) {
  return value?.slice(0, 10)
}

export function HistoryPage() {
  const search = useSearch({ from: '/history' })
  const navigate = useNavigate({ from: '/history' })
  const queryClient = useQueryClient()
  const [form] = Form.useForm<FilterForm>()

  const query = useQuery({
    queryKey: ['history', search],
    queryFn: () => listAnalyses(search),
  })

  const removeMutation = useMutation({
    mutationFn: deleteAnalysis,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['history'] })
    },
  })

  const applyFilters = (values: FilterForm) => {
    navigate({
      search: {
        product_id: values.product_id?.trim() || undefined,
        lot_id: values.lot_id?.trim() || undefined,
        wafer_id: values.wafer_id?.trim() || undefined,
        created_from: startOfDay(values.created_from),
        created_to: endOfDay(values.created_to),
        yield_min:
          values.yield_min_percent === undefined
            ? undefined
            : values.yield_min_percent / 100,
        yield_max:
          values.yield_max_percent === undefined
            ? undefined
            : values.yield_max_percent / 100,
        main_fail_bin: values.main_fail_bin,
        pattern: values.pattern,
        page: 1,
        page_size: search.page_size,
      },
    })
  }

  const resetFilters = () => {
    form.resetFields()
    navigate({
      search: {
        page: 1,
        page_size: 20,
      },
    })
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 170,
      render: (value: string) => new Date(value).toLocaleString(),
    },
    { title: 'Product', dataIndex: 'product_id', key: 'product_id', width: 140 },
    { title: 'Lot', dataIndex: 'lot_id', key: 'lot_id', width: 120 },
    { title: 'Wafer', dataIndex: 'wafer_id', key: 'wafer_id', width: 90 },
    { title: 'Flow', dataIndex: 'flow_id', key: 'flow_id', width: 90 },
    {
      title: 'Yield',
      dataIndex: 'yield',
      key: 'yield',
      width: 100,
      align: 'right' as const,
      render: (value: number | null) => displayPercent(value),
    },
    {
      title: 'Main Fail',
      dataIndex: 'main_fail_bin',
      key: 'main_fail_bin',
      width: 100,
      render: (value: number | null) => value === null ? '—' : `Bin ${value}`,
    },
    {
      title: 'Pattern',
      dataIndex: 'main_pattern',
      key: 'main_pattern',
      width: 160,
      render: (value: string | null) => value ? <Tag>{value}</Tag> : '—',
    },
    {
      title: '校验',
      dataIndex: 'validation_status',
      key: 'validation_status',
      width: 90,
      render: (value: string) => (
        <Tag color={value === 'VALID' ? 'success' : 'warning'}>{value}</Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      fixed: 'right' as const,
      width: 150,
      render: (_: unknown, record: AnalysisListItem) => (
        <Space>
          <Button
            type="text"
            aria-label={`查看 ${record.wafer_id ?? record.id}`}
            icon={<Eye size={16} />}
            onClick={() =>
              navigate({
                to: '/analyses/$analysisId',
                params: { analysisId: record.id },
              })
            }
          />
          <Popconfirm
            title="删除分析记录？"
            description="删除后无法从历史记录恢复。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => removeMutation.mutate(record.id)}
          >
            <Button
              danger
              type="text"
              aria-label={`删除 ${record.wafer_id ?? record.id}`}
              icon={<Trash2 size={16} />}
            />
          </Popconfirm>
        </Space>
      ),
    },
  ]

  const initialValues: FilterForm = {
    product_id: search.product_id,
    lot_id: search.lot_id,
    wafer_id: search.wafer_id,
    created_from: dateOnly(search.created_from),
    created_to: dateOnly(search.created_to),
    yield_min_percent:
      search.yield_min === undefined ? undefined : search.yield_min * 100,
    yield_max_percent:
      search.yield_max === undefined ? undefined : search.yield_max * 100,
    main_fail_bin: search.main_fail_bin,
    pattern: search.pattern,
  }

  return (
    <div className="page-container">
      <PageHeader
        title="分析历史"
        description="检索、恢复和管理已经持久化的 Wafer 分析。"
      />

      <Card size="small" className="history-filter-card">
        <Form<FilterForm>
          form={form}
          layout="vertical"
          initialValues={initialValues}
          onFinish={applyFilters}
        >
          <Row gutter={[12, 0]}>
            <Col xs={24} md={8} xl={4}>
              <Form.Item label="Product" name="product_id">
                <Input allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} md={8} xl={4}>
              <Form.Item label="Lot" name="lot_id">
                <Input allowClear />
              </Form.Item>
            </Col>
            <Col xs={24} md={8} xl={4}>
              <Form.Item label="Wafer" name="wafer_id">
                <Input allowClear />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Form.Item label="Yield ≥ (%)" name="yield_min_percent">
                <InputNumber min={0} max={100} precision={2} className="full-width" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Form.Item label="Yield ≤ (%)" name="yield_max_percent">
                <InputNumber min={0} max={100} precision={2} className="full-width" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Form.Item label="Main Bin" name="main_fail_bin">
                <InputNumber min={1} precision={0} className="full-width" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={3}>
              <Form.Item label="Pattern" name="pattern">
                <Select allowClear options={patternOptions} />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={4}>
              <Form.Item label="开始日期" name="created_from">
                <Input type="date" />
              </Form.Item>
            </Col>
            <Col xs={12} md={6} xl={4}>
              <Form.Item label="结束日期" name="created_to">
                <Input type="date" />
              </Form.Item>
            </Col>
          </Row>
          <Space>
            <Button type="primary" htmlType="submit" icon={<Filter size={16} />}>
              筛选
            </Button>
            <Button icon={<RotateCcw size={16} />} onClick={resetFilters}>
              重置
            </Button>
          </Space>
        </Form>
      </Card>

      {query.isError && (
        <Alert
          className="section-block"
          type="error"
          showIcon
          message="历史记录加载失败"
          description={
            query.error instanceof Error
              ? query.error.message
              : '无法读取分析历史。'
          }
        />
      )}

      <div className="section-card">
        {query.data?.data.length === 0 && !query.isFetching ? (
          <Empty description="暂无符合条件的分析记录" />
        ) : (
          <Table<AnalysisListItem>
            rowKey="id"
            columns={columns}
            dataSource={query.data?.data ?? []}
            loading={query.isFetching}
            scroll={{ x: 1220 }}
            pagination={{
              current: search.page,
              pageSize: search.page_size,
              total: query.data?.meta.total ?? 0,
              showSizeChanger: true,
              pageSizeOptions: [10, 20, 50, 100],
              showTotal: (total) => `共 ${total} 条`,
              onChange: (page, pageSize) => {
                navigate({
                  search: {
                    ...search,
                    page,
                    page_size: pageSize,
                  },
                })
              },
            }}
          />
        )}
      </div>

      <Typography.Text type="secondary" className="history-note">
        列表只读取摘要字段；打开单片详情时才加载完整 WaferDataset 与 AnalysisSummary。
      </Typography.Text>
    </div>
  )
}

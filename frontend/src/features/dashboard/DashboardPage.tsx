import { useQuery } from '@tanstack/react-query'
import { Alert, Col, Row, Skeleton } from 'antd'
import { MetricCard } from '../../components/common/MetricCard'
import { PageHeader } from '../../components/common/PageHeader'
import { getDashboardSummary } from './api'

function percent(value: number | null) {
  return value === null ? '—' : `${(value * 100).toFixed(2)}%`
}

function range(minimum: number | null, maximum: number | null) {
  if (minimum === null || maximum === null) return '—'
  return `${(minimum * 100).toFixed(2)}% – ${(maximum * 100).toFixed(2)}%`
}

export function DashboardPage() {
  const query = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: getDashboardSummary,
  })

  if (query.isPending) {
    return (
      <div className="page-container">
        <PageHeader
          title="总览"
          description="Wafer 良率、Lot 与分析记录的统一入口。"
        />
        <Skeleton active paragraph={{ rows: 6 }} />
      </div>
    )
  }

  if (query.isError) {
    return (
      <div className="page-container">
        <PageHeader
          title="总览"
          description="Wafer 良率、Lot 与分析记录的统一入口。"
        />
        <Alert
          type="error"
          showIcon
          message="总览数据加载失败"
          description={
            query.error instanceof Error
              ? query.error.message
              : '无法读取持久化分析汇总。'
          }
        />
      </div>
    )
  }

  const summary = query.data.data

  return (
    <div className="page-container">
      <PageHeader
        title="总览"
        description="Wafer 良率、Lot 与分析记录的统一入口。"
      />
      <Row gutter={[12, 12]}>
        <Col xs={12} lg={6}>
          <MetricCard
            title="Wafer"
            value={summary.analysis_count}
            note="已持久化分析"
          />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard
            title="Lot"
            value={summary.lot_count}
            note="已记录批次"
          />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard
            title="Avg Yield"
            value={percent(summary.average_yield)}
            note="全部历史分析平均值"
          />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard
            title="Yield Range"
            value={range(summary.minimum_yield, summary.maximum_yield)}
            note="历史最小值 – 最大值"
          />
        </Col>
      </Row>

      {summary.analysis_count === 0 ? (
        <Alert
          className="section-block"
          type="info"
          showIcon
          message="暂无分析数据"
          description="上传 PAT / CP 文件，或从“新建分析”使用脱敏 Simulator 生成演示 Wafer / Lot。"
        />
      ) : (
        <Alert
          className="section-block"
          type="success"
          showIcon
          message="分析历史已就绪"
          description={
            summary.latest_created_at
              ? `最近一次分析：${new Date(summary.latest_created_at).toLocaleString()}`
              : '已有持久化分析记录。'
          }
        />
      )}
    </div>
  )
}

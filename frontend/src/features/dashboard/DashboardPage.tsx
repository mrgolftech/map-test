import { useQuery } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { Alert, Button, Card, Skeleton, Space, Tag, Typography } from 'antd'
import {
  ArrowRight,
  Boxes,
  CircleGauge,
  FlaskConical,
  Layers3,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
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
        <Skeleton active paragraph={{ rows: 8 }} />
      </div>
    )
  }

  if (query.isError) {
    return (
      <div className="page-container">
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
    <div className="page-container dashboard-page">
      <section className="dashboard-heading">
        <div>
          <Typography.Text className="page-kicker">概览</Typography.Text>
          <Typography.Title level={1}>晶圆分析中心</Typography.Title>
          <Typography.Paragraph type="secondary">
            从 MAP / CP 文件解析到空间模式识别、Lot 对比和 AI 辅助诊断，都在这里保持清晰可控。
          </Typography.Paragraph>
        </div>
        <Space wrap className="dashboard-heading-actions">
          <span className="service-status">
            <span className="service-status-dot" />
            分析服务运行中
          </span>
          <Link to="/upload">
            <Button type="primary" icon={<FlaskConical size={17} />}>
              新建分析
            </Button>
          </Link>
        </Space>
      </section>

      <section className="dashboard-stat-grid" aria-label="分析数据">
        <Link to="/history" search={{ page: 1, page_size: 20 }} className="dashboard-stat-item">
          <span className="dashboard-stat-icon blue"><Layers3 size={19} /></span>
          <span className="dashboard-stat-copy">
            <small>Wafer</small>
            <strong>{summary.analysis_count}</strong>
            <em>已持久化分析</em>
          </span>
          <ArrowRight className="dashboard-stat-arrow" size={17} />
        </Link>
        <Link to="/lots" className="dashboard-stat-item">
          <span className="dashboard-stat-icon green"><Boxes size={19} /></span>
          <span className="dashboard-stat-copy">
            <small>Lot</small>
            <strong>{summary.lot_count}</strong>
            <em>已记录批次</em>
          </span>
          <ArrowRight className="dashboard-stat-arrow" size={17} />
        </Link>
        <div className="dashboard-stat-item">
          <span className="dashboard-stat-icon purple"><TrendingUp size={19} /></span>
          <span className="dashboard-stat-copy">
            <small>平均良率</small>
            <strong>{percent(summary.average_yield)}</strong>
            <em>全部历史分析</em>
          </span>
        </div>
        <div className="dashboard-stat-item">
          <span className="dashboard-stat-icon orange"><CircleGauge size={19} /></span>
          <span className="dashboard-stat-copy">
            <small>良率区间</small>
            <strong className="dashboard-stat-range">
              {range(summary.minimum_yield, summary.maximum_yield)}
            </strong>
            <em>历史最小值 – 最大值</em>
          </span>
        </div>
      </section>

      <section className="dashboard-main-grid">
        <Card className="dashboard-focus-card" bordered={false}>
          <div className="dashboard-focus-top">
            <div>
              <Typography.Text className="card-kicker">重点入口</Typography.Text>
              <Typography.Title level={2}>从 Wafer Map 到可验证结论</Typography.Title>
              <Typography.Paragraph type="secondary">
                上传真实 PAT / CP，或先用脱敏 Simulator 演示。系统先计算确定性统计与空间特征，再把结构化事实交给 LLM 解释。
              </Typography.Paragraph>
            </div>
            <div className="dashboard-focus-mark">
              <Sparkles size={30} />
            </div>
          </div>
          <div className="dashboard-workflow">
            <span><b>01</b> 文件解析</span>
            <span><b>02</b> Wafer Map</span>
            <span><b>03</b> 空间分析</span>
            <span><b>04</b> AI 诊断</span>
          </div>
          <div className="dashboard-focus-footer">
            <span>
              {summary.analysis_count
                ? `已积累 ${summary.analysis_count} 个可追溯分析记录`
                : '尚无分析记录，可从演示数据开始'}
            </span>
            <Link to="/upload">
              开始分析 <ArrowRight size={15} />
            </Link>
          </div>
        </Card>

        <Card className="dashboard-side-card" bordered={false}>
          <Typography.Text className="card-kicker">系统状态</Typography.Text>
          <Typography.Title level={4}>分析工作区</Typography.Title>
          <div className="dashboard-status-list">
            <div>
              <span>历史数据</span>
              <Tag color={summary.analysis_count ? 'success' : 'default'}>
                {summary.analysis_count ? '已就绪' : '暂无数据'}
              </Tag>
            </div>
            <div>
              <span>最近分析</span>
              <strong>
                {summary.latest_created_at
                  ? new Date(summary.latest_created_at).toLocaleString()
                  : '—'}
              </strong>
            </div>
            <div>
              <span>确定性分析</span>
              <Tag color="processing">优先执行</Tag>
            </div>
            <div>
              <span>AI 分析</span>
              <Tag>按需调用</Tag>
            </div>
          </div>
          <Link to="/settings" className="dashboard-side-link">
            查看系统设置 <ArrowRight size={15} />
          </Link>
        </Card>
      </section>
    </div>
  )
}

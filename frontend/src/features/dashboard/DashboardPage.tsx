import { Alert, Col, Row } from 'antd'
import { MetricCard } from '../../components/common/MetricCard'
import { PageHeader } from '../../components/common/PageHeader'

export function DashboardPage() {
  return (
    <div className="page-container">
      <PageHeader
        title="总览"
        description="Wafer 良率、异常与分析记录的统一入口。"
      />
      <Row gutter={[12, 12]}>
        <Col xs={12} lg={6}>
          <MetricCard title="Wafer" value={0} note="已分析晶圆" />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard title="Lot" value={0} note="已记录批次" />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard title="Avg Yield" value="—" note="等待分析数据" />
        </Col>
        <Col xs={12} lg={6}>
          <MetricCard title="异常 Wafer" value={0} note="等待分析规则" />
        </Col>
      </Row>
      <Alert
        className="section-block"
        type="info"
        showIcon
        message="Phase 0 工程基线已就绪"
        description="Parser、Wafer Map 与空间分析将在后续阶段按既定路线逐步实现。"
      />
    </div>
  )
}

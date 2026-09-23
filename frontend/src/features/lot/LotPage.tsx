import { Empty } from 'antd'
import { PageHeader } from '../../components/common/PageHeader'

export function LotPage() {
  return (
    <div className="page-container">
      <PageHeader
        title="Lot / 多 Wafer"
        description="比较良率、Fail Bin 与空间模式趋势。"
      />
      <div className="section-card">
        <Empty description="多 Wafer / Lot 分析将在 Phase 4 实现" />
      </div>
    </div>
  )
}

import { Empty } from 'antd'
import { PageHeader } from '../../components/common/PageHeader'

export function HistoryPage() {
  return (
    <div className="page-container">
      <PageHeader
        title="分析历史"
        description="检索并恢复已保存的 Wafer 分析。"
      />
      <div className="section-card">
        <Empty description="历史记录将在 Phase 3 实现" />
      </div>
    </div>
  )
}

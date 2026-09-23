import { Empty } from 'antd'
import { PageHeader } from '../../components/common/PageHeader'

export function UploadPage() {
  return (
    <div className="page-container">
      <PageHeader
        title="新建分析"
        description="上传 PAT / CP 测试文件并生成标准 Wafer 数据。"
      />
      <div className="section-card">
        <Empty description="文件解析能力将在 Phase 1 实现" />
      </div>
    </div>
  )
}

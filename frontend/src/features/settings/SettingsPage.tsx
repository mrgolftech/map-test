import { Descriptions, Tag } from 'antd'
import { PageHeader } from '../../components/common/PageHeader'

export function SettingsPage() {
  return (
    <div className="page-container">
      <PageHeader
        title="系统设置"
        description="查看系统基线与后续 LLM 配置入口。"
      />
      <div className="section-card">
        <Descriptions
          column={{ xs: 1, md: 2 }}
          bordered
          size="small"
          title="Foundation"
        >
          <Descriptions.Item label="Frontend">
            React + TypeScript + Ant Design
          </Descriptions.Item>
          <Descriptions.Item label="Charts">Apache ECharts</Descriptions.Item>
          <Descriptions.Item label="Backend">
            FastAPI + SQLAlchemy
          </Descriptions.Item>
          <Descriptions.Item label="Persistence">
            SQLite + Alembic
          </Descriptions.Item>
          <Descriptions.Item label="AI">
            <Tag>Phase 5</Tag>
          </Descriptions.Item>
        </Descriptions>
      </div>
    </div>
  )
}

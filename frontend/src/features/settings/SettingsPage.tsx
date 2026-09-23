import { useMutation, useQuery } from '@tanstack/react-query'
import { Alert, Button, Descriptions, Space, Tag, Typography } from 'antd'
import { PlugZap } from 'lucide-react'
import { PageHeader } from '../../components/common/PageHeader'
import { getLLMConfig, testLLMConnection } from '../ai/api'

export function SettingsPage() {
  const configQuery = useQuery({
    queryKey: ['llm-config'],
    queryFn: getLLMConfig,
  })
  const testMutation = useMutation({
    mutationFn: testLLMConnection,
  })

  const config = configQuery.data?.data

  return (
    <div className="page-container">
      <PageHeader
        title="系统设置"
        description="查看平台运行基线与服务端 LLM 配置状态。"
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
        </Descriptions>
      </div>

      <div className="section-card">
        <Space direction="vertical" size={12} className="ai-report-stack">
          <Typography.Title level={5}>LLM / AI</Typography.Title>

          {configQuery.isError && (
            <Alert
              type="error"
              showIcon
              message="LLM 配置状态读取失败"
              description={configQuery.error instanceof Error
                ? configQuery.error.message
                : '无法读取服务端 LLM 配置。'}
            />
          )}

          <Descriptions
            column={{ xs: 1, md: 2 }}
            bordered
            size="small"
            loading={configQuery.isPending}
          >
            <Descriptions.Item label="状态">
              <Tag color={config?.configured ? 'success' : 'default'}>
                {config?.configured ? '已配置' : '未配置'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="API Key">
              <Tag color={config?.api_key_configured ? 'success' : 'default'}>
                {config?.api_key_configured ? '服务端已设置' : '未设置'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Base URL">
              {config?.base_url ?? '—'}
            </Descriptions.Item>
            <Descriptions.Item label="Model">
              {config?.model ?? '—'}
            </Descriptions.Item>
          </Descriptions>

          <Alert
            type="info"
            showIcon
            message="API Key 仅通过服务器环境变量配置"
            description="前端不会读取、显示或保存 LLM_API_KEY。修改配置后重启服务使环境变量生效。"
          />

          <Space wrap>
            <Button
              type="primary"
              icon={<PlugZap size={16} />}
              disabled={!config?.configured}
              loading={testMutation.isPending}
              onClick={() => testMutation.mutate()}
            >
              测试 LLM 连接
            </Button>
            {testMutation.data && (
              <Tag color="success">
                {testMutation.data.data.model} · 连接成功
              </Tag>
            )}
          </Space>

          {testMutation.isError && (
            <Alert
              type="error"
              showIcon
              message="LLM 连接测试失败"
              description={testMutation.error instanceof Error
                ? testMutation.error.message
                : '无法连接 LLM Provider。'}
            />
          )}
        </Space>
      </div>
    </div>
  )
}

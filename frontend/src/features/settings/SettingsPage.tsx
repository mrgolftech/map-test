import { useEffect, useRef } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, AutoComplete, Button, Descriptions, Form, Input, Space, Tag, Typography } from 'antd'
import { PlugZap } from 'lucide-react'
import { PageHeader } from '../../components/common/PageHeader'
import { fetchLLMModels, getLLMConfig, saveLLMConfig, testLLMConnection } from '../ai/api'

type LLMFormValues = { base_url: string; model: string; api_key?: string }

export function SettingsPage() {
  const [form] = Form.useForm<LLMFormValues>()
  const initialized = useRef(false)
  const queryClient = useQueryClient()
  const configQuery = useQuery({ queryKey: ['llm-config'], queryFn: getLLMConfig })
  const modelsMutation = useMutation({
    mutationFn: (values: LLMFormValues) => fetchLLMModels(
      { base_url: values.base_url, api_key: values.api_key || undefined },
    ),
  })
  const testMutation = useMutation({
    mutationFn: (values: LLMFormValues) => testLLMConnection(
      { base_url: values.base_url, model: values.model, api_key: values.api_key || undefined },
    ),
  })
  const saveMutation = useMutation({
    mutationFn: (values: LLMFormValues) => saveLLMConfig(
      { base_url: values.base_url, model: values.model, api_key: values.api_key || undefined },
    ),
    onSuccess: () => {
      form.setFieldValue('api_key', undefined)
      void queryClient.invalidateQueries({ queryKey: ['llm-config'] })
    },
  })

  const config = configQuery.data?.data
  useEffect(() => {
    if (config && !initialized.current) {
      initialized.current = true
      if (!form.isFieldTouched('base_url')) form.setFieldValue('base_url', config.base_url ?? '')
      if (!form.isFieldTouched('model')) form.setFieldValue('model', config.model ?? '')
    }
  }, [config, form])

  function fetchModels() {
    void form.validateFields(['base_url'])
      .then(() => modelsMutation.mutate(form.getFieldsValue()))
      .catch(() => undefined)
  }

  function testModel() {
    void form.validateFields(['base_url', 'model'])
      .then(() => testMutation.mutate(form.getFieldsValue()))
      .catch(() => undefined)
  }

  const models = modelsMutation.data?.data ?? []
  return (
    <div className="page-container">
      <PageHeader title="系统设置" description="配置服务端 LLM，拉取模型列表并验证选定模型。" />
      <div className="section-card">
        <Descriptions column={{ xs: 1, md: 2 }} bordered size="small" title="Foundation">
          <Descriptions.Item label="Frontend">React + TypeScript + Ant Design</Descriptions.Item>
          <Descriptions.Item label="Charts">Apache ECharts</Descriptions.Item>
          <Descriptions.Item label="Backend">FastAPI + SQLAlchemy</Descriptions.Item>
          <Descriptions.Item label="Persistence">SQLite + Alembic</Descriptions.Item>
        </Descriptions>
      </div>
      <div className="section-card">
        <Space direction="vertical" size={16} className="ai-report-stack">
          <Typography.Title level={5}>LLM / AI</Typography.Title>
          {configQuery.isError && <Alert type="error" showIcon message="配置状态读取失败" />}
          <Descriptions column={{ xs: 1, md: 2 }} bordered size="small">
            <Descriptions.Item label="状态">
              <Tag color={config?.configured ? 'success' : 'default'}>{config?.configured ? '已配置' : '未配置'}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="API Key">
              <Tag color={config?.api_key_configured ? 'success' : 'default'}>
                {config?.api_key_configured ? '服务端已保存' : '未设置'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Base URL">{config?.base_url ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="模型">{config?.model ?? '—'}</Descriptions.Item>
          </Descriptions>
          <Alert
            type="info"
            showIcon
            message="配置受管理员登录保护"
            description="API Key 只在服务端保存并加密，不会从接口回显。LLM_SETTINGS_ADMIN_TOKEN 仅作为服务端加密密钥使用，不再需要在浏览器中重复输入。"
          />
          <Form form={form} layout="vertical" onFinish={(values) => saveMutation.mutate(values)}>
            <Form.Item label="接入类型"><Input value="OpenAI-compatible API" readOnly /></Form.Item>
            <Form.Item name="base_url" label="API Base URL"
              rules={[{ required: true, type: 'url', message: '请输入完整的 http(s) URL，如 https://example.com/v1' }]}>
              <Input placeholder="https://example.com/v1" autoComplete="off" />
            </Form.Item>
            <Form.Item name="api_key" label="API Key"
              extra={config?.api_key_configured ? '留空则沿用该 URL 已保存的密钥；切换 URL 时必须输入新密钥。' : '输入上游 API Key。'}>
              <Input.Password autoComplete="new-password" placeholder="输入密钥，保存后清空" />
            </Form.Item>
            <Form.Item name="model" label="模型名称 / 类型" rules={[{ required: true, message: '请选择或输入模型 ID' }]}>
              <AutoComplete options={models.map((value) => ({ value }))}
                placeholder="先拉取模型列表，或手动输入模型 ID" filterOption />
            </Form.Item>
            <Space wrap>
              <Button onClick={fetchModels} loading={modelsMutation.isPending}>拉取 /v1/models</Button>
              <Button icon={<PlugZap size={16} />} onClick={testModel} loading={testMutation.isPending}>测试选定模型</Button>
              <Button type="primary" htmlType="submit" loading={saveMutation.isPending}>保存配置</Button>
              {modelsMutation.isSuccess && <Tag color="success">获取 {models.length} 个模型</Tag>}
              {testMutation.isSuccess && <Tag color="success">{testMutation.data.data.model} · 连通成功</Tag>}
              {saveMutation.isSuccess && <Tag color="success">已保存</Tag>}
            </Space>
          </Form>
          {modelsMutation.isError && <Alert type="error" showIcon message="拉取模型失败" description={modelsMutation.error.message} />}
          {testMutation.isError && <Alert type="error" showIcon message="模型连通测试失败" description={testMutation.error.message} />}
          {saveMutation.isError && <Alert type="error" showIcon message="保存配置失败" description={saveMutation.error.message} />}
        </Space>
      </div>
    </div>
  )
}

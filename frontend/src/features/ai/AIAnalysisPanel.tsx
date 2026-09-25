import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Empty,
  Flex,
  Progress,
  Space,
  Tag,
  Typography,
} from 'antd'
import { Bot, RefreshCw } from 'lucide-react'
import type { AIReport } from '../../types/ai'
import { AIChatPanel } from './AIChatPanel'
import { analyzeWithAI, getLLMConfig } from './api'

type AIAnalysisPanelProps = {
  analysisId: string
  initialReport?: AIReport | null
  initialModel?: string | null
  initialGeneratedAt?: string | null
}

function findingColor(kind: string) {
  if (kind === 'FACT') return 'blue'
  if (kind === 'JUDGMENT') return 'purple'
  if (kind === 'HYPOTHESIS') return 'gold'
  return 'green'
}

function ReportView({
  report,
  model,
}: {
  report: AIReport
  model: string
}) {
  return (
    <Space direction="vertical" size={12} className="ai-report-stack">
      <Alert
        type="info"
        showIcon
        message="AI 是解释层，不替代确定性统计"
        description="事实与空间指标来自平台算法；可能原因均为待验证假设，不能视为已确认根因。"
      />

      <Card
        size="small"
        title="Executive Summary"
        extra={<Tag>{model}</Tag>}
      >
        <Typography.Paragraph>
          {report.executive_summary}
        </Typography.Paragraph>
        <Flex gap={12} align="center">
          <Typography.Text type="secondary">AI 置信度</Typography.Text>
          <Progress
            percent={Math.round(report.confidence * 100)}
            size="small"
            className="ai-confidence"
          />
        </Flex>
      </Card>

      <Card size="small" title="关键发现">
        <Space direction="vertical" size={10} className="ai-report-stack">
          {report.key_findings.map((item, index) => (
            <div key={`${item.kind}-${item.title}-${index}`} className="ai-report-item">
              <Flex gap={8} align="flex-start">
                <Tag color={findingColor(item.kind)}>{item.kind}</Tag>
                <div>
                  <Typography.Text strong>{item.title}</Typography.Text>
                  <Typography.Paragraph className="ai-report-detail">
                    {item.detail}
                  </Typography.Paragraph>
                  {item.evidence.length > 0 && (
                    <Typography.Text type="secondary">
                      依据：{item.evidence.join('；')}
                    </Typography.Text>
                  )}
                </div>
              </Flex>
            </div>
          ))}
        </Space>
      </Card>

      <Card size="small" title="空间模式解释">
        {report.spatial_patterns.length === 0 ? (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="无额外空间模式解释" />
        ) : (
          <Space direction="vertical" size={10} className="ai-report-stack">
            {report.spatial_patterns.map((item, index) => (
              <div key={`${item.title}-${index}`} className="ai-report-item">
                <Tag color="purple">判断</Tag>
                <Typography.Text strong>{item.title}</Typography.Text>
                <Typography.Paragraph className="ai-report-detail">
                  {item.detail}
                </Typography.Paragraph>
                <Typography.Text type="secondary">
                  依据：{item.evidence.join('；')}
                </Typography.Text>
              </div>
            ))}
          </Space>
        )}
      </Card>

      <Card size="small" title="可能原因">
        <Space direction="vertical" size={10} className="ai-report-stack">
          {report.possible_causes.map((item, index) => (
            <div key={`${item.title}-${index}`} className="ai-report-item">
              <Tag color="gold">假设</Tag>
              <Typography.Text strong>{item.title}</Typography.Text>
              <Typography.Paragraph className="ai-report-detail">
                {item.detail}
              </Typography.Paragraph>
              <Typography.Text type="secondary">
                推断依据：{item.rationale}
              </Typography.Text>
            </div>
          ))}
        </Space>
      </Card>

      <Card size="small" title="建议验证动作">
        <Space direction="vertical" size={10} className="ai-report-stack">
          {report.recommended_checks.map((item, index) => (
            <div key={`${item.title}-${index}`} className="ai-report-item">
              <Tag color="green">建议</Tag>
              <Typography.Text strong>{item.title}</Typography.Text>
              <Typography.Paragraph className="ai-report-detail">
                {item.action}
              </Typography.Paragraph>
              {item.expected_evidence && (
                <Typography.Text type="secondary">
                  预期证据：{item.expected_evidence}
                </Typography.Text>
              )}
            </div>
          ))}
        </Space>
      </Card>

      {report.limitations.length > 0 && (
        <Alert
          type="warning"
          showIcon
          message="AI 分析限制"
          description={
            <ul className="lot-limitations">
              {report.limitations.map((item) => <li key={item}>{item}</li>)}
            </ul>
          }
        />
      )}
    </Space>
  )
}

export function AIAnalysisPanel({
  analysisId,
  initialReport = null,
  initialModel = null,
  initialGeneratedAt = null,
}: AIAnalysisPanelProps) {
  const queryClient = useQueryClient()
  const configQuery = useQuery({
    queryKey: ['llm-config'],
    queryFn: getLLMConfig,
  })
  const mutation = useMutation({
    mutationFn: () => analyzeWithAI(analysisId),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['analysis', analysisId] })
    },
  })

  const report = mutation.data?.data.report ?? initialReport
  const model = mutation.data?.data.model
    ?? initialModel
    ?? configQuery.data?.data.model
    ?? '—'
  const configured = configQuery.data?.data.configured ?? false

  if (configQuery.isPending && !report) {
    return <Typography.Text type="secondary">正在读取 AI 配置…</Typography.Text>
  }

  if (configQuery.isError && !report) {
    return (
      <Alert
        type="error"
        showIcon
        message="无法读取 AI 配置"
        description={configQuery.error instanceof Error
          ? configQuery.error.message
          : 'AI 配置状态不可用。'}
      />
    )
  }

  if (!configured && !report && !configQuery.isPending) {
    return (
      <Alert
        type="info"
        showIcon
        message="AI 尚未配置"
        description="请在服务器环境变量中设置 LLM_BASE_URL、LLM_API_KEY 和 LLM_MODEL。核心 Wafer 分析不受影响。"
      />
    )
  }

  return (
    <Space direction="vertical" size={12} className="ai-report-stack">
      <Flex justify="space-between" align="center" wrap gap={8}>
        <Space direction="vertical" size={0}>
          <Space>
            <Bot size={18} />
            <Typography.Text>
              模型：{model}
            </Typography.Text>
          </Space>
          {initialGeneratedAt && !mutation.data && (
            <Typography.Text type="secondary">
              已保存：{new Date(initialGeneratedAt).toLocaleString()}
            </Typography.Text>
          )}
        </Space>
        {configured && (
          <Button
            type="primary"
            icon={report ? <RefreshCw size={16} /> : <Bot size={16} />}
            loading={mutation.isPending}
            onClick={() => mutation.mutate()}
          >
            {report ? '重新 AI 分析' : '生成 AI 分析'}
          </Button>
        )}
      </Flex>

      {!configured && report && (
        <Alert
          type="info"
          showIcon
          message="当前 LLM 未配置"
          description="正在显示历史中已保存的 AI 报告；重新生成需要先配置服务端 LLM。"
        />
      )}

      {mutation.isError && (
        <Alert
          type="error"
          showIcon
          message="AI 分析失败"
          description={mutation.error instanceof Error
            ? mutation.error.message
            : 'LLM 调用失败；确定性分析仍可正常使用。'}
        />
      )}

      {!report && !mutation.isPending && !mutation.isError && (
        <Empty
          image={Empty.PRESENTED_IMAGE_SIMPLE}
          description="点击“生成 AI 分析”，基于当前已保存的确定性统计生成解释与排查建议。"
        />
      )}

      {report && (
        <ReportView
          report={report}
          model={model}
        />
      )}
      <AIChatPanel analysisId={analysisId} reportReady={Boolean(report)} />
    </Space>
  )
}

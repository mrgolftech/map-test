import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Collapse,
  Empty,
  Flex,
  Input,
  Space,
  Tag,
  Typography,
} from 'antd'
import { MessageCircle, Send } from 'lucide-react'
import { getLLMConfig } from './api'
import {
  askAnalysisChat,
  askComparisonChat,
  getAnalysisChat,
  getComparisonChat,
  type ChatMessage,
} from './chatApi'

type AIChatPanelProps = {
  analysisId?: string
  analysisIds?: string[]
  reportReady?: boolean
}

const EMPTY_MESSAGES: ChatMessage[] = []

function questionFor(messages: ChatMessage[], assistantIndex: number) {
  return messages[assistantIndex - 1]?.role === 'user'
    ? messages[assistantIndex - 1].content
    : '追问'
}

export function AIChatPanel({
  analysisId,
  analysisIds = [],
  reportReady = true,
}: AIChatPanelProps) {
  const [question, setQuestion] = useState('')
  const queryClient = useQueryClient()
  const comparison = !analysisId
  const contextKey = comparison ? [...analysisIds].sort().join(',') : analysisId
  const enabled = comparison
    ? analysisIds.length >= 2
    : Boolean(analysisId && reportReady)

  const configQuery = useQuery({
    queryKey: ['llm-config'],
    queryFn: getLLMConfig,
  })
  const threadQuery = useQuery({
    queryKey: ['ai-chat', comparison ? 'comparison' : 'analysis', contextKey],
    queryFn: () => comparison
      ? getComparisonChat(analysisIds)
      : getAnalysisChat(analysisId as string),
    enabled,
  })
  const mutation = useMutation({
    mutationFn: () => comparison
      ? askComparisonChat(analysisIds, question.trim())
      : askAnalysisChat(analysisId as string, question.trim()),
    onSuccess: async () => {
      setQuestion('')
      await queryClient.invalidateQueries({
        queryKey: ['ai-chat', comparison ? 'comparison' : 'analysis', contextKey],
      })
    },
  })

  const messages = threadQuery.data?.data.messages ?? EMPTY_MESSAGES
  const items = useMemo(() => {
    const answerIndexes = messages
      .map((message, index) => message.role === 'assistant' ? index : -1)
      .filter((index) => index >= 0)
    return answerIndexes.map((index) => {
      const answer = messages[index]
      const questionText = questionFor(messages, index)
      return {
        key: answer.id,
        label: (
          <Flex justify="space-between" gap={12} wrap>
            <Typography.Text ellipsis={{ tooltip: questionText }}>
              {questionText}
            </Typography.Text>
            <Typography.Text type="secondary">
              {new Date(answer.created_at).toLocaleString()}
            </Typography.Text>
          </Flex>
        ),
        children: (
          <Space direction="vertical" size={10} className="ai-chat-turn">
            <Typography.Paragraph className="ai-chat-answer">
              {answer.content}
            </Typography.Paragraph>
            {answer.insufficient_evidence && (
              <Alert
                type="warning"
                showIcon
                message="现有证据不足以支持完整结论"
                description={answer.limitations.length > 0
                  ? answer.limitations.join('；')
                  : '回答已标明缺少的证据，请补充生产记录或复测数据后再判断。'}
              />
            )}
            {answer.citations.length > 0 && (
              <div>
                <Typography.Text type="secondary">引用指标</Typography.Text>
                <Flex gap={6} wrap className="ai-chat-citations">
                  {answer.citations.map((citation) => (
                    <Tag key={citation.id}>
                      {citation.label}：{citation.value}
                    </Tag>
                  ))}
                </Flex>
              </div>
            )}
            {answer.model && (
              <Typography.Text type="secondary" className="ai-chat-model">
                模型：{answer.model}
              </Typography.Text>
            )}
          </Space>
        ),
      }
    })
  }, [messages])

  if (!enabled) {
    return (
      <Card size="small" title="基于报告追问">
        <Alert
          type="info"
          showIcon
          message={comparison ? '请选择至少两片 Wafer' : '请先生成 AI 分析报告'}
          description={comparison
            ? '选择 Wafer 或进入一个 Lot 后，可针对所选数据提问。'
            : '报告保存后，可以围绕报告结论、Bin 分布和空间指标继续提问。'}
        />
      </Card>
    )
  }

  return (
    <Card
      size="small"
      title={(
        <Space>
          <MessageCircle size={17} />
          <span>{comparison ? '多 Wafer / Lot 对比问答' : '基于报告追问'}</span>
        </Space>
      )}
    >
      <Space direction="vertical" size={12} className="ai-chat-stack">
        {configQuery.data?.data.configured === false && (
          <Alert
            type="warning"
            showIcon
            message="LLM 尚未配置，暂时无法提问"
            description="请先在系统设置中配置并测试模型连接。已保存的问答仍可查看。"
          />
        )}
        {configQuery.isError && (
          <Alert type="error" showIcon message="无法读取 LLM 配置状态" />
        )}
        {threadQuery.isError && (
          <Alert
            type="error"
            showIcon
            message="问答记录加载失败"
            description={threadQuery.error instanceof Error
              ? threadQuery.error.message
              : '无法加载当前问答。'}
          />
        )}
        {items.length > 0 ? (
          <Collapse
            items={items}
            defaultActiveKey={[items[items.length - 1].key]}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="还没有提问记录"
          />
        )}
        {mutation.isError && (
          <Alert
            type="error"
            showIcon
            message="提问失败"
            description={mutation.error instanceof Error
              ? mutation.error.message
              : 'LLM 调用失败，请稍后重试。'}
          />
        )}
        <Input.TextArea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onPressEnter={(event) => {
            if (!event.shiftKey) {
              event.preventDefault()
              if (question.trim() && !mutation.isPending) mutation.mutate()
            }
          }}
          maxLength={2000}
          showCount
          autoSize={{ minRows: 3, maxRows: 7 }}
          placeholder={comparison
            ? '例如：良率下降主要发生在哪几片？Bin18 是否持续增加？'
            : '例如：Bin18 的聚集证据是什么？哪些根因还无法确认？'}
          disabled={configQuery.data?.data.configured === false || mutation.isPending}
          aria-label="输入追问"
        />
        <Flex justify="space-between" align="center" wrap gap={8}>
          <Typography.Text type="secondary">
            回答仅基于当前已选分析数据；具体指标会附带引用。
          </Typography.Text>
          <Button
            type="primary"
            icon={<Send size={15} />}
            loading={mutation.isPending}
            disabled={!question.trim() || configQuery.data?.data.configured === false}
            onClick={() => mutation.mutate()}
          >
            发送
          </Button>
        </Flex>
      </Space>
    </Card>
  )
}

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { Alert, Button, Empty, Popconfirm, Skeleton, Space } from 'antd'
import { History, Trash2 } from 'lucide-react'
import { AIAnalysisPanel } from '../ai/AIAnalysisPanel'
import { WaferPage } from '../wafer/WaferPage'
import { deleteAnalysis, getAnalysis } from './api'

type AnalysisDetailPageProps = {
  analysisId: string
}

export function AnalysisDetailPage({
  analysisId,
}: AnalysisDetailPageProps) {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const query = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysis(analysisId),
    enabled: Boolean(analysisId),
  })

  const deleteMutation = useMutation({
    mutationFn: () => deleteAnalysis(analysisId),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['history'] }),
        queryClient.removeQueries({ queryKey: ['analysis', analysisId] }),
      ])
      navigate({ to: '/history', search: { page: 1, page_size: 20 } })
    },
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
          message="分析记录加载失败"
          description={
            query.error instanceof Error
              ? query.error.message
              : '无法加载该分析记录。'
          }
        />
      </div>
    )
  }

  if (!query.data) {
    return (
      <div className="page-container">
        <Empty description="分析记录不存在" />
      </div>
    )
  }

  return (
    <WaferPage
      workspace={{
        dataset: query.data.data.dataset,
        analysis: query.data.data.analysis,
      }}
      extraTabs={[
        {
          key: 'ai',
          label: 'AI 分析',
          children: <AIAnalysisPanel analysisId={analysisId} />,
        },
      ]}
      extraActions={(
        <Space wrap>
          <Button
            icon={<History size={16} />}
            onClick={() =>
              navigate({
                to: '/history',
                search: { page: 1, page_size: 20 },
              })
            }
          >
            返回历史
          </Button>
          <Popconfirm
            title="删除这条分析记录？"
            description="删除后无法从历史记录恢复。"
            okText="删除"
            cancelText="取消"
            okButtonProps={{ danger: true }}
            onConfirm={() => deleteMutation.mutate()}
          >
            <Button
              danger
              icon={<Trash2 size={16} />}
              loading={deleteMutation.isPending}
            >
              删除记录
            </Button>
          </Popconfirm>
        </Space>
      )}
    />
  )
}

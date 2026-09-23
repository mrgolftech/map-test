import { useQuery } from '@tanstack/react-query'
import { Alert, Empty, Skeleton } from 'antd'
import { getAnalysis } from './api'
import { WaferPage } from '../wafer/WaferPage'

type AnalysisDetailPageProps = {
  analysisId: string
}

export function AnalysisDetailPage({
  analysisId,
}: AnalysisDetailPageProps) {
  const query = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysis(analysisId),
    enabled: Boolean(analysisId),
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
    />
  )
}

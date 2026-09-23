import { Card, Statistic, Typography } from 'antd'

type MetricCardProps = {
  title: string
  value: string | number
  note: string
}

export function MetricCard({ title, value, note }: MetricCardProps) {
  return (
    <Card size="small" className="metric-card">
      <Statistic title={title} value={value} />
      <Typography.Text type="secondary" className="metric-note">
        {note}
      </Typography.Text>
    </Card>
  )
}

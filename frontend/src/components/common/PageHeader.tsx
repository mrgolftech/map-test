import type { ReactNode } from 'react'
import { Flex, Typography } from 'antd'

type PageHeaderProps = {
  title: string
  description?: string
  actions?: ReactNode
}

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <Flex
      className="page-header"
      align="flex-start"
      justify="space-between"
      gap={16}
      wrap
    >
      <div>
        <Typography.Title level={2} className="page-title">
          {title}
        </Typography.Title>
        {description && (
          <Typography.Paragraph type="secondary" className="page-description">
            {description}
          </Typography.Paragraph>
        )}
      </div>
      {actions && <div>{actions}</div>}
    </Flex>
  )
}

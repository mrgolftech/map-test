import { useEffect, type PropsWithChildren } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Alert, Button, Card, Form, Input, Skeleton, Space, Typography } from 'antd'
import { LockKeyhole } from 'lucide-react'
import { ProductBrand } from '../../components/common/ProductBrand'
import { getAdminSession, loginAdmin } from './api'

type LoginValues = {
  username: string
  password: string
}

export function AuthGate({ children }: PropsWithChildren) {
  const queryClient = useQueryClient()
  const sessionQuery = useQuery({
    queryKey: ['admin-session'],
    queryFn: getAdminSession,
    staleTime: 60_000,
  })
  const loginMutation = useMutation({
    mutationFn: loginAdmin,
    onSuccess: (response) => {
      queryClient.setQueryData(['admin-session'], response)
    },
  })

  useEffect(() => {
    const handleExpired = () => {
      void queryClient.invalidateQueries({ queryKey: ['admin-session'] })
    }
    window.addEventListener('wafer-auth-expired', handleExpired)
    return () => window.removeEventListener('wafer-auth-expired', handleExpired)
  }, [queryClient])

  if (sessionQuery.isPending) {
    return (
      <div className="login-shell">
        <Card className="login-card">
          <Skeleton active paragraph={{ rows: 4 }} />
        </Card>
      </div>
    )
  }

  if (sessionQuery.isError) {
    return (
      <div className="login-shell">
        <Card className="login-card">
          <Space direction="vertical" size={16} className="full-width">
            <ProductBrand />
            <Alert
              type="error"
              showIcon
              message="无法读取登录状态"
              description={sessionQuery.error.message}
            />
            <Button onClick={() => void sessionQuery.refetch()}>重试</Button>
          </Space>
        </Card>
      </div>
    )
  }

  if (sessionQuery.data.data.authenticated) {
    return children
  }

  const configured = sessionQuery.data.data.configured

  return (
    <div className="login-shell">
      <Card className="login-card" bordered={false}>
        <Space direction="vertical" size={20} className="full-width">
          <ProductBrand />
          <div>
            <Typography.Title level={3} className="login-title">
              管理员登录
            </Typography.Title>
            <Typography.Paragraph type="secondary" className="login-description">
              登录后可访问晶圆解析、Wafer Map、Lot 对比、AI 分析与系统设置。
            </Typography.Paragraph>
          </div>
          {!configured && (
            <Alert
              type="warning"
              showIcon
              message="管理员登录尚未配置"
              description="请在服务端设置 ADMIN_PASSWORD 和至少 32 字符的 ADMIN_SESSION_SECRET 后重启。"
            />
          )}
          <Form<LoginValues>
            layout="vertical"
            initialValues={{ username: 'admin' }}
            onFinish={(values) => loginMutation.mutate(values)}
          >
            <Form.Item
              name="username"
              label="用户名"
              rules={[{ required: true, message: '请输入管理员用户名' }]}
            >
              <Input
                autoComplete="username"
                disabled={!configured}
                prefix={<LockKeyhole size={16} />}
              />
            </Form.Item>
            <Form.Item
              name="password"
              label="密码"
              rules={[{ required: true, message: '请输入管理员密码' }]}
            >
              <Input.Password
                autoComplete="current-password"
                disabled={!configured}
              />
            </Form.Item>
            {loginMutation.isError && (
              <Alert
                className="login-error"
                type="error"
                showIcon
                message="登录失败"
                description={loginMutation.error.message}
              />
            )}
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              disabled={!configured}
              loading={loginMutation.isPending}
            >
              登录
            </Button>
          </Form>
        </Space>
      </Card>
    </div>
  )
}

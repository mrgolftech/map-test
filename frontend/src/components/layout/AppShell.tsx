import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link, Outlet, useRouterState } from '@tanstack/react-router'
import { Button, Drawer, Grid, Layout, Menu, Space, Typography } from 'antd'
import {
  BarChart3,
  Database,
  FlaskConical,
  History,
  LogOut,
  Menu as MenuIcon,
  Moon,
  Settings,
  Sun,
} from 'lucide-react'
import { useAppTheme } from '../../app/theme'
import { logoutAdmin } from '../../features/auth/api'
import { ProductBrand } from '../common/ProductBrand'

const { Header, Content } = Layout

const navigation = [
  { key: '/', label: <Link to="/">总览</Link>, icon: <BarChart3 size={17} /> },
  {
    key: '/upload',
    label: <Link to="/upload">新建分析</Link>,
    icon: <FlaskConical size={17} />,
  },
  {
    key: '/history',
    label: (
      <Link to="/history" search={{ page: 1, page_size: 20 }}>
        分析历史
      </Link>
    ),
    icon: <History size={17} />,
  },
  {
    key: '/lots',
    label: <Link to="/lots">Lot / 多 Wafer</Link>,
    icon: <Database size={17} />,
  },
  {
    key: '/settings',
    label: <Link to="/settings">系统设置</Link>,
    icon: <Settings size={17} />,
  },
]

function activeNavigationKey(pathname: string) {
  if (pathname.startsWith('/analyses/')) return '/history'
  const match = navigation.find((item) =>
    item.key === '/' ? pathname === '/' : pathname.startsWith(item.key),
  )
  return match?.key ?? '/'
}

function NavigationMenu({
  mode,
  onNavigate,
}: {
  mode: 'horizontal' | 'inline'
  onNavigate?: () => void
}) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  return (
    <Menu
      mode={mode}
      selectedKeys={[activeNavigationKey(pathname)]}
      items={navigation}
      onClick={() => onNavigate?.()}
      className={mode === 'horizontal' ? 'app-nav-menu' : undefined}
    />
  )
}

export function AppShell() {
  const screens = Grid.useBreakpoint()
  const mobile = !screens.lg
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { mode, toggleTheme } = useAppTheme()
  const queryClient = useQueryClient()
  const logoutMutation = useMutation({
    mutationFn: logoutAdmin,
    onSuccess: (response) => {
      queryClient.setQueryData(['admin-session'], response)
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'admin-session' })
    },
  })

  return (
    <Layout className="app-shell">
      <Header className="app-topbar">
        <div className="app-topbar-inner">
          <div className="app-topbar-main">
            <Link to="/" className="brand-link" aria-label="返回总览">
              <ProductBrand />
            </Link>
            <Space size={4} className="app-topbar-actions">
              <Button
                aria-label="切换主题"
                type="text"
                icon={mode === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
                onClick={toggleTheme}
              >
                {!mobile && (mode === 'dark' ? '亮色' : '暗色')}
              </Button>
              <Button
                aria-label="退出登录"
                type="text"
                icon={<LogOut size={18} />}
                loading={logoutMutation.isPending}
                onClick={() => logoutMutation.mutate()}
              >
                {!mobile && '退出'}
              </Button>
              {mobile && (
                <Button
                  aria-label="打开导航"
                  type="text"
                  icon={<MenuIcon size={20} />}
                  onClick={() => setDrawerOpen(true)}
                />
              )}
            </Space>
          </div>
          {!mobile && (
            <nav className="app-nav" aria-label="主导航">
              <NavigationMenu mode="horizontal" />
            </nav>
          )}
        </div>
      </Header>

      <Content className="app-content">
        <Outlet />
      </Content>

      <Drawer
        title={<ProductBrand />}
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={288}
        styles={{ body: { padding: 0 } }}
      >
        <NavigationMenu mode="inline" onNavigate={() => setDrawerOpen(false)} />
        <div className="mobile-nav-caption">
          <Typography.Text type="secondary">
            晶圆解析 · 空间分析 · AI 辅助诊断
          </Typography.Text>
        </div>
      </Drawer>
    </Layout>
  )
}

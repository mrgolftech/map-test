import { useState } from 'react'
import { Link, Outlet, useRouterState } from '@tanstack/react-router'
import { Button, Drawer, Grid, Layout, Menu, Space, Typography } from 'antd'
import {
  BarChart3,
  Database,
  FlaskConical,
  History,
  Menu as MenuIcon,
  Moon,
  Settings,
  Sun,
} from 'lucide-react'
import { useAppTheme } from '../../app/theme'

const { Header, Sider, Content } = Layout

const navigation = [
  { key: '/', label: <Link to="/">总览</Link>, icon: <BarChart3 size={18} /> },
  {
    key: '/upload',
    label: <Link to="/upload">新建分析</Link>,
    icon: <FlaskConical size={18} />,
  },
  {
    key: '/history',
    label: <Link to="/history">分析历史</Link>,
    icon: <History size={18} />,
  },
  {
    key: '/lots',
    label: <Link to="/lots">Lot / 多 Wafer</Link>,
    icon: <Database size={18} />,
  },
  {
    key: '/settings',
    label: <Link to="/settings">系统设置</Link>,
    icon: <Settings size={18} />,
  },
]

function Brand() {
  return (
    <div className="app-brand">
      <div className="app-brand-mark">W</div>
      <div>
        <Typography.Text strong>Wafer Intelligence</Typography.Text>
        <Typography.Text type="secondary" className="app-brand-subtitle">
          Yield Analytics
        </Typography.Text>
      </div>
    </div>
  )
}

function NavigationMenu({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = useRouterState({ select: (state) => state.location.pathname })
  return (
    <Menu
      mode="inline"
      selectedKeys={[pathname]}
      items={navigation}
      onClick={() => onNavigate?.()}
    />
  )
}

export function AppShell() {
  const screens = Grid.useBreakpoint()
  const mobile = !screens.lg
  const [drawerOpen, setDrawerOpen] = useState(false)
  const { mode, toggleTheme } = useAppTheme()

  return (
    <Layout className="app-shell">
      {!mobile && (
        <Sider width={232} theme="light" className="app-sider">
          <Brand />
          <NavigationMenu />
        </Sider>
      )}
      <Layout>
        <Header className="app-header">
          <Space>
            {mobile && (
              <Button
                aria-label="打开导航"
                type="text"
                icon={<MenuIcon size={20} />}
                onClick={() => setDrawerOpen(true)}
              />
            )}
            {mobile && <Typography.Text strong>Wafer Intelligence</Typography.Text>}
          </Space>
          <Button
            aria-label="切换主题"
            type="text"
            icon={mode === 'dark' ? <Sun size={19} /> : <Moon size={19} />}
            onClick={toggleTheme}
          />
        </Header>
        <Content className="app-content">
          <Outlet />
        </Content>
      </Layout>
      <Drawer
        title={<Brand />}
        placement="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        width={280}
        styles={{ body: { padding: 0 } }}
      >
        <NavigationMenu onNavigate={() => setDrawerOpen(false)} />
      </Drawer>
    </Layout>
  )
}

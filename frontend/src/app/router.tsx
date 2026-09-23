import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppShell } from '../components/layout/AppShell'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { HistoryPage } from '../features/history/HistoryPage'
import { LotPage } from '../features/lot/LotPage'
import { SettingsPage } from '../features/settings/SettingsPage'
import { UploadPage } from '../features/upload/UploadPage'
import { WaferPage } from '../features/wafer/WaferPage'

const rootRoute = createRootRoute({ component: AppShell })

const dashboardRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: DashboardPage,
})
const uploadRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/upload',
  component: UploadPage,
})
const historyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/history',
  component: HistoryPage,
})
const lotRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/lots',
  component: LotPage,
})
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})
const waferRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/wafer',
  component: WaferPage,
})

const routeTree = rootRoute.addChildren([
  dashboardRoute,
  uploadRoute,
  historyRoute,
  lotRoute,
  settingsRoute,
  waferRoute,
])

export const router = createRouter({ routeTree, defaultPreload: 'intent' })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

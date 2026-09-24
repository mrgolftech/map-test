import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { AppShell } from '../components/layout/AppShell'
import { AuthGate } from '../features/auth/AuthGate'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { AnalysisDetailPage } from '../features/history/AnalysisDetailPage'
import { HistoryPage } from '../features/history/HistoryPage'
import { LotPage } from '../features/lot/LotPage'
import { SettingsPage } from '../features/settings/SettingsPage'
import { UploadPage } from '../features/upload/UploadPage'

function RootLayout() {
  return (
    <AuthGate>
      <AppShell />
    </AuthGate>
  )
}

const rootRoute = createRootRoute({ component: RootLayout })

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

export type HistorySearch = {
  product_id?: string
  lot_id?: string
  wafer_id?: string
  created_from?: string
  created_to?: string
  yield_min?: number
  yield_max?: number
  main_fail_bin?: number
  pattern?: string
  page: number
  page_size: number
}

function stringValue(value: unknown) {
  return typeof value === 'string' && value.trim() ? value.trim() : undefined
}

function numberValue(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) return value
  if (typeof value === 'string' && value.trim()) {
    const parsed = Number(value)
    return Number.isFinite(parsed) ? parsed : undefined
  }
  return undefined
}

const historyRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/history',
  validateSearch: (search: Record<string, unknown>): HistorySearch => ({
    product_id: stringValue(search.product_id),
    lot_id: stringValue(search.lot_id),
    wafer_id: stringValue(search.wafer_id),
    created_from: stringValue(search.created_from),
    created_to: stringValue(search.created_to),
    yield_min: numberValue(search.yield_min),
    yield_max: numberValue(search.yield_max),
    main_fail_bin: numberValue(search.main_fail_bin),
    pattern: stringValue(search.pattern),
    page: Math.max(1, Math.trunc(numberValue(search.page) ?? 1)),
    page_size: Math.min(
      100,
      Math.max(1, Math.trunc(numberValue(search.page_size) ?? 20)),
    ),
  }),
  component: HistoryPage,
})
export type LotSearch = {
  product_id?: string
  lot_id?: string
  analysis_ids?: string
}

const lotRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/lots',
  validateSearch: (search: Record<string, unknown>): LotSearch => ({
    product_id: stringValue(search.product_id),
    lot_id: stringValue(search.lot_id),
    analysis_ids: stringValue(search.analysis_ids),
  }),
  component: LotPage,
})
const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/settings',
  component: SettingsPage,
})
function AnalysisDetailRouteComponent() {
  const { analysisId } = analysisDetailRoute.useParams()
  return <AnalysisDetailPage analysisId={analysisId} />
}

const analysisDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/analyses/$analysisId',
  component: AnalysisDetailRouteComponent,
})

const routeTree = rootRoute.addChildren([
  dashboardRoute,
  uploadRoute,
  historyRoute,
  lotRoute,
  settingsRoute,
  analysisDetailRoute,
])

export const router = createRouter({ routeTree, defaultPreload: 'intent' })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}

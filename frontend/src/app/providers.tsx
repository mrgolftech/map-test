import type { PropsWithChildren } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { App as AntApp, ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { AppThemeProvider, useAppTheme } from './theme'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

function AntDesignProvider({ children }: PropsWithChildren) {
  const { antdTheme } = useAppTheme()

  return (
    <ConfigProvider locale={zhCN} theme={antdTheme}>
      <AntApp>{children}</AntApp>
    </ConfigProvider>
  )
}

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <QueryClientProvider client={queryClient}>
      <AppThemeProvider>
        <AntDesignProvider>{children}</AntDesignProvider>
      </AppThemeProvider>
    </QueryClientProvider>
  )
}

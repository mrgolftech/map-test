import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type PropsWithChildren,
} from 'react'
import { theme, type ThemeConfig } from 'antd'

type ThemeMode = 'light' | 'dark'

type ThemeContextValue = {
  mode: ThemeMode
  toggleTheme: () => void
  antdTheme: ThemeConfig
}

const ThemeContext = createContext<ThemeContextValue | null>(null)

function initialMode(): ThemeMode {
  const stored = window.localStorage.getItem('map-test-theme')
  if (stored === 'dark' || stored === 'light') return stored
  return window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
}

export function AppThemeProvider({ children }: PropsWithChildren) {
  const [mode, setMode] = useState<ThemeMode>(initialMode)

  useEffect(() => {
    document.documentElement.dataset.theme = mode
    window.localStorage.setItem('map-test-theme', mode)
  }, [mode])

  const antdTheme = useMemo<ThemeConfig>(
    () => ({
      algorithm: mode === 'dark' ? theme.darkAlgorithm : theme.defaultAlgorithm,
      cssVar: {},
      token: {
        colorPrimary: mode === 'dark' ? '#4096ff' : '#1677ff',
        borderRadius: 8,
        fontSize: 14,
        controlHeight: 36,
      },
    }),
    [mode],
  )

  const value = useMemo(
    () => ({
      mode,
      toggleTheme: () => setMode((current) => (current === 'light' ? 'dark' : 'light')),
      antdTheme,
    }),
    [mode, antdTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useAppTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useAppTheme must be used inside AppThemeProvider')
  return context
}

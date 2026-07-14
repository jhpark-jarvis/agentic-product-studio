import { StrictMode, useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { CssBaseline, ThemeProvider } from '@mui/material'
import App from './App'
import { buildAppTheme, DEFAULT_THEME_MODE, THEME_STORAGE_KEY } from './theme'
import { ThemeModeContext } from './theme-mode'

const CHUNK_RELOAD_KEY = 'ml_docs_chunk_reload_once'

function resolveRouterBasename() {
  if (window.location.pathname.startsWith('/static/frontend/')) {
    return '/static/frontend'
  }
  return '/'
}

function shouldReloadForChunkError(message) {
  const normalized = String(message || '')
  return (
    normalized.includes('Failed to fetch dynamically imported module') ||
    normalized.includes('Importing a module script failed')
  )
}

function RootApp() {
  const [themeMode, setThemeMode] = useState(() => {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY)
    return saved || DEFAULT_THEME_MODE
  })
  const routerBasename = useMemo(() => resolveRouterBasename(), [])

  const theme = useMemo(() => buildAppTheme(themeMode), [themeMode])

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, themeMode)
    document.documentElement.setAttribute('data-app-theme', themeMode)
  }, [themeMode])

  useEffect(() => {
    window.sessionStorage.removeItem(CHUNK_RELOAD_KEY)
  }, [])

  useEffect(() => {
    const reloadOnce = () => {
      if (window.sessionStorage.getItem(CHUNK_RELOAD_KEY) === '1') {
        return
      }
      window.sessionStorage.setItem(CHUNK_RELOAD_KEY, '1')
      window.location.reload()
    }

    const handleError = (event) => {
      if (shouldReloadForChunkError(event?.message)) {
        reloadOnce()
      }
    }

    const handleRejection = (event) => {
      const reason = event?.reason
      const message =
        typeof reason === 'string'
          ? reason
          : reason?.message || reason?.toString?.() || ''
      if (shouldReloadForChunkError(message)) {
        reloadOnce()
      }
    }

    window.addEventListener('error', handleError)
    window.addEventListener('unhandledrejection', handleRejection)
    return () => {
      window.removeEventListener('error', handleError)
      window.removeEventListener('unhandledrejection', handleRejection)
    }
  }, [])

  const contextValue = useMemo(
    () => ({
      themeMode,
      toggleThemeMode: () => setThemeMode((prev) => (prev === 'studio' ? 'midnight' : 'studio')),
    }),
    [themeMode],
  )

  return (
    <ThemeModeContext.Provider value={contextValue}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter basename={routerBasename}>
          <App />
        </BrowserRouter>
      </ThemeProvider>
    </ThemeModeContext.Provider>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <RootApp />
  </StrictMode>,
)

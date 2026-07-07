import { StrictMode, useEffect, useMemo, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { CssBaseline, ThemeProvider } from '@mui/material'
import App from './App'
import { buildAppTheme, DEFAULT_THEME_MODE, THEME_STORAGE_KEY } from './theme'
import { ThemeModeContext } from './theme-mode'

function RootApp() {
  const [themeMode, setThemeMode] = useState(() => {
    const saved = window.localStorage.getItem(THEME_STORAGE_KEY)
    return saved || DEFAULT_THEME_MODE
  })

  const theme = useMemo(() => buildAppTheme(themeMode), [themeMode])

  useEffect(() => {
    window.localStorage.setItem(THEME_STORAGE_KEY, themeMode)
    document.documentElement.setAttribute('data-app-theme', themeMode)
  }, [themeMode])

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
        <BrowserRouter>
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

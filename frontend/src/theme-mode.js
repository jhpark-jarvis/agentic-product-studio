import { createContext, useContext } from 'react'

export const ThemeModeContext = createContext({
  themeMode: 'studio',
  toggleThemeMode: () => {},
})

export function useThemeMode() {
  return useContext(ThemeModeContext)
}

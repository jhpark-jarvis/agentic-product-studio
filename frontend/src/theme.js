import { createTheme } from '@mui/material/styles'

const themeTokens = {
  studio: {
    mode: 'light',
    primary: { main: '#c06b2b', dark: '#8a4616', light: '#f4ddbf', contrastText: '#ffffff' },
    secondary: { main: '#4b3124' },
    background: { default: '#e8ddd0', paper: '#f8f1e6' },
    text: { primary: '#2f241f', secondary: '#6d5a4d' },
    divider: '#d5c2ab',
    success: { main: '#5b7b45' },
    warning: { main: '#d08b2f' },
    error: { main: '#b14b2f' },
    paperBorder: '#d5c2ab',
    paperShadow: '0 12px 24px rgba(88, 57, 34, 0.08)',
    buttonGradient: 'linear-gradient(180deg, #d28a38 0%, #b35d24 100%)',
    inputBackground: '#fff9f2',
    tableHeadBackground: '#efe4d6',
  },
  midnight: {
    mode: 'dark',
    primary: { main: '#dbeafe', dark: '#93c5fd', light: '#f8fbff', contrastText: '#09111f' },
    secondary: { main: '#8fb4d9' },
    background: { default: '#08111f', paper: '#0f1b2d' },
    text: { primary: '#f8fbff', secondary: '#a9bbcf' },
    divider: '#233247',
    success: { main: '#34d399' },
    warning: { main: '#fbbf24' },
    error: { main: '#f97316' },
    paperBorder: '#1f3046',
    paperShadow: '0 18px 36px rgba(2, 8, 23, 0.36)',
    buttonGradient: 'linear-gradient(180deg, #24456f 0%, #10233b 100%)',
    inputBackground: '#0b1627',
    tableHeadBackground: '#12243a',
  },
}

export const THEME_STORAGE_KEY = 'agentic-product-studio-theme-mode'
export const DEFAULT_THEME_MODE = 'studio'

export function buildAppTheme(mode = DEFAULT_THEME_MODE) {
  const tokens = themeTokens[mode] || themeTokens[DEFAULT_THEME_MODE]

  return createTheme({
    palette: {
      mode: tokens.mode,
      primary: tokens.primary,
      secondary: tokens.secondary,
      background: tokens.background,
      text: tokens.text,
      divider: tokens.divider,
      success: tokens.success,
      warning: tokens.warning,
      error: tokens.error,
    },
    shape: {
      borderRadius: 6,
    },
    typography: {
      fontFamily: ['Pretendard', 'Noto Sans KR', 'Segoe UI', 'sans-serif'].join(','),
      h3: {
        fontWeight: 800,
        letterSpacing: '-0.03em',
        lineHeight: 1.05,
      },
      h5: {
        fontWeight: 800,
        letterSpacing: '-0.02em',
      },
      h6: {
        fontWeight: 800,
        letterSpacing: '-0.01em',
      },
      overline: {
        fontWeight: 800,
        letterSpacing: '0.18em',
      },
      button: {
        fontWeight: 700,
        textTransform: 'none',
      },
    },
    components: {
      MuiPaper: {
        styleOverrides: {
          root: {
            border: `1px solid ${tokens.paperBorder}`,
            boxShadow: tokens.paperShadow,
            backgroundImage: 'none',
            color: tokens.text.primary,
          },
        },
      },
      MuiButton: {
        defaultProps: {
          disableElevation: true,
        },
        styleOverrides: {
          root: {
            minHeight: 42,
            borderRadius: 4,
            paddingInline: 16,
            fontWeight: 800,
          },
          containedPrimary: {
            backgroundImage: tokens.buttonGradient,
          },
          outlined: {
            borderWidth: 1,
          },
        },
      },
      MuiOutlinedInput: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            backgroundColor: tokens.inputBackground,
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          standardInfo: {
            backgroundColor: tokens.mode === 'dark' ? '#10233b' : '#e0f2fe',
            color: tokens.text.primary,
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            borderRadius: 4,
            fontWeight: 700,
          },
        },
      },
      MuiTableCell: {
        styleOverrides: {
          root: {
            textAlign: 'left',
            verticalAlign: 'top',
          },
          head: {
            color: tokens.text.secondary,
            fontWeight: 700,
            backgroundColor: tokens.tableHeadBackground,
          },
        },
      },
    },
  })
}

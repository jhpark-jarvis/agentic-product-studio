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
    floatingPanelBackground: 'rgba(247, 238, 224, 0.92)',
    floatingPanelBorder: '#d2b18f',
    floatingToggleBackground: 'linear-gradient(180deg, #f0d3aa 0%, #ddb07a 100%)',
    floatingToggleHover: 'linear-gradient(180deg, #f6debc 0%, #e0b682 100%)',
    floatingToggleText: '#6a3412',
    floatingButtonBackground: 'linear-gradient(180deg, #9a5728 0%, #6f3d1d 100%)',
    floatingButtonHover: 'linear-gradient(180deg, #ae6430 0%, #7e4520 100%)',
    floatingButtonText: '#fff8f0',
    floatingButtonBorder: 'rgba(108, 59, 28, 0.24)',
    floatingButtonDisabledBackground: 'rgba(157, 116, 82, 0.32)',
    floatingButtonDisabledText: 'rgba(86, 54, 33, 0.5)',
    markdownLink: '#9a4e17',
    markdownLinkHover: '#6e330f',
    markdownLinkVisited: '#7b4a91',
    markdownLinkUnderline: 'rgba(154, 78, 23, 0.35)',
    hiddenChipBackground: '#fff3e4',
    hiddenChipBorder: '#d7a56d',
    hiddenChipText: '#8f4f1f',
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
    floatingPanelBackground: 'rgba(7, 17, 30, 0.92)',
    floatingPanelBorder: 'rgba(111, 168, 220, 0.26)',
    floatingToggleBackground: 'linear-gradient(180deg, #15304f 0%, #0d1d31 100%)',
    floatingToggleHover: 'linear-gradient(180deg, #1d4069 0%, #123055 100%)',
    floatingToggleText: '#d8ecff',
    floatingButtonBackground: 'linear-gradient(180deg, #28527f 0%, #173455 100%)',
    floatingButtonHover: 'linear-gradient(180deg, #356596 0%, #21486f 100%)',
    floatingButtonText: '#f3f9ff',
    floatingButtonBorder: 'rgba(143, 180, 217, 0.22)',
    floatingButtonDisabledBackground: 'rgba(24, 43, 66, 0.72)',
    floatingButtonDisabledText: 'rgba(212, 230, 248, 0.45)',
    markdownLink: '#8fd3ff',
    markdownLinkHover: '#d7efff',
    markdownLinkVisited: '#c7b8ff',
    markdownLinkUnderline: 'rgba(143, 211, 255, 0.38)',
    hiddenChipBackground: 'rgba(251, 191, 36, 0.12)',
    hiddenChipBorder: 'rgba(251, 191, 36, 0.38)',
    hiddenChipText: '#f7d68a',
  },
}

export const THEME_STORAGE_KEY = 'agentic-product-studio-theme-mode'
export const DEFAULT_THEME_MODE = 'studio'

export function hiddenStatusChipSx(theme) {
  const tokens = theme.customTokens

  return {
    color: tokens.hiddenChipText,
    backgroundColor: tokens.hiddenChipBackground,
    borderColor: tokens.hiddenChipBorder,
    '& .MuiChip-label': {
      color: tokens.hiddenChipText,
    },
  }
}

export function buildAppTheme(mode = DEFAULT_THEME_MODE) {
  const tokens = themeTokens[mode] || themeTokens[DEFAULT_THEME_MODE]

  return createTheme({
    customTokens: tokens,
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
      MuiCssBaseline: {
        styleOverrides: {
          '.markdown-body a': {
            color: tokens.markdownLink,
            textDecorationLine: 'underline',
            textDecorationThickness: '0.08em',
            textUnderlineOffset: '0.18em',
            textDecorationColor: tokens.markdownLinkUnderline,
            fontWeight: 700,
            transition: 'color 140ms ease, text-decoration-color 140ms ease',
          },
          '.markdown-body a:hover': {
            color: tokens.markdownLinkHover,
            textDecorationColor: tokens.markdownLinkHover,
          },
          '.markdown-body a:visited': {
            color: tokens.markdownLinkVisited,
          },
        },
      },
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

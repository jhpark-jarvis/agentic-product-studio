import { createTheme } from '@mui/material/styles'

export const appTheme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#2059dc',
      dark: '#1545b0',
      light: '#e8f0ff',
      contrastText: '#ffffff',
    },
    secondary: {
      main: '#162234',
    },
    background: {
      default: '#edf2f8',
      paper: '#ffffff',
    },
    text: {
      primary: '#172133',
      secondary: '#66758b',
    },
    divider: '#d9e1ec',
    success: {
      main: '#1d8f5a',
    },
    warning: {
      main: '#c78014',
    },
    error: {
      main: '#c54343',
    },
  },
  shape: {
    borderRadius: 16,
  },
  typography: {
    fontFamily: [
      'Pretendard',
      'Noto Sans KR',
      'Segoe UI',
      'sans-serif',
    ].join(','),
    h3: {
      fontWeight: 800,
      letterSpacing: '-0.03em',
    },
    h5: {
      fontWeight: 800,
      letterSpacing: '-0.02em',
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
          border: '1px solid #d9e1ec',
          boxShadow: '0 18px 40px rgba(15, 23, 42, 0.06)',
          backgroundImage: 'none',
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
          borderRadius: 12,
          paddingInline: 16,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          backgroundColor: '#ffffff',
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: {
          color: '#66758b',
          fontWeight: 700,
        },
      },
    },
  },
})

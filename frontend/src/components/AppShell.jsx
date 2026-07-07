import '../App.css'
import AutoAwesomeOutlinedIcon from '@mui/icons-material/AutoAwesomeOutlined'
import BedtimeOutlinedIcon from '@mui/icons-material/BedtimeOutlined'
import CalendarMonthOutlinedIcon from '@mui/icons-material/CalendarMonthOutlined'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined'
import MenuIcon from '@mui/icons-material/Menu'
import SchemaOutlinedIcon from '@mui/icons-material/SchemaOutlined'
import {
  AppBar,
  Box,
  Button,
  Chip,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import { useMemo, useState } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { useThemeMode } from '../theme-mode'

const drawerWidth = 272

const navigationItems = [
  { label: '대시보드', path: '/', icon: <DashboardOutlinedIcon /> },
  { label: '문서', path: '/documents', icon: <DescriptionOutlinedIcon /> },
  { label: 'WBS', path: '/wbs', icon: <SchemaOutlinedIcon /> },
  { label: '일정', path: '/schedules', icon: <CalendarMonthOutlinedIcon /> },
  { label: '멤버', path: '/members', icon: <Groups2OutlinedIcon /> },
]

const shellStyles = {
  studio: {
    drawerText: '#f7ead8',
    drawerBg: '#3a2a22',
    drawerGradient:
      'linear-gradient(180deg, rgba(255,255,255,0.06), rgba(255,255,255,0) 18%), linear-gradient(135deg, rgba(192,107,43,0.32), rgba(0,0,0,0) 44%)',
    drawerOverline: '#dabb8d',
    drawerBody: '#efdcc5',
    selectedBg: 'rgba(255, 232, 204, 0.1)',
    selectedBorder: 'rgba(242, 197, 125, 0.26)',
    selectedHover: 'rgba(255, 232, 204, 0.14)',
    chipBorder: 'rgba(242, 197, 125, 0.24)',
    chipBg: 'rgba(255, 244, 227, 0.08)',
    chipText: '#fff7ea',
    appBarBorder: '#d5c2ab',
    appBarBg: 'rgba(248, 241, 230, 0.9)',
    modeLabel: 'Studio Theme',
  },
  midnight: {
    drawerText: '#edf2f7',
    drawerBg: '#0f172a',
    drawerGradient:
      'linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0) 18%), linear-gradient(135deg, rgba(30,58,95,0.34), rgba(0,0,0,0) 44%)',
    drawerOverline: '#c9d5e3',
    drawerBody: '#d8e2ee',
    selectedBg: 'rgba(255,255,255,0.08)',
    selectedBorder: 'rgba(191, 219, 254, 0.24)',
    selectedHover: 'rgba(255,255,255,0.12)',
    chipBorder: 'rgba(191, 219, 254, 0.22)',
    chipBg: 'rgba(255,255,255,0.08)',
    chipText: '#f8fbff',
    appBarBorder: '#1f3046',
    appBarBg: 'rgba(8, 17, 31, 0.9)',
    modeLabel: 'Midnight Theme',
  },
}

function NavItems({ onNavigate, styleSet }) {
  const location = useLocation()

  return (
    <List sx={{ display: 'grid', gap: 1, px: 1.5, py: 1.5 }}>
      {navigationItems.map((item) => {
        const selected = item.path === '/' ? location.pathname === '/' : location.pathname.startsWith(item.path)
        return (
          <ListItemButton
            key={item.path}
            component={NavLink}
            to={item.path}
            onClick={onNavigate}
            selected={selected}
            sx={{
              borderRadius: 1,
              minHeight: 50,
              border: '1px solid transparent',
              '&.Mui-selected': {
                backgroundColor: styleSet.selectedBg,
                borderColor: styleSet.selectedBorder,
                color: '#fff',
              },
              '&.Mui-selected:hover': {
                backgroundColor: styleSet.selectedHover,
              },
            }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>
              {item.icon}
            </ListItemIcon>
            <ListItemText primary={item.label} />
          </ListItemButton>
        )
      })}
    </List>
  )
}

export function AppShell({ children }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()
  const { themeMode, toggleThemeMode } = useThemeMode()
  const styleSet = shellStyles[themeMode] || shellStyles.studio

  const pageTitle = useMemo(() => {
    return navigationItems.find((item) => location.pathname.startsWith(item.path))?.label ?? 'Agentic Product Studio'
  }, [location.pathname])

  const drawerContent = (
    <Box
      sx={{
        height: '100%',
        color: styleSet.drawerText,
        backgroundColor: styleSet.drawerBg,
        backgroundImage: styleSet.drawerGradient,
      }}
    >
      <Stack spacing={1.5} sx={{ px: 3, py: 3 }}>
        <Typography variant="overline" sx={{ color: styleSet.drawerOverline, letterSpacing: '0.18em', fontWeight: 800 }}>
          INTERNAL
        </Typography>
        <Typography variant="h5" sx={{ color: '#ffffff', lineHeight: 1.2 }}>
          Agentic Product Studio
        </Typography>
        <Typography variant="body2" sx={{ color: styleSet.drawerBody, lineHeight: 1.8 }}>
          문서, 작업, 일정, 팀 정보를 한곳에서 관리하는 내부 업무 공간입니다.
        </Typography>
      </Stack>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />
      <NavItems onNavigate={() => setMobileOpen(false)} styleSet={styleSet} />

      <Box sx={{ px: 3, pt: 2 }}>
        <Chip
          label={styleSet.modeLabel}
          sx={{
            borderRadius: 1,
            border: `1px solid ${styleSet.chipBorder}`,
            backgroundColor: styleSet.chipBg,
            color: styleSet.chipText,
            fontWeight: 700,
          }}
        />
      </Box>
    </Box>
  )

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: 'background.default' }}>
      <Box className="app-shell-gradient" />
      <AppBar
        position="fixed"
        color="inherit"
        elevation={0}
        sx={{
          width: { lg: `calc(100% - ${drawerWidth}px)` },
          ml: { lg: `${drawerWidth}px` },
          borderBottom: `1px solid ${styleSet.appBarBorder}`,
          backdropFilter: 'blur(10px)',
          backgroundColor: styleSet.appBarBg,
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 72, sm: 80 }, px: { xs: 2, sm: 3 }, justifyContent: 'space-between' }}>
          <Stack direction="row" spacing={1} alignItems="center">
            <IconButton
              color="inherit"
              edge="start"
              onClick={() => setMobileOpen(true)}
              sx={{ display: { lg: 'none' }, mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
            <Box>
              <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.18em', fontWeight: 800 }}>
                WORKSPACE
              </Typography>
              <Typography
                variant="h5"
                sx={{
                  fontSize: { xs: '1.25rem', sm: '1.5rem' },
                  lineHeight: 1.2,
                  wordBreak: 'keep-all',
                  letterSpacing: '-0.03em',
                }}
              >
                {pageTitle}
              </Typography>
            </Box>
          </Stack>

          <Button
            onClick={toggleThemeMode}
            variant="outlined"
            color={themeMode === 'midnight' ? 'primary' : 'secondary'}
            startIcon={themeMode === 'studio' ? <BedtimeOutlinedIcon /> : <AutoAwesomeOutlinedIcon />}
            sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
          >
            {themeMode === 'studio' ? '블랙/네이비' : '프로덕트 톤'}
          </Button>
        </Toolbar>
      </AppBar>

      <Box component="nav" sx={{ width: { lg: drawerWidth }, flexShrink: { lg: 0 } }}>
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={() => setMobileOpen(false)}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', lg: 'none' },
            '& .MuiDrawer-paper': { width: drawerWidth, border: 0 },
          }}
        >
          {drawerContent}
        </Drawer>
        <Drawer
          variant="permanent"
          open
          sx={{
            display: { xs: 'none', lg: 'block' },
            '& .MuiDrawer-paper': {
              width: drawerWidth,
              border: 0,
              boxSizing: 'border-box',
            },
          }}
        >
          {drawerContent}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          ml: { lg: `${drawerWidth}px` },
          px: { xs: 2, sm: 3, lg: 4 },
          pt: { xs: 11, sm: 12 },
          pb: 4,
        }}
      >
        {children}
      </Box>
    </Box>
  )
}

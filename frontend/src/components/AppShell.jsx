import '../App.css'
import CalendarMonthOutlinedIcon from '@mui/icons-material/CalendarMonthOutlined'
import DashboardOutlinedIcon from '@mui/icons-material/DashboardOutlined'
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import Groups2OutlinedIcon from '@mui/icons-material/Groups2Outlined'
import MenuIcon from '@mui/icons-material/Menu'
import SchemaOutlinedIcon from '@mui/icons-material/SchemaOutlined'
import {
  AppBar,
  Box,
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

const drawerWidth = 272

const navigationItems = [
  { label: '대시보드', path: '/dashboard', icon: <DashboardOutlinedIcon /> },
  { label: '문서', path: '/documents', icon: <DescriptionOutlinedIcon /> },
  { label: 'WBS', path: '/wbs', icon: <SchemaOutlinedIcon /> },
  { label: '일정', path: '/schedules', icon: <CalendarMonthOutlinedIcon /> },
  { label: '멤버', path: '/members', icon: <Groups2OutlinedIcon /> },
]

function NavItems({ onNavigate }) {
  const location = useLocation()

  return (
    <List sx={{ display: 'grid', gap: 1, px: 1.5, py: 1.5 }}>
      {navigationItems.map((item) => {
        const selected = location.pathname.startsWith(item.path)
        return (
          <ListItemButton
            key={item.path}
            component={NavLink}
            to={item.path}
            onClick={onNavigate}
            selected={selected}
            sx={{
              borderRadius: 3,
              minHeight: 48,
              '&.Mui-selected': {
                backgroundColor: 'rgba(255,255,255,0.08)',
                color: '#fff',
              },
              '&.Mui-selected:hover': {
                backgroundColor: 'rgba(255,255,255,0.12)',
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

  const pageTitle = useMemo(() => {
    return navigationItems.find((item) => location.pathname.startsWith(item.path))?.label ?? 'Agentic Product Studio'
  }, [location.pathname])

  const drawerContent = (
    <Box
      sx={{
        height: '100%',
        color: '#d9e4f4',
        backgroundColor: '#162234',
        backgroundImage:
          'linear-gradient(180deg, rgba(255,255,255,0.04), rgba(255,255,255,0) 22%)',
      }}
    >
      <Stack spacing={1.5} sx={{ px: 3, py: 3 }}>
        <Typography variant="overline" sx={{ color: '#87a1c8', letterSpacing: '0.18em', fontWeight: 800 }}>
          INTERNAL
        </Typography>
        <Typography variant="h5" sx={{ color: '#ffffff', lineHeight: 1.2 }}>
          Agentic Product Studio
        </Typography>
        <Typography variant="body2" sx={{ color: '#9db0cb', lineHeight: 1.8 }}>
          Flask API를 유지하면서 React + MUI로 프론트 화면을 단계적으로 이관하고 있습니다.
        </Typography>
      </Stack>

      <Divider sx={{ borderColor: 'rgba(255,255,255,0.08)' }} />
      <NavItems onNavigate={() => setMobileOpen(false)} />

      <Box sx={{ px: 3, pt: 2 }}>
        <Chip
          label="Flask API 연결"
          sx={{
            borderRadius: 999,
            backgroundColor: 'rgba(255,255,255,0.08)',
            color: '#fff',
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
          borderBottom: '1px solid #d9e1ec',
          backdropFilter: 'blur(14px)',
          backgroundColor: 'rgba(237, 242, 248, 0.78)',
        }}
      >
        <Toolbar sx={{ minHeight: { xs: 72, sm: 80 }, px: { xs: 2, sm: 3 } }}>
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
              REACT APP
            </Typography>
            <Typography variant="h5">{pageTitle}</Typography>
          </Box>
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

import { Suspense, lazy } from 'react'
import { CircularProgress, Stack, Typography } from '@mui/material'
import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { PageViewTracker } from './components/PageViewTracker'

const DashboardPage = lazy(() => import('./pages/DashboardPage').then((module) => ({ default: module.DashboardPage })))
const DocumentsPage = lazy(() => import('./pages/DocumentsPage').then((module) => ({ default: module.DocumentsPage })))
const AssetsPage = lazy(() => import('./pages/AssetsPage').then((module) => ({ default: module.AssetsPage })))
const AssetDetailPage = lazy(() => import('./pages/AssetDetailPage').then((module) => ({ default: module.AssetDetailPage })))
const AssetEditorPage = lazy(() => import('./pages/AssetEditorPage').then((module) => ({ default: module.AssetEditorPage })))
const DocumentEditorPage = lazy(() =>
  import('./pages/DocumentEditorPage').then((module) => ({ default: module.DocumentEditorPage })),
)
const DocumentDetailPage = lazy(() =>
  import('./pages/DocumentDetailPage').then((module) => ({ default: module.DocumentDetailPage })),
)
const WbsPage = lazy(() => import('./pages/WbsPage').then((module) => ({ default: module.WbsPage })))
const WbsDetailPage = lazy(() => import('./pages/WbsDetailPage').then((module) => ({ default: module.WbsDetailPage })))
const WbsEditorPage = lazy(() => import('./pages/WbsEditorPage').then((module) => ({ default: module.WbsEditorPage })))
const SchedulesPage = lazy(() =>
  import('./pages/SchedulesPage').then((module) => ({ default: module.SchedulesPage })),
)
const ScheduleEditorPage = lazy(() =>
  import('./pages/ScheduleEditorPage').then((module) => ({ default: module.ScheduleEditorPage })),
)
const MembersPage = lazy(() => import('./pages/MembersPage').then((module) => ({ default: module.MembersPage })))
const MemberEditorPage = lazy(() =>
  import('./pages/MemberEditorPage').then((module) => ({ default: module.MemberEditorPage })),
)
const LogsPage = lazy(() => import('./pages/LogsPage').then((module) => ({ default: module.LogsPage })))

function RouteLoading() {
  return (
    <Stack spacing={2} sx={{ py: 10, alignItems: 'center' }}>
      <CircularProgress size={30} />
      <Typography color="text.secondary">화면을 준비하는 중입니다...</Typography>
    </Stack>
  )
}

function App() {
  return (
    <AppShell>
      <PageViewTracker />
      <Suspense fallback={<RouteLoading />}>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/dashboard" element={<Navigate to="/" replace />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/documents/new" element={<DocumentEditorPage />} />
          <Route path="/documents/:documentId" element={<DocumentDetailPage />} />
          <Route path="/documents/:documentId/edit" element={<DocumentEditorPage />} />
          <Route path="/assets" element={<AssetsPage />} />
          <Route path="/assets/new" element={<AssetEditorPage />} />
          <Route path="/assets/:assetId" element={<AssetDetailPage />} />
          <Route path="/assets/:assetId/edit" element={<AssetEditorPage />} />
          <Route path="/wbs" element={<WbsPage />} />
          <Route path="/wbs/new" element={<WbsEditorPage />} />
          <Route path="/wbs/:taskId" element={<WbsDetailPage />} />
          <Route path="/wbs/:taskId/edit" element={<WbsEditorPage />} />
          <Route path="/schedules" element={<SchedulesPage />} />
          <Route path="/schedules/new" element={<ScheduleEditorPage />} />
          <Route path="/schedules/:scheduleId/edit" element={<ScheduleEditorPage />} />
          <Route path="/members" element={<MembersPage />} />
          <Route path="/members/new" element={<MemberEditorPage />} />
          <Route path="/members/:memberId/edit" element={<MemberEditorPage />} />
          <Route path="/log" element={<LogsPage />} />
          <Route path="/document/*" element={<Navigate to="/documents" replace />} />
          <Route path="/asset/*" element={<Navigate to="/assets" replace />} />
          <Route path="/task/*" element={<Navigate to="/wbs" replace />} />
          <Route path="/schedule/*" element={<Navigate to="/schedules" replace />} />
          <Route path="/member/*" element={<Navigate to="/members" replace />} />
        </Routes>
      </Suspense>
    </AppShell>
  )
}

export default App

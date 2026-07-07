import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentDetailPage } from './pages/DocumentDetailPage'
import { DocumentEditorPage } from './pages/DocumentEditorPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { MemberEditorPage } from './pages/MemberEditorPage'
import { MembersPage } from './pages/MembersPage'
import { ScheduleEditorPage } from './pages/ScheduleEditorPage'
import { WbsEditorPage } from './pages/WbsEditorPage'
import { SchedulesPage } from './pages/SchedulesPage'
import { WbsPage } from './pages/WbsPage'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/new" element={<DocumentEditorPage />} />
        <Route path="/documents/:documentId" element={<DocumentDetailPage />} />
        <Route path="/documents/:documentId/edit" element={<DocumentEditorPage />} />
        <Route path="/wbs" element={<WbsPage />} />
        <Route path="/wbs/new" element={<WbsEditorPage />} />
        <Route path="/wbs/:taskId/edit" element={<WbsEditorPage />} />
        <Route path="/schedules" element={<SchedulesPage />} />
        <Route path="/schedules/new" element={<ScheduleEditorPage />} />
        <Route path="/schedules/:scheduleId/edit" element={<ScheduleEditorPage />} />
        <Route path="/members" element={<MembersPage />} />
        <Route path="/members/new" element={<MemberEditorPage />} />
        <Route path="/members/:memberId/edit" element={<MemberEditorPage />} />
      </Routes>
    </AppShell>
  )
}

export default App

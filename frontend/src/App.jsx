import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentDetailPage } from './pages/DocumentDetailPage'
import { DocumentEditorPage } from './pages/DocumentEditorPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { MembersPage } from './pages/MembersPage'
import { ScheduleEditorPage } from './pages/ScheduleEditorPage'
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
        <Route path="/schedules" element={<SchedulesPage />} />
        <Route path="/schedules/new" element={<ScheduleEditorPage />} />
        <Route path="/schedules/:scheduleId/edit" element={<ScheduleEditorPage />} />
        <Route path="/members" element={<MembersPage />} />
      </Routes>
    </AppShell>
  )
}

export default App

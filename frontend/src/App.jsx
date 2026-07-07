import { Navigate, Route, Routes } from 'react-router-dom'
import { AppShell } from './components/AppShell'
import { DashboardPage } from './pages/DashboardPage'
import { DocumentDetailPage } from './pages/DocumentDetailPage'
import { DocumentsPage } from './pages/DocumentsPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { WbsPage } from './pages/WbsPage'

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/documents" element={<DocumentsPage />} />
        <Route path="/documents/:documentId" element={<DocumentDetailPage />} />
        <Route path="/wbs" element={<WbsPage />} />
        <Route
          path="/schedules"
          element={
            <PlaceholderPage
              title="일정"
              description="주간 및 월간 일정 화면은 다음 단계에서 React 라우트로 이관할 예정입니다."
            />
          }
        />
        <Route
          path="/members"
          element={
            <PlaceholderPage
              title="멤버"
              description="멤버 목록과 담당 현황 화면은 다음 단계에서 React 기반 관리 화면으로 전환할 예정입니다."
            />
          }
        />
      </Routes>
    </AppShell>
  )
}

export default App

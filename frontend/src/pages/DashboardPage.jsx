import ArrowForwardRoundedIcon from '@mui/icons-material/ArrowForwardRounded'
import CampaignRoundedIcon from '@mui/icons-material/CampaignRounded'
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import EventOutlinedIcon from '@mui/icons-material/EventOutlined'
import SchemaOutlinedIcon from '@mui/icons-material/SchemaOutlined'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'

function SummaryCard({ label, value, caption, tone = 'default' }) {
  const isAlert = tone === 'alert'
  return (
    <Paper
      sx={{
        p: 3,
        borderRadius: 1,
        borderTop: (theme) => `4px solid ${isAlert ? theme.palette.error.main : theme.palette.primary.main}`,
        background: (theme) =>
          isAlert
            ? theme.palette.mode === 'dark'
              ? `linear-gradient(135deg, ${theme.palette.background.paper}, rgba(249, 115, 22, 0.16))`
              : `linear-gradient(135deg, ${theme.palette.background.paper}, #fff5f0)`
            : `linear-gradient(135deg, ${theme.palette.background.paper}, ${theme.palette.background.default})`,
      }}
    >
      <Stack spacing={1}>
        <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.16em', fontWeight: 800 }}>
          {label}
        </Typography>
        <Typography variant="h3" sx={{ fontWeight: 800, color: isAlert ? 'error.main' : 'text.primary' }}>
          {value}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {caption}
        </Typography>
      </Stack>
    </Paper>
  )
}

function SectionCard({ title, description, actionLabel, actionTo, icon, children }) {
  return (
    <Paper sx={{ p: 3, borderRadius: 1 }}>
      <Stack spacing={2.5}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} sx={{ justifyContent: 'space-between' }}>
          <Stack spacing={0.75}>
            <Stack direction="row" spacing={1} alignItems="center">
              {icon}
              <Typography variant="h6">{title}</Typography>
            </Stack>
            <Typography variant="body2" color="text.secondary">
              {description}
            </Typography>
          </Stack>
          {actionLabel ? (
            <Button component={RouterLink} to={actionTo} size="small" endIcon={<ArrowForwardRoundedIcon />}>
              {actionLabel}
            </Button>
          ) : null}
        </Stack>
        {children}
      </Stack>
    </Paper>
  )
}

function EmptyState({ message }) {
  return <Alert severity="info">{message}</Alert>
}

export function DashboardPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet('/api/dashboard')
        setData(payload)
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  if (loading) {
    return (
      <Stack sx={{ py: 10, alignItems: 'center' }} spacing={2}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">대시보드를 불러오는 중입니다...</Typography>
      </Stack>
    )
  }

  if (error || !data) {
    return (
      <Stack spacing={3}>
        <PageHeader
          eyebrow="DASHBOARD"
          title="대시보드"
          description="운영 현황을 불러오는 중 문제가 발생했습니다."
        />
        <Alert severity="error">{error || '대시보드를 불러올 수 없습니다.'}</Alert>
      </Stack>
    )
  }

  const summary = data.summary || {}

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="OVERVIEW"
        title="프로젝트 대시보드"
        description={`오늘은 ${data.today} 기준이며, 이번 주 범위는 ${data.week_start} ~ ${data.week_end} 입니다.`}
      />

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', md: 'repeat(2, minmax(0, 1fr))', xl: 'repeat(4, minmax(0, 1fr))' },
          gap: 2,
        }}
      >
        <SummaryCard label="전체 작업" value={summary.total_tasks || 0} caption="등록된 전체 WBS 작업 수" />
        <SummaryCard label="진행 중" value={summary.in_progress_tasks || 0} caption="현재 처리 중인 작업 수" />
        <SummaryCard label="완료" value={summary.completed_tasks || 0} caption="완료 처리된 작업 수" />
        <SummaryCard label="지연 작업" value={summary.delayed_tasks || 0} caption="마감일이 지났지만 완료되지 않은 작업" tone="alert" />
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.4fr) minmax(320px, 0.6fr)' },
          gap: 3,
        }}
      >
        <SectionCard
          title="이번 주 마감 작업"
          description={`${data.week_due_tasks.length}건의 작업이 이번 주 마감 예정입니다.`}
          actionLabel="WBS 보기"
          actionTo="/wbs"
          icon={<SchemaOutlinedIcon color="primary" fontSize="small" />}
        >
          <Stack spacing={1.5}>
            {data.week_due_tasks.length ? data.week_due_tasks.map((task) => (
              <Paper key={task.id} variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
                <Stack spacing={1}>
                  <Typography fontWeight={700}>{task.title}</Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Chip size="small" label={task.status} />
                    <Chip size="small" variant="outlined" label={task.priority} />
                    <Chip size="small" variant="outlined" label={`담당 ${task.assignee_name || '-'}`} />
                    <Chip size="small" variant="outlined" label={`마감 ${task.due_date || '-'}`} />
                  </Stack>
                </Stack>
              </Paper>
            )) : <EmptyState message="이번 주 마감 작업이 없습니다." />}
          </Stack>
        </SectionCard>

        <SectionCard
          title="중요 공지"
          description="고정 공지 또는 운영 메모"
          icon={<CampaignRoundedIcon color="primary" fontSize="small" />}
        >
          {data.pinned_notice ? (
            <Paper
              variant="outlined"
              sx={{
                p: 2.5,
                borderRadius: 1,
                bgcolor: 'background.default',
              }}
            >
              <Stack spacing={1}>
                <Typography fontWeight={800}>{data.pinned_notice.title}</Typography>
                <Typography variant="body2" color="text.secondary">
                  {data.pinned_notice.content}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  업데이트 {data.pinned_notice.updated_at || '-'}
                </Typography>
              </Stack>
            </Paper>
          ) : (
            <EmptyState message="현재 고정 공지가 없습니다." />
          )}
        </SectionCard>
      </Box>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'repeat(3, minmax(0, 1fr))' },
          gap: 3,
        }}
      >
        <SectionCard
          title="최근 문서"
          description={`${data.recent_documents.length}건의 최근 업데이트 문서`}
          actionLabel="문서 보기"
          actionTo="/documents"
          icon={<DescriptionOutlinedIcon color="primary" fontSize="small" />}
        >
          <Stack spacing={1.25}>
            {data.recent_documents.length ? data.recent_documents.map((document) => (
              <Paper key={document.id} variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
                <Stack spacing={0.75}>
                  <Button
                    component={RouterLink}
                    to={`/documents/${document.id}`}
                    sx={{ justifyContent: 'flex-start', px: 0, textAlign: 'left' }}
                  >
                    {document.title}
                  </Button>
                  <Typography variant="body2" color="text.secondary">
                    {document.doc_type} · {document.author_name || '작성자 미지정'}
                  </Typography>
                </Stack>
              </Paper>
            )) : <EmptyState message="최근 문서가 없습니다." />}
          </Stack>
        </SectionCard>

        <SectionCard
          title="최근 WBS 업데이트"
          description={`${data.recent_tasks.length}건의 최근 업데이트 작업`}
          actionLabel="WBS 보기"
          actionTo="/wbs"
          icon={<SchemaOutlinedIcon color="primary" fontSize="small" />}
        >
          <Stack spacing={1.25}>
            {data.recent_tasks.length ? data.recent_tasks.map((task) => (
              <Paper key={task.id} variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
                <Stack spacing={0.75}>
                  <Button
                    component={RouterLink}
                    to={`/wbs/${task.id}`}
                    sx={{ justifyContent: 'flex-start', px: 0, textAlign: 'left', fontWeight: 700 }}
                  >
                    {task.title}
                  </Button>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Chip size="small" label={task.status} />
                    <Chip size="small" variant="outlined" label={task.priority} />
                  </Stack>
                </Stack>
              </Paper>
            )) : <EmptyState message="최근 WBS 업데이트가 없습니다." />}
          </Stack>
        </SectionCard>

        <SectionCard
          title="예정 일정"
          description={`${data.upcoming_schedules.length}건의 예정 일정`}
          actionLabel="일정 보기"
          actionTo="/schedules"
          icon={<EventOutlinedIcon color="primary" fontSize="small" />}
        >
          <Stack spacing={1.25}>
            {data.upcoming_schedules.length ? data.upcoming_schedules.map((item) => (
              <Paper key={item.id} variant="outlined" sx={{ p: 2, borderRadius: 1 }}>
                <Stack spacing={0.75}>
                  <Typography fontWeight={700}>{item.title}</Typography>
                  <Typography variant="body2" color="text.secondary">
                    {item.start_date} ~ {item.end_date}
                  </Typography>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    <Chip size="small" label={item.schedule_type} />
                    <Chip size="small" variant="outlined" label={`담당 ${item.assignee_name || '-'}`} />
                    {item.task_title ? <Chip size="small" variant="outlined" label={`WBS ${item.task_title}`} /> : null}
                  </Stack>
                </Stack>
              </Paper>
            )) : <EmptyState message="예정 일정이 없습니다." />}
          </Stack>
        </SectionCard>
      </Box>
    </Stack>
  )
}

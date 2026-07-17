import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import DescriptionOutlinedIcon from '@mui/icons-material/DescriptionOutlined'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
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
import { Link as RouterLink, useParams } from 'react-router-dom'
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { hiddenStatusChipSx } from '../theme'

function MetaBlock({ label, value }) {
  return (
    <Stack spacing={0.6}>
      <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.14em', fontWeight: 800 }}>
        {label}
      </Typography>
      <Typography variant="body1" fontWeight={700}>
        {value || '-'}
      </Typography>
    </Stack>
  )
}

export function WbsDetailPage() {
  const { taskId } = useParams()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const loadDetail = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet(`/api/wbs/${taskId}`)
        setData(payload)
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    loadDetail()
  }, [taskId])

  if (loading) {
    return (
      <Stack sx={{ py: 10, alignItems: 'center' }} spacing={2}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">작업 상세를 불러오는 중입니다...</Typography>
      </Stack>
    )
  }

  if (error || !data?.task) {
    return (
      <Stack spacing={3}>
        <PageHeader
          eyebrow="WORK BREAKDOWN STRUCTURE"
          title="작업 상세"
          description="작업 정보를 찾지 못했거나 불러오는 중 문제가 발생했습니다."
        />
        <Alert severity="error">{error || '작업을 찾을 수 없습니다.'}</Alert>
        <Button component={RouterLink} to="/wbs" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          작업 목록으로
        </Button>
      </Stack>
    )
  }

  const { task, linked_documents: linkedDocuments, is_completed: isCompleted } = data

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="WORK BREAKDOWN STRUCTURE"
        title={task.title}
        description={`${task.platform || 'Agentic Product Studio'} · ${task.assignee_name || '담당자 미지정'}`}
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/wbs" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          목록으로
        </Button>
        <Button variant="contained" startIcon={<EditRoundedIcon />} component={RouterLink} to={`/wbs/${task.id}/edit`}>
          작업 수정
        </Button>
      </Stack>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.35fr) minmax(320px, 0.65fr)' },
          gap: 3,
        }}
      >
        <Paper sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Stack spacing={2.5}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2} useFlexGap flexWrap="wrap">
              <Chip label={task.status} color={isCompleted ? 'success' : 'primary'} />
              <Chip label={task.priority} variant="outlined" />
              <Chip label={`진행률 ${task.progress || 0}%`} variant="outlined" />
              <Chip label={`마감 ${task.due_date || '-'}`} variant="outlined" />
            </Stack>

            <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
              {task.description || '설명이 없습니다.'}
            </Typography>

            {task.notes ? (
              <Paper variant="outlined" sx={{ p: 2.25, bgcolor: 'background.default' }}>
                <Stack spacing={0.75}>
                  <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.14em', fontWeight: 800 }}>
                    메모
                  </Typography>
                  <Typography sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>{task.notes}</Typography>
                </Stack>
              </Paper>
            ) : null}
          </Stack>
        </Paper>

        <Stack spacing={3}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2.5}>
              <Typography variant="h6">작업 메타데이터</Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', xl: '1fr' },
                  gap: 2.2,
                }}
              >
                <MetaBlock label="플랫폼" value={task.platform || 'Agentic Product Studio'} />
                <MetaBlock label="담당자" value={task.assignee_name || '-'} />
                <MetaBlock label="상위 작업" value={task.parent_title || '최상위 작업'} />
                <MetaBlock label="시작일" value={task.start_date || '-'} />
                <MetaBlock label="마감일" value={task.due_date || '-'} />
                <MetaBlock label="완료일" value={task.completed_date || '-'} />
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <DescriptionOutlinedIcon color="primary" fontSize="small" />
                <Typography variant="h6">연결 문서</Typography>
              </Stack>
              {linkedDocuments.length ? (
                linkedDocuments.map((document) => (
                  <Paper
                    key={document.id}
                    variant="outlined"
                    sx={{ p: 2, borderRadius: 1, bgcolor: 'background.default' }}
                  >
                    <Stack spacing={0.8}>
                      <Button
                        component={RouterLink}
                        to={`/documents/${document.id}`}
                        sx={{ justifyContent: 'flex-start', px: 0, textAlign: 'left' }}
                      >
                        {document.title}
                      </Button>
                      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                        <Chip size="small" label={document.doc_type} />
                        {document.is_hidden ? <Chip size="small" variant="outlined" label="숨김 문서" sx={hiddenStatusChipSx} /> : null}
                      </Stack>
                    </Stack>
                  </Paper>
                ))
              ) : (
                <Typography color="text.secondary">연결된 문서가 없습니다.</Typography>
              )}
            </Stack>
          </Paper>
        </Stack>
      </Box>
    </Stack>
  )
}

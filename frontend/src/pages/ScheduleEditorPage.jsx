import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { apiGet, apiJson } from '../api/client'
import { PageHeader } from '../components/PageHeader'

const initialForm = {
  title: '',
  description: '',
  schedule_type: '',
  assignee_id: '',
  wbs_task_id: '',
  start_date: '',
  end_date: '',
}

export function ScheduleEditorPage() {
  const { scheduleId } = useParams()
  const navigate = useNavigate()
  const isEditMode = Boolean(scheduleId)

  const [bootstrap, setBootstrap] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    let active = true

    const loadBootstrap = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet('/api/schedules/editor', isEditMode ? { schedule_id: scheduleId } : undefined)
        if (!active) {
          return
        }
        setBootstrap(payload)
        setForm({
          title: payload.schedule?.title || '',
          description: payload.schedule?.description || '',
          schedule_type: payload.schedule?.schedule_type || payload.schedule_types?.[0] || '',
          assignee_id: payload.schedule?.assignee_id || '',
          wbs_task_id: payload.schedule?.wbs_task_id || '',
          start_date: payload.schedule?.start_date || '',
          end_date: payload.schedule?.end_date || '',
        })
      } catch (fetchError) {
        if (active) {
          setError(fetchError.message)
        }
      } finally {
        if (active) {
          setLoading(false)
        }
      }
    }

    loadBootstrap()
    return () => {
      active = false
    }
  }, [isEditMode, scheduleId])

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (saving) {
      return
    }

    setSaving(true)
    setError('')
    setStatus('일정을 저장하는 중입니다...')
    try {
      const payload = await apiJson(isEditMode ? `/api/schedules/${scheduleId}` : '/api/schedules', {
        body: {
          ...form,
          assignee_id: form.assignee_id || null,
          wbs_task_id: form.wbs_task_id || null,
        },
      })
      navigate(payload.redirect_path)
    } catch (saveError) {
      setError(saveError.message)
      setStatus('일정 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!isEditMode || deleting || !window.confirm('이 일정을 삭제할까요?')) {
      return
    }

    setDeleting(true)
    setError('')
    setStatus('일정을 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/schedules/${scheduleId}`, { method: 'DELETE' })
      navigate(payload.redirect_path)
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('일정 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <Stack spacing={2} sx={{ py: 10, alignItems: 'center' }}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">일정 편집 화면을 준비하는 중입니다...</Typography>
      </Stack>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="SCHEDULES"
        title={isEditMode ? '일정 수정' : '새 일정'}
        description="일정 유형, 담당자, 연결 WBS, 기간을 React 화면에서 바로 관리할 수 있게 정리했습니다."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/schedules" variant="outlined">
          목록으로
        </Button>
        {isEditMode ? (
          <Button href={`/schedules/${scheduleId}/edit`} variant="text">
            기존 Flask 편집기 열기
          </Button>
        ) : null}
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}
      {status && !error ? <Alert severity="info">{status}</Alert> : null}

      <Paper component="form" onSubmit={handleSubmit} sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            <TextField
              label="일정명"
              value={form.title}
              onChange={(event) => updateField('title', event.target.value)}
            />
            <TextField
              select
              label="일정 유형"
              value={form.schedule_type}
              onChange={(event) => updateField('schedule_type', event.target.value)}
            >
              {(bootstrap?.schedule_types || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="담당자"
              value={form.assignee_id}
              onChange={(event) => updateField('assignee_id', event.target.value)}
            >
              <MenuItem value="">미지정</MenuItem>
              {(bootstrap?.members || []).map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="연결 WBS"
              value={form.wbs_task_id}
              onChange={(event) => updateField('wbs_task_id', event.target.value)}
            >
              <MenuItem value="">없음</MenuItem>
              {(bootstrap?.tasks || []).map((task) => (
                <MenuItem key={task.id} value={task.id}>
                  #{task.id} {task.title}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              type="date"
              label="시작일"
              value={form.start_date}
              onChange={(event) => updateField('start_date', event.target.value)}
              InputLabelProps={{ shrink: true }}
            />
            <TextField
              type="date"
              label="종료일"
              value={form.end_date}
              onChange={(event) => updateField('end_date', event.target.value)}
              InputLabelProps={{ shrink: true }}
            />
          </Box>

          <TextField
            label="설명"
            value={form.description}
            onChange={(event) => updateField('description', event.target.value)}
            multiline
            minRows={6}
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveRoundedIcon />}
              disabled={saving || deleting}
            >
              {saving ? '저장 중...' : isEditMode ? '변경 저장' : '일정 저장'}
            </Button>
            <Button component={RouterLink} to="/schedules" variant="outlined" disabled={saving || deleting}>
              취소
            </Button>
            {isEditMode ? (
              <Button
                type="button"
                color="error"
                variant="text"
                startIcon={deleting ? <CircularProgress size={16} color="inherit" /> : <DeleteOutlineRoundedIcon />}
                onClick={handleDelete}
                disabled={saving || deleting}
              >
                {deleting ? '삭제 중...' : '삭제'}
              </Button>
            ) : null}
          </Stack>
        </Stack>
      </Paper>
    </Stack>
  )
}

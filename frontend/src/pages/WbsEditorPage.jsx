import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  ListItemText,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { apiGet, apiJson, normalizeRedirectPath } from '../api/client'
import { PageHeader } from '../components/PageHeader'

const initialForm = {
  parent_id: '',
  title: '',
  description: '',
  assignee_id: '',
  platform: '',
  status: '',
  priority: '',
  start_date: '',
  due_date: '',
  completed_date: '',
  progress: 0,
  notes: '',
  document_ids: [],
}

function DateField({ label, value, onChange }) {
  return (
    <TextField
      type="date"
      label={label}
      value={value}
      onChange={onChange}
      InputLabelProps={{ shrink: true }}
      slotProps={{
        htmlInput: {
          'aria-label': label,
          className: value ? '' : 'date-input-empty',
        },
      }}
      sx={{
        '& input.date-input-empty::-webkit-datetime-edit': {
          color: 'transparent',
        },
        '& input.date-input-empty:focus::-webkit-datetime-edit': {
          color: 'inherit',
        },
      }}
    />
  )
}

export function WbsEditorPage() {
  const { taskId } = useParams()
  const navigate = useNavigate()
  const isEditMode = Boolean(taskId)

  const [bootstrap, setBootstrap] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const [statusMessage, setStatusMessage] = useState('')

  useEffect(() => {
    let active = true

    const loadBootstrap = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet('/api/wbs/editor', isEditMode ? { task_id: taskId } : undefined)
        if (!active) {
          return
        }
        setBootstrap(payload)
        setForm({
          parent_id: payload.task?.parent_id || '',
          title: payload.task?.title || '',
          description: payload.task?.description || '',
          assignee_id: payload.task?.assignee_id || '',
          platform: payload.task?.platform || payload.platforms?.[0] || '',
          status: payload.task?.status || payload.statuses?.[0] || '',
          priority: payload.task?.priority || payload.priorities?.[1] || payload.priorities?.[0] || '',
          start_date: payload.task?.start_date || '',
          due_date: payload.task?.due_date || '',
          completed_date: payload.task?.completed_date || '',
          progress: payload.task?.progress ?? 0,
          notes: payload.task?.notes || '',
          document_ids: payload.selected_document_ids || [],
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
  }, [isEditMode, taskId])

  const updateField = (key, value) => {
    setForm((prev) => {
      const next = { ...prev, [key]: value }
      const completedStatus = bootstrap?.statuses?.[3] || '완료'
      if (key === 'status' && value === completedStatus) {
        next.progress = 100
        if (!next.completed_date) {
          next.completed_date = new Date().toISOString().slice(0, 10)
        }
      }
      return next
    })
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (saving) {
      return
    }

    setSaving(true)
    setError('')
    setStatusMessage('WBS 작업을 저장하는 중입니다...')
    try {
      const payload = await apiJson(isEditMode ? `/api/wbs/${taskId}` : '/api/wbs', {
        body: {
          ...form,
          parent_id: form.parent_id || null,
          assignee_id: form.assignee_id || null,
          progress: Number(form.progress || 0),
        },
      })
      navigate(normalizeRedirectPath(payload.redirect_path))
    } catch (saveError) {
      setError(saveError.message)
      setStatusMessage('WBS 작업 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!isEditMode || deleting || !window.confirm('이 WBS 작업을 삭제할까요?')) {
      return
    }

    setDeleting(true)
    setError('')
    setStatusMessage('WBS 작업을 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/wbs/${taskId}`, { method: 'DELETE' })
      navigate(normalizeRedirectPath(payload.redirect_path), { replace: true })
    } catch (deleteError) {
      setError(deleteError.message)
      setStatusMessage('WBS 작업 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <Stack spacing={2} sx={{ py: 10, alignItems: 'center' }}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">WBS 편집 화면을 준비하는 중입니다...</Typography>
      </Stack>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="WORK BREAKDOWN STRUCTURE"
        title={isEditMode ? 'WBS 작업 수정' : '새 WBS 작업'}
        description="상위 작업, 담당자, 상태, 우선순위, 연관 문서까지 한 화면에서 바로 관리할 수 있게 정리했습니다."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/wbs" variant="outlined">
          목록으로
        </Button>
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}
      {statusMessage && !error ? <Alert severity="info">{statusMessage}</Alert> : null}

      <Paper component="form" onSubmit={handleSubmit} sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', lg: 'repeat(2, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            <TextField label="작업명" value={form.title} onChange={(event) => updateField('title', event.target.value)} />
            <TextField
              select
              label="상위 작업"
              value={form.parent_id}
              onChange={(event) => updateField('parent_id', event.target.value)}
            >
              <MenuItem value="">없음</MenuItem>
              {(bootstrap?.parent_tasks || []).map((task) => (
                <MenuItem key={task.id} value={task.id}>
                  #{task.id} {task.title}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="대상 플랫폼"
              value={form.platform}
              onChange={(event) => updateField('platform', event.target.value)}
            >
              {(bootstrap?.platforms || []).map((option) => (
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
                  {member.name}{member.part ? ` · ${member.part}` : ''}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="상태"
              value={form.status}
              onChange={(event) => updateField('status', event.target.value)}
            >
              {(bootstrap?.statuses || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="우선순위"
              value={form.priority}
              onChange={(event) => updateField('priority', event.target.value)}
            >
              {(bootstrap?.priorities || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              type="number"
              label="진행률"
              value={form.progress}
              onChange={(event) => updateField('progress', event.target.value)}
              inputProps={{ min: 0, max: 100 }}
            />
            <DateField
              label="시작일"
              value={form.start_date}
              onChange={(event) => updateField('start_date', event.target.value)}
            />
            <DateField
              label="종료 예정일"
              value={form.due_date}
              onChange={(event) => updateField('due_date', event.target.value)}
            />
            <DateField
              label="실제 완료일"
              value={form.completed_date}
              onChange={(event) => updateField('completed_date', event.target.value)}
            />
          </Box>

          <TextField
            label="설명"
            value={form.description}
            onChange={(event) => updateField('description', event.target.value)}
            multiline
            minRows={4}
          />

          <TextField
            select
            label="연관 문서"
            value={form.document_ids}
            onChange={(event) => updateField('document_ids', event.target.value)}
            SelectProps={{
              multiple: true,
              renderValue: (selected) =>
                selected.length
                  ? selected
                      .map((id) => bootstrap?.documents?.find((document) => document.id === id)?.title || `#${id}`)
                      .join(', ')
                  : '선택 없음',
            }}
            helperText="여러 문서를 선택해 이 작업과 연결할 수 있습니다."
          >
            {(bootstrap?.documents || []).map((document) => (
              <MenuItem key={document.id} value={document.id}>
                <Checkbox checked={form.document_ids.includes(document.id)} />
                <ListItemText
                  primary={document.title}
                  secondary={`${document.doc_type}${document.is_hidden ? ' · 숨김' : ''}`}
                />
              </MenuItem>
            ))}
          </TextField>

          <TextField
            label="메모"
            value={form.notes}
            onChange={(event) => updateField('notes', event.target.value)}
            multiline
            minRows={4}
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveRoundedIcon />}
              disabled={saving || deleting}
            >
              {saving ? '저장 중...' : isEditMode ? '변경 저장' : '작업 생성'}
            </Button>
            <Button component={RouterLink} to="/wbs" variant="outlined" disabled={saving || deleting}>
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

import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  FormControlLabel,
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
  name: '',
  role: '',
  part: '',
  contact: '',
  is_active: true,
}

export function MemberEditorPage() {
  const { memberId } = useParams()
  const navigate = useNavigate()
  const isEditMode = Boolean(memberId)

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
        const payload = await apiGet('/api/members/editor', isEditMode ? { member_id: memberId } : undefined)
        if (!active) {
          return
        }
        setForm({
          name: payload.member?.name || '',
          role: payload.member?.role || '',
          part: payload.member?.part || '',
          contact: payload.member?.contact || '',
          is_active: payload.member ? Boolean(payload.member.is_active) : true,
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
  }, [isEditMode, memberId])

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
    setStatus('멤버 정보를 저장하는 중입니다...')
    try {
      const payload = await apiJson(isEditMode ? `/api/members/${memberId}` : '/api/members', {
        body: form,
      })
      navigate(payload.redirect_path)
    } catch (saveError) {
      setError(saveError.message)
      setStatus('멤버 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (
      !isEditMode ||
      deleting ||
      !window.confirm('이 멤버를 삭제할까요? 연결된 담당자 정보는 해제됩니다.')
    ) {
      return
    }

    setDeleting(true)
    setError('')
    setStatus('멤버를 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/members/${memberId}`, { method: 'DELETE' })
      navigate(payload.redirect_path)
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('멤버 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <Stack spacing={2} sx={{ py: 10, alignItems: 'center' }}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">멤버 편집 화면을 준비하는 중입니다...</Typography>
      </Stack>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="MEMBERS"
        title={isEditMode ? '멤버 수정' : '새 멤버'}
        description="담당자 정보와 활성 상태를 React 화면에서 바로 관리할 수 있게 정리했습니다."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/members" variant="outlined">
          목록으로
        </Button>
        {isEditMode ? (
          <Button href={`/members/${memberId}/edit`} variant="text">
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
            <TextField label="이름" value={form.name} onChange={(event) => updateField('name', event.target.value)} />
            <TextField label="역할" value={form.role} onChange={(event) => updateField('role', event.target.value)} />
            <TextField label="담당 파트" value={form.part} onChange={(event) => updateField('part', event.target.value)} />
            <TextField
              label="이메일 또는 Discord ID"
              value={form.contact}
              onChange={(event) => updateField('contact', event.target.value)}
            />
          </Box>

          <FormControlLabel
            control={
              <Checkbox
                checked={form.is_active}
                onChange={(event) => updateField('is_active', event.target.checked)}
              />
            }
            label="활성 상태"
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveRoundedIcon />}
              disabled={saving || deleting}
            >
              {saving ? '저장 중...' : isEditMode ? '변경 저장' : '멤버 저장'}
            </Button>
            <Button component={RouterLink} to="/members" variant="outlined" disabled={saving || deleting}>
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

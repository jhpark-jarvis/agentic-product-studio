import AddRoundedIcon from '@mui/icons-material/AddRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import UploadFileRoundedIcon from '@mui/icons-material/UploadFileRounded'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Divider,
  FormControlLabel,
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { apiForm, apiGet, apiJson, normalizeRedirectPath } from '../api/client'
import { AssetGroupTree } from '../components/AssetGroupTree'
import { PageHeader } from '../components/PageHeader'

const NEW_TYPE_SENTINEL = '__new_asset_type__'

const initialForm = {
  title: '',
  asset_type: '',
  category: '',
  tags: '',
  status: '사용 가능',
  is_hidden: false,
  created_by: '',
  notes: '',
}

export function AssetEditorPage() {
  const { assetId } = useParams()
  const navigate = useNavigate()
  const isEditMode = Boolean(assetId)
  const fileInputRef = useRef(null)

  const [form, setForm] = useState(initialForm)
  const [customAssetType, setCustomAssetType] = useState('')
  const [file, setFile] = useState(null)
  const [currentAsset, setCurrentAsset] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [groupBusy, setGroupBusy] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')
  const [bootstrap, setBootstrap] = useState(null)

  useEffect(() => {
    let active = true
    const loadBootstrap = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet('/api/assets/editor', isEditMode ? { asset_id: assetId } : undefined)
        if (!active) {
          return
        }
        setBootstrap(payload)
        setCurrentAsset(payload.asset || null)
        setForm({
          title: payload.asset?.title || '',
          asset_type: payload.asset?.asset_type || '',
          category: payload.asset?.category || '',
          tags: (payload.tags || []).join(', '),
          status: payload.asset?.status || '사용 가능',
          is_hidden: payload.asset ? Boolean(payload.asset.is_hidden) : false,
          created_by: payload.asset?.created_by || '',
          notes: payload.asset?.notes || '',
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
  }, [assetId, isEditMode])

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const applyGroupBrowser = (groupBrowser) => {
    setBootstrap((prev) => ({
      ...(prev || {}),
      group_browser: groupBrowser,
    }))
  }

  const replaceGroupPrefix = (currentPath, previousPath, nextPath) => {
    if (!currentPath || !previousPath) {
      return currentPath
    }
    if (currentPath === previousPath) {
      return nextPath
    }
    if (currentPath.startsWith(`${previousPath}/`)) {
      return `${nextPath}${currentPath.slice(previousPath.length)}`
    }
    return currentPath
  }

  const resolvedAssetType = form.asset_type === NEW_TYPE_SENTINEL ? customAssetType.trim() : form.asset_type

  const handleCreateGroup = async ({ parentPath, name }) => {
    setGroupBusy(true)
    setError('')
    try {
      const payload = await apiJson('/api/assets/groups', {
        body: { parent_path: parentPath, name },
      })
      applyGroupBrowser(payload.group_browser)
      updateField('category', payload.path)
    } catch (groupError) {
      setError(groupError.message)
      throw groupError
    } finally {
      setGroupBusy(false)
    }
  }

  const handleRenameGroup = async ({ path, newName }) => {
    setGroupBusy(true)
    setError('')
    try {
      const payload = await apiJson('/api/assets/groups/rename', {
        body: { path, new_name: newName },
      })
      applyGroupBrowser(payload.group_browser)
      updateField('category', replaceGroupPrefix(form.category, path, payload.path))
    } catch (groupError) {
      setError(groupError.message)
      throw groupError
    } finally {
      setGroupBusy(false)
    }
  }

  const handleDeleteGroup = async ({ path }) => {
    setGroupBusy(true)
    setError('')
    try {
      const payload = await apiJson('/api/assets/groups', {
        method: 'DELETE',
        body: { path },
      })
      applyGroupBrowser(payload.group_browser)
      if (form.category === path || form.category.startsWith(`${path}/`)) {
        updateField('category', '')
      }
    } catch (groupError) {
      setError(groupError.message)
      throw groupError
    } finally {
      setGroupBusy(false)
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (saving) {
      return
    }
    setSaving(true)
    setError('')
    setStatus('Asset 정보를 저장하는 중입니다...')
    try {
      const body = new FormData()
      const submitForm = {
        ...form,
        asset_type: resolvedAssetType,
      }
      Object.entries(submitForm).forEach(([key, value]) => {
        if (typeof value === 'boolean') {
          if (value) {
            body.set(key, '1')
          }
          return
        }
        if (value !== '' && value !== null && value !== undefined) {
          body.set(key, value)
        }
      })
      if (file) {
        body.set('file', file)
      }

      const payload = await apiForm(isEditMode ? `/api/assets/${assetId}` : '/api/assets', body)
      navigate(normalizeRedirectPath(payload.redirect_path))
    } catch (saveError) {
      setError(saveError.message)
      setStatus('Asset 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async () => {
    if (!isEditMode || deleting || !window.confirm('이 Asset을 삭제할까요? 연결된 파일도 함께 삭제됩니다.')) {
      return
    }
    setDeleting(true)
    setError('')
    setStatus('Asset을 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/assets/${assetId}`, { method: 'DELETE' })
      navigate(normalizeRedirectPath(payload.redirect_path), { replace: true })
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('Asset 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  if (loading) {
    return (
      <Stack spacing={2} sx={{ py: 10, alignItems: 'center' }}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">Asset 편집 화면을 준비하는 중입니다...</Typography>
      </Stack>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="ASSETS"
        title={isEditMode ? 'Asset 수정' : '새 Asset 등록'}
        description="파일 교체, 상태 변경, 분류 수정, 태그 정리를 한 화면에서 처리할 수 있는 Asset 편집 화면입니다."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/assets" variant="outlined">
          목록으로
        </Button>
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
              label="제목"
              value={form.title}
              onChange={(event) => updateField('title', event.target.value)}
            />
            <TextField
              select
              label="Asset 유형"
              value={form.asset_type}
              onChange={(event) => updateField('asset_type', event.target.value)}
              helperText="대표적인 형식을 고르거나 새 유형을 직접 추가할 수 있습니다."
            >
              <MenuItem value="">미지정</MenuItem>
              {(bootstrap?.asset_type_options || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
              <Divider />
              <MenuItem value={NEW_TYPE_SENTINEL}>
                <Stack direction="row" spacing={1} alignItems="center">
                  <AddRoundedIcon fontSize="small" />
                  <span>Asset 유형 추가</span>
                </Stack>
              </MenuItem>
            </TextField>

            {form.asset_type === NEW_TYPE_SENTINEL ? (
              <TextField
                label="새 Asset 유형"
                value={customAssetType}
                onChange={(event) => setCustomAssetType(event.target.value)}
                placeholder="예: effect, portrait, cutscene"
                helperText="저장하면 이번 Asset 유형으로 바로 사용됩니다."
              />
            ) : null}

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
              label="태그"
              value={form.tags}
              onChange={(event) => updateField('tags', event.target.value)}
              placeholder="쉼표로 구분"
              helperText="태그는 검색, 연결, 세부 분류를 위한 키워드입니다. 그룹(폴더)보다 더 세밀한 구분에 사용합니다."
            />
            <TextField
              select
              label="등록자"
              value={form.created_by}
              onChange={(event) => updateField('created_by', event.target.value)}
            >
              <MenuItem value="">미지정</MenuItem>
              {(bootstrap?.members || []).map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name}
                </MenuItem>
              ))}
            </TextField>
          </Box>

          <Paper variant="outlined" sx={{ p: 2.25, bgcolor: 'background.default' }}>
            <Stack spacing={1.5}>
              <Typography variant="subtitle1" fontWeight={800}>
                그룹(폴더) 선택
              </Typography>
              <Typography variant="body2" color="text.secondary">
                폴더는 트리에서 선택하거나 바로 생성할 수 있습니다. 태그는 Asset 세부 검색용, 그룹은 큰 분류용으로 사용합니다.
              </Typography>
              <TextField
                label="선택된 그룹"
                value={form.category || ''}
                placeholder="그룹 미지정"
                InputProps={{ readOnly: true }}
                helperText="선택된 폴더 경로가 여기에 반영됩니다."
              />
              <AssetGroupTree
                tree={bootstrap?.group_browser?.tree || []}
                selectedPath={form.category}
                ungroupedCount={bootstrap?.group_browser?.ungrouped_asset_count || 0}
                ungroupedLabel="그룹 미지정"
                manageable
                busy={groupBusy}
                onSelect={(path) => updateField('category', path)}
                onCreate={handleCreateGroup}
                onRename={handleRenameGroup}
                onDelete={handleDeleteGroup}
              />
            </Stack>
          </Paper>

          <Paper variant="outlined" sx={{ p: 2.25, bgcolor: 'background.default' }}>
            <Stack spacing={1.5}>
              <Typography variant="subtitle1" fontWeight={800}>
                파일 업로드
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {isEditMode
                  ? '새 파일을 선택하면 기존 파일을 교체합니다.'
                  : '등록할 파일을 선택하세요.'}
              </Typography>
              <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25} alignItems={{ sm: 'center' }}>
                <Button
                  type="button"
                  variant="outlined"
                  startIcon={<UploadFileRoundedIcon />}
                  onClick={() => fileInputRef.current?.click()}
                >
                  {isEditMode ? '교체 파일 선택' : '파일 선택'}
                </Button>
                <Typography variant="body2" color="text.secondary">
                  {file?.name || currentAsset?.original_filename || '선택된 파일 없음'}
                </Typography>
              </Stack>
              <input
                ref={fileInputRef}
                type="file"
                style={{ display: 'none' }}
                onChange={(event) => setFile(event.target.files?.[0] || null)}
              />
            </Stack>
          </Paper>

          <TextField
            label="메모"
            value={form.notes}
            onChange={(event) => updateField('notes', event.target.value)}
            multiline
            minRows={5}
          />

          <FormControlLabel
            control={
              <Checkbox
                checked={form.is_hidden}
                onChange={(event) => updateField('is_hidden', event.target.checked)}
              />
            }
            label="숨김 Asset"
          />

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveRoundedIcon />}
              disabled={saving || deleting}
            >
              {saving ? '저장 중...' : isEditMode ? '변경 저장' : 'Asset 등록'}
            </Button>
            <Button component={RouterLink} to="/assets" variant="outlined" disabled={saving || deleting}>
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

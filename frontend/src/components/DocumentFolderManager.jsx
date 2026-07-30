import AddRoundedIcon from '@mui/icons-material/AddRounded'
import CreateRoundedIcon from '@mui/icons-material/CreateRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import FolderOpenRoundedIcon from '@mui/icons-material/FolderOpenRounded'
import {
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { apiGet, apiJson } from '../api/client'

const initialForm = {
  doc_type: '',
  name: '',
}

export function DocumentFolderManager({ onFoldersChanged }) {
  const [folders, setFolders] = useState([])
  const [documentTypes, setDocumentTypes] = useState([])
  const [dialogMode, setDialogMode] = useState('')
  const [activeFolder, setActiveFolder] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadFolders = async () => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/documents/folders')
      setFolders(payload.folders || [])
      setDocumentTypes(payload.document_types || [])
      onFoldersChanged?.(payload.folders || [])
    } catch (loadError) {
      setError(loadError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadFolders()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const closeDialog = () => {
    if (busy) {
      return
    }
    setDialogMode('')
    setActiveFolder(null)
    setForm(initialForm)
    setError('')
  }

  const openCreate = () => {
    setDialogMode('create')
    setActiveFolder(null)
    setForm({ doc_type: documentTypes[0] || '', name: '' })
    setError('')
  }

  const openManage = () => {
    setDialogMode('manage')
    setError('')
  }

  const openRename = (folder) => {
    setDialogMode('rename')
    setActiveFolder(folder)
    setForm({ doc_type: folder.doc_type, name: folder.name })
    setError('')
  }

  const openDelete = (folder) => {
    setDialogMode('delete')
    setActiveFolder(folder)
    setError('')
  }

  const refreshAfterChange = async () => {
    const payload = await apiGet('/api/documents/folders')
    const nextFolders = payload.folders || []
    setFolders(nextFolders)
    setDocumentTypes(payload.document_types || [])
    onFoldersChanged?.(nextFolders)
  }

  const handleSubmit = async () => {
    if (busy) {
      return
    }
    if (dialogMode === 'delete') {
      if (!activeFolder || !window.confirm("'" + activeFolder.name + "' 폴더를 삭제할까요?")) {
        return
      }
    } else if (!form.doc_type || !form.name.trim()) {
      setError('문서 유형과 폴더 이름을 입력해주세요.')
      return
    }

    setBusy(true)
    setError('')
    try {
      if (dialogMode === 'create') {
        await apiJson('/api/documents/folders', { body: form })
      } else if (dialogMode === 'rename') {
        await apiJson('/api/documents/folders/' + activeFolder.id, {
          method: 'PATCH',
          body: form,
        })
      } else {
        await apiJson('/api/documents/folders/' + activeFolder.id, { method: 'DELETE' })
      }
      await refreshAfterChange()
      closeDialog()
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <>
      <Button variant="outlined" startIcon={<FolderOpenRoundedIcon />} onClick={openManage} disabled={loading}>
        폴더 관리
      </Button>

      <Dialog open={Boolean(dialogMode)} onClose={closeDialog} fullWidth maxWidth={dialogMode === 'manage' ? 'md' : 'xs'}>
        <DialogTitle>
          {dialogMode === 'manage'
            ? '문서 폴더 관리'
            : dialogMode === 'create'
              ? '문서 폴더 추가'
              : dialogMode === 'rename'
                ? '문서 폴더 이름 변경'
                : '문서 폴더 삭제'}
        </DialogTitle>
        <DialogContent>
          {dialogMode === 'manage' ? (
            <Stack spacing={1.25} sx={{ pt: 1 }}>
              <Typography variant="body2" color="text.secondary">
                문서 유형별 폴더를 만들고 이름을 변경하거나 정리할 수 있습니다.
              </Typography>
              {error ? <Typography color="error">{error}</Typography> : null}
              {loading ? (
                <Typography color="text.secondary">폴더 목록을 불러오는 중입니다...</Typography>
              ) : folders.length ? (
                folders.map((folder) => (
                  <Stack
                    key={folder.id}
                    direction={{ xs: 'column', sm: 'row' }}
                    spacing={1}
                    sx={{
                      alignItems: { sm: 'center' },
                      justifyContent: 'space-between',
                      px: 1.5,
                      py: 1.25,
                      border: '1px solid',
                      borderColor: 'divider',
                      borderRadius: 1.5,
                    }}
                  >
                    <Stack direction="row" spacing={1} sx={{ alignItems: 'center', minWidth: 0 }}>
                      <Chip size="small" label={folder.doc_type} />
                      <Typography fontWeight={700} noWrap>
                        {folder.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        문서 {folder.document_count || 0}건
                      </Typography>
                    </Stack>
                    <Stack direction="row" spacing={0.5}>
                      <Button size="small" startIcon={<CreateRoundedIcon />} onClick={() => openRename(folder)}>
                        이름 변경
                      </Button>
                      <Button
                        size="small"
                        color="error"
                        startIcon={<DeleteOutlineRoundedIcon />}
                        onClick={() => openDelete(folder)}
                      >
                        삭제
                      </Button>
                    </Stack>
                  </Stack>
                ))
              ) : (
                <Typography color="text.secondary">등록된 문서 폴더가 없습니다.</Typography>
              )}
            </Stack>
          ) : dialogMode === 'delete' ? (
            <Stack spacing={1} sx={{ pt: 1 }}>
              {error ? <Typography color="error">{error}</Typography> : null}
              <Typography color="text.secondary">
                {activeFolder?.doc_type} / {activeFolder?.name} 폴더를 삭제합니다. 문서가 연결된 폴더는 삭제할 수 없습니다.
              </Typography>
            </Stack>
          ) : (
            <Stack spacing={2} sx={{ pt: 1 }}>
              <TextField
                select
                label="문서 유형"
                value={form.doc_type}
                onChange={(event) => setForm((prev) => ({ ...prev, doc_type: event.target.value }))}
                disabled={dialogMode === 'rename'}
              >
                {documentTypes.map((docType) => (
                  <MenuItem key={docType} value={docType}>
                    {docType}
                  </MenuItem>
                ))}
              </TextField>
              <TextField
                autoFocus
                label="폴더 이름"
                value={form.name}
                onChange={(event) => setForm((prev) => ({ ...prev, name: event.target.value }))}
                placeholder="예: 기획서, 개발, 참고자료"
                error={Boolean(error)}
                helperText={error || '같은 문서 유형 안에서 중복될 수 없습니다.'}
              />
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          {dialogMode === 'manage' ? (
            <Button onClick={openCreate} variant="contained" startIcon={<AddRoundedIcon />}>
              폴더 추가
            </Button>
          ) : (
            <>
              <Button onClick={openManage} disabled={busy}>
                취소
              </Button>
              <Button
                onClick={handleSubmit}
                variant="contained"
                color={dialogMode === 'delete' ? 'error' : 'primary'}
                disabled={busy || (dialogMode !== 'delete' && (!form.doc_type || !form.name.trim()))}
              >
                {busy ? '처리 중...' : dialogMode === 'delete' ? '삭제' : '저장'}
              </Button>
            </>
          )}
          <Button onClick={closeDialog} disabled={busy}>
            닫기
          </Button>
        </DialogActions>
      </Dialog>
    </>
  )
}

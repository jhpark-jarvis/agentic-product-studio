import AddPhotoAlternateRoundedIcon from '@mui/icons-material/AddPhotoAlternateRounded'
import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import AutoFixHighRoundedIcon from '@mui/icons-material/AutoFixHighRounded'
import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import CodeRoundedIcon from '@mui/icons-material/CodeRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import EditNoteRoundedIcon from '@mui/icons-material/EditNoteRounded'
import FormatBoldRoundedIcon from '@mui/icons-material/FormatBoldRounded'
import LinkRoundedIcon from '@mui/icons-material/LinkRounded'
import SaveRoundedIcon from '@mui/icons-material/SaveRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  MenuItem,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { apiForm, apiGet, apiJson, normalizeRedirectPath } from '../api/client'
import { hiddenStatusChipSx } from '../theme'
import { PageHeader } from '../components/PageHeader'

const initialForm = {
  asset_draft_key: '',
  title: '',
  doc_type: '',
  folder_id: '',
  new_folder_name: '',
  author_id: '',
  tags: '',
  is_hidden: false,
  related_task_ids: [],
  content: '',
}

function useDebouncedEffect(callback, delay, deps) {
  useEffect(() => {
    const handle = window.setTimeout(callback, delay)
    return () => window.clearTimeout(handle)
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps
}

export function DocumentEditorPage() {
  const { documentId } = useParams()
  const navigate = useNavigate()
  const isEditMode = Boolean(documentId)
  const fileInputRef = useRef(null)
  const textareaRef = useRef(null)
  const editorSelectionRef = useRef({ start: 0, end: 0 })
  const [bootstrap, setBootstrap] = useState(null)
  const [form, setForm] = useState(initialForm)
  const [previewHtml, setPreviewHtml] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [formatting, setFormatting] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('미리보기를 준비하는 중입니다...')
  const [previewPending, setPreviewPending] = useState(false)
  const [linkSearchOpen, setLinkSearchOpen] = useState(false)
  const [linkQuery, setLinkQuery] = useState('')
  const [linkResults, setLinkResults] = useState([])
  const [searchingLinks, setSearchingLinks] = useState(false)
  const [floatingBarCollapsed, setFloatingBarCollapsed] = useState(false)
  const [deletingAssetIds, setDeletingAssetIds] = useState([])

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet(
          '/api/documents/editor',
          documentId ? { document_id: documentId } : undefined,
        )

        setBootstrap(payload)
        setForm({
          asset_draft_key: payload.asset_draft_key || '',
          title: payload.document?.title || '',
          doc_type: payload.document?.doc_type || payload.selected_type || payload.document_types?.[0] || '',
          folder_id: payload.document?.folder_id || '',
          new_folder_name: '',
          author_id: payload.document?.author_id || '',
          tags: payload.tags?.join(', ') || '',
          is_hidden: Boolean(payload.document?.is_hidden),
          related_task_ids: payload.related_task_ids || [],
          content: payload.document?.content || '',
        })
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [documentId])

  useDebouncedEffect(
    async () => {
      if (loading) {
        return
      }

      setPreviewPending(true)
      setStatus('미리보기를 렌더링하는 중입니다...')
      try {
        const body = new FormData()
        body.set('content', form.content)
        const payload = await apiForm('/documents/preview-markdown', body)
        setPreviewHtml(payload.html || '')
        setStatus('미리보기가 동기화되었습니다.')
      } catch (_error) {
        setStatus('미리보기를 불러오지 못했습니다.')
      } finally {
        setPreviewPending(false)
      }
    },
    180,
    [form.content, loading],
  )

  useDebouncedEffect(
    async () => {
      if (!linkSearchOpen) {
        return
      }

      const keyword = linkQuery.trim()
      if (!keyword) {
        setLinkResults([])
        return
      }

      setSearchingLinks(true)
      try {
        const payload = await apiGet('/documents/search-links', { q: keyword, limit: 12 })
        setLinkResults(payload.items || [])
      } catch (_error) {
        setLinkResults([])
      } finally {
        setSearchingLinks(false)
      }
    },
    180,
    [linkQuery, linkSearchOpen],
  )

  const folderOptions = useMemo(() => {
    return (bootstrap?.document_folders || []).filter((folder) => {
      return !form.doc_type || folder.doc_type === form.doc_type
    })
  }, [bootstrap?.document_folders, form.doc_type])

  const busyFlags = [
    saving ? '저장 중' : null,
    uploading ? '이미지 업로드 중' : null,
    formatting ? '코드 정리 중' : null,
    previewPending ? '미리보기 동기화 중' : null,
  ].filter(Boolean)

  const updateField = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }))
  }

  const syncEditorSelection = () => {
    const textarea = textareaRef.current
    if (!textarea) {
      return
    }

    editorSelectionRef.current = {
      start: textarea.selectionStart ?? 0,
      end: textarea.selectionEnd ?? textarea.selectionStart ?? 0,
    }
  }

  const preserveEditorSelection = (event) => {
    syncEditorSelection()

    if (document.activeElement === textareaRef.current) {
      event.preventDefault()
    }
  }

  const openLinkSearch = () => {
    syncEditorSelection()
    setLinkSearchOpen(true)
  }

  const openImagePicker = () => {
    syncEditorSelection()
    fileInputRef.current?.click()
  }

  const focusEditorSelection = (start, end = start) => {
    const textarea = textareaRef.current
    if (!textarea) {
      return
    }

    const scrollX = window.scrollX
    const scrollY = window.scrollY
    const textareaScrollTop = textarea.scrollTop
    const textareaScrollLeft = textarea.scrollLeft

    textarea.focus({ preventScroll: true })
    textarea.setSelectionRange(start, end)
    textarea.scrollTop = textareaScrollTop
    textarea.scrollLeft = textareaScrollLeft
    window.scrollTo(scrollX, scrollY)
    editorSelectionRef.current = { start, end }
  }

  const toolbarActions = [
    {
      key: 'h1',
      label: 'H1',
      onClick: () => insertAtCursor('# {selection}', '제목'),
    },
    {
      key: 'h2',
      label: 'H2',
      onClick: () => insertAtCursor('## {selection}', '소제목'),
    },
    {
      key: 'list',
      label: 'List',
      onClick: () => insertAtCursor('- {selection}', '목록'),
    },
    {
      key: 'bold',
      label: 'Bold',
      onClick: () => insertAtCursor('**{selection}**', '강조'),
    },
    {
      key: 'inline-code',
      label: 'Code',
      onClick: () => insertAtCursor('`{selection}`', 'code'),
    },
    {
      key: 'code-block',
      label: 'Block',
      onClick: () => insertAtCursor('```\n{selection}\n```', 'code'),
    },
  ]

  const floatingActions = [
    {
      key: 'float-h1',
      label: 'H1',
      icon: <EditNoteRoundedIcon fontSize="small" />,
      onClick: () => insertAtCursor('# {selection}', '제목'),
    },
    {
      key: 'float-code',
      label: '코드',
      icon: <CodeRoundedIcon fontSize="small" />,
      onClick: () => insertAtCursor('```\n{selection}\n```', 'code'),
    },
    {
      key: 'float-bold',
      label: '강조',
      icon: <FormatBoldRoundedIcon fontSize="small" />,
      onClick: () => insertAtCursor('**{selection}**', '강조'),
    },
    {
      key: 'float-image',
      label: '이미지',
      icon: <AddPhotoAlternateRoundedIcon fontSize="small" />,
      onClick: openImagePicker,
      disabled: uploading || saving,
    },
    {
      key: 'float-link',
      label: '문서 검색',
      icon: <LinkRoundedIcon fontSize="small" />,
      onClick: openLinkSearch,
    },
  ]

  const insertAtCursor = (snippet, fallbackSelection = '') => {
    const textarea = textareaRef.current
    const savedSelection = editorSelectionRef.current
    if (!textarea) {
      updateField('content', `${form.content}${snippet}`)
      return
    }

    const hasTextareaFocus = document.activeElement === textarea
    const start = hasTextareaFocus ? (textarea.selectionStart ?? form.content.length) : savedSelection.start
    const end = hasTextareaFocus ? (textarea.selectionEnd ?? form.content.length) : savedSelection.end
    const selected = form.content.slice(start, end) || fallbackSelection
    const nextSnippet = snippet.replace('{selection}', selected)
    const nextValue = `${form.content.slice(0, start)}${nextSnippet}${form.content.slice(end)}`
    updateField('content', nextValue)

    requestAnimationFrame(() => {
      const cursor = start + nextSnippet.length
      focusEditorSelection(cursor, cursor)
    })
  }

  const handleFormat = async () => {
    setFormatting(true)
    setStatus('코드 블록을 정리하는 중입니다...')
    try {
      const body = new FormData()
      body.set('content', form.content)
      const payload = await apiForm('/documents/format-markdown', body)
      updateField('content', payload.content || form.content)
      setStatus('코드 정리가 적용되었습니다.')
    } catch (_error) {
      setStatus('코드 정리에 실패했습니다.')
    } finally {
      setFormatting(false)
    }
  }

  const handleImageUpload = async (file) => {
    if (!file || !file.type.startsWith('image/')) {
      return
    }

    setUploading(true)
    setStatus('이미지를 업로드하는 중입니다...')
    try {
      const body = new FormData()
      body.set('image', file)
      body.set('alt', file.name.replace(/\.[^.]+$/, ''))
      if (documentId) {
        body.set('document_id', documentId)
      }
      if (form.asset_draft_key) {
        body.set('draft_key', form.asset_draft_key)
      }

      const payload = await apiForm('/documents/upload-image', body)
      insertAtCursor(`\n${payload.markdown}\n`)
      setStatus('이미지 업로드가 완료되었습니다.')
    } catch (uploadError) {
      setStatus(uploadError.message || '이미지 업로드에 실패했습니다.')
    } finally {
      setUploading(false)
      setDragActive(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (saving) {
      return
    }

    setSaving(true)
    setError('')
    setStatus('문서를 저장하는 중입니다...')
    try {
      const payload = await apiJson(
        isEditMode ? `/api/documents/${documentId}` : '/api/documents',
        {
          body: {
            ...form,
            author_id: form.author_id || null,
            folder_id: form.folder_id || null,
            new_folder_name: form.new_folder_name,
            related_task_ids: form.related_task_ids,
            is_hidden: form.is_hidden,
          },
        },
      )

      navigate(normalizeRedirectPath(payload.redirect_path))
    } catch (saveError) {
      setError(saveError.message)
      setStatus('문서 저장에 실패했습니다.')
    } finally {
      setSaving(false)
    }
  }

  const handleDeleteAsset = async (assetId) => {
    if (!documentId) {
      return
    }
    if (deletingAssetIds.includes(assetId)) {
      return
    }
    if (!window.confirm('이 이미지 자산을 삭제할까요? 본문에 남아 있는 이미지 링크는 직접 같이 정리해야 합니다.')) {
      return
    }

    setDeletingAssetIds((prev) => [...prev, assetId])
    setStatus('이미지 자산을 삭제하는 중입니다...')
    try {
      await apiJson(`/api/documents/${documentId}/assets/${assetId}`, { method: 'DELETE' })
      setBootstrap((prev) => {
        if (!prev) {
          return prev
        }
        return {
          ...prev,
          assets: (prev.assets || []).filter((asset) => asset.id !== assetId),
        }
      })
      setStatus('이미지 자산을 삭제했습니다.')
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('이미지 자산 삭제에 실패했습니다.')
    } finally {
      setDeletingAssetIds((prev) => prev.filter((id) => id !== assetId))
    }
  }

  if (loading) {
    return (
      <Stack sx={{ py: 10, alignItems: 'center' }} spacing={2}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">문서 편집 화면을 불러오는 중입니다...</Typography>
      </Stack>
    )
  }

  if (error && !bootstrap) {
    return (
      <Stack spacing={3}>
        <PageHeader eyebrow="DOCUMENTS" title="문서 편집" description="초기 데이터를 불러오지 못했습니다." />
        <Alert severity="error">{error}</Alert>
        <Button component={RouterLink} to="/documents" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          문서 목록으로
        </Button>
      </Stack>
    )
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="DOCUMENT EDITOR"
        title={isEditMode ? '문서 편집' : '새 문서 작성'}
        description="넓은 작성 영역과 안정적인 미리보기, 이미지 업로드, 문서 검색 연결까지 한 화면 안에서 처리할 수 있게 정리하는 단계입니다."
      />

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/documents" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          목록으로
        </Button>
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}

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
              label="문서 유형"
              value={form.doc_type}
              onChange={(event) => {
                updateField('doc_type', event.target.value)
                updateField('folder_id', '')
                updateField('new_folder_name', '')
              }}
            >
              {(bootstrap?.document_types || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="폴더"
              value={form.folder_id}
              onChange={(event) => {
                updateField('folder_id', event.target.value)
                if (event.target.value) {
                  updateField('new_folder_name', '')
                }
              }}
            >
              <MenuItem value="">미지정</MenuItem>
              {folderOptions.map((option) => (
                <MenuItem key={option.id} value={option.id}>
                  {option.doc_type} / {option.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="새 폴더명"
              value={form.new_folder_name}
              onChange={(event) => {
                updateField('new_folder_name', event.target.value)
                if (event.target.value.trim()) {
                  updateField('folder_id', '')
                }
              }}
              helperText="없는 폴더면 새 이름을 입력하세요. 입력하면 기존 폴더 선택보다 우선합니다."
            />
            <TextField
              select
              label="작성자"
              value={form.author_id}
              onChange={(event) => updateField('author_id', event.target.value)}
            >
              <MenuItem value="">미지정</MenuItem>
              {(bootstrap?.members || []).map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name}
                </MenuItem>
              ))}
            </TextField>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <TextField
                label="태그"
                fullWidth
                value={form.tags}
                onChange={(event) => updateField('tags', event.target.value)}
                helperText="쉼표로 구분해서 입력합니다."
              />
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <TextField
                select
                fullWidth
                label="연결 WBS 작업"
                SelectProps={{
                  multiple: true,
                  value: form.related_task_ids,
                  renderValue: (selected) => `${selected.length}개 선택`,
                }}
                value={form.related_task_ids}
                onChange={(event) => updateField('related_task_ids', event.target.value)}
              >
                {(bootstrap?.tasks || []).map((task) => (
                  <MenuItem key={task.id} value={task.id}>
                    #{task.id} {task.title} · {task.status}
                  </MenuItem>
                ))}
              </TextField>
            </Box>
            <Box sx={{ gridColumn: '1 / -1' }}>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={form.is_hidden}
                    onChange={(event) => updateField('is_hidden', event.target.checked)}
                  />
                }
                label="숨김 문서로 처리"
              />
            </Box>
          </Box>

          <Box
            onDragEnter={(event) => {
              event.preventDefault()
              setDragActive(true)
            }}
            onDragOver={(event) => {
              event.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={(event) => {
              event.preventDefault()
              if (event.currentTarget.contains(event.relatedTarget)) {
                return
              }
              setDragActive(false)
            }}
            onDrop={async (event) => {
              event.preventDefault()
              const [file] = Array.from(event.dataTransfer?.files || [])
              await handleImageUpload(file)
            }}
          >
            <Paper
              variant="outlined"
              sx={{
                position: 'sticky',
                top: { xs: 84, sm: 92 },
                zIndex: 20,
                mb: 1.25,
                p: 1.5,
                borderRadius: 3,
                bgcolor: 'background.default',
                boxShadow: '0 10px 24px rgba(15, 23, 42, 0.08)',
              }}
            >
              <Stack
                direction={{ xs: 'column', md: 'row' }}
                spacing={1}
                sx={{
                  flexWrap: 'wrap',
                  alignItems: { md: 'center' },
                }}
              >
                {toolbarActions.map((action) => (
                  <Button
                    key={action.key}
                    size="small"
                    variant="outlined"
                    onMouseDown={preserveEditorSelection}
                    onClick={action.onClick}
                  >
                    {action.label}
                  </Button>
                ))}
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AddPhotoAlternateRoundedIcon />}
                  disabled={uploading || saving}
                  onMouseDown={preserveEditorSelection}
                  onClick={openImagePicker}
                >
                  이미지
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<LinkRoundedIcon />}
                  onMouseDown={preserveEditorSelection}
                  onClick={openLinkSearch}
                >
                  문서 검색
                </Button>
                <Button
                  size="small"
                  variant="outlined"
                  startIcon={<AutoFixHighRoundedIcon />}
                  disabled={formatting || saving || uploading}
                  onClick={handleFormat}
                >
                  코드 정리
                </Button>
                <Chip
                  label={status}
                  color={error ? 'error' : 'default'}
                  variant="outlined"
                  sx={{ ml: { md: 'auto' }, maxWidth: '100%' }}
                />
              </Stack>
            </Paper>

            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(event) => handleImageUpload(event.target.files?.[0])}
            />

            <Paper
              variant="outlined"
              sx={{
                overflow: 'hidden',
                borderRadius: 3,
                borderColor: dragActive ? 'primary.main' : undefined,
                boxShadow: dragActive ? '0 0 0 3px rgba(30, 58, 95, 0.14)' : undefined,
              }}
            >
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.15fr) minmax(0, 0.85fr)' },
                }}
              >
                <Box sx={{ borderRight: { xl: '1px solid' }, borderColor: { xl: 'divider' } }}>
                  <Typography variant="overline" sx={{ display: 'block', px: 2, py: 1.25, color: 'text.secondary' }}>
                    Editor
                  </Typography>
                  <TextField
                    id="react-document-content"
                    inputRef={textareaRef}
                    multiline
                    fullWidth
                    minRows={30}
                    value={form.content}
                    onChange={(event) => updateField('content', event.target.value)}
                    onClick={syncEditorSelection}
                    onKeyUp={syncEditorSelection}
                    onPaste={async (event) => {
                      const items = Array.from(event.clipboardData?.items || [])
                      const imageItem = items.find((item) => item.type?.startsWith('image/'))
                      const file = imageItem?.getAsFile()
                      if (!file) {
                        return
                      }

                      event.preventDefault()
                      await handleImageUpload(file)
                    }}
                    onSelect={syncEditorSelection}
                    sx={{
                      '& .MuiOutlinedInput-root': {
                        borderRadius: 0,
                        alignItems: 'stretch',
                      },
                      '& .MuiOutlinedInput-notchedOutline': {
                        border: 0,
                      },
                      '& textarea': {
                        fontFamily: 'Consolas, "Courier New", monospace',
                        lineHeight: 1.7,
                        fontSize: 14,
                      },
                    }}
                    helperText="클립보드 이미지 붙여넣기, 드래그 앤 드롭, 업로드 버튼을 모두 지원합니다."
                  />
                </Box>

                <Box>
                  <Stack
                    direction="row"
                    spacing={1}
                    useFlexGap
                    flexWrap="wrap"
                    sx={{ px: 2, py: 1.25, alignItems: 'center' }}
                  >
                    <Typography variant="overline" sx={{ color: 'text.secondary' }}>
                      Preview
                    </Typography>
                    {busyFlags.map((label) => (
                      <Chip key={label} size="small" label={label} variant="outlined" />
                    ))}
                  </Stack>
                  <Box
                    className="markdown-body"
                    sx={{
                      minHeight: 520,
                      p: 2.5,
                      overflowX: 'auto',
                      '& img': {
                        display: 'block',
                        maxWidth: '100%',
                        height: 'auto',
                        borderRadius: 2,
                      },
                      '& pre': {
                        overflowX: 'auto',
                      },
                      '& table': {
                        width: '100%',
                        borderCollapse: 'collapse',
                      },
                      '& th, & td': {
                        border: '1px solid',
                        borderColor: 'divider',
                        p: 1,
                        textAlign: 'left',
                      },
                    }}
                  >
                    {previewHtml ? (
                      <Box dangerouslySetInnerHTML={{ __html: previewHtml }} />
                    ) : (
                      <Alert severity="info">본문을 입력하면 여기에서 Markdown 미리보기를 확인할 수 있습니다.</Alert>
                    )}
                  </Box>
                </Box>
              </Box>
            </Paper>
          </Box>

          <Typography variant="body2" color="text.secondary">
            이미지는 버튼으로 업로드하거나 에디터에 드래그 앤 드롭, 클립보드 붙여넣기로 삽입할 수 있습니다.
          </Typography>

          {bootstrap?.assets?.length ? (
            <Paper variant="outlined" sx={{ p: 2.5 }}>
              <Stack spacing={1.5}>
                <Typography variant="h6">기존 이미지 자산</Typography>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>파일명</TableCell>
                        <TableCell>유형</TableCell>
                        <TableCell>크기</TableCell>
                        <TableCell align="right">관리</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {bootstrap.assets.map((asset) => (
                        <TableRow key={asset.id}>
                          <TableCell>{asset.original_filename}</TableCell>
                          <TableCell>{asset.content_type || 'image/*'}</TableCell>
                          <TableCell>{asset.size} bytes</TableCell>
                          <TableCell align="right">
                            <Button
                              size="small"
                              color="error"
                              variant="outlined"
                              startIcon={
                                deletingAssetIds.includes(asset.id) ? (
                                  <CircularProgress size={14} color="inherit" />
                                ) : (
                                  <DeleteOutlineRoundedIcon />
                                )
                              }
                              disabled={deletingAssetIds.includes(asset.id) || saving || uploading}
                              onClick={() => handleDeleteAsset(asset.id)}
                            >
                              {deletingAssetIds.includes(asset.id) ? '삭제 중...' : '삭제'}
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Stack>
            </Paper>
          ) : null}

          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveRoundedIcon />}
              disabled={saving || uploading}
            >
              {saving ? '저장 중...' : isEditMode ? '변경 저장' : '문서 저장'}
            </Button>
            <Button component={RouterLink} to="/documents" variant="outlined" disabled={saving || uploading}>
              취소
            </Button>
          </Stack>
        </Stack>
      </Paper>

      <Box
        sx={{
          position: 'fixed',
          right: { xs: 8, md: 12 },
          bottom: { xs: 20, md: 28 },
          zIndex: 1200,
          display: 'flex',
          flexDirection: 'row-reverse',
          alignItems: 'flex-end',
          gap: 0,
        }}
      >
        <Paper
          elevation={0}
          sx={{
            borderRadius: '6px 0 0 6px',
            bgcolor: 'background.paper',
            border: '1px solid',
            borderRight: 0,
            borderColor: 'divider',
          }}
        >
          <IconButton
            size="small"
            onClick={() => setFloatingBarCollapsed((prev) => !prev)}
            sx={{
              width: 34,
              height: 58,
              borderRadius: '6px 0 0 6px',
              color: 'text.secondary',
              bgcolor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
              '&:hover': {
                bgcolor: 'action.hover',
              },
            }}
          >
            {floatingBarCollapsed ? <ChevronLeftRoundedIcon /> : <ChevronRightRoundedIcon />}
          </IconButton>
        </Paper>

        {floatingBarCollapsed ? null : (
          <Paper
            elevation={0}
            sx={{
              p: 1,
              mr: -0.5,
              borderRadius: 1.5,
              borderTopRightRadius: 0,
              borderBottomRightRadius: 0,
              bgcolor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              boxShadow: 'none',
            }}
          >
            <Stack direction="column" spacing={1}>
              {floatingActions.map((action) => (
                <Button
                  key={action.key}
                  size="small"
                  variant="outlined"
                  startIcon={action.icon}
                  onClick={action.onClick}
                  onMouseDown={preserveEditorSelection}
                  disabled={action.disabled}
                  sx={{
                    justifyContent: 'flex-start',
                    minHeight: 38,
                    px: 1.5,
                    borderRadius: 1,
                    boxShadow: 'none',
                    '& .MuiButton-startIcon': {
                      marginRight: 0.75,
                    },
                    '&:hover': {
                      boxShadow: 'none',
                    },
                  }}
                >
                  {action.label}
                </Button>
              ))}
            </Stack>
          </Paper>
        )}
      </Box>

      <Dialog
        open={linkSearchOpen}
        onClose={() => setLinkSearchOpen(false)}
        disableRestoreFocus
        fullWidth
        maxWidth="md"
      >
        <DialogTitle>기존 문서 검색</DialogTitle>
        <DialogContent>
          <Stack spacing={2}>
            <TextField
              autoFocus
              label="문서 제목 검색"
              value={linkQuery}
              onChange={(event) => setLinkQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  event.preventDefault()
                }
              }}
              InputProps={{
                endAdornment: searchingLinks ? <CircularProgress size={18} /> : <SearchRoundedIcon color="disabled" />,
              }}
            />
            {linkResults.length ? (
              <Stack spacing={1.25}>
                {linkResults.map((item) => (
                  <Paper key={item.id} variant="outlined" sx={{ p: 2 }}>
                    <Stack spacing={1}>
                      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center">
                        <Typography fontWeight={700}>{item.title}</Typography>
                        {item.is_hidden ? <Chip size="small" label="숨김" variant="outlined" sx={hiddenStatusChipSx} /> : null}
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        {item.doc_type} · {item.folder_name || '폴더 없음'}
                      </Typography>
                      <Typography variant="body2" sx={{ fontFamily: 'monospace', overflowWrap: 'anywhere' }}>
                        {item.path}
                      </Typography>
                      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1}>
                        <Button
                          variant="outlined"
                          onClick={async () => {
                            await navigator.clipboard.writeText(new URL(item.path, window.location.origin).toString())
                            setStatus('문서 URL을 클립보드에 복사했습니다.')
                          }}
                        >
                          URL 복사
                        </Button>
                        <Button
                          variant="contained"
                          onClick={() => {
                            setLinkSearchOpen(false)
                            insertAtCursor(`[${item.title}](${item.path})`)
                            setStatus('문서 링크를 본문에 삽입했습니다.')
                          }}
                        >
                          URL 삽입
                        </Button>
                      </Stack>
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            ) : (
              <Alert severity="info">
                {linkQuery.trim()
                  ? '검색 결과가 없습니다.'
                  : '문서 제목을 입력하면 연결 가능한 문서를 검색합니다.'}
              </Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkSearchOpen(false)}>닫기</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

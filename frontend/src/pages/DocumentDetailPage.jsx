import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import ImageRoundedIcon from '@mui/icons-material/ImageRounded'
import LabelRoundedIcon from '@mui/icons-material/LabelRounded'
import SchemaRoundedIcon from '@mui/icons-material/SchemaRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Link,
  Paper,
  Stack,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { Link as RouterLink, useNavigate, useParams } from 'react-router-dom'
import { apiGet, apiJson, normalizeRedirectPath } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import { formatDateTimeKst } from '../utils/datetime'

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

function TagBadge({ label }) {
  return (
    <span
      style={{
        display: 'inline-block',
        flex: 'none',
        width: 'auto',
        minWidth: 'max-content',
        maxWidth: 'none',
        padding: '8px 12px',
        border: '1px solid var(--mui-palette-divider)',
        borderRadius: '4px',
        backgroundColor: 'var(--mui-palette-background-default)',
        color: 'var(--mui-palette-text-primary)',
        fontSize: '0.875rem',
        fontWeight: 700,
        lineHeight: 1.2,
        whiteSpace: 'nowrap',
        wordBreak: 'keep-all',
        overflowWrap: 'normal',
        writingMode: 'horizontal-tb',
        verticalAlign: 'top',
      }}
    >
      {label}
    </span>
  )
}

export function DocumentDetailPage() {
  const { documentId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState('')
  const [status, setStatus] = useState('')

  useEffect(() => {
    const loadDetail = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet(`/api/documents/${documentId}`)
        setData(payload)
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    loadDetail()
  }, [documentId])

  if (loading) {
    return (
      <Stack sx={{ py: 10, alignItems: 'center' }} spacing={2}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">문서 상세를 불러오는 중입니다...</Typography>
      </Stack>
    )
  }

  if (error || !data?.document) {
    return (
      <Stack spacing={3}>
        <PageHeader
          eyebrow="DOCUMENTS"
          title="문서 상세"
          description="문서를 찾지 못했거나 불러오는 중 문제가 발생했습니다."
        />
        <Alert severity="error">{error || '문서를 찾을 수 없습니다.'}</Alert>
        <Button component={RouterLink} to="/documents" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          문서 목록으로
        </Button>
      </Stack>
    )
  }

  const { document, tags, assets, related_tasks, rendered_content, word_count, heading_count } = data

  const handleDelete = async () => {
    if (
      deleting ||
      !window.confirm('이 문서를 삭제할까요? 연결된 태그, 문서 이미지, WBS 연결 정보도 함께 정리됩니다.')
    ) {
      return
    }

    setDeleting(true)
    setError('')
    setStatus('문서를 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/documents/${document.id}`, { method: 'DELETE' })
      navigate(normalizeRedirectPath(payload.redirect_path), { replace: true })
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('문서 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="DOCUMENTS"
        title={document.title}
        description={`${document.doc_type}${document.folder_name ? ` · ${document.folder_name}` : ''} · ${document.author_name || '작성자 미지정'}`}
      />

      {error ? <Alert severity="error">{error}</Alert> : null}
      {status && !error ? <Alert severity="info">{status}</Alert> : null}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/documents" variant="outlined" startIcon={<ArrowBackRoundedIcon />} disabled={deleting}>
          목록으로
        </Button>
        <Button
          variant="contained"
          startIcon={<EditRoundedIcon />}
          component={RouterLink}
          to={`/documents/${document.id}/edit`}
          disabled={deleting}
        >
          문서 편집
        </Button>
        <Button
          type="button"
          color="error"
          variant="text"
          startIcon={deleting ? <CircularProgress size={16} color="inherit" /> : <DeleteOutlineRoundedIcon />}
          onClick={handleDelete}
          disabled={deleting}
        >
          {deleting ? '삭제 중...' : '문서 삭제'}
        </Button>
      </Stack>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.45fr) minmax(340px, 0.55fr)' },
          gap: 3,
        }}
      >
        <Paper sx={{ p: { xs: 2.5, sm: 3.5 } }}>
          <Stack spacing={2.5}>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.2} useFlexGap flexWrap="wrap">
              <Chip label={document.doc_type} color="primary" />
              <Chip
                label={document.is_hidden ? '숨김 문서' : '일반 문서'}
                variant="outlined"
                color={document.is_hidden ? 'warning' : 'default'}
              />
              <Chip label={`수정 ${formatDateTimeKst(document.updated_at)}`} variant="outlined" />
            </Stack>

            <Divider />

            <Box
              className="markdown-body"
              sx={{
                '& h1, & h2, & h3': {
                  fontWeight: 800,
                  letterSpacing: '-0.02em',
                },
                '& img': {
                  maxWidth: '100%',
                  borderRadius: 2.5,
                },
                '& pre': {
                  overflowX: 'auto',
                  p: 2,
                  borderRadius: 2,
                  bgcolor: 'secondary.main',
                  color: '#eff6ff',
                },
                '& code': {
                  fontFamily: 'Consolas, "Courier New", monospace',
                },
                '& table': {
                  width: '100%',
                  borderCollapse: 'collapse',
                },
                '& th, & td': {
                  border: '1px solid',
                  borderColor: 'divider',
                  p: 1.25,
                  textAlign: 'left',
                },
              }}
              dangerouslySetInnerHTML={{ __html: rendered_content }}
            />
          </Stack>
        </Paper>

        <Stack spacing={3}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={2.5}>
              <Typography variant="h6">문서 메타데이터</Typography>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', xl: '1fr' },
                  gap: 2.2,
                }}
              >
                <MetaBlock label="유형" value={document.doc_type} />
                <MetaBlock label="폴더" value={document.folder_name || '미지정'} />
                <MetaBlock label="작성자" value={document.author_name || '-'} />
                <MetaBlock label="통계" value={`${word_count} words · ${heading_count} headings`} />
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <LabelRoundedIcon color="primary" fontSize="small" />
                <Typography variant="h6">태그</Typography>
              </Stack>
              <Box
                sx={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 1,
                  minWidth: 0,
                }}
              >
                {tags.length ? tags.map((tag) => (
                  <TagBadge key={tag} label={tag} />
                )) : (
                  <Typography color="text.secondary">태그가 없습니다.</Typography>
                )}
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <SchemaRoundedIcon color="primary" fontSize="small" />
                <Typography variant="h6">연결 WBS 작업</Typography>
              </Stack>
              {related_tasks.length ? related_tasks.map((task) => (
                <Paper
                  key={task.id}
                  variant="outlined"
                  sx={{ p: 2, borderRadius: 3, bgcolor: 'background.default' }}
                >
                  <Stack spacing={0.8}>
                    <Typography fontWeight={700}>{task.title}</Typography>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      <Chip size="small" label={task.status} />
                      <Chip size="small" variant="outlined" label={task.priority} />
                    </Stack>
                  </Stack>
                </Paper>
              )) : (
                <Typography color="text.secondary">연결된 WBS 작업이 없습니다.</Typography>
              )}
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={2}>
              <Stack direction="row" spacing={1} alignItems="center">
                <ImageRoundedIcon color="primary" fontSize="small" />
                <Typography variant="h6">이미지 자산</Typography>
              </Stack>
              {assets.length ? assets.map((asset) => (
                <Paper
                  key={asset.id}
                  variant="outlined"
                  sx={{ p: 2, borderRadius: 3, bgcolor: 'background.default' }}
                >
                  <Stack spacing={1}>
                    <Link href={asset.url} target="_blank" rel="noreferrer" underline="hover" fontWeight={700}>
                      {asset.original_filename}
                    </Link>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      <Chip size="small" label={asset.content_type || 'image/*'} />
                      <Chip size="small" variant="outlined" label={`${asset.size} bytes`} />
                    </Stack>
                  </Stack>
                </Paper>
              )) : (
                <Typography color="text.secondary">업로드된 문서 이미지가 없습니다.</Typography>
              )}
            </Stack>
          </Paper>
        </Stack>
      </Box>
    </Stack>
  )
}

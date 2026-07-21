import ArrowBackRoundedIcon from '@mui/icons-material/ArrowBackRounded'
import DeleteOutlineRoundedIcon from '@mui/icons-material/DeleteOutlineRounded'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'
import EditRoundedIcon from '@mui/icons-material/EditRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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

function TagBadge({ label }) {
  return (
    <Chip
      label={label}
      variant="outlined"
      sx={{ whiteSpace: 'nowrap', '& .MuiChip-label': { fontWeight: 700 } }}
    />
  )
}

export function AssetDetailPage() {
  const { assetId } = useParams()
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
        const payload = await apiGet(`/api/assets/${assetId}`)
        setData(payload)
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    loadDetail()
  }, [assetId])

  if (loading) {
    return (
      <Stack sx={{ py: 10, alignItems: 'center' }} spacing={2}>
        <CircularProgress size={30} />
        <Typography color="text.secondary">Asset 상세를 불러오는 중입니다...</Typography>
      </Stack>
    )
  }

  if (error || !data?.asset) {
    return (
      <Stack spacing={3}>
        <PageHeader eyebrow="ASSETS" title="Asset 상세" description="Asset을 찾지 못했거나 불러오는 중 문제가 발생했습니다." />
        <Alert severity="error">{error || 'Asset을 찾을 수 없습니다.'}</Alert>
        <Button component={RouterLink} to="/assets" variant="outlined" startIcon={<ArrowBackRoundedIcon />}>
          Assets 목록으로
        </Button>
      </Stack>
    )
  }

  const { asset, tags, is_image: isImage } = data
  const downloadUrl = `/api/assets/${asset.id}/download`

  const handleDelete = async () => {
    if (deleting || !window.confirm('이 Asset을 삭제할까요? 연결된 파일과 관리 정보가 함께 정리됩니다.')) {
      return
    }
    setDeleting(true)
    setError('')
    setStatus('Asset을 삭제하는 중입니다...')
    try {
      const payload = await apiJson(`/api/assets/${asset.id}`, { method: 'DELETE' })
      navigate(normalizeRedirectPath(payload.redirect_path), { replace: true })
    } catch (deleteError) {
      setError(deleteError.message)
      setStatus('Asset 삭제에 실패했습니다.')
      setDeleting(false)
    }
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="ASSETS"
        title={asset.title}
        description={`${asset.asset_type || '미분류'} · ${asset.category || '그룹 미지정'} · ${asset.created_by_name || '등록자 미지정'}`}
      />

      {error ? <Alert severity="error">{error}</Alert> : null}
      {status && !error ? <Alert severity="info">{status}</Alert> : null}

      <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
        <Button component={RouterLink} to="/assets" variant="outlined" startIcon={<ArrowBackRoundedIcon />} disabled={deleting}>
          목록으로
        </Button>
        <Button variant="contained" startIcon={<EditRoundedIcon />} component={RouterLink} to={`/assets/${asset.id}/edit`} disabled={deleting}>
          메타데이터 편집
        </Button>
        <Button variant="outlined" startIcon={<DownloadRoundedIcon />} component="a" href={downloadUrl} disabled={deleting}>
          다운로드
        </Button>
        <Button type="button" color="error" variant="text" startIcon={deleting ? <CircularProgress size={16} color="inherit" /> : <DeleteOutlineRoundedIcon />} onClick={handleDelete} disabled={deleting}>
          {deleting ? '삭제 중...' : '삭제'}
        </Button>
      </Stack>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: 'minmax(0, 1.1fr) minmax(320px, 0.9fr)' },
          gap: 3,
        }}
      >
        <Paper sx={{ p: 3 }}>
          <Stack spacing={2}>
            <Typography variant="h6">미리보기</Typography>
            {isImage ? (
              <Box
                component="img"
                src={asset.url}
                alt={asset.title}
                sx={{ width: '100%', maxHeight: 560, objectFit: 'contain', borderRadius: 1, bgcolor: 'background.default' }}
              />
            ) : (
              <Alert severity="info">이 파일 형식은 브라우저 썸네일 미리보기를 제공하지 않습니다.</Alert>
            )}
          </Stack>
        </Paper>

        <Stack spacing={3}>
          <Paper sx={{ p: 3 }}>
            <Stack spacing={1.2}>
              <Typography variant="h6">메타데이터</Typography>
              <Typography variant="body2" color="text.secondary">원본 파일명: {asset.original_filename || asset.file_name}</Typography>
              <Typography variant="body2" color="text.secondary">상태: {asset.status}</Typography>
              <Typography variant="body2" color="text.secondary">유형: {asset.asset_type || '-'}</Typography>
              <Typography variant="body2" color="text.secondary">그룹(폴더): {asset.category || '-'}</Typography>
              <Typography variant="body2" color="text.secondary">크기: {asset.size} bytes</Typography>
              <Typography variant="body2" color="text.secondary">콘텐츠 타입: {asset.content_type || '-'}</Typography>
              <Typography variant="body2" color="text.secondary">체크섬: {asset.checksum || '-'}</Typography>
              <Typography variant="body2" color="text.secondary">업데이트: {formatDateTimeKst(asset.updated_at)}</Typography>
              <Link href={asset.url} target="_blank" rel="noreferrer" underline="hover">
                {asset.url}
              </Link>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={1.5}>
              <Typography variant="h6">태그</Typography>
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {tags.length ? tags.map((tag) => <TagBadge key={tag} label={tag} />) : <Typography color="text.secondary">등록된 Tag가 없습니다.</Typography>}
              </Box>
            </Stack>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Stack spacing={1}>
              <Typography variant="h6">메모</Typography>
              <Typography color="text.secondary" sx={{ whiteSpace: 'pre-wrap' }}>
                {asset.notes || '메모가 없습니다.'}
              </Typography>
            </Stack>
          </Paper>
        </Stack>
      </Box>
    </Stack>
  )
}

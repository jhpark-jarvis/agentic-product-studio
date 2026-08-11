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
  MenuItem,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useRef, useState } from 'react'
import { apiGet } from '../api/client'

const categoryLabels = {
  hair: '헤어',
  face: '성형',
}

function defaultVariant(item) {
  return item.variants?.find((variant) => variant.resource_id === item.resource_id) || item.variants?.[0] || item
}

export function CatalogAssetSearchDialog({
  open,
  onClose,
  onSelect,
  actionLabel = '선택',
  title = 'External Asset Catalog 에셋 검색',
  enableAvatarCatalog = false,
}) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [selectedResourceIdByGroup, setSelectedResourceIdByGroup] = useState({})
  const [catalogOptionsByGroup, setCatalogOptionsByGroup] = useState({})
  const [loading, setLoading] = useState(false)
  const [selectingResourceId, setSelectingResourceId] = useState('')
  const [error, setError] = useState('')
  const searchRequestRef = useRef(0)

  useEffect(() => {
    if (!open) {
      searchRequestRef.current += 1
      setError('')
      setLoading(false)
      setSelectingResourceId('')
    }
  }, [open])

  const search = async ({ keyword = query.trim(), offset = 0, append = false } = {}) => {
    if (!keyword) {
      return
    }
    const requestId = searchRequestRef.current + 1
    searchRequestRef.current = requestId
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/catalog-assets/search', { q: keyword, limit: 12, offset })
      if (searchRequestRef.current !== requestId) {
        return
      }
      setItems((current) => (append ? [...current, ...(payload.items || [])] : payload.items || []))
      setPagination(payload.pagination || null)
    } catch (searchError) {
      if (searchRequestRef.current !== requestId) {
        return
      }
      setError(searchError.message)
      if (!append) {
        setItems([])
      }
    } finally {
      if (searchRequestRef.current === requestId) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    if (!open) {
      return undefined
    }

    const keyword = query.trim()
    if (!keyword) {
      searchRequestRef.current += 1
      setItems([])
      setPagination(null)
      setError('')
      setLoading(false)
      return undefined
    }

    const handle = window.setTimeout(() => search({ keyword }), 180)
    return () => window.clearTimeout(handle)
  }, [query, open]) // eslint-disable-line react-hooks/exhaustive-deps

  const selectItem = async (item) => {
    const groupKey = item.group_id || item.resource_id
    const selectedResourceId = selectedResourceIdByGroup[groupKey] || defaultVariant(item)?.resource_id
    const variant = item.variants?.find((candidate) => candidate.resource_id === selectedResourceId) || defaultVariant(item)
    const catalogOption = catalogOptionsByGroup[groupKey] || { enabled: false, gender: '' }
    if (!variant) {
      return
    }
    if (catalogOption.enabled && !catalogOption.gender) {
      setError('아바타 카탈로그에 추가하려면 성별을 선택해주세요.')
      return
    }
    setSelectingResourceId(variant.resource_id)
    setError('')
    try {
      await onSelect({
        ...variant,
        category: item.category,
        group_id: item.group_id,
        parent_name: item.name,
        add_to_avatar_catalog: catalogOption.enabled,
        gender: catalogOption.gender || null,
      })
    } catch (selectError) {
      setError(selectError.message)
    } finally {
      setSelectingResourceId('')
    }
  }

  return (
    <Dialog open={open} onClose={selectingResourceId ? undefined : onClose} fullWidth maxWidth="lg">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ pt: 1 }}>
          <TextField
            autoFocus
            fullWidth
            label="에셋 이름 또는 RESOURCE_ID"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === 'Enter') {
                event.preventDefault()
              }
            }}
            placeholder="예: 히어로 헤어"
            helperText="입력을 멈추면 자동으로 검색합니다."
            InputProps={{
              endAdornment: loading ? <CircularProgress size={18} /> : <SearchRoundedIcon color="disabled" />,
            }}
          />

          {error ? <Alert severity="error">{error}</Alert> : null}

          {!loading && query.trim() && !items.length && !error ? (
            <Alert severity="info">검색 결과가 없습니다.</Alert>
          ) : null}

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', lg: 'repeat(3, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            {items.map((item) => {
              const groupKey = item.group_id || item.resource_id
              const selectedResourceId = selectedResourceIdByGroup[groupKey] || defaultVariant(item)?.resource_id
              const variant = item.variants?.find((candidate) => candidate.resource_id === selectedResourceId) || defaultVariant(item)
              const catalogOption = catalogOptionsByGroup[groupKey] || { enabled: false, gender: '' }
              const supportsAvatarCatalog = enableAvatarCatalog && ['hair', 'face'].includes(item.category)
              return (
                <Paper key={groupKey} variant="outlined" sx={{ p: 2 }}>
                  <Stack spacing={1.5}>
                    <Box
                      component="img"
                      src={variant?.thumbnail_url}
                      alt={variant?.name || item.name}
                      sx={{ width: '100%', height: 180, objectFit: 'contain', borderRadius: 2, bgcolor: 'background.default' }}
                    />
                    <Typography fontWeight={800}>{variant?.name || item.name}</Typography>
                    <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                      <Chip size="small" label={categoryLabels[item.category] || item.category || '미분류'} />
                      <Chip size="small" variant="outlined" label={`${item.variants?.length || 1}색상`} />
                    </Stack>
                    <TextField
                      select
                      size="small"
                      label="색상 변형"
                      value={selectedResourceId || ''}
                      onChange={(event) => setSelectedResourceIdByGroup((current) => ({ ...current, [groupKey]: event.target.value }))}
                    >
                      {(item.variants || []).map((candidate) => (
                        <MenuItem key={candidate.resource_id} value={candidate.resource_id}>
                          {candidate.name} {candidate.color_hex ? `(${candidate.color_hex})` : ''}
                        </MenuItem>
                      ))}
                    </TextField>
                    {supportsAvatarCatalog ? (
                      <Stack spacing={1}>
                        <FormControlLabel
                          control={(
                            <Checkbox
                              checked={catalogOption.enabled}
                              onChange={(event) => setCatalogOptionsByGroup((current) => ({
                                ...current,
                                [groupKey]: { ...catalogOption, enabled: event.target.checked },
                              }))}
                            />
                          )}
                          label="아바타 카탈로그에도 추가"
                        />
                        <TextField
                          select
                          size="small"
                          label="카탈로그 성별"
                          value={catalogOption.gender}
                          disabled={!catalogOption.enabled}
                          onChange={(event) => setCatalogOptionsByGroup((current) => ({
                            ...current,
                            [groupKey]: { ...catalogOption, gender: event.target.value },
                          }))}
                        >
                          <MenuItem value="male">남성</MenuItem>
                          <MenuItem value="female">여성</MenuItem>
                        </TextField>
                      </Stack>
                    ) : null}
                    <Stack direction="row" spacing={0.75} alignItems="center">
                      <Chip size="small" color="info" variant="outlined" label="RESOURCE_ID" />
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', overflowWrap: 'anywhere' }}>
                        {variant?.resource_id}
                      </Typography>
                    </Stack>
                    <Button
                      variant="contained"
                      onClick={() => selectItem(item)}
                      disabled={Boolean(selectingResourceId)}
                    >
                      {selectingResourceId === variant?.resource_id ? '처리 중...' : actionLabel}
                    </Button>
                  </Stack>
                </Paper>
              )
            })}
          </Box>

          {pagination?.has_more ? (
            <Button
              variant="outlined"
              disabled={loading || Boolean(selectingResourceId)}
              onClick={() => search({ offset: pagination.next_offset, append: true })}
            >
              {loading ? '불러오는 중...' : '검색 결과 더 보기'}
            </Button>
          ) : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={Boolean(selectingResourceId)}>닫기</Button>
      </DialogActions>
    </Dialog>
  )
}

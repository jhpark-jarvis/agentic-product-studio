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
  title = '외부 카탈로그 에셋 검색',
  enableAvatarCatalog = false,
}) {
  const [query, setQuery] = useState('')
  const [items, setItems] = useState([])
  const [pagination, setPagination] = useState(null)
  const [selectedResourceIdByGroup, setSelectedResourceIdByGroup] = useState({})
  const [loading, setLoading] = useState(false)
  const [selectingResourceId, setSelectingResourceId] = useState('')
  const [error, setError] = useState('')
  const [pendingSelection, setPendingSelection] = useState(null)
  const [catalogOption, setCatalogOption] = useState({ enabled: false, gender: '' })
  const searchRequestRef = useRef(0)

  useEffect(() => {
    if (!open) {
      searchRequestRef.current += 1
      setError('')
      setLoading(false)
      setSelectingResourceId('')
      setPendingSelection(null)
      setCatalogOption({ enabled: false, gender: '' })
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

  const submitSelection = async (selection, option = { enabled: false, gender: '' }) => {
    if (option.enabled && !option.gender) {
      setError('아바타 카탈로그에 추가하려면 성별을 선택해주세요.')
      return
    }
    setSelectingResourceId(selection.resource_id)
    setError('')
    try {
      await onSelect({
        ...selection,
        add_to_avatar_catalog: option.enabled,
        gender: option.gender || null,
      })
      setPendingSelection(null)
    } catch (selectError) {
      setError(selectError.message)
    } finally {
      setSelectingResourceId('')
    }
  }

  const selectItem = async (item) => {
    const groupKey = item.group_id || item.resource_id
    const selectedResourceId = selectedResourceIdByGroup[groupKey] || defaultVariant(item)?.resource_id
    const variant = item.variants?.find((candidate) => candidate.resource_id === selectedResourceId) || defaultVariant(item)
    if (!variant) {
      return
    }
    const selection = {
      ...variant,
      category: item.category,
      group_id: item.group_id,
      parent_name: item.name,
    }
    if (enableAvatarCatalog && ['hair', 'face'].includes(item.category)) {
      setError('')
      setCatalogOption({ enabled: false, gender: '' })
      setPendingSelection(selection)
      return
    }
    await submitSelection(selection)
  }

  return (
    <>
    <Dialog open={open} onClose={selectingResourceId || pendingSelection ? undefined : onClose} fullWidth maxWidth="lg">
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <Stack spacing={2.5} sx={{ pt: 1 }}>
          <TextField
            autoFocus
            fullWidth
            label="에셋 이름 또는 Resource ID"
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
              return (
                <Paper key={groupKey} variant="outlined" sx={{ p: 2, height: '100%' }}>
                  <Stack spacing={1.5} sx={{ height: '100%' }}>
                    <Box
                      component="img"
                      src={variant?.thumbnail_url}
                      alt={variant?.name || item.name}
                      sx={{ width: '100%', height: 180, objectFit: 'contain', borderRadius: 2, bgcolor: 'background.default' }}
                    />
                    <Typography
                      fontWeight={800}
                      sx={{ minHeight: 48, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}
                    >
                      {variant?.name || item.name}
                    </Typography>
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
                    <Box sx={{ display: 'grid', gridTemplateColumns: 'auto minmax(0, 1fr)', gap: 1, alignItems: 'center' }}>
                      <Chip size="small" color="info" variant="outlined" label="Resource ID" />
                      <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', lineHeight: 1.4, wordBreak: 'break-all' }}>
                        {variant?.resource_id}
                      </Typography>
                    </Box>
                    <Button
                      variant="contained"
                      onClick={() => selectItem(item)}
                      disabled={Boolean(selectingResourceId)}
                      sx={{ mt: 'auto' }}
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
    <Dialog
      open={Boolean(pendingSelection)}
      onClose={selectingResourceId ? undefined : () => setPendingSelection(null)}
      fullWidth
      maxWidth="xs"
    >
      <DialogTitle>아바타 에셋 등록 옵션</DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Alert severity="info">
            선택한 색상만 Assets에 저장하며, 카탈로그 추가를 선택하면 같은 그룹의 전체 색상 정보를 함께 등록합니다.
          </Alert>
          <Stack spacing={0.5}>
            <Typography fontWeight={800}>{pendingSelection?.name}</Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: 'auto minmax(0, 1fr)', gap: 1, alignItems: 'center' }}>
              <Chip size="small" color="info" variant="outlined" label="Resource ID" />
              <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', wordBreak: 'break-all' }}>
                {pendingSelection?.resource_id}
              </Typography>
            </Box>
          </Stack>
          <FormControlLabel
            control={(
              <Checkbox
                checked={catalogOption.enabled}
                onChange={(event) => setCatalogOption((current) => ({ ...current, enabled: event.target.checked }))}
              />
            )}
            label="아바타 카탈로그에도 추가"
          />
          <TextField
            select
            label="카탈로그 성별"
            value={catalogOption.gender}
            disabled={!catalogOption.enabled}
            onChange={(event) => setCatalogOption((current) => ({ ...current, gender: event.target.value }))}
          >
            <MenuItem value="male">남성</MenuItem>
            <MenuItem value="female">여성</MenuItem>
          </TextField>
          {error ? <Alert severity="error">{error}</Alert> : null}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setPendingSelection(null)} disabled={Boolean(selectingResourceId)}>취소</Button>
        <Button
          variant="contained"
          onClick={() => submitSelection(pendingSelection, catalogOption)}
          disabled={Boolean(selectingResourceId)}
        >
          {selectingResourceId ? '처리 중...' : actionLabel}
        </Button>
      </DialogActions>
    </Dialog>
    </>
  )
}

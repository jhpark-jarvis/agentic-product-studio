import AddRoundedIcon from '@mui/icons-material/AddRounded'
import DownloadRoundedIcon from '@mui/icons-material/DownloadRounded'
import PreviewRoundedIcon from '@mui/icons-material/PreviewRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import VisibilityOffRoundedIcon from '@mui/icons-material/VisibilityOffRounded'
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Chip,
  FormControlLabel,
  Link,
  MenuItem,
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
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { apiGet } from '../api/client'
import { AssetGroupTree } from '../components/AssetGroupTree'
import { EmptyState, ErrorMessage, LoadingState } from '../components/FeedbackStates'
import { FilterPanel } from '../components/FilterPanel'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'
import { hiddenStatusChipSx } from '../theme'
import { formatDateTimeKst } from '../utils/datetime'

const initialFilters = {
  q: '',
  asset_type: '',
  category: '',
  status: '',
  tag: '',
  updated_since: '',
  include_hidden: false,
  page: 1,
  per_page: 20,
}

function isImageAsset(asset) {
  return String(asset.content_type || '').startsWith('image/')
}

function normalizeCategoryLabel(category) {
  return category || '미분류'
}

export function AssetsPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [showPreview, setShowPreview] = useState(false)
  const [selectedAssetIds, setSelectedAssetIds] = useState([])

  const loadAssets = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/assets', nextFilters)
      setData(payload)
    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAssets(initialFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    const visibleAssetIds = new Set((data?.assets || []).map((asset) => asset.id))
    setSelectedAssetIds((prev) => prev.filter((assetId) => visibleAssetIds.has(assetId)))
  }, [data?.assets])

  const applyFilters = async (event) => {
    event.preventDefault()
    const nextFilters = { ...filters, page: 1 }
    setFilters(nextFilters)
    await loadAssets(nextFilters)
  }

  const resetFilters = async () => {
    setFilters(initialFilters)
    setShowPreview(false)
    setSelectedAssetIds([])
    await loadAssets(initialFilters)
  }

  const movePage = async (page) => {
    const nextFilters = { ...filters, page }
    setFilters(nextFilters)
    await loadAssets(nextFilters)
  }

  const selectCategory = async (category) => {
    const nextFilters = { ...filters, category, page: 1 }
    setFilters(nextFilters)
    await loadAssets(nextFilters)
  }

  const visibleAssets = data?.assets || []
  const visibleAssetIds = visibleAssets.map((asset) => asset.id)
  const allVisibleSelected = visibleAssetIds.length > 0 && visibleAssetIds.every((assetId) => selectedAssetIds.includes(assetId))
  const someVisibleSelected = visibleAssetIds.some((assetId) => selectedAssetIds.includes(assetId))
  const hasAnySelection = selectedAssetIds.length > 0

  const toggleAssetSelection = (assetId) => {
    setSelectedAssetIds((prev) =>
      prev.includes(assetId) ? prev.filter((id) => id !== assetId) : [...prev, assetId]
    )
  }

  const toggleSelectAllVisible = (checked) => {
    setSelectedAssetIds((prev) => {
      if (checked) {
        return Array.from(new Set([...prev, ...visibleAssetIds]))
      }
      return prev.filter((assetId) => !visibleAssetIds.includes(assetId))
    })
  }

  const handleBatchDownload = () => {
    if (!selectedAssetIds.length) {
      return
    }
    const params = new URLSearchParams()
    selectedAssetIds.forEach((assetId) => {
      params.append('asset_ids', String(assetId))
    })
    window.location.assign(`/api/assets/download?${params.toString()}`)
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="ASSETS"
        title="Assets Library"
        description="그룹별로 Assets를 정리하고, 필요한 파일만 찾아서 상세 확인과 편집으로 이어질 수 있도록 구성한 화면입니다."
      />

      <FilterPanel
        title="Assets 필터"
        onSubmit={applyFilters}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button type="submit" variant="contained" startIcon={<SearchRoundedIcon />}>
              필터 적용
            </Button>
            <Button variant="outlined" onClick={resetFilters} startIcon={<RefreshRoundedIcon />}>
              초기화
            </Button>
            <Button
              variant={showPreview ? 'contained' : 'outlined'}
              color={showPreview ? 'secondary' : 'primary'}
              startIcon={showPreview ? <PreviewRoundedIcon /> : <VisibilityOffRoundedIcon />}
              onClick={() => setShowPreview((prev) => !prev)}
            >
              {showPreview ? '미리보기 켜짐' : '미리보기 끔'}
            </Button>
            <Button
              variant="outlined"
              color="secondary"
              startIcon={<AddRoundedIcon />}
              component={RouterLink}
              to="/assets/new"
            >
              Asset 등록
            </Button>
          </Stack>
        }
      >
        <Stack spacing={2.5}>
          <FormControlLabel
            control={
              <Checkbox
                checked={filters.include_hidden}
                onChange={(event) =>
                  setFilters((prev) => ({ ...prev, include_hidden: event.target.checked }))
                }
              />
            }
            label="숨김 Asset 포함"
          />

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1.2fr 1fr 1fr 1fr 1fr 0.7fr' },
              gap: 2,
            }}
          >
            <TextField
              label="제목 / 파일명 검색"
              value={filters.q}
              onChange={(event) => setFilters((prev) => ({ ...prev, q: event.target.value }))}
            />
            <TextField
              label="Asset 유형"
              select
              value={filters.asset_type}
              onChange={(event) => setFilters((prev) => ({ ...prev, asset_type: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.asset_type_options || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="상태"
              select
              value={filters.status}
              onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.statuses || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="태그"
              select
              value={filters.tag}
              onChange={(event) => setFilters((prev) => ({ ...prev, tag: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.tag_options || []).map((option) => (
                <MenuItem key={option.tag} value={option.tag}>
                  {option.tag} ({option.usage_count})
                </MenuItem>
              ))}
            </TextField>
            <TextField
              label="업데이트 이후"
              value={filters.updated_since}
              onChange={(event) => setFilters((prev) => ({ ...prev, updated_since: event.target.value }))}
              placeholder="YYYY-MM-DD"
              helperText="예: 2026-07-13"
            />
            <TextField
              label="표시 수"
              select
              value={filters.per_page}
              onChange={(event) =>
                setFilters((prev) => ({ ...prev, per_page: Number(event.target.value) }))
              }
            >
              {(data?.per_page_options || [10, 20, 50, 100]).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Box>

          <Alert severity="info">
            그룹(폴더)은 Assets를 크게 묶는 분류값이고, 태그는 검색과 연결을 위한 세부 키워드입니다.
          </Alert>
        </Stack>
      </FilterPanel>

      <Box
        sx={{
          display: 'grid',
          gridTemplateColumns: { xs: '1fr', xl: '280px minmax(0, 1fr)' },
          gap: 3,
        }}
      >
        <SectionCard
          title="그룹(폴더) 보기"
          description="트리 구조로 폴더를 따라 내려가며 Assets를 빠르게 좁혀볼 수 있습니다."
          metric={`${data?.group_browser?.tree?.length || 0}개 루트`}
        >
          <Stack spacing={1.5} sx={{ px: 2, pb: 2.5 }}>
            <Button
              variant={filters.category ? 'outlined' : 'contained'}
              onClick={() => selectCategory('')}
            >
              전체 보기
            </Button>
            <AssetGroupTree
              tree={data?.group_browser?.tree || []}
              selectedPath={filters.category}
              ungroupedCount={data?.group_browser?.ungrouped_asset_count || 0}
              ungroupedSelectValue="미분류"
              ungroupedLabel="미분류"
              onSelect={selectCategory}
            />
          </Stack>
        </SectionCard>

        <SectionCard
          title={filters.category ? `${filters.category} Assets` : 'Assets 목록'}
          description={
            showPreview
              ? `${filters.include_hidden ? '숨김 포함' : '숨김 제외'} 상태로 Assets 목록과 미리보기를 함께 표시합니다.`
              : `${filters.include_hidden ? '숨김 포함' : '숨김 제외'} 상태로 메타데이터 중심 목록을 표시합니다.`
          }
          metric={data?.pagination ? `${data.pagination.page} / ${data.pagination.total_pages} 페이지` : null}
        >
          {hasAnySelection ? (
            <Box
              sx={{
                mx: 3,
                mt: 3,
                mb: 2,
                px: 2,
                py: 1.5,
                display: 'flex',
                flexDirection: { xs: 'column', md: 'row' },
                alignItems: { md: 'center' },
                justifyContent: 'space-between',
                gap: 1.5,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
                bgcolor: 'background.default',
              }}
            >
              <Stack direction="row" spacing={1} alignItems="center" sx={{ minWidth: 0 }}>
                <Checkbox
                  checked
                  size="small"
                  sx={{
                    p: 0.5,
                    '&.Mui-checked': {
                      color: 'primary.main',
                    },
                  }}
                />
                <Typography variant="body2" fontWeight={700}>
                  Asset {selectedAssetIds.length}건 선택됨
                </Typography>
              </Stack>
              <Button
                size="small"
                variant="outlined"
                color="primary"
                startIcon={<DownloadRoundedIcon />}
                onClick={handleBatchDownload}
              >
                선택 다운로드
              </Button>
            </Box>
          ) : null}

          <ErrorMessage message={error} sx={{ px: 3, pb: 3 }} />

          {loading ? (
            <LoadingState message="Assets 목록을 불러오는 중입니다..." />
          ) : (
            <>
              <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
                <Table sx={{ minWidth: { xs: showPreview ? 980 : 760, md: showPreview ? 1140 : 980 } }}>
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox" sx={{ width: 52 }}>
                        <Checkbox
                          checked={allVisibleSelected}
                          indeterminate={hasAnySelection && !allVisibleSelected && someVisibleSelected}
                          onChange={(event) => toggleSelectAllVisible(event.target.checked)}
                          inputProps={{ 'aria-label': '현재 페이지 Asset 전체 선택' }}
                        />
                      </TableCell>
                      {showPreview ? <TableCell sx={{ minWidth: 120 }}>미리보기</TableCell> : null}
                      <TableCell>제목</TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>유형</TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>그룹</TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>상태</TableCell>
                      <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' }, minWidth: 120 }}>등록자</TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>크기</TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>업데이트</TableCell>
                      <TableCell>관리</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(data?.assets || []).map((asset) => (
                      <TableRow
                        key={asset.id}
                        hover
                        selected={selectedAssetIds.includes(asset.id)}
                        sx={{
                          '&.Mui-selected': {
                            bgcolor: 'rgba(192, 107, 43, 0.08)',
                          },
                          '&.Mui-selected:hover': {
                            bgcolor: 'rgba(192, 107, 43, 0.12)',
                          },
                        }}
                      >
                        <TableCell padding="checkbox" sx={{ verticalAlign: 'top', pt: 2.25 }}>
                          <Checkbox
                            checked={selectedAssetIds.includes(asset.id)}
                            onChange={() => toggleAssetSelection(asset.id)}
                            inputProps={{ 'aria-label': `${asset.title} 선택` }}
                          />
                        </TableCell>
                        {showPreview ? (
                          <TableCell sx={{ verticalAlign: 'top', pt: 2 }}>
                            {isImageAsset(asset) ? (
                              <Box
                                component="img"
                                src={asset.url}
                                alt={asset.title}
                                sx={{
                                  width: 84,
                                  height: 64,
                                  objectFit: 'cover',
                                  borderRadius: 1,
                                  border: '1px solid',
                                  borderColor: 'divider',
                                  bgcolor: 'background.default',
                                }}
                              />
                            ) : (
                              <Chip size="small" label="미리보기 없음" variant="outlined" />
                            )}
                          </TableCell>
                        ) : null}
                        <TableCell sx={{ minWidth: 280, verticalAlign: 'top' }}>
                          <Stack spacing={0.5}>
                            <Stack direction="row" spacing={0.75} alignItems="flex-start" useFlexGap flexWrap="wrap">
                              <Link
                                component={RouterLink}
                                to={`/assets/${asset.id}`}
                                underline="hover"
                                color="inherit"
                                sx={{
                                  minWidth: 0,
                                  typography: 'body1',
                                  fontWeight: 700,
                                  lineHeight: 1.45,
                                  textAlign: 'left',
                                  textDecorationColor: 'currentColor',
                                  overflowWrap: 'anywhere',
                                  wordBreak: 'break-word',
                                }}
                              >
                                {asset.title}
                              </Link>
                              {asset.is_hidden ? (
                                <Chip
                                  size="small"
                                  label="숨김"
                                  variant="outlined"
                                  sx={(theme) => ({
                                    ...hiddenStatusChipSx(theme),
                                    alignSelf: 'flex-start',
                                    mt: '2px',
                                  })}
                                />
                              ) : null}
                            </Stack>
                            <Typography variant="body2" color="text.secondary">
                              {asset.original_filename || asset.file_name}
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {(asset.asset_type || '미분류')} · {normalizeCategoryLabel(asset.category)}
                            </Typography>
                          </Stack>
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                          <Chip size="small" label={asset.asset_type || '미분류'} />
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                          {normalizeCategoryLabel(asset.category)}
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                          <Chip size="small" variant="outlined" label={asset.status} />
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                          {asset.created_by_name || '-'}
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                          {asset.size} bytes
                        </TableCell>
                        <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                          {formatDateTimeKst(asset.updated_at)}
                        </TableCell>
                        <TableCell>
                          <Stack direction="row" spacing={1} justifyContent="flex-start" sx={{ flexWrap: 'nowrap' }}>
                            <Button
                              component={RouterLink}
                              to={`/assets/${asset.id}`}
                              size="small"
                              variant="outlined"
                              sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                            >
                              상세
                            </Button>
                            <Button
                              size="small"
                              variant="contained"
                              component={RouterLink}
                              to={`/assets/${asset.id}/edit`}
                              sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                            >
                              편집
                            </Button>
                          </Stack>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              {data?.assets?.length ? null : (
                <EmptyState message="조건에 맞는 Assets가 없습니다." sx={{ px: 3, py: 6 }} />
              )}

              {data?.pagination ? (
                <Stack
                  direction={{ xs: 'column', sm: 'row' }}
                  spacing={1.25}
                  sx={{
                    px: 3,
                    py: 2.5,
                    borderTop: '1px solid',
                    borderColor: 'divider',
                    justifyContent: 'space-between',
                  }}
                >
                  <Typography variant="body2" color="text.secondary">
                    현재 페이지 {data.pagination.page} / {data.pagination.total_pages}
                  </Typography>
                  <Stack direction="row" spacing={1.25}>
                    <Button
                      variant="outlined"
                      disabled={!data.pagination.has_prev}
                      onClick={() => movePage(data.pagination.prev_page)}
                    >
                      이전
                    </Button>
                    <Button
                      variant="outlined"
                      disabled={!data.pagination.has_next}
                      onClick={() => movePage(data.pagination.next_page)}
                    >
                      다음
                    </Button>
                  </Stack>
                </Stack>
              ) : null}
            </>
          )}
        </SectionCard>
      </Box>
    </Stack>
  )
}

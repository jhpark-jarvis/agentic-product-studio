import CloseRoundedIcon from '@mui/icons-material/CloseRounded'
import OpenInNewRoundedIcon from '@mui/icons-material/OpenInNewRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  Divider,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'
import { EmptyState, ErrorMessage, LoadingState } from '../components/FeedbackStates'
import { FilterPanel } from '../components/FilterPanel'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'

const initialFilters = {
  q: '',
  asset_type: '',
  gender: '',
}

const typeLabels = { hair: '헤어', face: '성형' }
const genderLabels = { male: '남성', female: '여성' }

function ColorSwatch({ variant, selected, onClick, compact = false }) {
  return (
    <Box
      component="button"
      type="button"
      onClick={onClick}
      title={`${variant.name || '색상 변형'} (${variant.hex_code || 'HEX 없음'})`}
      aria-label={`${variant.name || '색상 변형'} 선택`}
      sx={{
        width: compact ? 20 : 30,
        height: compact ? 20 : 30,
        p: 0,
        borderRadius: '50%',
        border: '2px solid',
        borderColor: selected ? 'primary.main' : 'divider',
        outline: selected ? '2px solid' : 'none',
        outlineColor: selected ? 'primary.light' : 'transparent',
        outlineOffset: 1,
        backgroundColor: variant.hex_code || 'transparent',
        cursor: 'pointer',
        transition: 'transform 140ms ease, border-color 140ms ease',
        '&:hover': { transform: 'scale(1.12)' },
        '&:focus-visible': { outline: '2px solid', outlineColor: 'primary.main', outlineOffset: 2 },
      }}
    />
  )
}

function VariantImage({ variant, alt, size = 112 }) {
  return variant?.thumbnail_url ? (
    <Box
      component="img"
      src={variant.thumbnail_url}
      alt={alt}
      loading="lazy"
      sx={{
        width: size,
        height: size,
        display: 'block',
        objectFit: 'contain',
        borderRadius: 1,
        backgroundColor: 'background.default',
      }}
    />
  ) : (
    <Box sx={{ width: size, height: size, borderRadius: 1, backgroundColor: 'background.default' }} />
  )
}

function defaultVariant(asset) {
  return asset.variants.find((variant) => variant.resource_id === asset.master_resource_id) || asset.variants[0]
}

export function AvatarCatalogPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedAsset, setSelectedAsset] = useState(null)
  const [selectedVariantResourceId, setSelectedVariantResourceId] = useState('')
  const [previewResourceIdByAsset, setPreviewResourceIdByAsset] = useState({})

  const loadCatalog = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      setData(await apiGet('/api/avatar-assets', nextFilters))
    } catch (loadError) {
      setError(loadError.message || '아바타 에셋 데이터를 불러오는 중 문제가 발생했습니다.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadCatalog(initialFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const catalog = data?.assets || []
  const stats = data?.summary || { asset_count: 0, variant_count: 0, hair_count: 0, face_count: 0 }

  const selectedVariant = selectedAsset?.variants.find((variant) => variant.resource_id === selectedVariantResourceId) ||
    (selectedAsset ? defaultVariant(selectedAsset) : null)

  const openDetail = (asset) => {
    const variant = previewResourceIdByAsset[asset.id]
      ? asset.variants.find((item) => item.resource_id === previewResourceIdByAsset[asset.id])
      : defaultVariant(asset)
    setSelectedAsset(asset)
    setSelectedVariantResourceId(variant?.resource_id || '')
  }

  const applyFilters = async (event) => {
    event.preventDefault()
    await loadCatalog(filters)
  }

  const resetFilters = async () => {
    setFilters(initialFilters)
    await loadCatalog(initialFilters)
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="AVATAR ASSETS"
        title="Avatar Asset Catalog"
        description="CATALOG Resource Search에서 검증한 헤어·성형 색상 변형 데이터입니다. 썸네일은 원본 API URL을 사용해 바로 확인할 수 있습니다."
      />

      <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' }, gap: 2 }}>
        {[ 
          ['기준 외형', `${stats.asset_count}개`],
          ['색상 변형', `${stats.variant_count}개`],
          ['헤어', `${stats.hair_count}개`],
          ['성형', `${stats.face_count}개`],
        ].map(([label, value]) => (
          <SectionCard key={label} title={value} description={label} contentSx={{ display: 'none' }} />
        ))}
      </Box>

      <FilterPanel
        title="아바타 에셋 필터"
        onSubmit={applyFilters}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button type="submit" variant="contained" startIcon={<SearchRoundedIcon />}>
              필터 적용
            </Button>
            <Chip color="primary" variant="outlined" label={`${catalog.length}개 표시`} />
            <Button variant="outlined" onClick={resetFilters} startIcon={<RefreshRoundedIcon />}>
              초기화
            </Button>
          </Stack>
        }
      >
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'minmax(260px, 1.4fr) 1fr 1fr' }, gap: 2 }}>
          <TextField
            label="이름 또는 RESOURCE_ID 검색"
            value={filters.q}
            onChange={(event) => setFilters((current) => ({ ...current, q: event.target.value }))}
            placeholder="예: 히어로 헤어"
          />
          <TextField
            label="유형"
            select
            value={filters.asset_type}
            onChange={(event) => setFilters((current) => ({ ...current, asset_type: event.target.value }))}
          >
            <MenuItem value="">전체 유형</MenuItem>
            <MenuItem value="hair">헤어</MenuItem>
            <MenuItem value="face">성형</MenuItem>
          </TextField>
          <TextField
            label="성별"
            select
            value={filters.gender}
            onChange={(event) => setFilters((current) => ({ ...current, gender: event.target.value }))}
          >
            <MenuItem value="">전체 성별</MenuItem>
            <MenuItem value="male">남성</MenuItem>
            <MenuItem value="female">여성</MenuItem>
          </TextField>
        </Box>
      </FilterPanel>

      <SectionCard
        title="외형 목록"
        description="색상칩을 누르면 카드의 미리보기가 바뀌고, 카드를 누르면 각 변형의 RESOURCE_ID와 원본 썸네일을 확인할 수 있습니다."
        metric={`${catalog.length}개 외형`}
      >
        <ErrorMessage message={error} sx={{ px: 3, pb: 3 }} />
        {loading ? <LoadingState message="아바타 에셋 카탈로그를 불러오는 중입니다..." /> : null}
        {!loading && !error && !catalog.length ? <EmptyState message="조건에 맞는 아바타 에셋이 없습니다." sx={{ px: 3, py: 7 }} /> : null}
        {!loading && !error && catalog.length ? (
          <Box
            sx={{
              p: 3,
              pt: 0,
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, minmax(0, 1fr))', xl: 'repeat(3, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            {catalog.map((asset) => {
              const preview = asset.variants.find((variant) => variant.resource_id === previewResourceIdByAsset[asset.id]) || defaultVariant(asset)
              return (
                <Box
                  key={asset.id}
                  component="article"
                  sx={{
                    display: 'grid',
                    gridTemplateColumns: '112px minmax(0, 1fr)',
                    gap: 1.75,
                    p: 1.75,
                    minWidth: 0,
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    backgroundColor: 'background.default',
                  }}
                >
                  <Box sx={{ cursor: 'pointer' }} onClick={() => openDetail(asset)}>
                    <VariantImage variant={preview} alt={`${asset.name} ${preview?.name || ''}`} />
                  </Box>
                  <Stack spacing={1} sx={{ minWidth: 0 }}>
                    <Box sx={{ cursor: 'pointer' }} onClick={() => openDetail(asset)}>
                      <Typography fontWeight={800} sx={{ lineHeight: 1.4, overflowWrap: 'anywhere' }}>
                        {asset.name}
                      </Typography>
                      <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap" sx={{ mt: 0.75 }}>
                        <Chip size="small" label={typeLabels[asset.asset_type] || asset.asset_type} />
                        <Chip size="small" variant="outlined" label={genderLabels[asset.gender] || asset.gender} />
                        <Chip size="small" variant="outlined" label={`${asset.variants.length}색상`} />
                      </Stack>
                    </Box>
                    <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                      {asset.variants.map((variant) => (
                        <ColorSwatch
                          key={variant.resource_id}
                          variant={variant}
                          compact
                          selected={preview?.resource_id === variant.resource_id}
                          onClick={() => setPreviewResourceIdByAsset((current) => ({ ...current, [asset.id]: variant.resource_id }))}
                        />
                      ))}
                    </Stack>
                    <Typography variant="caption" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>
                      {preview?.name || '색상 정보 없음'} · {preview?.hex_code || '-'}
                    </Typography>
                  </Stack>
                </Box>
              )
            })}
          </Box>
        ) : null}
      </SectionCard>

      <Dialog open={Boolean(selectedAsset)} onClose={() => setSelectedAsset(null)} maxWidth="md" fullWidth>
        <DialogTitle sx={{ pr: 7 }}>
          {selectedAsset?.name}
          <IconButton aria-label="상세 닫기" onClick={() => setSelectedAsset(null)} sx={{ position: 'absolute', right: 14, top: 14 }}>
            <CloseRoundedIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent dividers>
          {selectedAsset && selectedVariant ? (
            <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', sm: '220px minmax(0, 1fr)' }, gap: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'flex-start', p: 2, borderRadius: 1, backgroundColor: 'background.default' }}>
                <VariantImage variant={selectedVariant} alt={`${selectedAsset.name} ${selectedVariant.name}`} size={180} />
              </Box>
              <Stack spacing={2}>
                <Stack direction="row" spacing={0.75} useFlexGap flexWrap="wrap">
                  <Chip label={typeLabels[selectedAsset.asset_type] || selectedAsset.asset_type} />
                  <Chip variant="outlined" label={genderLabels[selectedAsset.gender] || selectedAsset.gender} />
                  <Chip variant="outlined" label={selectedAsset.availability || '제공 범위 미상'} />
                </Stack>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {selectedAsset.variants.map((variant) => (
                    <ColorSwatch
                      key={variant.resource_id}
                      variant={variant}
                      selected={variant.resource_id === selectedVariant.resource_id}
                      onClick={() => setSelectedVariantResourceId(variant.resource_id)}
                    />
                  ))}
                </Box>
                <Divider />
                <Stack spacing={0.75}>
                  <Typography variant="body2" color="text.secondary">선택 색상: {selectedVariant.name || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary">HEX: {selectedVariant.hex_code || '-'}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>변형 RESOURCE_ID: {selectedVariant.resource_id}</Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ overflowWrap: 'anywhere' }}>기준 RESOURCE_ID: {selectedAsset.master_resource_id}</Typography>
                  <Typography variant="body2" color="text.secondary">내부명: {selectedVariant.dname || '-'}</Typography>
                </Stack>
                <Button component="a" href={selectedVariant.thumbnail_url} target="_blank" rel="noreferrer" variant="outlined" startIcon={<OpenInNewRoundedIcon />} sx={{ alignSelf: 'flex-start' }}>
                  원본 썸네일 열기
                </Button>
              </Stack>
            </Box>
          ) : null}
        </DialogContent>
      </Dialog>
    </Stack>
  )
}

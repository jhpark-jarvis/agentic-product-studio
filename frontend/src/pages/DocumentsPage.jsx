import CreateRoundedIcon from '@mui/icons-material/CreateRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import {
  Box,
  Button,
  Checkbox,
  Chip,
  FormControlLabel,
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
import { EmptyState, ErrorMessage, LoadingState } from '../components/FeedbackStates'
import { FilterPanel } from '../components/FilterPanel'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'

const initialFilters = {
  q: '',
  doc_type: '',
  tag: '',
  folder_id: '',
  include_hidden: false,
  page: 1,
  per_page: 20,
}

export function DocumentsPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadDocuments = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/documents', nextFilters)
      setData(payload)
    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDocuments(initialFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyFilters = async (event) => {
    event.preventDefault()
    const nextFilters = { ...filters, page: 1 }
    setFilters(nextFilters)
    await loadDocuments(nextFilters)
  }

  const resetFilters = async () => {
    setFilters(initialFilters)
    await loadDocuments(initialFilters)
  }

  const movePage = async (page) => {
    const nextFilters = { ...filters, page }
    setFilters(nextFilters)
    await loadDocuments(nextFilters)
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="DOCUMENTS"
        title="문서 관리"
        description="문서 검색, 분류, 상세 확인, 편집 진입까지 한 흐름으로 관리할 수 있도록 정리한 화면입니다."
      />

      <FilterPanel
        title="문서 필터"
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
              variant="outlined"
              color="secondary"
              startIcon={<CreateRoundedIcon />}
              component={RouterLink}
              to="/documents/new"
            >
              새 문서 작성
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
            label="숨김 문서 포함"
          />

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1.4fr 1fr 1fr 1fr 0.7fr' },
              gap: 2,
            }}
          >
            <TextField
              label="문서 제목 검색"
              value={filters.q}
              onChange={(event) => setFilters((prev) => ({ ...prev, q: event.target.value }))}
            />
            <TextField
              select
              label="문서 유형"
              value={filters.doc_type}
              onChange={(event) => setFilters((prev) => ({ ...prev, doc_type: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.document_types || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="폴더"
              value={filters.folder_id}
              onChange={(event) => setFilters((prev) => ({ ...prev, folder_id: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.folder_options || []).map((option) => (
                <MenuItem key={option.id} value={option.id}>
                  {option.doc_type} / {option.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="태그"
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
              select
              label="표시 수"
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
        </Stack>
      </FilterPanel>

      <SectionCard
        title="문서 목록"
        description={`${filters.include_hidden ? '숨김 포함' : '숨김 제외'} 전체 ${data?.pagination?.total_count ?? 0}건 중 ${data?.documents?.length ?? 0}건 표시`}
        metric={data?.pagination ? `${data.pagination.page} / ${data.pagination.total_pages} 페이지` : null}
      >
        <ErrorMessage message={error} sx={{ px: 3, pb: 3 }} />

        {loading ? (
          <LoadingState message="문서 목록을 불러오는 중입니다..." />
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
              <Table sx={{ minWidth: { xs: 720, md: 960 } }}>
                <TableHead>
                  <TableRow>
                    <TableCell>제목</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>유형</TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>폴더</TableCell>
                    <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>작성자</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>수정일</TableCell>
                    <TableCell>관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.documents || []).map((document) => (
                    <TableRow key={document.id} hover>
                      <TableCell sx={{ minWidth: 280 }}>
                        <Stack spacing={0.5}>
                          <Button
                            component={RouterLink}
                            to={`/documents/${document.id}`}
                            sx={{ justifyContent: 'flex-start', px: 0, textAlign: 'left' }}
                          >
                            {document.title}
                          </Button>
                          <Typography variant="body2" color="text.secondary">
                            {document.folder_name
                              ? `${document.doc_type} / ${document.folder_name}`
                              : document.doc_type}
                          </Typography>
                          {document.is_hidden ? (
                            <Chip size="small" label="숨김" color="warning" variant="outlined" />
                          ) : null}
                        </Stack>
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        <Chip size="small" label={document.doc_type} />
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>
                        {document.folder_name ? `${document.doc_type} / ${document.folder_name}` : '미지정'}
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>
                        {document.author_name || '-'}
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                        {document.updated_at || '-'}
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} justifyContent="flex-start" sx={{ flexWrap: 'nowrap' }}>
                          <Button
                            size="small"
                            variant="outlined"
                            component={RouterLink}
                            to={`/documents/${document.id}`}
                            sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                          >
                            상세
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            component={RouterLink}
                            to={`/documents/${document.id}/edit`}
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

            {data?.documents?.length ? null : (
              <EmptyState message="조건에 맞는 문서가 없습니다." sx={{ px: 3, py: 6 }} />
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
                <Stack direction="row" spacing={1.25} sx={{ justifyContent: { xs: 'stretch', sm: 'flex-end' } }}>
                  <Button
                    variant="outlined"
                    disabled={!data.pagination.has_prev}
                    onClick={() => movePage(data.pagination.prev_page)}
                    sx={{ flex: { xs: 1, sm: '0 0 auto' } }}
                  >
                    이전
                  </Button>
                  <Button
                    variant="outlined"
                    disabled={!data.pagination.has_next}
                    onClick={() => movePage(data.pagination.next_page)}
                    sx={{ flex: { xs: 1, sm: '0 0 auto' } }}
                  >
                    다음
                  </Button>
                </Stack>
              </Stack>
            ) : null}
          </>
        )}
      </SectionCard>
    </Stack>
  )
}

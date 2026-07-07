import CreateRoundedIcon from '@mui/icons-material/CreateRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
import SearchRoundedIcon from '@mui/icons-material/SearchRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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
import { useEffect, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'

const initialFilters = {
  q: '',
  doc_type: '',
  tag: '',
  folder_id: '',
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
        description="문서 조회와 편집 진입 흐름을 React 기준으로 정리한 상태입니다. 이제 목록, 상세, 작성, 편집을 같은 라우팅 체계 안에서 사용할 수 있습니다."
      />

      <Paper component="form" onSubmit={applyFilters} sx={{ p: 3 }}>
        <Stack spacing={2.5}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between' }}
          >
            <Typography variant="h6">문서 필터</Typography>
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
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1.4fr 1fr 1fr 1fr 0.7fr' },
              gap: 2,
            }}
          >
            <TextField
              label="검색"
              placeholder="문서 제목 검색"
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
      </Paper>

      <Paper sx={{ p: 0, overflow: 'hidden' }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={1.5}
          sx={{ px: 3, py: 2.5, alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Box>
            <Typography variant="h6">문서 목록</Typography>
            <Typography variant="body2" color="text.secondary">
              숨김 문서를 제외한 전체 {data?.pagination?.total_count ?? 0}건 중 {data?.documents?.length ?? 0}건 표시
            </Typography>
          </Box>
          {data?.pagination ? (
            <Chip
              label={`${data.pagination.page} / ${data.pagination.total_pages} 페이지`}
              color="primary"
              variant="outlined"
            />
          ) : null}
        </Stack>

        {error ? (
          <Box sx={{ px: 3, pb: 3 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : null}

        {loading ? (
          <Stack sx={{ py: 8, alignItems: 'center', justifyContent: 'center' }} spacing={2}>
            <CircularProgress size={30} />
            <Typography color="text.secondary">문서 목록을 불러오는 중입니다...</Typography>
          </Stack>
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid #d9e1ec' }}>
              <Table sx={{ minWidth: 960 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>제목</TableCell>
                    <TableCell>유형</TableCell>
                    <TableCell>폴더</TableCell>
                    <TableCell>작성자</TableCell>
                    <TableCell>수정일</TableCell>
                    <TableCell align="right">관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.documents || []).map((document) => (
                    <TableRow key={document.id} hover>
                      <TableCell sx={{ minWidth: 280 }}>
                        <Stack spacing={0.5}>
                          <Typography fontWeight={700}>{document.title}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            상세는 React 상세 화면에서 확인하고, 편집은 React 에디터로 바로 이어집니다.
                          </Typography>
                        </Stack>
                      </TableCell>
                      <TableCell>
                        <Chip size="small" label={document.doc_type} />
                      </TableCell>
                      <TableCell>
                        {document.folder_name ? `${document.doc_type} / ${document.folder_name}` : '미지정'}
                      </TableCell>
                      <TableCell>{document.author_name || '-'}</TableCell>
                      <TableCell>{document.updated_at || '-'}</TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button
                            size="small"
                            variant="outlined"
                            component={RouterLink}
                            to={`/documents/${document.id}`}
                          >
                            상세
                          </Button>
                          <Button
                            size="small"
                            variant="contained"
                            component={RouterLink}
                            to={`/documents/${document.id}/edit`}
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
              <Box sx={{ px: 3, py: 6 }}>
                <Alert severity="info">조건에 맞는 문서가 없습니다.</Alert>
              </Box>
            )}

            {data?.pagination ? (
              <Stack
                direction={{ xs: 'column', sm: 'row' }}
                spacing={1.25}
                sx={{ px: 3, py: 2.5, borderTop: '1px solid #d9e1ec', justifyContent: 'space-between' }}
              >
                <Typography variant="body2" color="text.secondary">
                  현재 페이지 {data.pagination.page} / {data.pagination.total_pages}
                </Typography>
                <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
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
      </Paper>
    </Stack>
  )
}

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
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'

const initialFilters = {
  q: '',
  visitor_id: '',
  limit: 200,
}

function SummaryChip({ label, value }) {
  return <Chip label={`${label} ${value}`} color="primary" variant="outlined" />
}

export function LogsPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadLogs = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/logs/page-views', nextFilters)
      setData(payload)
    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadLogs(initialFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyFilters = async (event) => {
    event.preventDefault()
    await loadLogs(filters)
  }

  const resetFilters = async () => {
    setFilters(initialFilters)
    await loadLogs(initialFilters)
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="LOGS"
        title="접속 로그 조회"
        description="최근 페이지 이동 로그를 숨김 관리자 경로에서 조회합니다. visitor_id와 session_id 기준으로 같은 브라우저 흐름을 추적할 수 있습니다."
      />

      <Paper component="form" onSubmit={applyFilters} sx={{ p: 3 }}>
        <Stack spacing={2.5}>
          <Stack direction={{ xs: 'column', md: 'row' }} spacing={2} sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between' }}>
            <Typography variant="h6">로그 필터</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
              <Button type="submit" variant="contained" startIcon={<SearchRoundedIcon />}>
                조회
              </Button>
              <Button variant="outlined" startIcon={<RefreshRoundedIcon />} onClick={resetFilters}>
                초기화
              </Button>
            </Stack>
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: '1.2fr 1fr 180px' },
              gap: 2,
            }}
          >
            <TextField
              label="통합 검색"
              value={filters.q}
              onChange={(event) => setFilters((prev) => ({ ...prev, q: event.target.value }))}
              helperText="path, referrer, visitor_id, session_id, ip, user agent 기준 검색"
            />
            <TextField
              label="visitor_id"
              value={filters.visitor_id}
              onChange={(event) => setFilters((prev) => ({ ...prev, visitor_id: event.target.value }))}
            />
            <TextField
              select
              label="조회 수"
              value={filters.limit}
              onChange={(event) => setFilters((prev) => ({ ...prev, limit: Number(event.target.value) }))}
            >
              {[50, 100, 200, 500, 1000].map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </Stack>
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={1.25} useFlexGap flexWrap="wrap">
          <SummaryChip label="로그" value={data?.summary?.total ?? 0} />
          <SummaryChip label="방문자" value={data?.summary?.unique_visitors ?? 0} />
          <SummaryChip label="세션" value={data?.summary?.unique_sessions ?? 0} />
          <SummaryChip label="경로" value={data?.summary?.unique_paths ?? 0} />
        </Stack>
      </Paper>

      <Paper sx={{ overflow: 'hidden' }}>
        {error ? (
          <Box sx={{ p: 3 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : null}

        {loading ? (
          <Stack sx={{ py: 8, alignItems: 'center' }} spacing={2}>
            <CircularProgress size={30} />
            <Typography color="text.secondary">접속 로그를 불러오는 중입니다...</Typography>
          </Stack>
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
              <Table sx={{ minWidth: 1280 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>시각</TableCell>
                    <TableCell>Path</TableCell>
                    <TableCell>Referrer</TableCell>
                    <TableCell>Visitor</TableCell>
                    <TableCell>Session</TableCell>
                    <TableCell>IP</TableCell>
                    <TableCell>User Agent</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.logs || []).map((row, index) => (
                    <TableRow key={`${row.ts}-${row.path}-${index}`} hover>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>{row.ts || '-'}</TableCell>
                      <TableCell sx={{ fontWeight: 700 }}>{row.path || '-'}</TableCell>
                      <TableCell>{row.referrer || '-'}</TableCell>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{row.visitor_id || '-'}</TableCell>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{row.session_id || '-'}</TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>{row.ip || '-'}</TableCell>
                      <TableCell sx={{ minWidth: 320, wordBreak: 'break-all' }}>{row.user_agent || '-'}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {data?.logs?.length ? null : (
              <Box sx={{ p: 3 }}>
                <Alert severity="info">조회 조건에 맞는 접속 로그가 없습니다.</Alert>
              </Box>
            )}
          </>
        )}
      </Paper>
    </Stack>
  )
}

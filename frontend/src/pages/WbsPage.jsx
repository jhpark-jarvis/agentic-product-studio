import AddRoundedIcon from '@mui/icons-material/AddRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
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
  status: '',
  assignee_id: '',
  priority: '',
  platform: '',
}

function ProgressBar({ value }) {
  return (
    <Stack spacing={0.75} sx={{ minWidth: 120 }}>
      <Box
        sx={{
          height: 8,
          borderRadius: 999,
          bgcolor: '#e2e8f0',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            width: `${value}%`,
            height: '100%',
            borderRadius: 999,
            bgcolor: '#4f46e5',
          }}
        />
      </Box>
      <Typography variant="caption" color="text.secondary">
        {value}%
      </Typography>
    </Stack>
  )
}

function TaskTitleCell({ row }) {
  const task = row.task
  const subtext = row.is_delayed
    ? '지연'
    : row.is_due_soon
      ? '마감 임박'
      : task.parent_title
        ? `상위 작업: ${task.parent_title}`
        : '최상위 작업'

  return (
    <Stack spacing={0.4} sx={{ pl: `${row.depth * 18}px` }}>
      <Typography fontWeight={700}>{task.title}</Typography>
      <Typography variant="body2" color="text.secondary">
        {subtext}
      </Typography>
    </Stack>
  )
}

export function WbsPage() {
  const [filters, setFilters] = useState(initialFilters)
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadTasks = async (nextFilters = filters) => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/wbs', nextFilters)
      setData(payload)
    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadTasks(initialFilters)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const applyFilters = async (event) => {
    event.preventDefault()
    await loadTasks(filters)
  }

  const resetFilters = async () => {
    setFilters(initialFilters)
    await loadTasks(initialFilters)
  }

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="WORK BREAKDOWN STRUCTURE"
        title="WBS 작업 관리"
        description="필터, 계층 구조, 진행률, 지연 상태를 React 테이블로 먼저 이관했습니다. 생성 및 수정은 기존 폼을 당분간 함께 사용합니다."
      />

      <Paper component="form" onSubmit={applyFilters} sx={{ p: 3 }}>
        <Stack spacing={2.5}>
          <Stack
            direction={{ xs: 'column', md: 'row' }}
            spacing={2}
            sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between' }}
          >
            <Typography variant="h6">작업 필터</Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
              <Button type="submit" variant="contained">
                필터 적용
              </Button>
              <Button variant="outlined" startIcon={<RefreshRoundedIcon />} onClick={resetFilters}>
                초기화
              </Button>
              <Button variant="outlined" color="secondary" startIcon={<AddRoundedIcon />} href="/wbs/new">
                작업 생성
              </Button>
            </Stack>
          </Stack>

          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', md: 'repeat(4, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            <TextField
              select
              label="상태"
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
              select
              label="담당자"
              value={filters.assignee_id}
              onChange={(event) => setFilters((prev) => ({ ...prev, assignee_id: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.members || []).map((member) => (
                <MenuItem key={member.id} value={member.id}>
                  {member.name}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="우선순위"
              value={filters.priority}
              onChange={(event) => setFilters((prev) => ({ ...prev, priority: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.priorities || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
            <TextField
              select
              label="플랫폼"
              value={filters.platform}
              onChange={(event) => setFilters((prev) => ({ ...prev, platform: event.target.value }))}
            >
              <MenuItem value="">전체</MenuItem>
              {(data?.platforms || []).map((option) => (
                <MenuItem key={option} value={option}>
                  {option}
                </MenuItem>
              ))}
            </TextField>
          </Box>
        </Stack>
      </Paper>

      <Paper sx={{ overflow: 'hidden' }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={1.5}
          sx={{ px: 3, py: 2.5, alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Box>
            <Typography variant="h6">작업 목록</Typography>
            <Typography variant="body2" color="text.secondary">
              상위/하위 작업 구조와 현재 진행 상태를 함께 관리합니다.
            </Typography>
          </Box>
          <Chip label={`${data?.task_rows?.length || 0}건`} color="primary" variant="outlined" />
        </Stack>

        {error ? (
          <Box sx={{ px: 3, pb: 3 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : null}

        {loading ? (
          <Stack sx={{ py: 8, alignItems: 'center', justifyContent: 'center' }} spacing={2}>
            <CircularProgress size={30} />
            <Typography color="text.secondary">WBS 목록을 불러오는 중입니다...</Typography>
          </Stack>
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid #d9e1ec' }}>
              <Table sx={{ minWidth: 1240 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell sx={{ minWidth: 300 }}>작업명</TableCell>
                    <TableCell>플랫폼</TableCell>
                    <TableCell>담당자</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell>우선순위</TableCell>
                    <TableCell>진행률</TableCell>
                    <TableCell>시작일</TableCell>
                    <TableCell>마감일</TableCell>
                    <TableCell align="right">관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.task_rows || []).map((row) => (
                    <TableRow
                      key={row.task.id}
                      hover
                      sx={{
                        bgcolor: row.is_delayed ? '#fff1f2' : row.is_due_soon ? '#fffdf3' : 'inherit',
                      }}
                    >
                      <TableCell>#{row.task.id}</TableCell>
                      <TableCell>
                        <TaskTitleCell row={row} />
                      </TableCell>
                      <TableCell>{row.task.platform || 'Agentic Product Studio'}</TableCell>
                      <TableCell>{row.task.assignee_name || '-'}</TableCell>
                      <TableCell>
                        <Chip size="small" label={row.task.status} />
                      </TableCell>
                      <TableCell>
                        <Chip size="small" variant="outlined" label={row.task.priority} />
                      </TableCell>
                      <TableCell>
                        <ProgressBar value={row.task.progress || 0} />
                      </TableCell>
                      <TableCell>{row.task.start_date || '-'}</TableCell>
                      <TableCell>{row.task.due_date || '-'}</TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button size="small" variant="outlined" href={`/wbs/${row.task.id}/edit`}>
                            수정
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {data?.task_rows?.length ? null : (
              <Box sx={{ px: 3, py: 6 }}>
                <Alert severity="info">조건에 맞는 WBS 작업이 없습니다.</Alert>
              </Box>
            )}
          </>
        )}
      </Paper>
    </Stack>
  )
}

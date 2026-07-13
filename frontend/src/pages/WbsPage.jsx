import AddRoundedIcon from '@mui/icons-material/AddRounded'
import RefreshRoundedIcon from '@mui/icons-material/RefreshRounded'
import {
  Box,
  Button,
  Chip,
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
          bgcolor: 'action.hover',
          overflow: 'hidden',
        }}
      >
        <Box
          sx={{
            width: `${value}%`,
            height: '100%',
            borderRadius: 999,
            bgcolor: 'primary.main',
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
      <Button
        component={RouterLink}
        to={`/wbs/${task.id}`}
        sx={{ justifyContent: 'flex-start', px: 0, textAlign: 'left', fontWeight: 700 }}
      >
        {task.title}
      </Button>
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
        description="필터, 계층 구조, 진행률, 지연 상태를 한 화면에서 확인하고 작업 상세와 편집으로 이어질 수 있도록 정리했습니다."
      />

      <FilterPanel
        title="작업 필터"
        onSubmit={applyFilters}
        actions={
          <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.25}>
            <Button type="submit" variant="contained">
              필터 적용
            </Button>
            <Button variant="outlined" startIcon={<RefreshRoundedIcon />} onClick={resetFilters}>
              초기화
            </Button>
            <Button
              component={RouterLink}
              to="/wbs/new"
              variant="outlined"
              color="secondary"
              startIcon={<AddRoundedIcon />}
            >
              작업 생성
            </Button>
          </Stack>
        }
      >
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
      </FilterPanel>

      <SectionCard
        title="작업 목록"
        description="상위/하위 작업 구조와 현재 진행 상태를 함께 관리합니다."
        metric={`${data?.task_rows?.length || 0}건`}
      >
        <ErrorMessage message={error} sx={{ px: 3, pb: 3 }} />

        {loading ? (
          <LoadingState message="WBS 목록을 불러오는 중입니다..." />
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
              <Table sx={{ minWidth: { xs: 980, md: 1320 } }}>
                <TableHead>
                  <TableRow>
                    <TableCell>ID</TableCell>
                    <TableCell sx={{ minWidth: 300 }}>작업명</TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 150 }}>
                      플랫폼
                    </TableCell>
                    <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 104 }}>
                      담당자
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 88 }}>상태</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 96 }}>
                      우선순위
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 132 }}>진행률</TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 112 }}>
                      시작일
                    </TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 112 }}>
                      마감일
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 130 }}>관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.task_rows || []).map((row) => (
                    <TableRow
                      key={row.task.id}
                      hover
                      sx={{
                        bgcolor: row.is_delayed
                          ? 'rgba(177, 75, 47, 0.10)'
                          : row.is_due_soon
                            ? 'rgba(212, 160, 23, 0.10)'
                            : 'inherit',
                      }}
                    >
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>#{row.task.id}</TableCell>
                      <TableCell>
                        <TaskTitleCell row={row} />
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, whiteSpace: 'nowrap' }}>
                        {row.task.platform || 'Agentic Product Studio'}
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' }, whiteSpace: 'nowrap' }}>
                        {row.task.assignee_name || '-'}
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>
                        <Chip size="small" label={row.task.status} />
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap' }}>
                        <Chip size="small" variant="outlined" label={row.task.priority} />
                      </TableCell>
                      <TableCell sx={{ whiteSpace: 'nowrap' }}>
                        <ProgressBar value={row.task.progress || 0} />
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, whiteSpace: 'nowrap' }}>
                        {row.task.start_date || '-'}
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap' }}>
                        {row.task.due_date || '-'}
                      </TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} justifyContent="flex-start" sx={{ flexWrap: 'nowrap' }}>
                          <Button
                            size="small"
                            variant="outlined"
                            component={RouterLink}
                            to={`/wbs/${row.task.id}`}
                            sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                          >
                            상세
                          </Button>
                          <Button
                            size="small"
                            variant="outlined"
                            component={RouterLink}
                            to={`/wbs/${row.task.id}/edit`}
                            sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                          >
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
              <EmptyState message="조건에 맞는 WBS 작업이 없습니다." sx={{ px: 3, py: 6 }} />
            )}
          </>
        )}
      </SectionCard>
    </Stack>
  )
}

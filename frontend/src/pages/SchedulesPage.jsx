import AddRoundedIcon from '@mui/icons-material/AddRounded'
import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import CalendarMonthRoundedIcon from '@mui/icons-material/CalendarMonthRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Paper,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material'
import { useEffect, useMemo, useState } from 'react'
import { Link as RouterLink } from 'react-router-dom'
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'

function formatMonthLabel(monthQuery) {
  const [year, month] = monthQuery.split('-')
  return `${year}년 ${Number(month)}월`
}

function shiftMonth(monthQuery, diff) {
  const [year, month] = monthQuery.split('-').map(Number)
  const next = new Date(year, month - 1 + diff, 1)
  const nextYear = next.getFullYear()
  const nextMonth = String(next.getMonth() + 1).padStart(2, '0')
  return `${nextYear}-${nextMonth}`
}

function formatDateRange(item) {
  if (!item.start_date && !item.end_date) {
    return '-'
  }
  if (item.start_date === item.end_date || !item.end_date) {
    return item.start_date
  }
  return `${item.start_date} ~ ${item.end_date}`
}

function WeekScheduleCard({ item }) {
  return (
    <Paper sx={{ p: 2.25, height: '100%' }}>
      <Stack spacing={1.2}>
        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center">
          <Typography fontWeight={700}>{item.title}</Typography>
          <Chip size="small" label={item.schedule_type} color="primary" variant="outlined" />
        </Stack>
        <Typography variant="body2" color="text.secondary">
          {formatDateRange(item)}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          담당자: {item.assignee_name || '-'}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          연결 작업: {item.task_title || '-'}
        </Typography>
        {item.description ? (
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              display: '-webkit-box',
              WebkitLineClamp: 3,
              WebkitBoxOrient: 'vertical',
              overflow: 'hidden',
            }}
          >
            {item.description}
          </Typography>
        ) : null}
      </Stack>
    </Paper>
  )
}

export function SchedulesPage() {
  const [monthQuery, setMonthQuery] = useState(() => {
    const now = new Date()
    return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}`
  })
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [selectedDay, setSelectedDay] = useState(null)

  const loadSchedules = async (nextMonth = monthQuery) => {
    setLoading(true)
    setError('')
    try {
      const payload = await apiGet('/api/schedules', { month: nextMonth })
      setData(payload)
      setMonthQuery(payload.month_query)
    } catch (fetchError) {
      setError(fetchError.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSchedules(monthQuery)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const weekdays = useMemo(() => ['월', '화', '수', '목', '금', '토', '일'], [])

  const monthCells = useMemo(() => {
    if (!data?.month_days?.length) {
      return []
    }

    const cells = []
    const firstDate = new Date(`${data.month_days[0].date}T00:00:00`)
    const mondayIndex = (firstDate.getDay() + 6) % 7
    for (let index = 0; index < mondayIndex; index += 1) {
      cells.push({ key: `blank-start-${index}`, empty: true })
    }
    data.month_days.forEach((day) => {
      cells.push({ ...day, key: day.date })
    })
    while (cells.length % 7 !== 0) {
      cells.push({ key: `blank-end-${cells.length}`, empty: true })
    }
    return cells
  }, [data])

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="SCHEDULES"
        title="일정 관리"
        description="이번 주 일정, 월간 캘린더, 전체 일정 목록을 React 화면으로 이어서 사용할 수 있게 정리했습니다. 이제 생성과 수정도 같은 라우팅 안에서 이어집니다."
      />

      <Paper sx={{ p: 3 }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h6">이번 주 일정</Typography>
            <Typography variant="body2" color="text.secondary">
              {data?.week_range?.start || '-'} ~ {data?.week_range?.end || '-'}
            </Typography>
          </Stack>
          <Button component={RouterLink} to="/schedules/new" variant="outlined" color="secondary" startIcon={<AddRoundedIcon />}>
            새 일정
          </Button>
        </Stack>

        {error ? <Alert severity="error" sx={{ mt: 2.5 }}>{error}</Alert> : null}

        {loading ? (
          <Stack spacing={2} sx={{ py: 8, alignItems: 'center', justifyContent: 'center' }}>
            <CircularProgress size={30} />
            <Typography color="text.secondary">일정 정보를 불러오는 중입니다...</Typography>
          </Stack>
        ) : (
          <Box
            sx={{
              mt: 2.5,
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', xl: 'repeat(3, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            {data?.week_items?.length ? (
              data.week_items.map((item) => <WeekScheduleCard key={item.id} item={item} />)
            ) : (
              <Alert severity="info">이번 주 일정이 없습니다.</Alert>
            )}
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 3 }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between', mb: 2.5 }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h6">월간 일정</Typography>
            <Typography variant="body2" color="text.secondary">
              날짜를 누르면 해당 일자에 걸린 일정을 확인할 수 있습니다.
            </Typography>
          </Stack>
          <Stack direction="row" spacing={1} alignItems="center">
            <Button variant="outlined" onClick={() => loadSchedules(shiftMonth(monthQuery, -1))}>
              <ChevronLeftRoundedIcon fontSize="small" />
            </Button>
            <Chip icon={<CalendarMonthRoundedIcon />} label={formatMonthLabel(monthQuery)} color="primary" />
            <Button variant="outlined" onClick={() => loadSchedules(shiftMonth(monthQuery, 1))}>
              <ChevronRightRoundedIcon fontSize="small" />
            </Button>
          </Stack>
        </Stack>

        {loading ? null : (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
              gap: 1.25,
            }}
          >
            {weekdays.map((weekday) => (
              <Box
                key={weekday}
                sx={{
                  px: 1,
                  py: 1.25,
                  textAlign: 'center',
                  borderRadius: 2,
                  bgcolor: '#eef4ff',
                  color: 'text.secondary',
                  fontWeight: 700,
                  fontSize: 13,
                }}
              >
                {weekday}
              </Box>
            ))}
            {monthCells.map((day) =>
              day.empty ? (
                <Box key={day.key} sx={{ minHeight: 132, borderRadius: 3, bgcolor: '#f8fafc' }} />
              ) : (
                <Paper
                  key={day.key}
                  variant="outlined"
                  onClick={() => setSelectedDay(day)}
                  sx={{
                    minHeight: 132,
                    p: 1.25,
                    cursor: 'pointer',
                    borderColor: day.is_today ? 'primary.main' : 'divider',
                    bgcolor: day.is_today ? '#eef4ff' : 'background.paper',
                  }}
                >
                  <Stack spacing={0.8}>
                    <Typography variant="subtitle2" fontWeight={800}>
                      {Number(day.date.slice(-2))}
                    </Typography>
                    {day.start_items.map((item) => (
                      <Chip
                        key={`${day.date}-${item.id}`}
                        size="small"
                        label={item.title}
                        color="primary"
                        variant="outlined"
                        sx={{
                          justifyContent: 'flex-start',
                          '& .MuiChip-label': {
                            display: 'block',
                            overflow: 'hidden',
                            textOverflow: 'ellipsis',
                            whiteSpace: 'nowrap',
                          },
                        }}
                      />
                    ))}
                    {day.hidden_start_count ? (
                      <Typography variant="caption" color="text.secondary">
                        + 새 일정 {day.hidden_start_count}건
                      </Typography>
                    ) : null}
                    {day.continuing_count ? (
                      <Typography variant="caption" color="text.secondary">
                        이어지는 일정 {day.continuing_count}건
                      </Typography>
                    ) : null}
                  </Stack>
                </Paper>
              ),
            )}
          </Box>
        )}
      </Paper>

      <Paper sx={{ p: 0, overflow: 'hidden' }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={1.5}
          sx={{ px: 3, py: 2.5, alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Stack spacing={0.5}>
            <Typography variant="h6">전체 일정 목록</Typography>
            <Typography variant="body2" color="text.secondary">
              WBS와 연결된 전체 일정을 한 번에 확인합니다.
            </Typography>
          </Stack>
          <Chip label={`${data?.schedules?.length || 0}건`} color="primary" variant="outlined" />
        </Stack>

        {loading ? null : (
          <TableContainer sx={{ borderTop: '1px solid #d9e1ec' }}>
            <Table sx={{ minWidth: 980 }}>
              <TableHead>
                <TableRow>
                  <TableCell>일정명</TableCell>
                  <TableCell>유형</TableCell>
                  <TableCell>기간</TableCell>
                  <TableCell>담당자</TableCell>
                  <TableCell>연결 작업</TableCell>
                  <TableCell align="right">관리</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(data?.schedules || []).map((item) => (
                  <TableRow key={item.id} hover>
                    <TableCell sx={{ minWidth: 280 }}>
                      <Stack spacing={0.5}>
                        <Typography fontWeight={700}>{item.title}</Typography>
                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{
                            display: '-webkit-box',
                            WebkitLineClamp: 2,
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden',
                          }}
                        >
                          {item.description || '설명 없음'}
                        </Typography>
                      </Stack>
                    </TableCell>
                    <TableCell>
                      <Chip size="small" label={item.schedule_type} />
                    </TableCell>
                    <TableCell>{formatDateRange(item)}</TableCell>
                    <TableCell>{item.assignee_name || '-'}</TableCell>
                    <TableCell>{item.task_title || '-'}</TableCell>
                    <TableCell align="right">
                      <Button size="small" variant="outlined" component={RouterLink} to={`/schedules/${item.id}/edit`}>
                        수정
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Dialog open={Boolean(selectedDay)} onClose={() => setSelectedDay(null)} fullWidth maxWidth="md">
        <DialogTitle>{selectedDay ? `${selectedDay.date} 일정` : '일정 상세'}</DialogTitle>
        <DialogContent dividers>
          <Stack spacing={1.5}>
            {(selectedDay?.modal_items || []).length ? (
              selectedDay.modal_items.map((item) => (
                <Paper key={`${selectedDay.date}-${item.id}`} variant="outlined" sx={{ p: 2 }}>
                  <Stack spacing={1}>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" alignItems="center">
                      <Typography fontWeight={700}>{item.title}</Typography>
                      <Chip size="small" label={item.schedule_type} color="primary" variant="outlined" />
                    </Stack>
                    <Typography variant="body2" color="text.secondary">
                      {formatDateRange(item)}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      담당자: {item.assignee_name || '-'}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      연결 작업: {item.task_title || '-'}
                    </Typography>
                    {item.summary ? <Typography variant="body2">{item.summary}</Typography> : null}
                  </Stack>
                </Paper>
              ))
            ) : (
              <Alert severity="info">해당 날짜에 표시할 일정이 없습니다.</Alert>
            )}
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedDay(null)}>닫기</Button>
        </DialogActions>
      </Dialog>
    </Stack>
  )
}

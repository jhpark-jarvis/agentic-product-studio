import AddRoundedIcon from '@mui/icons-material/AddRounded'
import CalendarMonthRoundedIcon from '@mui/icons-material/CalendarMonthRounded'
import ChevronLeftRoundedIcon from '@mui/icons-material/ChevronLeftRounded'
import ChevronRightRoundedIcon from '@mui/icons-material/ChevronRightRounded'
import {
  Box,
  Button,
  Chip,
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
import { EmptyState, ErrorMessage, LoadingState } from '../components/FeedbackStates'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'

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
        description="이번 주 일정과 월간 캘린더, 전체 일정 목록을 한 화면에서 확인하고 바로 수정할 수 있도록 정리했습니다."
      />

      <SectionCard
        title="이번 주 일정"
        description={`${data?.week_range?.start || '-'} ~ ${data?.week_range?.end || '-'}`}
        actions={
          <Button
            component={RouterLink}
            to="/schedules/new"
            variant="outlined"
            color="secondary"
            startIcon={<AddRoundedIcon />}
          >
            새 일정
          </Button>
        }
        contentSx={{ px: 3, pb: 3 }}
      >
        <ErrorMessage message={error} sx={{ pb: 2.5 }} />

        {loading ? (
          <LoadingState message="일정 정보를 불러오는 중입니다..." />
        ) : (
          <Box
            sx={{
              display: 'grid',
              gridTemplateColumns: { xs: '1fr', xl: 'repeat(3, minmax(0, 1fr))' },
              gap: 2,
            }}
          >
            {data?.week_items?.length ? (
              data.week_items.map((item) => <WeekScheduleCard key={item.id} item={item} />)
            ) : (
              <EmptyState message="이번 주 일정이 없습니다." />
            )}
          </Box>
        )}
      </SectionCard>

      <SectionCard
        title="월간 일정"
        description="날짜를 누르면 해당 일자의 등록 일정 목록을 바로 확인할 수 있습니다."
        actions={
          <Stack direction="row" spacing={1} alignItems="center" sx={{ alignSelf: { xs: 'stretch', md: 'auto' } }}>
            <Button
              variant="outlined"
              onClick={() => loadSchedules(shiftMonth(monthQuery, -1))}
              sx={{ minWidth: { xs: 44, sm: 64 } }}
            >
              <ChevronLeftRoundedIcon fontSize="small" />
            </Button>
            <Chip
              icon={<CalendarMonthRoundedIcon />}
              label={formatMonthLabel(monthQuery)}
              color="primary"
              sx={{ flex: { xs: 1, md: '0 0 auto' } }}
            />
            <Button
              variant="outlined"
              onClick={() => loadSchedules(shiftMonth(monthQuery, 1))}
              sx={{ minWidth: { xs: 44, sm: 64 } }}
            >
              <ChevronRightRoundedIcon fontSize="small" />
            </Button>
          </Stack>
        }
        contentSx={{ px: 3, pb: 3 }}
      >
        {loading ? null : (
          <Box sx={{ overflowX: 'auto' }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(7, minmax(0, 1fr))',
                gap: 1.25,
                minWidth: 720,
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
                    bgcolor: 'action.hover',
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
                  <Box key={day.key} sx={{ minHeight: 132, borderRadius: 3, bgcolor: 'background.default' }} />
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
                      bgcolor: day.is_today ? 'rgba(192, 107, 43, 0.14)' : 'background.paper',
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
                          + 시작 일정 {day.hidden_start_count}건
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
          </Box>
        )}
      </SectionCard>

      <SectionCard
        title="전체 일정 목록"
        description="연결 작업과 함께 일정 전체를 한 번에 확인할 수 있습니다."
        metric={`${data?.schedules?.length || 0}건`}
      >
        {loading ? null : (
          <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
            <Table sx={{ minWidth: { xs: 880, md: 1100 } }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ minWidth: 280 }}>일정명</TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 88 }}>유형</TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 180 }}>기간</TableCell>
                  <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 112 }}>
                    담당자
                  </TableCell>
                  <TableCell sx={{ display: { xs: 'none', md: 'table-cell' }, whiteSpace: 'nowrap', minWidth: 180 }}>
                    연결 작업
                  </TableCell>
                  <TableCell sx={{ whiteSpace: 'nowrap', minWidth: 100 }}>관리</TableCell>
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
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>
                      <Chip size="small" label={item.schedule_type} />
                    </TableCell>
                    <TableCell sx={{ whiteSpace: 'nowrap' }}>{formatDateRange(item)}</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' }, whiteSpace: 'nowrap' }}>
                      {item.assignee_name || '-'}
                    </TableCell>
                    <TableCell
                      sx={{
                        display: { xs: 'none', md: 'table-cell' },
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {item.task_title || '-'}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        variant="outlined"
                        component={RouterLink}
                        to={`/schedules/${item.id}/edit`}
                        sx={{ whiteSpace: 'nowrap', minWidth: 0 }}
                      >
                        수정
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </SectionCard>

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
              <EmptyState message="해당 날짜에 표시할 일정이 없습니다." />
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

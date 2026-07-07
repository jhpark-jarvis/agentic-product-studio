import AddRoundedIcon from '@mui/icons-material/AddRounded'
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
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
import { useEffect, useState } from 'react'
import { apiGet } from '../api/client'
import { PageHeader } from '../components/PageHeader'

export function MembersPage() {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const payload = await apiGet('/api/members')
        setData(payload)
      } catch (fetchError) {
        setError(fetchError.message)
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [])

  return (
    <Stack spacing={3}>
      <PageHeader
        eyebrow="MEMBERS"
        title="멤버 관리"
        description="담당자 정보와 작업/일정 연결 현황을 React 화면으로 먼저 정리했습니다. 생성과 수정은 당분간 기존 폼을 함께 사용합니다."
      />

      <Paper sx={{ p: 0, overflow: 'hidden' }}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={1.5}
          sx={{ px: 3, py: 2.5, alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Box>
            <Typography variant="h6">멤버 목록</Typography>
            <Typography variant="body2" color="text.secondary">
              WBS 담당자와 일정 담당자 선택에 사용하는 멤버 정보입니다.
            </Typography>
          </Box>
          <Button variant="outlined" color="secondary" startIcon={<AddRoundedIcon />} href="/members/new">
            멤버 추가
          </Button>
        </Stack>

        {error ? (
          <Box sx={{ px: 3, pb: 3 }}>
            <Alert severity="error">{error}</Alert>
          </Box>
        ) : null}

        {loading ? (
          <Stack sx={{ py: 8, alignItems: 'center', justifyContent: 'center' }} spacing={2}>
            <CircularProgress size={30} />
            <Typography color="text.secondary">멤버 목록을 불러오는 중입니다...</Typography>
          </Stack>
        ) : (
          <>
            <TableContainer sx={{ borderTop: '1px solid #d9e1ec' }}>
              <Table sx={{ minWidth: 960 }}>
                <TableHead>
                  <TableRow>
                    <TableCell>이름</TableCell>
                    <TableCell>역할</TableCell>
                    <TableCell>담당 파트</TableCell>
                    <TableCell>연락처</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell>작업 수</TableCell>
                    <TableCell>일정 수</TableCell>
                    <TableCell align="right">관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.members || []).map((member) => (
                    <TableRow key={member.id} hover>
                      <TableCell sx={{ fontWeight: 700 }}>{member.name}</TableCell>
                      <TableCell>{member.role || '-'}</TableCell>
                      <TableCell>{member.part || '-'}</TableCell>
                      <TableCell>{member.contact || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={member.is_active ? '활성' : '비활성'}
                          color={member.is_active ? 'success' : 'default'}
                          variant={member.is_active ? 'filled' : 'outlined'}
                        />
                      </TableCell>
                      <TableCell>{member.task_count}</TableCell>
                      <TableCell>{member.schedule_count}</TableCell>
                      <TableCell align="right">
                        <Stack direction="row" spacing={1} justifyContent="flex-end">
                          <Button size="small" variant="outlined" href={`/members/${member.id}/edit`}>
                            수정
                          </Button>
                        </Stack>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>

            {data?.members?.length ? null : (
              <Box sx={{ px: 3, py: 6 }}>
                <Alert severity="info">등록된 멤버가 없습니다.</Alert>
              </Box>
            )}
          </>
        )}
      </Paper>
    </Stack>
  )
}

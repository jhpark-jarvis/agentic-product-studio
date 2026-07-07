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
import { Link as RouterLink } from 'react-router-dom'
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
        description="담당자 정보와 작업/일정 연결 현황을 한 화면에서 확인하고 생성과 수정으로 이어질 수 있도록 정리했습니다."
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
              WBS 담당자와 일정 담당자로 사용하는 멤버 정보입니다.
            </Typography>
          </Box>
          <Button component={RouterLink} to="/members/new" variant="outlined" color="secondary" startIcon={<AddRoundedIcon />}>
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
            <TableContainer sx={{ borderTop: '1px solid', borderColor: 'divider' }}>
              <Table sx={{ minWidth: { xs: 720, md: 960 } }}>
                <TableHead>
                  <TableRow>
                    <TableCell>이름</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>역할</TableCell>
                    <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>담당 파트</TableCell>
                    <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>연락처</TableCell>
                    <TableCell>상태</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>작업 수</TableCell>
                    <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>일정 수</TableCell>
                    <TableCell>관리</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {(data?.members || []).map((member) => (
                    <TableRow key={member.id} hover>
                      <TableCell sx={{ fontWeight: 700 }}>{member.name}</TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{member.role || '-'}</TableCell>
                      <TableCell sx={{ display: { xs: 'none', md: 'table-cell' } }}>{member.part || '-'}</TableCell>
                      <TableCell sx={{ display: { xs: 'none', lg: 'table-cell' } }}>{member.contact || '-'}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={member.is_active ? '활성' : '비활성'}
                          color={member.is_active ? 'success' : 'default'}
                          variant={member.is_active ? 'filled' : 'outlined'}
                        />
                      </TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{member.task_count}</TableCell>
                      <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{member.schedule_count}</TableCell>
                      <TableCell>
                        <Stack direction="row" spacing={1} justifyContent="flex-start" sx={{ flexWrap: 'nowrap' }}>
                          <Button size="small" variant="outlined" component={RouterLink} to={`/members/${member.id}/edit`} sx={{ whiteSpace: 'nowrap', minWidth: 0 }}>
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

import AddRoundedIcon from '@mui/icons-material/AddRounded'
import {
  Button,
  Chip,
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
import { EmptyState, ErrorMessage, LoadingState } from '../components/FeedbackStates'
import { PageHeader } from '../components/PageHeader'
import { SectionCard } from '../components/SectionCard'

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

      <SectionCard
        title="멤버 목록"
        description="WBS 담당자와 일정 담당자로 사용하는 멤버 정보입니다."
        metric={`${data?.members?.length || 0}명`}
        actions={
          <Button
            component={RouterLink}
            to="/members/new"
            variant="outlined"
            color="secondary"
            startIcon={<AddRoundedIcon />}
          >
            멤버 추가
          </Button>
        }
      >
        <ErrorMessage message={error} sx={{ px: 3, pb: 3 }} />

        {loading ? (
          <LoadingState message="멤버 목록을 불러오는 중입니다..." />
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
                          <Button
                            size="small"
                            variant="outlined"
                            component={RouterLink}
                            to={`/members/${member.id}/edit`}
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

            {data?.members?.length ? null : (
              <EmptyState message="등록된 멤버가 없습니다." sx={{ px: 3, py: 6 }} />
            )}
          </>
        )}
      </SectionCard>
    </Stack>
  )
}

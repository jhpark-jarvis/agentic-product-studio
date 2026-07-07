import ConstructionOutlinedIcon from '@mui/icons-material/ConstructionOutlined'
import { Alert, Paper, Stack, Typography } from '@mui/material'
import { PageHeader } from '../components/PageHeader'

export function PlaceholderPage({ title, description }) {
  return (
    <Stack spacing={3}>
      <PageHeader eyebrow="WORK IN PROGRESS" title={title} description={description} />
      <Paper sx={{ p: 3 }}>
        <Alert
          icon={<ConstructionOutlinedIcon fontSize="inherit" />}
          severity="info"
          sx={{ alignItems: 'center' }}
        >
          <Typography variant="body1">
            이 화면은 현재 순차적으로 정리 중입니다.
          </Typography>
        </Alert>
      </Paper>
    </Stack>
  )
}

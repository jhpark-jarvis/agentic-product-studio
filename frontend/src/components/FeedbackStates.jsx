import { Alert, Box, CircularProgress, Stack, Typography } from '@mui/material'

export function ErrorMessage({ message, sx }) {
  if (!message) {
    return null
  }

  return (
    <Box sx={sx}>
      <Alert severity="error">{message}</Alert>
    </Box>
  )
}

export function LoadingState({ message }) {
  return (
    <Stack sx={{ py: 8, alignItems: 'center', justifyContent: 'center' }} spacing={2}>
      <CircularProgress size={30} />
      <Typography color="text.secondary">{message}</Typography>
    </Stack>
  )
}

export function EmptyState({ message, sx }) {
  return (
    <Box sx={sx}>
      <Alert severity="info">{message}</Alert>
    </Box>
  )
}

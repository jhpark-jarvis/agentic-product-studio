import { Paper, Stack, Typography } from '@mui/material'

export function FilterPanel({ title, actions = null, children, onSubmit }) {
  return (
    <Paper component="form" onSubmit={onSubmit} sx={{ p: 3 }}>
      <Stack spacing={2.5}>
        <Stack
          direction={{ xs: 'column', md: 'row' }}
          spacing={2}
          sx={{ alignItems: { md: 'center' }, justifyContent: 'space-between' }}
        >
          <Typography variant="h6">{title}</Typography>
          {actions}
        </Stack>
        {children}
      </Stack>
    </Paper>
  )
}

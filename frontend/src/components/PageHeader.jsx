import { Stack, Typography } from '@mui/material'

export function PageHeader({ eyebrow, title, description }) {
  return (
    <Stack spacing={0.75} sx={{ mb: 3 }}>
      {eyebrow ? (
        <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.18em', fontWeight: 800 }}>
          {eyebrow}
        </Typography>
      ) : null}
      <Typography variant="h3">{title}</Typography>
      {description ? (
        <Typography variant="body1" color="text.secondary" sx={{ maxWidth: 760, lineHeight: 1.8 }}>
          {description}
        </Typography>
      ) : null}
    </Stack>
  )
}

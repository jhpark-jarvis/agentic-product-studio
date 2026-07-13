import { Box, Chip, Paper, Stack, Typography } from '@mui/material'

export function SectionCard({
  title,
  description,
  metric,
  metricColor = 'primary',
  actions = null,
  children,
  contentSx,
  ...paperProps
}) {
  return (
    <Paper sx={{ overflow: 'hidden' }} {...paperProps}>
      <Stack
        direction={{ xs: 'column', md: 'row' }}
        spacing={1.5}
        sx={{ px: 3, py: 2.5, alignItems: { md: 'center' }, justifyContent: 'space-between' }}
      >
        <Box>
          <Typography variant="h6">{title}</Typography>
          {description ? (
            <Typography variant="body2" color="text.secondary">
              {description}
            </Typography>
          ) : null}
        </Box>

        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap" sx={{ alignItems: 'center' }}>
          {metric ? <Chip label={metric} color={metricColor} variant="outlined" /> : null}
          {actions}
        </Stack>
      </Stack>

      <Box sx={contentSx}>{children}</Box>
    </Paper>
  )
}

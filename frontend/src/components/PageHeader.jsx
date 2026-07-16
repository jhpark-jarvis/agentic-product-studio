import { Box, Stack, Typography } from '@mui/material'

export function PageHeader({ eyebrow, title, description }) {
  return (
    <Stack spacing={1} sx={{ mb: 3.5 }}>
      <Stack direction="row" spacing={1.5} alignItems="flex-start">
        <Box
          sx={{
            width: 6,
            minWidth: 6,
            alignSelf: 'stretch',
            background: (theme) =>
              `linear-gradient(180deg, ${theme.palette.primary.main} 0%, ${theme.palette.secondary.main} 100%)`,
          }}
        />
        <Stack spacing={0.75}>
          {eyebrow ? (
            <Typography variant="overline" color="text.secondary" sx={{ letterSpacing: '0.18em', fontWeight: 800 }}>
              {eyebrow}
            </Typography>
          ) : null}
          <Typography
            variant="h3"
            sx={{
              minWidth: 0,
              overflowWrap: 'anywhere',
              wordBreak: 'break-word',
            }}
          >
            {title}
          </Typography>
          {description ? (
            <Typography
              variant="body1"
              color="text.secondary"
              sx={{
                maxWidth: 760,
                lineHeight: 1.8,
                overflowWrap: 'anywhere',
                wordBreak: 'break-word',
              }}
            >
              {description}
            </Typography>
          ) : null}
        </Stack>
      </Stack>
    </Stack>
  )
}

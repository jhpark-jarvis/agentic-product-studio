const SEOUL_TIMEZONE = 'Asia/Seoul'

function parseUtcTimestamp(value) {
  if (!value) {
    return null
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value
  }

  const normalized = String(value).trim()
  if (!normalized) {
    return null
  }

  const withTimezone = /[zZ]|[+\-]\d{2}:\d{2}$/.test(normalized)
    ? normalized
    : `${normalized.replace(' ', 'T')}Z`
  const parsed = new Date(withTimezone)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function formatDateTimeKst(value, options = {}) {
  const parsed = parseUtcTimestamp(value)
  if (!parsed) {
    return value || '-'
  }

  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: SEOUL_TIMEZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
    ...options,
  }).format(parsed)
}

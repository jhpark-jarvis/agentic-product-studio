async function parseApiResponse(response) {
  const raw = await response.text()
  let payload = null

  if (raw) {
    try {
      payload = JSON.parse(raw)
    } catch {
      // Some proxy/runtime errors are returned as plain text instead of JSON.
    }
  }

  if (!response.ok) {
    const detail = payload?.error || payload?.detail?.error || payload?.detail
    const message = typeof detail === 'string' ? detail : raw.trim()
    throw new Error(message || 'API request failed')
  }

  if (payload === null) {
    throw new Error('서버가 올바른 JSON 응답을 반환하지 않았습니다.')
  }
  return payload
}

export async function apiGet(path, searchParams) {
  const url = new URL(path, window.location.origin)
  if (searchParams) {
    Object.entries(searchParams).forEach(([key, value]) => {
      if (value !== '' && value !== null && value !== undefined) {
        url.searchParams.set(key, String(value))
      }
    })
  }

  const response = await fetch(url.toString(), {
    headers: {
      Accept: 'application/json',
    },
  })

  return parseApiResponse(response)
}

export function normalizeRedirectPath(path) {
  if (!path) {
    return '/'
  }
  const normalized = path.startsWith('/app/') ? path.slice(4) : path
  return normalized
    .replace(/^\/dashboard$/, '/')
    .replace(/^\/document(?=\/|$)/, '/documents')
    .replace(/^\/asset(?=\/|$)/, '/assets')
    .replace(/^\/task(?=\/|$)/, '/wbs')
    .replace(/^\/schedule(?=\/|$)/, '/schedules')
    .replace(/^\/member(?=\/|$)/, '/members')
}

export async function apiJson(path, { method = 'POST', body } = {}) {
  const response = await fetch(new URL(path, window.location.origin).toString(), {
    method,
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body ?? {}),
  })

  return parseApiResponse(response)
}

export async function apiForm(path, formData, { method = 'POST' } = {}) {
  const response = await fetch(new URL(path, window.location.origin).toString(), {
    method,
    headers: {
      Accept: 'application/json',
    },
    body: formData,
  })

  return parseApiResponse(response)
}

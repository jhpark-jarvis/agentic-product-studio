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

  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload.error || 'API request failed')
  }
  return payload
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

  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload.error || 'API request failed')
  }
  return payload
}

export async function apiForm(path, formData, { method = 'POST' } = {}) {
  const response = await fetch(new URL(path, window.location.origin).toString(), {
    method,
    headers: {
      Accept: 'application/json',
    },
    body: formData,
  })

  const payload = await response.json()
  if (!response.ok) {
    throw new Error(payload.error || 'API request failed')
  }
  return payload
}

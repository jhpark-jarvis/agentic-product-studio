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

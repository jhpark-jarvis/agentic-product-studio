import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import { apiJson } from '../api/client'

const LAST_EVENT_KEY = 'agentic-product-studio:last-page-view'
const VISITOR_ID_KEY = 'agentic-product-studio:visitor-id'
const SESSION_ID_KEY = 'agentic-product-studio:session-id'
const DUPLICATE_WINDOW_MS = 1500

function normalizeTrackedPath(pathname, search, hash) {
  return `${pathname}${search || ''}${hash || ''}`
}

function generateId(prefix) {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return `${prefix}_${crypto.randomUUID()}`
  }
  return `${prefix}_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`
}

function getOrCreateStorageId(storage, key, prefix) {
  try {
    const existing = storage.getItem(key)
    if (existing) {
      return existing
    }
    const created = generateId(prefix)
    storage.setItem(key, created)
    return created
  } catch {
    return generateId(prefix)
  }
}

export function PageViewTracker() {
  const location = useLocation()

  useEffect(() => {
    const path = normalizeTrackedPath(location.pathname, location.search, location.hash)
    const now = Date.now()

    let previousPath = ''
    let shouldSkip = false

    try {
      const raw = window.sessionStorage.getItem(LAST_EVENT_KEY)
      if (raw) {
        const parsed = JSON.parse(raw)
        previousPath = typeof parsed.path === 'string' ? parsed.path : ''
        const previousTs = Number(parsed.ts || 0)
        if (previousPath === path && now - previousTs < DUPLICATE_WINDOW_MS) {
          shouldSkip = true
        }
      }
    } catch {
      previousPath = ''
    }

    if (shouldSkip) {
      return
    }

    const referrer = previousPath || document.referrer || ''
    const visitorId = getOrCreateStorageId(window.localStorage, VISITOR_ID_KEY, 'visitor')
    const sessionId = getOrCreateStorageId(window.sessionStorage, SESSION_ID_KEY, 'session')

    try {
      window.sessionStorage.setItem(
        LAST_EVENT_KEY,
        JSON.stringify({
          path,
          ts: now,
        }),
      )
    } catch {
      // Ignore session storage issues and continue logging.
    }

    apiJson('/api/telemetry/page-view', {
      body: {
        path,
        referrer,
        visitor_id: visitorId,
        session_id: sessionId,
        identity_type: 'anonymous_browser',
      },
    }).catch(() => {
      // Page view logging should never interrupt the UI flow.
    })
  }, [location.hash, location.pathname, location.search])

  return null
}

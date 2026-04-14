const ENV_API_BASE =
  typeof import.meta !== 'undefined' && import.meta.env ? String(import.meta.env.VITE_API_BASE_URL || '').trim() : ''

function normalizeBase(url) {
  return String(url || '').replace(/\/+$/, '')
}

function inferDevBase() {
  if (typeof window === 'undefined') return ''
  const host = window.location.host || ''
  if (host.includes('101.33.210.169:5052') || host.includes('localhost:5052')) {
    return 'http://101.33.210.169:5051'
  }
  return ''
}

export const API_BASE = normalizeBase(ENV_API_BASE || inferDevBase())

export function buildApiUrl(path) {
  return `${API_BASE}${path}`
}

export function buildWsBase() {
  if (typeof window === 'undefined') return 'ws://101.33.210.169:5051'
  if (API_BASE) {
    return API_BASE.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:')
  }
  return window.location.origin.replace(/^http:/i, 'ws:').replace(/^https:/i, 'wss:')
}

function buildHeaders(headers = {}) {
  const token = localStorage.getItem('xm_token')
  return {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...headers,
  }
}

async function request(path, options = {}) {
  const response = await fetch(buildApiUrl(path), {
    ...options,
    headers: buildHeaders(options.headers),
  })

  const text = await response.text()
  const contentType = response.headers.get('content-type') || ''
  const data = text
    ? contentType.includes('application/json')
      ? JSON.parse(text)
      : { message: text }
    : {}

  if (!response.ok) {
    const message = data?.detail || data?.message || `Request failed: ${response.status}`
    const error = new Error(message)
    error.status = response.status
    error.path = path
    throw error
  }

  return data
}

export const api = {
  get(path, options = {}) {
    return request(path, { ...options, method: 'GET' })
  },
  post(path, body, options = {}) {
    return request(path, { ...options, method: 'POST', body: JSON.stringify(body ?? {}) })
  },
  put(path, body, options = {}) {
    return request(path, { ...options, method: 'PUT', body: JSON.stringify(body ?? {}) })
  },
  patch(path, body, options = {}) {
    return request(path, { ...options, method: 'PATCH', body: JSON.stringify(body ?? {}) })
  },
  del(path, options = {}) {
    return request(path, { ...options, method: 'DELETE' })
  },
}

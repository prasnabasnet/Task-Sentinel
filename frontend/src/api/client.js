const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(message, status, body) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function getToken() {
  return localStorage.getItem('token')
}

export function setToken(token) {
  if (token) localStorage.setItem('token', token)
  else localStorage.removeItem('token')
}

export async function apiRequest(method, path, { body, auth = true } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth) {
    const token = getToken()
    if (token) headers.Authorization = `Token ${token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  let data = null
  const text = await res.text()
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!res.ok) {
    const message =
      (data && (data.error || data.detail || data.message)) ||
      (typeof data === 'object' ? JSON.stringify(data) : `Request failed (${res.status})`)
    throw new ApiError(message, res.status, data)
  }

  return data
}

export const api = {
  get: (path, opts) => apiRequest('GET', path, opts),
  post: (path, body, opts) => apiRequest('POST', path, { ...opts, body }),
  put: (path, body, opts) => apiRequest('PUT', path, { ...opts, body }),
  patch: (path, body, opts) => apiRequest('PATCH', path, { ...opts, body }),
  delete: (path, opts) => apiRequest('DELETE', path, opts),
}

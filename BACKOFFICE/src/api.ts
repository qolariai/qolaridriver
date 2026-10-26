// Cliente da API da consola (/api/*). Token Bearer em localStorage (com fallback em memória).

const TOKEN_KEY = 'qolari_console_token'
let token: string | null = readToken()

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY)
  } catch {
    return null
  }
}

export function setToken(t: string | null) {
  token = t
  try {
    if (t) localStorage.setItem(TOKEN_KEY, t)
    else localStorage.removeItem(TOKEN_KEY)
  } catch {
    /* sem storage: dura até recarregar */
  }
}
export const hasToken = () => !!token
export const authHeaders = (): Record<string, string> => (token ? { Authorization: `Bearer ${token}` } : {})

export class HttpError extends Error {
  constructor(public status: number, message: string) {
    super(message)
  }
}

type Opts = { method?: string; body?: unknown; blob?: Blob; signal?: AbortSignal }

export async function request<T>(path: string, opts: Opts = {}): Promise<T> {
  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`
  let body: BodyInit | undefined
  if (opts.blob) {
    body = opts.blob
    headers['Content-Type'] = opts.blob.type || 'application/octet-stream'
  } else if (opts.body !== undefined) {
    body = JSON.stringify(opts.body)
    headers['Content-Type'] = 'application/json'
  }
  const r = await fetch('/api' + path, { method: opts.method ?? (body ? 'POST' : 'GET'), headers, body, signal: opts.signal })
  if (r.status === 401 && path !== '/auth/login') {
    setToken(null)
    window.dispatchEvent(new Event('qolari:logout'))
  }
  if (!r.ok) {
    let msg = `${r.status} ${r.statusText}`
    try {
      const j = await r.json()
      if (typeof j.detail === 'string') msg = j.detail
      else if (Array.isArray(j.detail)) msg = j.detail.map((d: { loc?: string[]; msg: string }) => `${d.loc?.slice(-1)[0] ?? ''}: ${d.msg}`).join('; ')
    } catch {
      /* sem JSON */
    }
    throw new HttpError(r.status, msg)
  }
  return r.json() as Promise<T>
}

export const api = {
  get: <T,>(p: string, signal?: AbortSignal) => request<T>(p, { signal }),
  post: <T,>(p: string, body: unknown = {}) => request<T>(p, { method: 'POST', body }),
  patch: <T,>(p: string, body: unknown) => request<T>(p, { method: 'PATCH', body }),
  put: <T,>(p: string, blob: Blob) => request<T>(p, { method: 'PUT', blob }),
}

export function qs(params: Record<string, string | number | boolean | null | undefined>): string {
  const u = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== null && v !== '') u.set(k, String(v))
  const s = u.toString()
  return s ? `?${s}` : ''
}

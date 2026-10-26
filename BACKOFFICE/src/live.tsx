import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { api, hasToken, setToken } from './api'
import type { Admin } from './types'

// ---- sessão ----------------------------------------------------------------------------------
type Auth = { user: Admin | null; ready: boolean; login: (email: string, password: string) => Promise<void>; logout: () => void }
const AuthCtx = createContext<Auth>(null as unknown as Auth)
export const useAuth = () => useContext(AuthCtx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<Admin | null>(null)
  const [ready, setReady] = useState(!hasToken())

  useEffect(() => {
    if (!hasToken()) return
    api.get<Admin>('/auth/me').then(setUser).catch(() => setUser(null)).finally(() => setReady(true))
  }, [])
  useEffect(() => {
    const off = () => setUser(null)
    window.addEventListener('qolari:logout', off)
    return () => window.removeEventListener('qolari:logout', off)
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const r = await api.post<{ token: string; user: Admin }>('/auth/login', { email, password })
    setToken(r.token)
    setUser(r.user)
  }, [])
  const logout = useCallback(() => {
    setToken(null)
    setUser(null)
  }, [])
  return <AuthCtx.Provider value={{ user, ready, login, logout }}>{children}</AuthCtx.Provider>
}

export const can = (user: Admin | null, ...roles: string[]) => !!user && (user.role === 'admin' || roles.includes(user.role))

// ---- tempo real: /changes acorda quando a BD muda -------------------------------------------
type Live = { version: number; online: boolean }
const LiveCtx = createContext<Live>({ version: 0, online: false })
export const useLive = () => useContext(LiveCtx)

export function LiveProvider({ children }: { children: ReactNode }) {
  const [live, setLive] = useState<Live>({ version: 0, online: false })
  useEffect(() => {
    let stop = false
    const ctrl = new AbortController()
    ;(async () => {
      let since: number | undefined
      while (!stop) {
        try {
          const r = await api.get<{ version: number }>(`/changes${since === undefined ? '' : `?since=${since}`}`, ctrl.signal)
          setLive((l) => (since !== undefined && r.version !== since ? { version: r.version, online: true } : l.online ? l : { ...l, online: true }))
          since = r.version
          await wait(1200) // mudanças em rajada (motoristas a mexer) -> no máximo ~1 recarga/s
        } catch {
          if (stop) return
          setLive((l) => ({ ...l, online: false }))
          await wait(3000)
        }
      }
    })()
    return () => {
      stop = true
      ctrl.abort()
    }
  }, [])
  return <LiveCtx.Provider value={live}>{children}</LiveCtx.Provider>
}

const wait = (ms: number) => new Promise((r) => setTimeout(r, ms))

/** GET com recarga automática quando a BD muda (live=false desliga). */
export function useData<T>(path: string | null, live = true) {
  const { version } = useLive()
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const seq = useRef(0)

  const load = useCallback(
    async (quiet = false) => {
      if (!path) return
      const n = ++seq.current
      if (!quiet) setLoading(true)
      try {
        const d = await api.get<T>(path)
        if (n === seq.current) {
          setData(d)
          setError(null)
        }
      } catch (e) {
        if (n === seq.current) setError((e as Error).message)
      } finally {
        if (n === seq.current) setLoading(false)
      }
    },
    [path],
  )
  useEffect(() => {
    load()
  }, [load])
  useEffect(() => {
    if (live && version) load(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version])
  return { data, error, loading, reload: () => load(true), setData }
}

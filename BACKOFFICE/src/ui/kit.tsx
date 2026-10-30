import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AVAIL, AVAIL_TONE, DRIVER_STATUS, DRIVER_TONE, TRIP_STATE, TRIP_TONE } from '../format'
import type { Availability, DriverStatus, TripState } from '../types'

// ---- avisos ----------------------------------------------------------------------------------
type Toast = { id: number; text: string; kind: 'ok' | 'error' }
const ToastCtx = createContext<(text: string, kind?: Toast['kind']) => void>(() => {})
export const useToast = () => useContext(ToastCtx)

export function ToastProvider({ children }: { children: ReactNode }) {
  const [list, setList] = useState<Toast[]>([])
  const seq = useRef(0)
  const push = useCallback((text: string, kind: Toast['kind'] = 'ok') => {
    const id = ++seq.current
    setList((l) => [...l, { id, text, kind }])
    setTimeout(() => setList((l) => l.filter((t) => t.id !== id)), kind === 'error' ? 6000 : 2600)
  }, [])
  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="toasts" role="status" aria-live="polite">
        {list.map((t) => <div key={t.id} className={`toast ${t.kind}`}>{t.text}</div>)}
      </div>
    </ToastCtx.Provider>
  )
}

/** Corre uma ação e mostra erro/sucesso. */
export function useRun() {
  const toast = useToast()
  const [busy, setBusy] = useState(false)
  const run = useCallback(
    async <T,>(fn: () => Promise<T>, ok?: string): Promise<T | undefined> => {
      setBusy(true)
      try {
        const r = await fn()
        if (ok) toast(ok)
        return r
      } catch (e) {
        toast((e as Error).message || 'Erro', 'error')
        return undefined
      } finally {
        setBusy(false)
      }
    },
    [toast],
  )
  return { run, busy }
}

// ---- estrutura -------------------------------------------------------------------------------
export function Page({ title, sub, actions, back, children }: {
  title: ReactNode; sub?: ReactNode; actions?: ReactNode; back?: { to: string; label: string }; children: ReactNode
}) {
  return (
    <div className="page">
      <header className="page-head">
        <div className="page-title">
          {back && <Link className="back" to={back.to}><Icon name="back" size={14} /> {back.label}</Link>}
          <h1>{title}</h1>
          {sub && <p className="muted">{sub}</p>}
        </div>
        {actions && <div className="page-actions">{actions}</div>}
      </header>
      {children}
    </div>
  )
}

export function Card({ title, actions, children, className = '', pad = true }: {
  title?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; pad?: boolean
}) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          {title && <h2>{title}</h2>}
          {actions && <div className="card-actions">{actions}</div>}
        </header>
      )}
      <div className={pad ? 'card-body' : ''}>{children}</div>
    </section>
  )
}

export function Stat({ label, value, hint, tone }: { label: string; value: ReactNode; hint?: ReactNode; tone?: string }) {
  return (
    <div className={`stat ${tone ? `stat-${tone}` : ''}`}>
      <span className="stat-label">{label}</span>
      <strong className="stat-value">{value}</strong>
      {hint && <span className="stat-hint">{hint}</span>}
    </div>
  )
}

export function Modal({ title, onClose, children, footer, wide }: {
  title: string; onClose: () => void; children: ReactNode; footer?: ReactNode; wide?: boolean
}) {
  useEffect(() => {
    const k = (e: KeyboardEvent) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', k)
    return () => window.removeEventListener('keydown', k)
  }, [onClose])
  return (
    <div className="backdrop" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal ${wide ? 'wide' : ''}`} role="dialog" aria-modal="true" aria-label={title}>
        <header className="modal-head">
          <h2>{title}</h2>
          <button className="icon-btn" onClick={onClose} aria-label="Fechar"><Icon name="x" /></button>
        </header>
        <div className="modal-body">{children}</div>
        {footer && <footer className="modal-foot">{footer}</footer>}
      </div>
    </div>
  )
}

export function Field({ label, hint, children, wide }: { label: string; hint?: ReactNode; children: ReactNode; wide?: boolean }) {
  return (
    <label className={`field ${wide ? 'span-2' : ''}`}>
      <span className="field-label">{label}</span>
      {children}
      {hint && <span className="field-hint">{hint}</span>}
    </label>
  )
}

export function Tabs<T extends string>({ value, onChange, items }: { value: T; onChange: (v: T) => void; items: [T, ReactNode][] }) {
  return (
    <div className="tabs" role="tablist">
      {items.map(([k, label]) => (
        <button key={k} role="tab" aria-selected={value === k} className={value === k ? 'on' : ''} onClick={() => onChange(k)}>
          {label}
        </button>
      ))}
    </div>
  )
}

export function Switch({ checked, onChange, label, disabled }: { checked: boolean; onChange: (v: boolean) => void; label: string; disabled?: boolean }) {
  return (
    <button type="button" role="switch" aria-checked={checked} aria-label={label} title={label} disabled={disabled}
      className={`switch ${checked ? 'on' : ''}`} onClick={() => onChange(!checked)}>
      <span />
    </button>
  )
}

export const Badge = ({ tone = 'muted', children }: { tone?: string; children: ReactNode }) => <span className={`badge t-${tone}`}>{children}</span>
export const TripBadge = ({ state }: { state: TripState }) => <Badge tone={TRIP_TONE[state]}>{TRIP_STATE[state] ?? state}</Badge>
export const DriverBadge = ({ status }: { status: DriverStatus }) => <Badge tone={DRIVER_TONE[status]}>{DRIVER_STATUS[status]}</Badge>
export const AvailBadge = ({ a }: { a: Availability }) => (
  <span className={`avail t-${AVAIL_TONE[a]}`}><i />{AVAIL[a]}</span>
)

export function Stars({ value }: { value: number | null | undefined }) {
  if (value == null) return <span className="muted">—</span>
  return <span className="stars" title={`${value}`}>★ {value.toFixed(2).replace('.', ',')}</span>
}

export const Empty = ({ children }: { children: ReactNode }) => <div className="empty">{children}</div>
export const Loading = () => <div className="loading" aria-label="A carregar"><span /><span /><span /></div>
export function ErrorBox({ error, retry }: { error: string; retry?: () => void }) {
  return (
    <div className="error-box"><Icon name="alert" /> <span>{error}</span>
      {retry && <button className="btn sm" onClick={retry}>Tentar de novo</button>}
    </div>
  )
}

/** Mostra loading/erro ou o conteúdo. */
export function Gate<T>({ d, children }: { d: { data: T | null; error: string | null; loading: boolean; reload: () => void }; children: (v: T) => ReactNode }) {
  if (d.error && !d.data) return <ErrorBox error={d.error} retry={d.reload} />
  if (!d.data) return <Loading />
  return <>{children(d.data)}</>
}

// ---- ícones (traço 24x24) --------------------------------------------------------------------
const P: Record<string, string> = {
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  route: 'M6 19a2 2 0 100-4 2 2 0 000 4zM18 9a2 2 0 100-4 2 2 0 000 4zM6 15V9a4 4 0 014-4h2M18 9v6a4 4 0 01-4 4h-2',
  steering: 'M12 22a10 10 0 100-20 10 10 0 000 20zM12 15a3 3 0 100-6 3 3 0 000 6zM3 11l6 1M21 11l-6 1M12 15v7',
  user: 'M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z',
  users: 'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8',
  building: 'M4 21V5a2 2 0 012-2h8a2 2 0 012 2v16M16 9h2a2 2 0 012 2v10M8 7h4M8 11h4M8 15h4M2 21h20',
  car: 'M5 17h14M5 17a2 2 0 11-4 0v-5l2-5a2 2 0 012-1h12a2 2 0 012 1l2 5v5a2 2 0 11-4 0M3 12h18M7 17v2M17 17v2',
  file: 'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8zM14 2v6h6M9 13l2 2 4-4',
  tag: 'M20.6 13.4l-7.2 7.2a2 2 0 01-2.8 0L2 12V2h10l8.6 8.6a2 2 0 010 2.8zM7 7h.01',
  euro: 'M18 7a7 7 0 100 10M4 10h10M4 14h10',
  sliders: 'M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6',
  plug: 'M9 2v6M15 2v6M6 8h12v4a6 6 0 01-12 0zM12 18v4',
  play: 'M5 3l14 9-14 9z',
  settings: 'M12 15a3 3 0 100-6 3 3 0 000 6zM19.4 15a1.7 1.7 0 00.3 1.8l.1.1a2 2 0 11-2.8 2.8l-.1-.1a1.7 1.7 0 00-1.8-.3 1.7 1.7 0 00-1 1.5V21a2 2 0 11-4 0v-.1a1.7 1.7 0 00-1.1-1.5 1.7 1.7 0 00-1.8.3l-.1.1a2 2 0 11-2.8-2.8l.1-.1a1.7 1.7 0 00.3-1.8 1.7 1.7 0 00-1.5-1H3a2 2 0 110-4h.1a1.7 1.7 0 001.5-1.1 1.7 1.7 0 00-.3-1.8l-.1-.1a2 2 0 112.8-2.8l.1.1a1.7 1.7 0 001.8.3H9a1.7 1.7 0 001-1.5V3a2 2 0 114 0v.1a1.7 1.7 0 001 1.5 1.7 1.7 0 001.8-.3l.1-.1a2 2 0 112.8 2.8l-.1.1a1.7 1.7 0 00-.3 1.8V9a1.7 1.7 0 001.5 1H21a2 2 0 110 4h-.1a1.7 1.7 0 00-1.5 1z',
  logout: 'M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9',
  plus: 'M12 5v14M5 12h14',
  x: 'M18 6L6 18M6 6l12 12',
  back: 'M19 12H5M12 19l-7-7 7-7',
  menu: 'M3 6h18M3 12h18M3 18h18',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  alert: 'M12 9v4M12 17h.01M10.3 3.9L1.8 18a2 2 0 001.7 3h17a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z',
  check: 'M20 6L9 17l-5-5',
  pin: 'M21 10c0 7-9 13-9 13S3 17 3 10a9 9 0 0118 0zM12 13a3 3 0 100-6 3 3 0 000 6z',
  refresh: 'M23 4v6h-6M1 20v-6h6M3.5 9a9 9 0 0114.9-3.4L23 10M1 14l4.6 4.4A9 9 0 0020.5 15',
  power: 'M18.4 6.6a9 9 0 11-12.8 0M12 2v10',
  edit: 'M12 20h9M16.5 3.5a2.1 2.1 0 013 3L7 19l-4 1 1-4z',
  upload: 'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12',
  eye: 'M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12zM12 15a3 3 0 100-6 3 3 0 000 6z',
  phone: 'M5 2h14v20H5zM11 18h2',
  map: 'M1 6v16l7-4 8 4 7-4V2l-7 4-8-4zM8 2v16M16 6v16',
  shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
}

export function Icon({ name, size = 18 }: { name: string; size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8}
      strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="icon">
      <path d={P[name] ?? ''} />
    </svg>
  )
}

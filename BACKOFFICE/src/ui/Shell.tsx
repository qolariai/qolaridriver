import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth, useData, useLive } from '../live'
import { Icon } from './kit'

type Nav = { to: string; label: string; icon: string; end?: boolean; badge?: 'docs' | 'searching' }

const GROUPS: { title: string; items: Nav[] }[] = [
  { title: 'Operação', items: [
    { to: '/', label: 'Painel', icon: 'grid', end: true },
    { to: '/viagens', label: 'Viagens', icon: 'route', badge: 'searching' },
    { to: '/simulador', label: 'Simulador', icon: 'play' },
  ] },
  { title: 'Rede', items: [
    { to: '/motoristas', label: 'Motoristas', icon: 'steering' },
    { to: '/passageiros', label: 'Passageiros', icon: 'users' },
    { to: '/frotas', label: 'Frotas', icon: 'building' },
    { to: '/veiculos', label: 'Veículos', icon: 'car' },
    { to: '/documentos', label: 'Documentos', icon: 'file', badge: 'docs' },
  ] },
  { title: 'Negócio', items: [
    { to: '/tarifas', label: 'Categorias e tarifas', icon: 'sliders' },
    { to: '/promocoes', label: 'Promoções', icon: 'tag' },
    { to: '/financas', label: 'Finanças', icon: 'euro' },
  ] },
  { title: 'Sistema', items: [
    { to: '/integracao', label: 'Integração das apps', icon: 'plug' },
    { to: '/definicoes', label: 'Definições', icon: 'settings' },
  ] },
]

type Counts = { kpis: { docs_pending: number; searching_trips: number } }

export function Shell() {
  const { user, logout } = useAuth()
  const { online } = useLive()
  const [open, setOpen] = useState(false)
  const loc = useLocation()
  const counts = useData<Counts>('/dashboard')
  useEffect(() => setOpen(false), [loc.pathname])
  const badge = (b?: Nav['badge']) => {
    const k = counts.data?.kpis
    const n = b === 'docs' ? k?.docs_pending : b === 'searching' ? k?.searching_trips : 0
    return n ? <span className="nav-count">{n}</span> : null
  }

  return (
    <div className={`shell ${open ? 'nav-open' : ''}`}>
      <aside className="side">
        <div className="brand">
          <span className="logo">Q</span>
          <span>Qolari Mobility<small>consola de operação</small></span>
        </div>
        <nav>
          {GROUPS.map((g) => (
            <div key={g.title} className="nav-group">
              <span className="nav-title">{g.title}</span>
              {g.items.map((n) => (
                <NavLink key={n.to} to={n.to} end={n.end} className="nav-link">
                  <Icon name={n.icon} /> <span>{n.label}</span> {badge(n.badge)}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        <div className="side-foot">
          <NavLink to="/conta" className="nav-link"><Icon name="user" /><span className="ellipsis">{user?.name || user?.email}</span></NavLink>
          <button className="nav-link" onClick={logout}><Icon name="logout" /> Sair</button>
          <div className={`live ${online ? 'on' : ''}`}><i /> {online ? 'Tempo real' : 'Sem ligação ao backend'}</div>
        </div>
      </aside>
      <div className="scrim" onClick={() => setOpen(false)} />
      <div className="main">
        <header className="topbar">
          <button className="icon-btn" onClick={() => setOpen(true)} aria-label="Abrir menu"><Icon name="menu" /></button>
          <span className="logo sm">Q</span><strong>Qolari Mobility</strong>
        </header>
        <main className="content"><Outlet /></main>
      </div>
    </div>
  )
}

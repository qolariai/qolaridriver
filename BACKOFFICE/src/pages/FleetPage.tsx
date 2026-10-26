import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { api } from '../api'
import { ago, dateTime, eur, LEDGER_KIND } from '../format'
import { can, useAuth, useData } from '../live'
import type { Driver, Fleet, FleetUser, Payout, Vehicle } from '../types'
import { AvailBadge, Badge, Card, DriverBadge, Field, Gate, Modal, Page, Stars, Stat, useRun } from '../ui/kit'
import { FleetForm } from './Fleets'
import { VehicleForm } from './Vehicles'

type Detail = Fleet & {
  balance: number; week: { by_kind: Record<string, number>; total: number }; week_trips: number
  drivers: Driver[]; vehicles: Vehicle[]; users: FleetUser[]; payouts: Payout[]
}

export function FleetPage() {
  const { id } = useParams()
  const d = useData<Detail>(`/fleets/${id}`)
  const { user } = useAuth()
  const ops = can(user, 'operator')
  const { run, busy } = useRun()
  const nav = useNavigate()
  const [modal, setModal] = useState<'edit' | 'user' | 'vehicle' | null>(null)

  return (
    <Gate d={d}>
      {(f) => (
        <Page back={{ to: '/frotas', label: 'Frotas' }}
          title={<>{f.name} {f.status === 'suspended' && <Badge tone="bad">Suspensa</Badge>}</>}
          sub={`NIF ${f.tax_id || '—'} · ${f.email || 'sem email'} · ${f.phone || 'sem telefone'} · taxa ${f.fleet_fee_pct}%`}
          actions={ops && (
            <>
              <button className="btn" onClick={() => setModal('edit')}>Editar</button>
              <button className={`btn ${f.status === 'active' ? 'danger' : ''}`} disabled={busy}
                onClick={() => run(() => api.patch(`/fleets/${f.id}`, { status: f.status === 'active' ? 'suspended' : 'active' }), 'Guardado').then(d.reload)}>
                {f.status === 'active' ? 'Suspender' : 'Reativar'}
              </button>
            </>
          )}>
          <div className="stats">
            <Stat label="Motoristas" value={f.drivers.length} hint={`${f.online_count} online agora`} />
            <Stat label="Veículos" value={f.vehicles.length} hint={`${f.vehicles.filter((v) => v.status === 'active').length} ativos`} />
            <Stat label="Viagens (7 dias)" value={f.week_trips} />
            <Stat label="Taxas de frota (7 dias)" value={eur(f.week.by_kind.fleet_fee ?? 0)} tone="ok" />
            <Stat label="Saldo a pagar" value={eur(f.balance)} hint={<Link to="/financas">pagamentos</Link>} />
          </div>

          <Card title="Motoristas" pad={false}>
            <div className="table-wrap">
              <table className="table hover">
                <thead><tr><th>Motorista</th><th>Conta</th><th>Agora</th><th>Veículo</th><th className="num">Avaliação</th><th className="num">Saldo</th></tr></thead>
                <tbody>{f.drivers.map((x) => (
                  <tr key={x.id} onClick={() => nav(`/motoristas/${x.id}`)}>
                    <td><strong>{x.name}</strong><small className="muted block">{x.phone}</small></td>
                    <td><DriverBadge status={x.status} /></td><td><AvailBadge a={x.availability} /></td>
                    <td>{x.vehicle?.plate ?? '—'}</td><td className="num"><Stars value={x.rating} /></td>
                    <td className={`num ${(x.balance ?? 0) < 0 ? 'neg' : ''}`}>{eur(x.balance)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
            {!f.drivers.length && <div className="empty">Sem motoristas. A frota convida pela app Fleet, ou associa um motorista na página dele.</div>}
          </Card>

          <div className="grid-2">
            <Card title="Veículos" actions={ops && <button className="btn sm" onClick={() => setModal('vehicle')}>Adicionar</button>} pad={false}>
              <table className="table compact">
                <thead><tr><th>Veículo</th><th>Estado</th><th>Motorista</th></tr></thead>
                <tbody>{f.vehicles.map((v) => (
                  <tr key={v.id}><td><span className="swatch sm" style={{ background: v.color_hex }} /> {v.make} {v.model} <span className="mono muted">{v.plate}</span></td>
                    <td><Badge tone={v.status === 'active' ? 'ok' : v.status === 'pending' ? 'warn' : 'muted'}>{v.status}</Badge></td>
                    <td>{v.drivers.map((x) => x.name).join(', ') || '—'}</td></tr>
                ))}</tbody>
              </table>
            </Card>
            <Card title="Acessos à app Fleet" actions={ops && <button className="btn sm" onClick={() => setModal('user')}>Adicionar</button>} pad={false}>
              <table className="table compact">
                <thead><tr><th>Utilizador</th><th>Papel</th><th>Visto</th><th></th></tr></thead>
                <tbody>{f.users.map((u) => (
                  <tr key={u.id}><td>{u.first_name} {u.last_name}<small className="muted block">{u.phone}</small></td><td>{u.role === 'owner' ? 'Dono' : 'Gestor'}</td>
                    <td className="muted">{ago(u.last_seen_at)}</td>
                    <td>{ops && <button className="btn sm" onClick={() => run(() => api.patch(`/fleet-users/${u.id}`, { active: !u.active }), 'Guardado').then(d.reload)}>{u.active ? 'Desativar' : 'Ativar'}</button>}</td></tr>
                ))}</tbody>
              </table>
            </Card>
          </div>

          <div className="grid-2">
            <Card title="Últimos 7 dias por tipo">
              <ul className="plain">{Object.entries(f.week.by_kind).map(([k, v]) => <li key={k}>{LEDGER_KIND[k] ?? k}: <strong>{eur(v)}</strong></li>)}</ul>
              {!Object.keys(f.week.by_kind).length && <p className="muted">Sem movimentos.</p>}
            </Card>
            <Card title="Pagamentos à frota">
              {f.payouts.length ? <ul className="plain">{f.payouts.map((p) => <li key={p.id}>{dateTime(p.created_at)} · <strong>{eur(p.amount)}</strong> <Badge tone={p.status === 'paid' ? 'ok' : p.status === 'pending' ? 'warn' : 'muted'}>{p.status}</Badge> {p.reference}</li>)}</ul> : <p className="muted">Nenhum.</p>}
            </Card>
          </div>

          {modal === 'edit' && <FleetForm fleet={f} onClose={() => setModal(null)} onSaved={() => { setModal(null); d.reload() }} />}
          {modal === 'user' && <FleetUserForm orgId={f.id} onClose={() => setModal(null)} onSaved={() => { setModal(null); d.reload() }} />}
          {modal === 'vehicle' && <VehicleForm orgId={f.id} onClose={() => setModal(null)} onSaved={() => { setModal(null); d.reload() }} />}
        </Page>
      )}
    </Gate>
  )
}

function FleetUserForm({ orgId, onClose, onSaved }: { orgId: number; onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState({ first_name: '', last_name: '', phone: '+351', email: '', role: 'manager' })
  const { run, busy } = useRun()
  return (
    <Modal title="Novo acesso à app Fleet" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.first_name} onClick={() => run(() => api.post(`/fleets/${orgId}/users`, f), 'Criado').then((r) => r && onSaved())}>Criar</button></>}>
      <div className="form-grid">
        <Field label="Nome"><input value={f.first_name} onChange={(e) => setF({ ...f, first_name: e.target.value })} autoFocus /></Field>
        <Field label="Apelido"><input value={f.last_name} onChange={(e) => setF({ ...f, last_name: e.target.value })} /></Field>
        <Field label="Telemóvel" hint="Login na app Fleet (código 0000)"><input value={f.phone} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
        <Field label="Papel"><select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="owner">Dono</option><option value="manager">Gestor</option></select></Field>
        <Field label="Email" wide><input value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
      </div>
    </Modal>
  )
}

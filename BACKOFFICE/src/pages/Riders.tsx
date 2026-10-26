import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api, qs } from '../api'
import { ago, dateTime, eur } from '../format'
import { can, useAuth, useData } from '../live'
import type { Rider, Session, TripRow } from '../types'
import { Badge, Card, Empty, Field, Gate, Icon, Modal, Page, Stars, Stat, useRun } from '../ui/kit'
import { SessionTable } from './Settings'
import { TripTable } from './Trips'

export function Riders() {
  const [q, setQ] = useState('')
  const [status, setStatus] = useState('')
  const [creating, setCreating] = useState(false)
  const d = useData<Rider[]>(`/riders${qs({ q, status })}`)
  const { user } = useAuth()
  const nav = useNavigate()
  return (
    <Page title="Passageiros" sub="Contas da app Rider (criadas no 1.º login com o telemóvel)"
      actions={can(user, 'operator') && <button className="btn primary" onClick={() => setCreating(true)}><Icon name="plus" /> Novo passageiro</button>}>
      <div className="toolbar">
        <div className="toolbar-right grow">
          <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Estado"><option value="">Todos</option><option value="active">Ativos</option><option value="blocked">Bloqueados</option></select>
          <div className="search"><Icon name="search" /><input placeholder="Nome, telefone ou email" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        </div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(rows) => rows.length ? (
            <div className="table-wrap">
              <table className="table hover">
                <thead><tr><th>Passageiro</th><th>Telefone</th><th>Estado</th><th className="num">Viagens</th><th className="num">Avaliação</th><th>Pagamento</th><th>Visto</th></tr></thead>
                <tbody>{rows.map((r) => (
                  <tr key={r.id} onClick={() => nav(`/passageiros/${r.id}`)}>
                    <td><strong>{r.name}</strong><small className="muted block">{r.email}</small></td>
                    <td className="nowrap">{r.phone}</td>
                    <td>{r.status === 'blocked' ? <Badge tone="bad">Bloqueado</Badge> : <Badge tone="ok">Ativo</Badge>}</td>
                    <td className="num">{r.trips ?? 0}</td>
                    <td className="num"><Stars value={r.rating} /></td>
                    <td>{r.default_payment === 'cash' ? 'Dinheiro' : 'Cartão'}</td>
                    <td className="muted nowrap">{ago(r.last_seen_at)}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          ) : <Empty>Sem passageiros.</Empty>}
        </Gate>
      </Card>
      {creating && <RiderForm onClose={() => setCreating(false)} onSaved={(r) => nav(`/passageiros/${r.id}`)} />}
    </Page>
  )
}

type Detail = Rider & { recent_trips: TripRow[]; spent: number; promos: { code: string; used_trip_id: number | null; created_at: number }[]; sessions: Session[] }

export function RiderPage() {
  const { id } = useParams()
  const d = useData<Detail>(`/riders/${id}`)
  const { user } = useAuth()
  const { run, busy } = useRun()
  const [edit, setEdit] = useState(false)
  return (
    <Gate d={d}>
      {(r) => (
        <Page back={{ to: '/passageiros', label: 'Passageiros' }}
          title={<>{r.name} {r.status === 'blocked' && <Badge tone="bad">Bloqueado</Badge>}</>}
          sub={`${r.phone} · ${r.email || 'sem email'} · cliente desde ${dateTime(r.created_at)}`}
          actions={can(user, 'operator') && (
            <>
              <button className="btn" onClick={() => setEdit(true)}>Editar</button>
              <button className={`btn ${r.status === 'active' ? 'danger' : ''}`} disabled={busy}
                onClick={() => run(() => api.patch(`/riders/${r.id}`, { status: r.status === 'active' ? 'blocked' : 'active' }), 'Guardado').then(d.reload)}>
                {r.status === 'active' ? 'Bloquear' : 'Desbloquear'}
              </button>
            </>
          )}>
          <div className="stats">
            <Stat label="Viagens" value={r.recent_trips.filter((t) => t.state === 'completed').length} hint="das últimas 20" />
            <Stat label="Total gasto" value={eur(r.spent)} />
            <Stat label="Avaliação (motoristas)" value={<Stars value={r.rating} />} hint={`${r.rating_count} avaliações`} />
            <Stat label="Pagamento por omissão" value={r.default_payment === 'cash' ? 'Dinheiro' : 'Cartão'} />
          </div>
          <Card title="Viagens" pad={false}><TripTable rows={r.recent_trips} hide={['rider']} /></Card>
          <div className="grid-2">
            <Card title="Códigos promocionais">
              {r.promos.length ? <ul className="plain">{r.promos.map((p, i) => <li key={i}><span className="mono">{p.code}</span> · {p.used_trip_id ? 'usado' : <Badge tone="ok">por usar</Badge>} <span className="muted">{dateTime(p.created_at)}</span></li>)}</ul> : <p className="muted">Nenhum.</p>}
            </Card>
            <Card title="Sessões na app Rider" pad={false}><SessionTable rows={r.sessions} onChange={d.reload} /></Card>
          </div>
          {edit && <RiderForm rider={r} onClose={() => setEdit(false)} onSaved={() => { setEdit(false); d.reload() }} />}
        </Page>
      )}
    </Gate>
  )
}

function RiderForm({ rider, onClose, onSaved }: { rider?: Rider; onClose: () => void; onSaved: (r: Rider) => void }) {
  const [f, setF] = useState({ first_name: rider?.first_name ?? '', last_name: rider?.last_name ?? '', phone: rider?.phone ?? '+351', email: rider?.email ?? '' })
  const { run, busy } = useRun()
  const save = async () => {
    const body = rider ? { first_name: f.first_name, last_name: f.last_name, email: f.email } : f
    const r = await run(() => (rider ? api.patch<Rider>(`/riders/${rider.id}`, body) : api.post<Rider>('/riders', body)), 'Guardado')
    if (r) onSaved(r)
  }
  return (
    <Modal title={rider ? 'Editar passageiro' : 'Novo passageiro'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy} onClick={save}>Guardar</button></>}>
      <div className="form-grid">
        <Field label="Nome"><input value={f.first_name} onChange={(e) => setF({ ...f, first_name: e.target.value })} autoFocus /></Field>
        <Field label="Apelido"><input value={f.last_name} onChange={(e) => setF({ ...f, last_name: e.target.value })} /></Field>
        <Field label="Telemóvel" hint={rider ? 'O telemóvel é o login: não se muda aqui' : 'Login na app Rider'}><input value={f.phone} disabled={!!rider} onChange={(e) => setF({ ...f, phone: e.target.value })} /></Field>
        <Field label="Email"><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} /></Field>
      </div>
    </Modal>
  )
}

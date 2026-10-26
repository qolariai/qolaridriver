import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, qs } from '../api'
import { ago, AVAIL, DRIVER_STATUS, eur, pct } from '../format'
import { can, useAuth, useData } from '../live'
import type { Driver, Fleet } from '../types'
import { AvailBadge, Card, DriverBadge, Empty, Field, Gate, Icon, Modal, Page, Stars, useRun } from '../ui/kit'

export function Drivers() {
  const [status, setStatus] = useState('')
  const [availability, setAvailability] = useState('')
  const [org, setOrg] = useState('')
  const [q, setQ] = useState('')
  const [creating, setCreating] = useState(false)
  const d = useData<Driver[]>(`/drivers${qs({ status, availability, org_id: org, q })}`)
  const fleets = useData<Fleet[]>('/fleets', false)
  const { user } = useAuth()
  const nav = useNavigate()

  return (
    <Page title="Motoristas" sub="Quem conduz na app Driver: aprovação, frota, veículo e estado em tempo real"
      actions={can(user, 'operator') && <button className="btn primary" onClick={() => setCreating(true)}><Icon name="plus" /> Novo motorista</button>}>
      <div className="toolbar">
        <div className="toolbar-right grow">
          <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Estado">
            <option value="">Todos os estados</option>
            {Object.entries(DRIVER_STATUS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={availability} onChange={(e) => setAvailability(e.target.value)} aria-label="Disponibilidade">
            <option value="">Qualquer disponibilidade</option>
            {Object.entries(AVAIL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
          </select>
          <select value={org} onChange={(e) => setOrg(e.target.value)} aria-label="Frota">
            <option value="">Todas as frotas</option>
            <option value="0">Independentes</option>
            {fleets.data?.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          <div className="search"><Icon name="search" /><input placeholder="Nome ou telefone" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        </div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(rows) => rows.length ? (
            <div className="table-wrap">
              <table className="table hover">
                <thead><tr><th>Motorista</th><th>Conta</th><th>Agora</th><th>Frota</th><th>Veículo</th><th className="num">Avaliação</th><th className="num">Aceitação</th><th className="num">Saldo</th><th>Visto</th></tr></thead>
                <tbody>
                  {rows.map((r) => (
                    <tr key={r.id} onClick={() => nav(`/motoristas/${r.id}`)}>
                      <td><strong>{r.name}</strong><small className="muted block">{r.phone}</small></td>
                      <td><DriverBadge status={r.status} /></td>
                      <td><AvailBadge a={r.availability} /></td>
                      <td>{r.org?.name ?? <span className="muted">Independente</span>}</td>
                      <td className="nowrap">{r.vehicle ? r.vehicle.plate : <span className="muted">—</span>}</td>
                      <td className="num"><Stars value={r.rating} /></td>
                      <td className="num">{pct(r.acceptance_rate)}</td>
                      <td className={`num ${(r.balance ?? 0) < 0 ? 'neg' : ''}`}>{eur(r.balance)}</td>
                      <td className="nowrap muted">{ago(r.last_seen_at ?? r.location_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty>Nenhum motorista com estes filtros.</Empty>}
        </Gate>
      </Card>
      {creating && <DriverForm onClose={() => setCreating(false)} onSaved={(x) => nav(`/motoristas/${x.id}`)} />}
    </Page>
  )
}

export function DriverForm({ driver, onClose, onSaved }: { driver?: Driver; onClose: () => void; onSaved: (d: Driver) => void }) {
  const fleets = useData<Fleet[]>('/fleets', false)
  const [f, setF] = useState({
    first_name: driver?.first_name ?? '', last_name: driver?.last_name ?? '', phone: driver?.phone ?? '+351',
    email: driver?.email ?? '', license_number: driver?.license_number ?? '', org_id: driver?.org?.id ?? 0,
  })
  const { run, busy } = useRun()
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: k === 'org_id' ? Number(e.target.value) : e.target.value })

  async function save() {
    const body = { ...f, org_id: f.org_id || undefined, clear_org: !f.org_id }
    const r = await run(() => (driver ? api.patch<Driver>(`/drivers/${driver.id}`, body) : api.post<Driver>('/drivers', body)), 'Guardado')
    if (r) onSaved(r)
  }
  return (
    <Modal title={driver ? 'Editar motorista' : 'Novo motorista'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.first_name || f.phone.length < 9} onClick={save}>Guardar</button></>}>
      <div className="form-grid">
        <Field label="Nome"><input value={f.first_name} onChange={set('first_name')} autoFocus /></Field>
        <Field label="Apelido"><input value={f.last_name} onChange={set('last_name')} /></Field>
        <Field label="Telemóvel" hint="É o login na app Driver"><input value={f.phone} onChange={set('phone')} inputMode="tel" /></Field>
        <Field label="Email"><input value={f.email} onChange={set('email')} type="email" /></Field>
        <Field label="N.º carta de condução"><input value={f.license_number} onChange={set('license_number')} /></Field>
        <Field label="Frota">
          <select value={f.org_id} onChange={set('org_id')}>
            <option value={0}>Independente</option>
            {fleets.data?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}
          </select>
        </Field>
      </div>
      {!driver && <p className="muted">Fica “Em verificação” até aprovares a conta e os documentos.</p>}
    </Modal>
  )
}

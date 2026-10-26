import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'
import { eur } from '../format'
import { can, useAuth, useData } from '../live'
import type { Fleet } from '../types'
import { Badge, Card, Empty, Field, Gate, Icon, Modal, Page, useRun } from '../ui/kit'

export function Fleets() {
  const d = useData<Fleet[]>('/fleets')
  const { user } = useAuth()
  const nav = useNavigate()
  const [creating, setCreating] = useState(false)
  return (
    <Page title="Frotas" sub="Parceiros que gerem motoristas e veículos na app Fleet e ficam com uma % do ganho dos seus motoristas"
      actions={can(user, 'operator') && <button className="btn primary" onClick={() => setCreating(true)}><Icon name="plus" /> Nova frota</button>}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <div className="cards">
            {rows.map((f) => (
              <button key={f.id} className="card fleet-card" onClick={() => nav(`/frotas/${f.id}`)}>
                <div className="fleet-top">
                  <span className="avatar">{f.name.slice(0, 2).toUpperCase()}</span>
                  <div><strong>{f.name}</strong><small className="muted block">NIF {f.tax_id || '—'} · taxa {f.fleet_fee_pct}%</small></div>
                  {f.status === 'suspended' && <Badge tone="bad">Suspensa</Badge>}
                </div>
                <div className="fleet-stats">
                  <span><strong>{f.drivers_count}</strong> motoristas</span>
                  <span><strong>{f.online_count}</strong> online</span>
                  <span><strong>{f.vehicles_count}</strong> veículos</span>
                  <span><strong>{eur(f.balance ?? 0)}</strong> saldo</span>
                </div>
              </button>
            ))}
          </div>
        ) : <Card><Empty>Sem frotas.</Empty></Card>}
      </Gate>
      {creating && <FleetForm onClose={() => setCreating(false)} onSaved={(f) => nav(`/frotas/${f.id}`)} />}
    </Page>
  )
}

export function FleetForm({ fleet, onClose, onSaved }: { fleet?: Fleet; onClose: () => void; onSaved: (f: Fleet) => void }) {
  const [f, setF] = useState({ name: fleet?.name ?? '', tax_id: fleet?.tax_id ?? '', email: fleet?.email ?? '', phone: fleet?.phone ?? '', iban: fleet?.iban ?? '', fleet_fee_pct: String(fleet?.fleet_fee_pct ?? 10) })
  const { run, busy } = useRun()
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF({ ...f, [k]: e.target.value })
  async function save() {
    const body = { ...f, fleet_fee_pct: Number(f.fleet_fee_pct.replace(',', '.')) }
    const r = await run(() => (fleet ? api.patch<Fleet>(`/fleets/${fleet.id}`, body) : api.post<Fleet>('/fleets', body)), 'Guardado')
    if (r) onSaved(r)
  }
  return (
    <Modal title={fleet ? 'Editar frota' : 'Nova frota'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.name} onClick={save}>Guardar</button></>}>
      <div className="form-grid">
        <Field label="Nome" wide><input value={f.name} onChange={set('name')} autoFocus /></Field>
        <Field label="NIF"><input value={f.tax_id} onChange={set('tax_id')} /></Field>
        <Field label="Taxa da frota (%)" hint="Sobre o ganho do motorista depois da comissão"><input value={f.fleet_fee_pct} onChange={set('fleet_fee_pct')} inputMode="decimal" /></Field>
        <Field label="Email"><input value={f.email} onChange={set('email')} type="email" /></Field>
        <Field label="Telefone"><input value={f.phone} onChange={set('phone')} /></Field>
        <Field label="IBAN" wide><input value={f.iban} onChange={set('iban')} /></Field>
      </div>
      {!fleet && <p className="muted">Depois cria o utilizador da app Fleet (dono/gestor) na página da frota.</p>}
    </Modal>
  )
}

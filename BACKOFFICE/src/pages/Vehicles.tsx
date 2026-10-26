import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, qs } from '../api'
import { can, useAuth, useData } from '../live'
import type { Fleet, Product, Vehicle } from '../types'
import { Badge, Card, Empty, Field, Gate, Icon, Modal, Page, useRun } from '../ui/kit'

const TONE = { active: 'ok', pending: 'warn', inactive: 'muted' } as const
const LABEL = { active: 'Ativo', pending: 'Por aprovar', inactive: 'Inativo' } as const

export function Vehicles() {
  const [org, setOrg] = useState('')
  const [status, setStatus] = useState('')
  const [q, setQ] = useState('')
  const [edit, setEdit] = useState<Vehicle | 'new' | null>(null)
  const d = useData<Vehicle[]>(`/vehicles${qs({ org_id: org, status, q })}`)
  const fleets = useData<Fleet[]>('/fleets', false)
  const catalog = useData<{ products: Product[] }>('/catalog', false)
  const { user } = useAuth()
  const ops = can(user, 'operator')
  const pname = (id: number) => catalog.data?.products.find((p) => p.id === id)?.name ?? `#${id}`

  return (
    <Page title="Veículos" sub="Só veículos ativos podem ir online; as categorias definem que viagens podem receber"
      actions={ops && <button className="btn primary" onClick={() => setEdit('new')}><Icon name="plus" /> Novo veículo</button>}>
      <div className="toolbar">
        <div className="toolbar-right grow">
          <select value={org} onChange={(e) => setOrg(e.target.value)} aria-label="Frota"><option value="">Todas as frotas</option><option value="0">Sem frota</option>{fleets.data?.map((f) => <option key={f.id} value={f.id}>{f.name}</option>)}</select>
          <select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Estado"><option value="">Todos</option>{Object.entries(LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
          <div className="search"><Icon name="search" /><input placeholder="Matrícula, marca…" value={q} onChange={(e) => setQ(e.target.value)} /></div>
        </div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(rows) => rows.length ? (
            <div className="table-wrap">
              <table className="table hover">
                <thead><tr><th>Veículo</th><th>Matrícula</th><th>Ano</th><th>Lugares</th><th>Frota</th><th>Categorias</th><th>Motorista</th><th>Estado</th></tr></thead>
                <tbody>{rows.map((v) => (
                  <tr key={v.id} onClick={() => ops && setEdit(v)}>
                    <td><span className="swatch sm" style={{ background: v.color_hex }} /> <strong>{v.make} {v.model}</strong> <span className="muted">{v.color}</span></td>
                    <td className="mono">{v.plate}</td><td>{v.year}</td><td>{v.seats}</td>
                    <td>{v.org ? <Link to={`/frotas/${v.org.id}`} onClick={(e) => e.stopPropagation()}>{v.org.name}</Link> : <span className="muted">—</span>}</td>
                    <td>{v.product_ids.length ? v.product_ids.map(pname).join(', ') : <span className="muted">todas</span>}</td>
                    <td>{v.drivers.map((x) => <Link key={x.id} to={`/motoristas/${x.id}`} onClick={(e) => e.stopPropagation()}>{x.name}</Link>)}</td>
                    <td><Badge tone={TONE[v.status]}>{LABEL[v.status]}</Badge></td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          ) : <Empty>Sem veículos.</Empty>}
        </Gate>
      </Card>
      {edit && <VehicleForm vehicle={edit === 'new' ? undefined : edit} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); d.reload() }} />}
    </Page>
  )
}

export function VehicleForm({ vehicle, orgId, onClose, onSaved }: { vehicle?: Vehicle; orgId?: number; onClose: () => void; onSaved: () => void }) {
  const fleets = useData<Fleet[]>('/fleets', false)
  const catalog = useData<{ products: Product[] }>('/catalog', false)
  const [f, setF] = useState({
    make: vehicle?.make ?? '', model: vehicle?.model ?? '', year: String(vehicle?.year ?? 2020), color: vehicle?.color ?? '',
    color_hex: vehicle?.color_hex ?? '#222222', plate: vehicle?.plate ?? '', seats: String(vehicle?.seats ?? 4),
    status: vehicle?.status ?? 'pending', org_id: vehicle?.org?.id ?? orgId ?? 0, product_ids: vehicle?.product_ids ?? [],
  })
  const { run, busy } = useRun()
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })
  const toggleP = (id: number) => setF({ ...f, product_ids: f.product_ids.includes(id) ? f.product_ids.filter((x) => x !== id) : [...f.product_ids, id] })

  async function save() {
    const body = { ...f, year: Number(f.year), seats: Number(f.seats), org_id: Number(f.org_id) || undefined, clear_org: !Number(f.org_id) }
    const r = await run(() => (vehicle ? api.patch(`/vehicles/${vehicle.id}`, body) : api.post('/vehicles', body)), 'Guardado')
    if (r) onSaved()
  }
  return (
    <Modal title={vehicle ? `Veículo ${vehicle.plate}` : 'Novo veículo'} onClose={onClose} wide
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.make || !f.model || !f.plate} onClick={save}>Guardar</button></>}>
      <div className="form-grid three">
        <Field label="Marca"><input value={f.make} onChange={set('make')} autoFocus /></Field>
        <Field label="Modelo"><input value={f.model} onChange={set('model')} /></Field>
        <Field label="Matrícula"><input value={f.plate} onChange={set('plate')} placeholder="AA-00-BB" /></Field>
        <Field label="Ano"><input value={f.year} onChange={set('year')} inputMode="numeric" /></Field>
        <Field label="Lugares"><input value={f.seats} onChange={set('seats')} inputMode="numeric" /></Field>
        <Field label="Cor"><div className="color-row"><input type="color" value={f.color_hex} onChange={set('color_hex')} aria-label="Cor no mapa" /><input value={f.color} onChange={set('color')} placeholder="Cinzento" /></div></Field>
        <Field label="Frota">
          <select value={f.org_id} onChange={set('org_id')}><option value={0}>Sem frota</option>{fleets.data?.map((o) => <option key={o.id} value={o.id}>{o.name}</option>)}</select>
        </Field>
        <Field label="Estado">
          <select value={f.status} onChange={set('status')}>{Object.entries(LABEL).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
        </Field>
      </div>
      <Field label="Categorias permitidas" hint="Nenhuma marcada = todas (respeitando lugares e ano mínimo de cada categoria)">
        <div className="checks">
          {catalog.data?.products.map((p) => (
            <label key={p.id} className="check"><input type="checkbox" checked={f.product_ids.includes(p.id)} onChange={() => toggleP(p.id)} /> {p.name} <small className="muted">≥{p.min_vehicle_year} · {p.capacity} lug.</small></label>
          ))}
        </div>
      </Field>
    </Modal>
  )
}

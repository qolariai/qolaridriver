import { useState } from 'react'
import { api } from '../api'
import { centsInput, eur, parseCents } from '../format'
import { can, useAuth, useData } from '../live'
import type { City, Product, Quote } from '../types'
import { Badge, Card, Field, Gate, Icon, Modal, Page, Switch, useRun } from '../ui/kit'
import { FareTable } from './TripPage'

const MONEY: [keyof Product, string][] = [
  ['base_fare', 'Base'], ['per_km', 'Por km'], ['per_min', 'Por minuto'], ['minimum_fare', 'Mínimo'],
  ['booking_fee', 'Taxa de reserva'], ['cancel_fee', 'Taxa de cancelamento'],
]

export function Pricing() {
  const d = useData<{ cities: City[]; products: Product[] }>('/catalog')
  const { user } = useAuth()
  const admin = can(user)
  const [edit, setEdit] = useState<Product | 'new' | null>(null)
  const [sample, setSample] = useState({ km: '8', min: '18' })
  const { run } = useRun()

  return (
    <Page title="Categorias e tarifas" sub="O que o passageiro escolhe na app Rider (vehicle views) e quanto paga"
      actions={admin && <button className="btn primary" onClick={() => setEdit('new')}><Icon name="plus" /> Nova categoria</button>}>
      <Gate d={d}>
        {(x) => (
          <>
            {x.cities.map((c) => (
              <Card key={c.id} title={<>{c.name} <Badge>{c.currency}</Badge> <small className="muted">raio {c.radius_km} km</small></>}
                actions={<label className="inline">Exemplo: <input className="xs" value={sample.km} onChange={(e) => setSample({ ...sample, km: e.target.value })} /> km <input className="xs" value={sample.min} onChange={(e) => setSample({ ...sample, min: e.target.value })} /> min</label>} pad={false}>
                <div className="table-wrap">
                  <table className="table hover">
                    <thead><tr><th>Categoria</th><th className="num">Lugares</th>{MONEY.map(([, l]) => <th key={l} className="num">{l}</th>)}<th className="num">Dinâmica</th><th className="num">Exemplo</th><th>Ativa</th></tr></thead>
                    <tbody>{x.products.filter((p) => p.city_id === c.id).map((p) => {
                      const k = Number(sample.km.replace(',', '.')) || 0
                      const m = Number(sample.min.replace(',', '.')) || 0
                      const metered = p.base_fare + k * p.per_km + m * p.per_min
                      const ex = Math.round(Math.max(metered, p.minimum_fare) * p.surge) + p.booking_fee
                      return (
                        <tr key={p.id} onClick={() => admin && setEdit(p)}>
                          <td><strong>{p.name}</strong><small className="muted block">{p.description} · ano ≥ {p.min_vehicle_year}</small></td>
                          <td className="num">{p.capacity}</td>
                          {MONEY.map(([f]) => <td key={f} className="num">{eur(p[f] as number)}</td>)}
                          <td className="num">{p.surge > 1 ? <Badge tone="warn">×{p.surge}</Badge> : '×1'}</td>
                          <td className="num"><strong>{eur(ex)}</strong></td>
                          <td onClick={(e) => e.stopPropagation()}><Switch checked={p.active} label="Ativa" disabled={!admin} onChange={(v) => run(() => api.patch(`/products/${p.id}`, { active: v })).then(d.reload)} /></td>
                        </tr>
                      )
                    })}</tbody>
                  </table>
                </div>
              </Card>
            ))}
            {edit && <ProductForm product={edit === 'new' ? undefined : edit} cities={x.cities} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); d.reload() }} />}
          </>
        )}
      </Gate>
    </Page>
  )
}

function ProductForm({ product, cities, onClose, onSaved }: { product?: Product; cities: City[]; onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState<Record<string, string>>(() => {
    const o: Record<string, string> = {
      city_id: String(product?.city_id ?? cities[0]?.id ?? ''), code: product?.code ?? '', name: product?.name ?? '',
      description: product?.description ?? '', capacity: String(product?.capacity ?? 4), surge: String(product?.surge ?? 1),
      min_vehicle_year: String(product?.min_vehicle_year ?? 2012), sort_order: String(product?.sort_order ?? 9),
    }
    for (const [k] of MONEY) o[k] = centsInput((product?.[k] as number) ?? 0)
    return o
  })
  const [preview, setPreview] = useState<Quote | null>(null)
  const { run, busy } = useRun()
  const set = (k: string) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })

  function body() {
    const b: Record<string, unknown> = {
      city_id: Number(f.city_id), code: f.code, name: f.name, description: f.description, capacity: Number(f.capacity),
      surge: Number(f.surge.replace(',', '.')), min_vehicle_year: Number(f.min_vehicle_year), sort_order: Number(f.sort_order),
    }
    for (const [k, label] of MONEY) {
      const c = parseCents(f[k])
      if (c == null) throw new Error(`${label}: valor inválido`)
      b[k] = c
    }
    return b
  }
  async function save() {
    const r = await run(async () => {
      const b = body()
      return product ? api.patch(`/products/${product.id}`, b) : api.post('/products', b)
    }, 'Guardado')
    if (r) onSaved()
  }
  async function simulate() {
    // pré-visualizar com os valores guardados de uma viagem Rossio -> Aeroporto
    if (!product) return
    const r = await run(() => api.post<{ quote: Quote }[]>('/quote', { product_id: product.id, pickup: { lat: 38.7139, lng: -9.1394 }, dropoff: { lat: 38.7742, lng: -9.1342 } }))
    if (r) setPreview(r[0].quote)
  }
  return (
    <Modal title={product ? `Categoria ${product.name}` : 'Nova categoria'} onClose={onClose} wide
      footer={<>{product && <button className="btn" onClick={simulate}>Simular Rossio → Aeroporto</button>}<button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.name || !f.code} onClick={save}>Guardar</button></>}>
      <div className="form-grid three">
        <Field label="Nome"><input value={f.name} onChange={set('name')} autoFocus /></Field>
        <Field label="Código"><input value={f.code} onChange={set('code')} disabled={!!product} /></Field>
        <Field label="Cidade"><select value={f.city_id} onChange={set('city_id')} disabled={!!product}>{cities.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></Field>
        <Field label="Descrição" wide><input value={f.description} onChange={set('description')} /></Field>
        <Field label="Lugares"><input value={f.capacity} onChange={set('capacity')} inputMode="numeric" /></Field>
        {MONEY.map(([k, l]) => <Field key={k} label={`${l} (€)`}><input value={f[k]} onChange={set(k)} inputMode="decimal" /></Field>)}
        <Field label="Multiplicador dinâmico" hint="1 = normal; até 5"><input value={f.surge} onChange={set('surge')} inputMode="decimal" /></Field>
        <Field label="Ano mínimo do veículo"><input value={f.min_vehicle_year} onChange={set('min_vehicle_year')} inputMode="numeric" /></Field>
        <Field label="Ordem na app"><input value={f.sort_order} onChange={set('sort_order')} inputMode="numeric" /></Field>
      </div>
      {preview && <><h3 className="sub-head">Simulação (valores guardados)</h3><FareTable q={preview} /></>}
    </Modal>
  )
}

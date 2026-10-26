import { useState } from 'react'
import { api } from '../api'
import { centsInput, dateTime, eur, isoDay, parseCents } from '../format'
import { can, useAuth, useData } from '../live'
import type { Product, Promo } from '../types'
import { Badge, Card, Empty, Field, Gate, Icon, Modal, Page, Switch, useRun } from '../ui/kit'

const toTs = (day: string) => (day ? Math.floor(new Date(`${day}T00:00:00`).getTime() / 1000) : null)
const toDay = (ts: number | null) => (ts ? isoDay(new Date(ts * 1000)) : '')

export function Promos() {
  const d = useData<Promo[]>('/promos')
  const catalog = useData<{ products: Product[] }>('/catalog', false)
  const { user } = useAuth()
  const ops = can(user, 'operator')
  const [edit, setEdit] = useState<Promo | 'new' | null>(null)
  const { run } = useRun()
  const now = Date.now() / 1000

  return (
    <Page title="Promoções" sub="Códigos que o passageiro aplica na app Rider (Pagamento → Promoções). O desconto é pago pela plataforma."
      actions={ops && <button className="btn primary" onClick={() => setEdit('new')}><Icon name="plus" /> Novo código</button>}>
      <Card pad={false}>
        <Gate d={d}>
          {(rows) => rows.length ? (
            <table className="table hover">
              <thead><tr><th>Código</th><th>Desconto</th><th>Validade</th><th>Categoria</th><th className="num">Usos</th><th>Ativo</th></tr></thead>
              <tbody>{rows.map((p) => {
                const expired = p.valid_to && p.valid_to < now
                return (
                  <tr key={p.id} onClick={() => ops && setEdit(p)}>
                    <td><strong className="mono">{p.code}</strong><small className="muted block">{p.description}</small></td>
                    <td>{p.kind === 'percent' ? `${p.value}%` : eur(p.value)}{p.max_discount ? <small className="muted"> (máx. {eur(p.max_discount)})</small> : null}</td>
                    <td>{p.valid_from || p.valid_to ? `${p.valid_from ? dateTime(p.valid_from) : '…'} → ${p.valid_to ? dateTime(p.valid_to) : '…'}` : 'sempre'} {expired && <Badge tone="muted">expirado</Badge>}</td>
                    <td>{p.product_id ? catalog.data?.products.find((x) => x.id === p.product_id)?.name : 'Todas'}</td>
                    <td className="num">{p.uses}{p.max_uses != null ? ` / ${p.max_uses}` : ''}</td>
                    <td onClick={(e) => e.stopPropagation()}><Switch checked={p.active} label="Ativo" disabled={!ops} onChange={(v) => run(() => api.patch(`/promos/${p.id}`, { active: v })).then(d.reload)} /></td>
                  </tr>
                )
              })}</tbody>
            </table>
          ) : <Empty>Sem códigos promocionais.</Empty>}
        </Gate>
      </Card>
      {edit && <PromoForm promo={edit === 'new' ? undefined : edit} products={catalog.data?.products ?? []} onClose={() => setEdit(null)} onSaved={() => { setEdit(null); d.reload() }} />}
    </Page>
  )
}

function PromoForm({ promo, products, onClose, onSaved }: { promo?: Promo; products: Product[]; onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState({
    code: promo?.code ?? '', description: promo?.description ?? '', kind: promo?.kind ?? 'percent',
    value: promo ? (promo.kind === 'percent' ? String(promo.value) : centsInput(promo.value)) : '10',
    max_discount: promo?.max_discount != null ? centsInput(promo.max_discount) : '', max_uses: promo?.max_uses != null ? String(promo.max_uses) : '',
    per_rider: String(promo?.per_rider ?? 1), product_id: String(promo?.product_id ?? ''), valid_from: toDay(promo?.valid_from ?? null), valid_to: toDay(promo?.valid_to ?? null),
  })
  const { run, busy } = useRun()
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setF({ ...f, [k]: e.target.value })
  async function save() {
    const r = await run(async () => {
      const value = f.kind === 'percent' ? Number(f.value) : parseCents(f.value)
      if (value == null || Number.isNaN(value)) throw new Error('valor inválido')
      const body = {
        code: f.code, description: f.description, kind: f.kind, value,
        max_discount: f.max_discount ? parseCents(f.max_discount) : null, max_uses: f.max_uses ? Number(f.max_uses) : null,
        per_rider: Number(f.per_rider) || 1, product_id: f.product_id ? Number(f.product_id) : null,
        valid_from: toTs(f.valid_from), valid_to: toTs(f.valid_to),
      }
      return promo ? api.patch(`/promos/${promo.id}`, body) : api.post('/promos', body)
    }, 'Guardado')
    if (r) onSaved()
  }
  return (
    <Modal title={promo ? `Código ${promo.code}` : 'Novo código'} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.code} onClick={save}>Guardar</button></>}>
      <div className="form-grid">
        <Field label="Código"><input value={f.code} onChange={set('code')} disabled={!!promo} autoFocus style={{ textTransform: 'uppercase' }} /></Field>
        <Field label="Tipo"><select value={f.kind} onChange={set('kind')}><option value="percent">Percentagem</option><option value="amount">Valor fixo</option></select></Field>
        <Field label={f.kind === 'percent' ? 'Desconto (%)' : 'Desconto (€)'}><input value={f.value} onChange={set('value')} inputMode="decimal" /></Field>
        <Field label="Desconto máximo (€)" hint="vazio = sem limite"><input value={f.max_discount} onChange={set('max_discount')} inputMode="decimal" /></Field>
        <Field label="Usos totais" hint="vazio = ilimitado"><input value={f.max_uses} onChange={set('max_uses')} inputMode="numeric" /></Field>
        <Field label="Usos por passageiro"><input value={f.per_rider} onChange={set('per_rider')} inputMode="numeric" /></Field>
        <Field label="Válido de"><input type="date" value={f.valid_from} onChange={set('valid_from')} /></Field>
        <Field label="Válido até (exclusive)"><input type="date" value={f.valid_to} onChange={set('valid_to')} /></Field>
        <Field label="Categoria"><select value={f.product_id} onChange={set('product_id')}><option value="">Todas</option>{products.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}</select></Field>
        <Field label="Descrição (aparece na app)"><input value={f.description} onChange={set('description')} /></Field>
      </div>
    </Modal>
  )
}

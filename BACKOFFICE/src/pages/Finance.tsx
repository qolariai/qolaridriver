import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, qs } from '../api'
import { dateTime, eur, isoDay, LEDGER_KIND, PARTY, parseCents } from '../format'
import { can, useAuth, useData } from '../live'
import type { Ledger, Payout } from '../types'
import { Badge, Card, Empty, Field, Gate, Modal, Page, Stat, Tabs, useRun } from '../ui/kit'

type Overview = {
  from: number; to: number; trips: number; gross: number; commission: number; promo_cost: number; fleet_fees: number
  cash_collected: number; cancel_fees: number; payouts_pending: number; payouts_paid: number
  driver_balances: { id: number; name: string; org: string | null; balance: number }[]
  fleet_balances: { id: number; name: string; balance: number }[]
}

const weekAgo = () => isoDay(new Date(Date.now() - 6 * 86400_000))

export function Finance() {
  const [from, setFrom] = useState(weekAgo())
  const [to, setTo] = useState(isoDay(new Date()))
  const [tab, setTab] = useState<'balances' | 'payouts' | 'ledger'>('balances')
  const d = useData<Overview>(`/finance/overview${qs({ day_from: from, day_to: to })}`)
  const { user } = useAuth()
  const fin = can(user, 'finance')
  const [pay, setPay] = useState<{ party: 'driver' | 'fleet'; id: number; name: string; balance: number } | null>(null)
  const [adjust, setAdjust] = useState<{ party: 'driver' | 'fleet'; id: number; name: string } | null>(null)

  return (
    <Page title="Finanças" sub="Comissões, taxas de frota, dinheiro recebido pelos motoristas e pagamentos"
      actions={<><input type="date" value={from} onChange={(e) => setFrom(e.target.value)} aria-label="De" /><input type="date" value={to} onChange={(e) => setTo(e.target.value)} aria-label="Até" /></>}>
      <Gate d={d}>
        {(x) => (
          <>
            <div className="stats">
              <Stat label="Faturação bruta" value={eur(x.gross)} hint={`${x.trips} viagens concluídas`} />
              <Stat label="Comissão da plataforma" value={eur(x.commission)} tone="ok" hint={`promoções −${eur(x.promo_cost)} · líquido ${eur(x.commission - x.promo_cost)}`} />
              <Stat label="Taxas de frota" value={eur(x.fleet_fees)} />
              <Stat label="Recebido em dinheiro" value={eur(x.cash_collected)} hint="fica com os motoristas" />
              <Stat label="Pagamentos" value={eur(x.payouts_paid)} hint={`${eur(x.payouts_pending)} pendentes`} tone={x.payouts_pending ? 'warn' : undefined} />
            </div>
            <Tabs value={tab} onChange={setTab} items={[['balances', 'Saldos'], ['payouts', 'Pagamentos'], ['ledger', 'Movimentos']]} />
            {tab === 'balances' && (
              <div className="grid-2">
                <BalanceCard title="Motoristas" rows={x.driver_balances.map((b) => ({ ...b, sub: b.org ?? 'independente', link: `/motoristas/${b.id}` }))}
                  fin={fin} onPay={(b) => setPay({ party: 'driver', ...b })} onAdjust={(b) => setAdjust({ party: 'driver', ...b })} />
                <BalanceCard title="Frotas" rows={x.fleet_balances.map((b) => ({ ...b, sub: '', link: `/frotas/${b.id}` }))}
                  fin={fin} onPay={(b) => setPay({ party: 'fleet', ...b })} onAdjust={(b) => setAdjust({ party: 'fleet', ...b })} />
              </div>
            )}
            {tab === 'payouts' && <Payouts fin={fin} />}
            {tab === 'ledger' && <LedgerTable />}
            {pay && <PayModal p={pay} onClose={() => setPay(null)} onDone={() => { setPay(null); d.reload() }} />}
            {adjust && <AdjustModal p={adjust} onClose={() => setAdjust(null)} onDone={() => { setAdjust(null); d.reload() }} />}
          </>
        )}
      </Gate>
    </Page>
  )
}

type Bal = { id: number; name: string; balance: number; sub: string; link: string }

function BalanceCard({ title, rows, fin, onPay, onAdjust }: { title: string; rows: Bal[]; fin: boolean; onPay: (b: Bal) => void; onAdjust: (b: Bal) => void }) {
  return (
    <Card title={title} pad={false}>
      {rows.length ? (
        <table className="table compact">
          <thead><tr><th>Nome</th><th className="num">Saldo</th><th></th></tr></thead>
          <tbody>{rows.map((b) => (
            <tr key={b.id}>
              <td><Link to={b.link}>{b.name}</Link>{b.sub && <small className="muted block">{b.sub}</small>}</td>
              <td className={`num ${b.balance < 0 ? 'neg' : ''}`}><strong>{eur(b.balance)}</strong>{b.balance < 0 && <small className="muted block">deve à plataforma</small>}</td>
              <td className="row-actions nowrap">{fin && <><button className="btn sm" onClick={() => onAdjust(b)}>Acerto</button><button className="btn sm primary" disabled={b.balance <= 0} onClick={() => onPay(b)}>Pagar</button></>}</td>
            </tr>
          ))}</tbody>
        </table>
      ) : <Empty>Sem movimentos.</Empty>}
    </Card>
  )
}

function Payouts({ fin }: { fin: boolean }) {
  const [status, setStatus] = useState('')
  const d = useData<Payout[]>(`/payouts${qs({ status })}`)
  const { run, busy } = useRun()
  return (
    <Card pad={false} title="Pagamentos" actions={<select value={status} onChange={(e) => setStatus(e.target.value)} aria-label="Estado"><option value="">Todos</option><option value="pending">Pendentes</option><option value="paid">Pagos</option><option value="cancelled">Cancelados</option></select>}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <table className="table">
            <thead><tr><th>Criado</th><th>Para</th><th className="num">Valor</th><th>Estado</th><th>Referência</th><th></th></tr></thead>
            <tbody>{rows.map((p) => (
              <tr key={p.id}>
                <td>{dateTime(p.created_at)}</td>
                <td><Link to={p.party === 'driver' ? `/motoristas/${p.party_id}` : `/frotas/${p.party_id}`}>{p.party_name}</Link> <small className="muted">{PARTY[p.party]}</small></td>
                <td className="num"><strong>{eur(p.amount)}</strong></td>
                <td><Badge tone={p.status === 'paid' ? 'ok' : p.status === 'pending' ? 'warn' : 'muted'}>{p.status === 'paid' ? 'Pago' : p.status === 'pending' ? 'Pendente' : 'Cancelado'}</Badge>{p.paid_at && <small className="muted block">{dateTime(p.paid_at)}</small>}</td>
                <td className="mono">{p.reference || '—'}</td>
                <td className="row-actions nowrap">{fin && p.status === 'pending' && (
                  <>
                    <button className="btn sm" disabled={busy} onClick={() => run(() => api.post(`/payouts/${p.id}/cancel`), 'Cancelado').then(d.reload)}>Cancelar</button>
                    <button className="btn sm primary" disabled={busy} onClick={() => { const ref = window.prompt('Referência da transferência', p.reference); if (ref !== null) run(() => api.post(`/payouts/${p.id}/paid`, { reference: ref }), 'Marcado como pago').then(d.reload) }}>Marcar pago</button>
                  </>
                )}</td>
              </tr>
            ))}</tbody>
          </table>
        ) : <Empty>Sem pagamentos.</Empty>}
      </Gate>
    </Card>
  )
}

function LedgerTable() {
  const [party, setParty] = useState('')
  const [kind, setKind] = useState('')
  const [page, setPage] = useState(1)
  const d = useData<{ total: number; items: Ledger[] }>(`/finance/ledger${qs({ party, kind, page })}`)
  return (
    <Card pad={false} title="Movimentos" actions={<>
      <select value={party} onChange={(e) => { setParty(e.target.value); setPage(1) }} aria-label="Parte"><option value="">Todas as partes</option>{Object.entries(PARTY).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
      <select value={kind} onChange={(e) => { setKind(e.target.value); setPage(1) }} aria-label="Tipo"><option value="">Todos os tipos</option>{Object.entries(LEDGER_KIND).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select>
    </>}>
      <Gate d={d}>
        {(x) => (
          <>
            <table className="table compact">
              <thead><tr><th>Data</th><th>Parte</th><th>Tipo</th><th>Viagem</th><th>Nota</th><th className="num">Valor</th></tr></thead>
              <tbody>{x.items.map((e) => (
                <tr key={e.id}><td className="nowrap">{dateTime(e.at)}</td><td>{PARTY[e.party]} {e.party_id ?? ''}</td><td>{LEDGER_KIND[e.kind] ?? e.kind}</td>
                  <td>{e.trip_uuid ? <Link className="mono" to={`/viagens/${e.trip_uuid}`}>{e.trip_uuid.slice(0, 8)}</Link> : '—'}</td>
                  <td className="muted">{e.note}</td><td className={`num ${e.amount < 0 ? 'neg' : ''}`}>{eur(e.amount)}</td></tr>
              ))}</tbody>
            </table>
            <div className="pager"><span className="muted">{x.total} movimentos</span>
              <button className="btn sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button><span>{page}</span>
              <button className="btn sm" disabled={page * 50 >= x.total} onClick={() => setPage(page + 1)}>Seguinte</button></div>
          </>
        )}
      </Gate>
    </Card>
  )
}

function PayModal({ p, onClose, onDone }: { p: { party: 'driver' | 'fleet'; id: number; name: string; balance: number }; onClose: () => void; onDone: () => void }) {
  const [amount, setAmount] = useState((p.balance / 100).toFixed(2).replace('.', ','))
  const [reference, setReference] = useState('')
  const { run, busy } = useRun()
  const go = () => run(async () => {
    const c = parseCents(amount)
    if (!c || c <= 0) throw new Error('valor inválido')
    return api.post('/payouts', { party: p.party, party_id: p.id, amount: c, reference })
  }, 'Pagamento criado (pendente)').then((r) => r && onDone())
  return (
    <Modal title={`Pagar a ${p.name}`} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy} onClick={go}>Criar pagamento</button></>}>
      <p className="muted">Saldo atual {eur(p.balance)}. O pagamento fica pendente até o marcares como pago (com a referência da transferência).</p>
      <div className="form-grid">
        <Field label="Valor (€)"><input value={amount} onChange={(e) => setAmount(e.target.value)} inputMode="decimal" /></Field>
        <Field label="Referência"><input value={reference} onChange={(e) => setReference(e.target.value)} placeholder="opcional" /></Field>
      </div>
    </Modal>
  )
}

function AdjustModal({ p, onClose, onDone }: { p: { party: 'driver' | 'fleet'; id: number; name: string }; onClose: () => void; onDone: () => void }) {
  const [amount, setAmount] = useState('')
  const [note, setNote] = useState('')
  const { run, busy } = useRun()
  const go = () => run(async () => {
    const c = parseCents(amount)
    if (!c) throw new Error('valor inválido (use − para descontar)')
    return api.post('/finance/adjust', { party: p.party, party_id: p.id, amount: c, note })
  }, 'Acerto registado').then((r) => r && onDone())
  return (
    <Modal title={`Acerto · ${p.name}`} onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || note.length < 3} onClick={go}>Registar</button></>}>
      <div className="form-grid">
        <Field label="Valor (€)" hint="positivo = a plataforma deve mais; negativo = desconta"><input value={amount} onChange={(e) => setAmount(e.target.value)} placeholder="-5,00" /></Field>
        <Field label="Motivo"><input value={note} onChange={(e) => setNote(e.target.value)} placeholder="ex.: bónus de fim de semana" /></Field>
      </div>
    </Modal>
  )
}

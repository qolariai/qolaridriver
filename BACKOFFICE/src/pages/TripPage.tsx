import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { ACTOR, clock, dateTime, eur, EVENT, km, LEDGER_KIND, mins, PARTY, TRIP_STATE } from '../format'
import { can, useAuth, useData } from '../live'
import type { Driver, Quote, Trip, TripState } from '../types'
import { MapView } from '../ui/MapView'
import { Badge, Card, Field, Gate, Modal, Page, TripBadge, useRun } from '../ui/kit'

const NEXT: Partial<Record<TripState, [string, string][]>> = {
  requested: [['accept', 'Motorista aceita'], ['reject', 'Motorista recusa'], ['redispatch', 'Repetir despacho']],
  accepted: [['arrive', 'Chegou à recolha'], ['start', 'Iniciar viagem']],
  arrived: [['start', 'Iniciar viagem']],
  in_progress: [['complete', 'Concluir viagem']],
}

export function TripPage() {
  const { id = '' } = useParams()
  const d = useData<Trip>(`/trips/${id}`)
  const { user } = useAuth()
  const { run, busy } = useRun()
  const [modal, setModal] = useState<'offer' | 'cancel' | 'force' | null>(null)
  const ops = can(user, 'operator')

  const act = (action: string, extra: Record<string, unknown> = {}) =>
    run(async () => {
      const t = await api.post<Trip>(`/trips/${id}/action`, { action, ...extra })
      d.setData(t)
      setModal(null)
    }, 'Feito')

  return (
    <Gate d={d}>
      {(t) => {
        const q = t.breakdown.final ?? t.breakdown.estimate
        const active = ['requested', 'accepted', 'arrived', 'in_progress'].includes(t.state)
        const pending = t.offers.find((o) => o.state === 'pending')
        const driverPt = t.driver_live?.lat != null && t.driver ? [{ id: t.driver.id, name: t.driver.name, lat: t.driver_live.lat!, lng: t.driver_live.lng!, heading: t.driver_live.heading, availability: active ? 'on_trip' : 'online' }] : []
        return (
          <Page back={{ to: '/viagens', label: 'Viagens' }}
            title={<>Viagem <span className="mono">{t.uuid.slice(0, 8)}</span> <TripBadge state={t.state} /></>}
            sub={`${t.product.name} · ${t.city} · pedida ${dateTime(t.requested_at)}${t.source === 'console' ? ' · criada no simulador' : ''}`}
            actions={ops && active && (
              <>
                {(NEXT[t.state] ?? []).filter(([a]) => a !== 'accept' && a !== 'reject' || pending).map(([a, label]) => (
                  <button key={a} className="btn" disabled={busy} onClick={() => act(a)}>{label}</button>
                ))}
                {t.state === 'requested' && <button className="btn" onClick={() => setModal('offer')}>Propor a…</button>}
                <button className="btn" onClick={() => setModal('force')}>Forçar estado</button>
                <button className="btn danger" onClick={() => setModal('cancel')}>Cancelar</button>
              </>
            )}>
            <div className="grid-2-1">
              <Card pad={false}>
                <MapView center={[t.pickup.lat, t.pickup.lng]} fit height={340} drivers={driverPt}
                  trips={[{ uuid: t.uuid, state: t.state, pickup: [t.pickup.lat, t.pickup.lng], dropoff: t.dropoff ? [t.dropoff.lat, t.dropoff.lng] : null, label: t.pickup_address }]} />
                <div className="route-box">
                  <div><span className="pin a">A</span><div><strong>{t.pickup_address || 'Recolha'}</strong><small className="muted">{t.pickup.lat.toFixed(5)}, {t.pickup.lng.toFixed(5)}</small></div></div>
                  <div><span className="pin b">B</span><div><strong>{t.dropoff_address || 'Sem destino'}</strong>{t.dropoff && <small className="muted">{t.dropoff.lat.toFixed(5)}, {t.dropoff.lng.toFixed(5)}</small>}</div></div>
                </div>
              </Card>
              <div className="stack">
                <Card title="Pessoas">
                  <dl className="kv">
                    <dt>Passageiro</dt><dd>{t.rider ? <Link to={`/passageiros/${t.rider.id}`}>{t.rider.name}</Link> : '—'} <span className="muted">{t.rider?.phone}</span></dd>
                    <dt>Motorista</dt><dd>{t.driver ? <Link to={`/motoristas/${t.driver.id}`}>{t.driver.name}</Link> : <span className="muted">{t.state === 'requested' ? (pending ? `proposta a ${pending.driver.name}` : 'à procura…') : '—'}</span>}</dd>
                    <dt>Veículo</dt><dd>{t.vehicle ? `${t.vehicle.label}` : '—'}</dd>
                    <dt>PIN</dt><dd className="mono">{t.pin || '—'}</dd>
                    <dt>Pagamento</dt><dd>{t.payment_method === 'cash' ? 'Dinheiro' : 'Cartão'}</dd>
                    {t.rider_to_driver_rating != null && <><dt>Avaliação</dt><dd>★ {t.rider_to_driver_rating} {t.rider_comment && <span className="muted">“{t.rider_comment}”</span>}</dd></>}
                    {t.cancel_reason && <><dt>Cancelamento</dt><dd>{ACTOR[t.cancelled_by] ?? t.cancelled_by}: {t.cancel_reason}</dd></>}
                  </dl>
                </Card>
                <Card title={t.breakdown.final ? 'Tarifa final' : 'Estimativa'}>
                  {q ? <FareTable q={q} /> : <p className="muted">—</p>}
                  {t.breakdown.cancel_fee != null && <p>Taxa de cancelamento cobrada: <strong>{eur(t.breakdown.cancel_fee)}</strong></p>}
                </Card>
              </div>
            </div>

            <div className="grid-2">
              <Card title="Cronologia">
                <ol className="timeline">
                  {t.events.map((e) => (
                    <li key={e.id}>
                      <time>{clock(e.at)}</time>
                      <div><strong>{EVENT[e.kind] ?? e.kind}</strong> <Badge>{ACTOR[e.actor] ?? e.actor}</Badge>{e.detail && <p className="muted">{e.detail}</p>}</div>
                    </li>
                  ))}
                </ol>
              </Card>
              <div className="stack">
                <Card title="Propostas (despacho)">
                  {t.offers.length ? (
                    <table className="table compact">
                      <thead><tr><th>Motorista</th><th>Estado</th><th className="num">Distância</th><th>Hora</th></tr></thead>
                      <tbody>{t.offers.map((o) => (
                        <tr key={o.id}><td>{o.driver.name}</td><td><Badge tone={o.state === 'accepted' ? 'ok' : o.state === 'pending' ? 'warn' : 'muted'}>{o.state}</Badge></td><td className="num">{km(o.pickup_distance_m)}</td><td>{clock(o.created_at)}</td></tr>
                      ))}</tbody>
                    </table>
                  ) : <p className="muted">Nenhuma proposta.</p>}
                </Card>
                <Card title="Movimentos financeiros">
                  {t.ledger.length ? (
                    <table className="table compact">
                      <thead><tr><th>Parte</th><th>Tipo</th><th className="num">Valor</th></tr></thead>
                      <tbody>{t.ledger.map((e) => (
                        <tr key={e.id}><td>{PARTY[e.party]}</td><td>{LEDGER_KIND[e.kind] ?? e.kind}<small className="muted"> {e.note}</small></td><td className={`num ${e.amount < 0 ? 'neg' : ''}`}>{eur(e.amount)}</td></tr>
                      ))}</tbody>
                    </table>
                  ) : <p className="muted">Sem movimentos (só depois de concluída).</p>}
                </Card>
              </div>
            </div>

            {modal === 'offer' && <OfferModal onClose={() => setModal(null)} onPick={(driver_id) => act('offer', { driver_id })} busy={busy} />}
            {modal === 'cancel' && <CancelModal onClose={() => setModal(null)} onOk={(reason) => act('cancel', { reason })} busy={busy} />}
            {modal === 'force' && <ForceModal current={t.state} onClose={() => setModal(null)} onOk={(state) => act('force', { state })} busy={busy} />}
          </Page>
        )
      }}
    </Gate>
  )
}

export function FareTable({ q }: { q: Quote }) {
  return (
    <table className="table compact fare">
      <tbody>
        <tr><td>Distância / duração</td><td className="num">{km(q.distance_m)} · {mins(q.duration_s)}</td></tr>
        <tr><td>Tarifa base</td><td className="num">{eur(q.base)}</td></tr>
        <tr><td>Distância</td><td className="num">{eur(q.distance)}</td></tr>
        <tr><td>Tempo</td><td className="num">{eur(q.time)}</td></tr>
        {q.minimum_applied && <tr><td colSpan={2} className="muted">Aplicado o valor mínimo</td></tr>}
        {q.surge_amount > 0 && <tr><td>Dinâmica ×{q.surge}</td><td className="num">{eur(q.surge_amount)}</td></tr>}
        <tr><td>Taxa de reserva</td><td className="num">{eur(q.booking_fee)}</td></tr>
        {q.discount > 0 && <tr><td>Desconto</td><td className="num neg">−{eur(q.discount)}</td></tr>}
        <tr className="total"><td>Total</td><td className="num">{eur(q.total)}</td></tr>
      </tbody>
    </table>
  )
}

function OfferModal({ onClose, onPick, busy }: { onClose: () => void; onPick: (id: number) => void; busy: boolean }) {
  const d = useData<Driver[]>('/drivers?status=approved&availability=online')
  return (
    <Modal title="Propor a um motorista" onClose={onClose}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <ul className="pick-list">
            {rows.map((r) => (
              <li key={r.id}><button disabled={busy} onClick={() => onPick(r.id)}><strong>{r.name}</strong><span className="muted">{r.vehicle?.label ?? 'sem veículo'} · ★ {r.rating}</span></button></li>
            ))}
          </ul>
        ) : <p className="muted">Nenhum motorista disponível. Põe um online na página do motorista ou no simulador.</p>}
      </Gate>
    </Modal>
  )
}

function CancelModal({ onClose, onOk, busy }: { onClose: () => void; onOk: (r: string) => void; busy: boolean }) {
  const [reason, setReason] = useState('')
  return (
    <Modal title="Cancelar viagem" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Voltar</button><button className="btn danger" disabled={busy} onClick={() => onOk(reason)}>Cancelar viagem</button></>}>
      <Field label="Motivo (fica no histórico)"><input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="ex.: pedido duplicado" autoFocus /></Field>
      <p className="muted">Cancelado pela consola não cobra taxa ao passageiro.</p>
    </Modal>
  )
}

function ForceModal({ current, onClose, onOk, busy }: { current: TripState; onClose: () => void; onOk: (s: string) => void; busy: boolean }) {
  const [state, setState] = useState<TripState>(current)
  return (
    <Modal title="Forçar estado" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Voltar</button><button className="btn primary" disabled={busy || state === current} onClick={() => onOk(state)}>Aplicar</button></>}>
      <p className="muted">Salta a máquina de estados (para desbloquear testes). “Concluída” calcula a tarifa e os movimentos; voltar a “A procurar” liberta o motorista.</p>
      <Field label="Novo estado">
        <select value={state} onChange={(e) => setState(e.target.value as TripState)}>
          {(['requested', 'accepted', 'arrived', 'in_progress', 'completed', 'cancelled'] as TripState[]).map((s) => <option key={s} value={s}>{TRIP_STATE[s]}</option>)}
        </select>
      </Field>
    </Modal>
  )
}

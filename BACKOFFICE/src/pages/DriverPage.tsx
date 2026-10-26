import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../api'
import { ago, dateTime, DOC_KIND, eur, LEDGER_KIND, pct } from '../format'
import { can, useAuth, useData } from '../live'
import type { Device, Doc, Driver, Offer, Session, TripRow, Vehicle } from '../types'
import { MapView } from '../ui/MapView'
import { AvailBadge, Badge, Card, DriverBadge, Field, Gate, Modal, Page, Stars, Stat, useRun } from '../ui/kit'
import { DocRow } from './Documents'
import { DriverForm } from './Drivers'
import { SessionTable } from './Settings'
import { TripTable } from './Trips'

type Detail = Driver & {
  documents: Doc[]; recent_trips: TripRow[]; week: { by_kind: Record<string, number>; trips: number }
  completed_total: number; sessions: Session[]; devices: Device[]; pending_offer: Offer | null; active_trip: TripRow | null
}

export function DriverPage() {
  const { id } = useParams()
  const d = useData<Detail>(`/drivers/${id}`)
  const { user } = useAuth()
  const ops = can(user, 'operator')
  const { run, busy } = useRun()
  const [modal, setModal] = useState<'edit' | 'vehicle' | null>(null)

  const patch = (body: object, ok = 'Guardado') => run(async () => d.setData(await api.patch<Detail>(`/drivers/${id}`, body)), ok)
  const toggle = (x: Detail) => run(async () => d.setData(await api.post<Detail>(`/drivers/${id}/${x.availability === 'offline' ? 'online' : 'offline'}`, {})))

  return (
    <Gate d={d}>
      {(x) => {
        const w = x.week.by_kind
        const net = (w.fare ?? 0) + (w.cancel_fee ?? 0) + (w.commission ?? 0) + (w.fleet_fee ?? 0)
        return (
          <Page back={{ to: '/motoristas', label: 'Motoristas' }}
            title={<>{x.name} <DriverBadge status={x.status} /> <AvailBadge a={x.availability} /></>}
            sub={<>{x.phone} · {x.email || 'sem email'} · {x.org ? <Link to={`/frotas/${x.org.id}`}>{x.org.name}</Link> : 'independente'} · registo {dateTime(x.created_at)}</>}
            actions={ops && (
              <>
                {x.status === 'pending' && <button className="btn primary" disabled={busy} onClick={() => patch({ status: 'approved' }, 'Motorista aprovado')}>Aprovar</button>}
                {x.status === 'pending' && <button className="btn" disabled={busy} onClick={() => patch({ status: 'rejected' })}>Recusar</button>}
                {x.status === 'approved' && <button className="btn" disabled={busy || x.availability === 'on_trip' || !x.vehicle} onClick={() => toggle(x)}>{x.availability === 'offline' ? 'Pôr online' : 'Pôr offline'}</button>}
                {x.status === 'approved' && <button className="btn danger" disabled={busy || x.availability === 'on_trip'} onClick={() => patch({ status: 'suspended' }, 'Suspenso')}>Suspender</button>}
                {(x.status === 'suspended' || x.status === 'rejected') && <button className="btn" disabled={busy} onClick={() => patch({ status: 'approved' }, 'Reativado')}>Reativar</button>}
                <button className="btn" onClick={() => setModal('edit')}>Editar</button>
              </>
            )}>
            <div className="stats">
              <Stat label="Avaliação" value={<Stars value={x.rating} />} hint={`${x.rating_count} avaliações`} />
              <Stat label="Viagens" value={x.completed_total} hint={`${x.week.trips} nos últimos 7 dias`} />
              <Stat label="Ganho líquido (7 dias)" value={eur(net)} hint={`comissão ${eur(w.commission ?? 0)} · frota ${eur(w.fleet_fee ?? 0)}`} />
              <Stat label="Saldo" value={eur(x.balance)} hint={(x.balance ?? 0) < 0 ? 'deve à plataforma (dinheiro recebido)' : 'a pagar ao motorista'} tone={(x.balance ?? 0) < 0 ? 'bad' : 'ok'} />
              <Stat label="Aceitação" value={pct(x.acceptance_rate)} hint={`${x.offers_accepted} de ${x.offers_received} propostas`} />
            </div>

            <div className="grid-2-1">
              <Card title="Posição" actions={<span className="muted">{x.location_at ? `atualizada ${ago(x.location_at)}` : 'sem posição'}{x.simulated ? ' · simulado' : ' · app'}</span>} pad={false}>
                {x.lat != null ? (
                  <MapView center={[x.lat, x.lng!]} height={300} drivers={[{ id: x.id, name: x.name, lat: x.lat, lng: x.lng!, heading: x.heading, availability: x.availability }]} />
                ) : <div className="empty">O motorista ainda não enviou localização.</div>}
              </Card>
              <div className="stack">
                <Card title="Veículo" actions={ops && <button className="btn sm" onClick={() => setModal('vehicle')}>Mudar</button>}>
                  {x.vehicle ? (
                    <div className="vehicle-chip"><span className="swatch" style={{ background: x.vehicle.color_hex }} /><div><strong>{x.vehicle.make} {x.vehicle.model}</strong><small className="muted block">{x.vehicle.plate} · {x.vehicle.color}</small></div></div>
                  ) : <p className="muted">Sem veículo — não pode ficar online.</p>}
                </Card>
                <Card title="Agora">
                  {x.active_trip ? <p>Em viagem: <Link to={`/viagens/${x.active_trip.uuid}`}>{x.active_trip.pickup_address} → {x.active_trip.dropoff_address}</Link></p>
                    : x.pending_offer ? <p>Proposta pendente (expira {ago(x.pending_offer.expires_at).replace('há', 'em')})</p>
                      : <p className="muted">{x.availability === 'online' ? 'À espera de propostas.' : 'Offline.'}</p>}
                  <p className="muted">Online desde: {x.online_since ? dateTime(x.online_since) : '—'}</p>
                </Card>
              </div>
            </div>

            <Card title="Documentos" pad={false}>
              <table className="table">
                <thead><tr><th>Documento</th><th>N.º</th><th>Validade</th><th>Estado</th><th></th></tr></thead>
                <tbody>{x.documents.map((doc) => <DocRow key={doc.id} doc={doc} onChange={d.reload} hideOwner />)}</tbody>
              </table>
              {!x.documents.length && <div className="empty">Sem documentos. Tipos: {Object.values(DOC_KIND).slice(0, 5).join(', ')}.</div>}
            </Card>

            <Card title="Viagens recentes" pad={false}><TripTable rows={x.recent_trips} hide={['driver']} /></Card>

            <div className="grid-2">
              <Card title="Sessões na app Driver" pad={false}><SessionTable rows={x.sessions} onChange={d.reload} /></Card>
              <Card title="Dispositivos">
                {x.devices.length ? <ul className="plain">{x.devices.map((v) => <li key={v.id}><strong>{v.model || v.device_key}</strong> <span className="muted">Android {v.os_version} · app {v.app_version} · {ago(v.last_seen_at)}</span></li>)}</ul>
                  : <p className="muted">Ainda não abriu a app Driver.</p>}
                <h3 className="sub-head">Ganhos 7 dias por tipo</h3>
                <ul className="plain">{Object.entries(w).map(([k, v]) => <li key={k}>{LEDGER_KIND[k] ?? k}: <strong className={v < 0 ? 'neg' : ''}>{eur(v)}</strong></li>)}</ul>
              </Card>
            </div>

            {modal === 'edit' && <DriverForm driver={x} onClose={() => setModal(null)} onSaved={() => { setModal(null); d.reload() }} />}
            {modal === 'vehicle' && <VehicleModal driver={x} onClose={() => setModal(null)} onPick={(vid) => patch(vid ? { vehicle_id: vid } : { clear_vehicle: true }).then(() => setModal(null))} />}
          </Page>
        )
      }}
    </Gate>
  )
}

function VehicleModal({ driver, onClose, onPick }: { driver: Driver; onClose: () => void; onPick: (id: number | null) => void }) {
  const v = useData<Vehicle[]>(`/vehicles${driver.org ? `?org_id=${driver.org.id}` : '?org_id=0'}`, false)
  const [sel, setSel] = useState<number | null>(driver.vehicle?.id ?? null)
  return (
    <Modal title="Veículo do motorista" onClose={onClose}
      footer={<><button className="btn" onClick={() => onPick(null)}>Sem veículo</button><button className="btn primary" onClick={() => onPick(sel)} disabled={!sel}>Atribuir</button></>}>
      <Gate d={v}>
        {(rows) => (
          <Field label={driver.org ? `Veículos da frota ${driver.org.name}` : 'Veículos sem frota'}>
            <select value={sel ?? ''} onChange={(e) => setSel(Number(e.target.value) || null)}>
              <option value="">escolher…</option>
              {rows.map((r) => <option key={r.id} value={r.id} disabled={r.status !== 'active'}>{r.label}{r.status !== 'active' ? ` (${r.status})` : ''}{r.drivers.length ? ` — ${r.drivers.map((x) => x.name).join(', ')}` : ''}</option>)}
            </select>
          </Field>
        )}
      </Gate>
      <p className="muted">Se o veículo estiver com outro motorista, passa para este. <Badge>só veículos ativos</Badge></p>
    </Modal>
  )
}

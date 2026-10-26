import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api } from '../api'
import { eur, km, mins, TRIP_STATE } from '../format'
import { useData } from '../live'
import type { Driver, Product, Quote, Rider, Trip } from '../types'
import { MapView } from '../ui/MapView'
import { AvailBadge, Card, Field, Page, TripBadge, useRun } from '../ui/kit'
import type { LiveMap } from './Dashboard'

type Pt = { lat: number; lng: number; address: string }
type Place = { name: string; lat: number; lng: number }

const NEXT: Record<string, [string, string]> = {
  requested: ['accept', 'Aceitar proposta'],
  accepted: ['arrive', 'Chegou'],
  arrived: ['start', 'Iniciar'],
  in_progress: ['complete', 'Concluir'],
}

export function Simulator() {
  const map = useData<LiveMap>('/map')
  const riders = useData<Rider[]>('/riders', false)
  const catalog = useData<{ products: Product[] }>('/catalog', false)
  const places = useData<Place[]>('/places', false)
  const drivers = useData<Driver[]>('/drivers?status=approved')
  const { run, busy } = useRun()
  const nav = useNavigate()

  const [riderId, setRiderId] = useState<number | ''>('')
  const [productId, setProductId] = useState<number | ''>('')
  const [payment, setPayment] = useState<'cash' | 'card'>('cash')
  const [pickup, setPickup] = useState<Pt | null>(null)
  const [dropoff, setDropoff] = useState<Pt | null>(null)
  const [target, setTarget] = useState<'pickup' | 'dropoff' | 'driver'>('pickup')
  const [moveDriver, setMoveDriver] = useState<number | ''>('')
  const [quote, setQuote] = useState<Quote | null>(null)

  useEffect(() => {
    if (riders.data && riderId === '' && riders.data.length) setRiderId(riders.data[0].id)
  }, [riders.data, riderId])
  useEffect(() => {
    const p = catalog.data?.products.find((x) => x.active)
    if (p && productId === '') setProductId(p.id)
  }, [catalog.data, productId])
  useEffect(() => {
    if (!pickup || !productId) return setQuote(null)
    api.post<{ quote: Quote }[]>('/quote', { product_id: productId, pickup, dropoff }).then((r) => setQuote(r[0]?.quote ?? null)).catch(() => setQuote(null))
  }, [pickup, dropoff, productId])

  const nameFor = (lat: number, lng: number) => {
    const near = places.data?.find((p) => Math.abs(p.lat - lat) < 0.004 && Math.abs(p.lng - lng) < 0.004)
    return near?.name ?? `${lat.toFixed(4)}, ${lng.toFixed(4)}`
  }

  function onMap(lat: number, lng: number) {
    const pt = { lat, lng, address: nameFor(lat, lng) }
    if (target === 'pickup') {
      setPickup(pt)
      setTarget('dropoff')
    } else if (target === 'dropoff') {
      setDropoff(pt)
    } else if (moveDriver) {
      run(() => api.post(`/drivers/${moveDriver}/location`, { lat, lng }), 'Motorista movido')
    }
  }

  const extra = useMemo(() => [
    ...(pickup ? [{ lat: pickup.lat, lng: pickup.lng, color: '#0ea5e9', letter: 'A' }] : []),
    ...(dropoff ? [{ lat: dropoff.lat, lng: dropoff.lng, color: '#111827', letter: 'B' }] : []),
  ], [pickup, dropoff])

  async function request() {
    if (!pickup || !riderId || !productId) return
    const r = await run(() => api.post<{ uuid: string }>('/trips', { rider_id: riderId, product_id: productId, pickup, dropoff, payment }), 'Viagem pedida')
    if (r) {
      setPickup(null)
      setDropoff(null)
      setTarget('pickup')
    }
  }

  const step = (uuid: string, action: string) => run(() => api.post<Trip>(`/trips/${uuid}/action`, { action }))
  const online = (d: Driver) => run(() => api.post(`/drivers/${d.id}/${d.availability === 'offline' ? 'online' : 'offline'}`, {}))

  const activeTrips = map.data?.trips ?? []

  return (
    <Page title="Simulador" sub="Faz o papel do passageiro e dos motoristas sem telemóveis: pede viagens no mapa e avança-as passo a passo. Usa a mesma máquina de estados e despacho que as apps.">
      <div className="sim">
        <Card pad={false} className="sim-map">
          <div className="sim-bar">
            <span>Clique no mapa define:</span>
            <div className="seg">
              <button className={target === 'pickup' ? 'on' : ''} onClick={() => setTarget('pickup')}>A · Recolha</button>
              <button className={target === 'dropoff' ? 'on' : ''} onClick={() => setTarget('dropoff')}>B · Destino</button>
              <button className={target === 'driver' ? 'on' : ''} onClick={() => setTarget('driver')}>Mover motorista</button>
            </div>
            {target === 'driver' && (
              <select value={moveDriver} onChange={(e) => setMoveDriver(Number(e.target.value) || '')} aria-label="Motorista a mover">
                <option value="">escolher…</option>
                {drivers.data?.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
              </select>
            )}
          </div>
          {map.data && (
            <MapView center={map.data.center} height={520} drivers={map.data.drivers} extra={extra} onMapClick={onMap}
              selectedDriver={moveDriver || null} onDriverClick={(id) => { setTarget('driver'); setMoveDriver(id) }}
              trips={activeTrips.map((t) => ({ ...t, label: `${t.rider} · ${TRIP_STATE[t.state as keyof typeof TRIP_STATE]}` }))} />
          )}
          <div className="places">
            {places.data?.map((p) => (
              <button key={p.name} className="chip" onClick={() => onMap(p.lat, p.lng)}>{p.name}</button>
            ))}
          </div>
        </Card>

        <div className="stack">
          <Card title="1 · Pedir viagem">
            <div className="form-grid">
              <Field label="Passageiro">
                <select value={riderId} onChange={(e) => setRiderId(Number(e.target.value))}>
                  {riders.data?.map((r) => <option key={r.id} value={r.id}>{r.name}{r.status === 'blocked' ? ' (bloqueado)' : ''}</option>)}
                </select>
              </Field>
              <Field label="Categoria">
                <select value={productId} onChange={(e) => setProductId(Number(e.target.value))}>
                  {catalog.data?.products.filter((p) => p.active).map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
                </select>
              </Field>
              <Field label="Recolha (A)" wide><input readOnly value={pickup?.address ?? ''} placeholder="clica no mapa" /></Field>
              <Field label="Destino (B)" wide><input readOnly value={dropoff?.address ?? ''} placeholder="opcional" /></Field>
              <Field label="Pagamento">
                <select value={payment} onChange={(e) => setPayment(e.target.value as 'cash' | 'card')}><option value="cash">Dinheiro</option><option value="card">Cartão</option></select>
              </Field>
              <Field label="Estimativa"><output className="quote">{quote ? `${eur(quote.total)} · ${km(quote.distance_m)} · ${mins(quote.duration_s)}` : '—'}</output></Field>
            </div>
            <div className="row-actions">
              <button className="btn" onClick={() => { setPickup(null); setDropoff(null); setTarget('pickup') }}>Limpar</button>
              <button className="btn primary" disabled={!pickup || busy} onClick={request}>Pedir viagem</button>
            </div>
          </Card>

          <Card title="2 · Viagens ativas">
            {activeTrips.length ? (
              <ul className="sim-trips">
                {activeTrips.map((t) => {
                  const nx = NEXT[t.state]
                  return (
                    <li key={t.uuid}>
                      <div>
                        <TripBadge state={t.state as Trip['state']} /> <Link to={`/viagens/${t.uuid}`}>{t.rider}</Link>
                        <small className="muted ellipsis">{t.pickup_address} → {t.dropoff_address || '—'}</small>
                      </div>
                      <div className="row-actions">
                        {nx && <button className="btn sm primary" disabled={busy} onClick={() => step(t.uuid, nx[0])}>{nx[1]}</button>}
                        <button className="btn sm" onClick={() => nav(`/viagens/${t.uuid}`)}>Abrir</button>
                      </div>
                    </li>
                  )
                })}
              </ul>
            ) : <p className="muted">Sem viagens ativas.</p>}
          </Card>

          <Card title="3 · Motoristas de teste">
            <ul className="sim-drivers">
              {drivers.data?.map((d) => (
                <li key={d.id}>
                  <div><Link to={`/motoristas/${d.id}`}>{d.name}</Link> <AvailBadge a={d.availability} />
                    <small className="muted">{d.vehicle?.label ?? 'sem veículo'}{d.simulated ? '' : ' · posição da app'}</small></div>
                  <button className="btn sm" disabled={busy || d.availability === 'on_trip' || !d.vehicle} onClick={() => online(d)}>
                    {d.availability === 'offline' ? 'Pôr online' : 'Pôr offline'}
                  </button>
                </li>
              ))}
            </ul>
            <p className="hint">Os motoristas simulados andam sozinhos até à recolha e ao destino (Definições → “Simular movimento”).</p>
          </Card>
        </div>
      </div>
    </Page>
  )
}

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { dayLabel, eur } from '../format'
import { useData } from '../live'
import type { TripRow } from '../types'
import { Bars } from '../ui/Bars'
import { MapView, type MapDriver } from '../ui/MapView'
import { Card, Gate, Page, Stat, Tabs } from '../ui/kit'
import { TripTable } from './Trips'

type Dash = {
  kpis: Record<string, number | null>
  days: { day: number; trips: number; gross: number }[]
  by_product: { name: string; trips: number; gross: number }[]
  top_drivers: { id: number; name: string; trips: number; gross: number }[]
  recent: TripRow[]
}
export type LiveMap = {
  center: [number, number]
  drivers: (MapDriver & { status: string; simulated: boolean; location_at: number | null })[]
  trips: { uuid: string; state: string; pickup: [number, number]; dropoff: [number, number] | null; driver_id: number | null; rider: string; pickup_address: string; dropoff_address: string }[]
}

export function Dashboard() {
  const d = useData<Dash>('/dashboard')
  const map = useData<LiveMap>('/map')
  const [series, setSeries] = useState<'gross' | 'trips'>('gross')
  const nav = useNavigate()

  return (
    <Page title="Painel" sub="Estado da operação agora e nos últimos 14 dias">
      <Gate d={d}>
        {(x) => {
          const k = x.kpis as Record<string, number>
          return (
            <>
              <div className="stats">
                <Stat label="Viagens hoje" value={k.trips_today} hint={`${k.completed_today} concluídas · ${k.cancelled_today} canceladas`} />
                <Stat label="Faturação hoje" value={eur(k.gross_today)} hint={`comissão ${eur(k.commission_today)}`} tone="ok" />
                <Stat label="Viagens ativas" value={k.active_trips} hint={k.searching_trips ? `${k.searching_trips} à procura de motorista` : 'nenhuma à espera'} tone={k.searching_trips ? 'warn' : undefined} />
                <Stat label="Motoristas" value={`${k.drivers_online + k.drivers_on_trip} / ${k.drivers_total}`} hint={`${k.drivers_online} disponíveis · ${k.drivers_on_trip} em viagem`} />
                <Stat label="Por aprovar" value={k.drivers_pending + k.docs_pending} hint={<Link to="/documentos">{k.docs_pending} documentos · {k.drivers_pending} motoristas</Link>} tone={k.docs_pending ? 'warn' : undefined} />
              </div>

              <div className="grid-2-1">
                <Card title="Mapa ao vivo" actions={<span className="legend"><i className="lg-online" />disponível <i className="lg-trip" />em viagem <i className="lg-off" />offline</span>} pad={false}>
                  {map.data ? (
                    <MapView center={map.data.center} drivers={map.data.drivers} height={380}
                      trips={map.data.trips.map((t) => ({ ...t, label: `${t.rider} · ${t.pickup_address}` }))}
                      onDriverClick={(id) => nav(`/motoristas/${id}`)} />
                  ) : <div className="map" style={{ height: 380 }} />}
                </Card>
                <Card title="Hoje por categoria">
                  {x.by_product.length ? (
                    <table className="table compact">
                      <thead><tr><th>Categoria</th><th className="num">Viagens</th><th className="num">Faturação</th></tr></thead>
                      <tbody>{x.by_product.map((p) => <tr key={p.name}><td>{p.name}</td><td className="num">{p.trips}</td><td className="num">{eur(p.gross)}</td></tr>)}</tbody>
                    </table>
                  ) : <p className="muted">Ainda sem viagens concluídas hoje.</p>}
                  <h3 className="sub-head">Top motoristas (7 dias)</h3>
                  <ol className="rank">
                    {x.top_drivers.map((t) => (
                      <li key={t.id}><Link to={`/motoristas/${t.id}`}>{t.name}</Link><span>{t.trips} viagens · {eur(t.gross)}</span></li>
                    ))}
                  </ol>
                </Card>
              </div>

              <Card title="Últimos 14 dias" actions={<Tabs value={series} onChange={setSeries} items={[['gross', 'Faturação'], ['trips', 'Viagens']]} />}>
                <Bars data={x.days.map((p) => ({ label: dayLabel(p.day), value: series === 'gross' ? p.gross : p.trips, sub: series === 'gross' ? `${p.trips} viagens` : eur(p.gross) }))}
                  format={(v) => (series === 'gross' ? eur(Math.round(v)) : String(Math.round(v)))} />
              </Card>

              <Card title="Viagens recentes" actions={<Link className="btn sm" to="/viagens">Ver todas</Link>} pad={false}>
                <TripTable rows={x.recent} />
              </Card>
            </>
          )
        }}
      </Gate>
    </Page>
  )
}

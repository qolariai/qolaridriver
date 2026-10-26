import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { qs } from '../api'
import { dateTime, eur, TRIP_STATE } from '../format'
import { useData } from '../live'
import type { TripRow, TripState } from '../types'
import { Badge, Card, Empty, Gate, Icon, Page, TripBadge } from '../ui/kit'

export function TripTable({ rows, hide = [] }: { rows: TripRow[]; hide?: ('rider' | 'driver')[] }) {
  const nav = useNavigate()
  if (!rows.length) return <Empty>Sem viagens.</Empty>
  return (
    <div className="table-wrap">
      <table className="table hover">
        <thead>
          <tr>
            <th>Pedida</th><th>Estado</th><th>Percurso</th>
            {!hide.includes('rider') && <th>Passageiro</th>}
            {!hide.includes('driver') && <th>Motorista</th>}
            <th>Categoria</th><th className="num">Valor</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((t) => (
            <tr key={t.uuid} onClick={() => nav(`/viagens/${t.uuid}`)}>
              <td className="nowrap">{dateTime(t.requested_at)}</td>
              <td><TripBadge state={t.state} /></td>
              <td className="route-cell">
                <span className="ellipsis">{t.pickup_address || 'Recolha'}</span>
                <span className="ellipsis muted">→ {t.dropoff_address || 'sem destino'}</span>
              </td>
              {!hide.includes('rider') && <td className="nowrap">{t.rider?.name ?? '—'}</td>}
              {!hide.includes('driver') && <td className="nowrap">{t.driver?.name ?? <span className="muted">—</span>}</td>}
              <td className="nowrap">{t.product.name}{t.source === 'console' && <> <Badge>simulada</Badge></>}</td>
              <td className="num nowrap">{t.fare != null ? eur(t.fare) : <span className="muted">~{eur(t.est_fare)}</span>}{t.payment_method === 'cash' ? ' 💶' : ''}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const FILTERS: [string, string][] = [['', 'Todas'], ['active', 'Ativas'], ...(Object.entries(TRIP_STATE) as [TripState, string][])]

export function Trips() {
  const [state, setState] = useState('')
  const [q, setQ] = useState('')
  const [page, setPage] = useState(1)
  const [dayFrom, setDayFrom] = useState('')
  const [dayTo, setDayTo] = useState('')
  const size = 25
  const d = useData<{ total: number; items: TripRow[] }>(`/trips${qs({ state, q, page, size, day_from: dayFrom, day_to: dayTo })}`)

  return (
    <Page title="Viagens" sub="Todas as viagens pedidas na app Rider ou criadas no simulador"
      actions={<Link className="btn primary" to="/simulador"><Icon name="plus" /> Nova viagem</Link>}>
      <div className="toolbar">
        <div className="chips">
          {FILTERS.map(([k, label]) => (
            <button key={k} className={`chip ${state === k ? 'on' : ''}`} onClick={() => { setState(k); setPage(1) }}>{label}</button>
          ))}
        </div>
        <div className="toolbar-right">
          <input type="date" value={dayFrom} onChange={(e) => { setDayFrom(e.target.value); setPage(1) }} aria-label="De" />
          <input type="date" value={dayTo} onChange={(e) => { setDayTo(e.target.value); setPage(1) }} aria-label="Até" />
          <div className="search"><Icon name="search" /><input placeholder="Morada ou ID" value={q} onChange={(e) => { setQ(e.target.value); setPage(1) }} /></div>
        </div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => (
            <>
              <TripTable rows={x.items} />
              <div className="pager">
                <span className="muted">{x.total} viagens</span>
                <button className="btn sm" disabled={page <= 1} onClick={() => setPage(page - 1)}>Anterior</button>
                <span>{page} / {Math.max(1, Math.ceil(x.total / size))}</span>
                <button className="btn sm" disabled={page * size >= x.total} onClick={() => setPage(page + 1)}>Seguinte</button>
              </div>
            </>
          )}
        </Gate>
      </Card>
    </Page>
  )
}

import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api, qs } from '../api'
import { ago } from '../format'
import { can, useAuth, useData } from '../live'
import type { MapReport } from '../types'
import { Badge, Card, Empty, Gate, Icon, Page, Tabs, useRun } from '../ui/kit'

const TONE = { open: 'warn', resolved: 'ok', dismissed: 'muted' } as const
const LABEL = { open: 'Aberto', resolved: 'Resolvido', dismissed: 'Ignorado' } as const

export function MapReports() {
  const [status, setStatus] = useState<'open' | 'resolved' | 'dismissed' | ''>('open')
  const d = useData<{ total: number; items: MapReport[] }>(`/map-reports${qs({ status })}`)
  const { user } = useAuth()
  const { run, busy } = useRun()
  const ops = can(user, 'operator')

  const setReport = (r: MapReport, next: 'open' | 'resolved' | 'dismissed') =>
    run(() => api.patch(`/map-reports/${r.id}`, { status: next }), 'Estado atualizado').then(() => d.reload())

  return (
    <Page
      title="Problemas de mapa"
      sub="Registos enviados pelos motoristas no mapa. Triagem do suporte/operação."
      actions={<button className="btn" onClick={d.reload}><Icon name="refresh" size={14} /> Atualizar</button>}
    >
      <div className="toolbar">
        <Tabs
          value={status}
          onChange={setStatus}
          items={[['open', 'Abertos'], ['resolved', 'Resolvidos'], ['dismissed', 'Ignorados'], ['', 'Todos']]}
        />
        <div className="toolbar-right muted">{d.data?.total ?? 0} registo(s)</div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => x.items.length ? (
            <div className="table-wrap">
              <table className="table">
                <thead>
                  <tr><th>Motorista</th><th>Motivo</th><th>Detalhe</th><th>Local</th><th>Quando</th><th>Estado</th><th></th></tr>
                </thead>
                <tbody>
                  {x.items.map((r) => (
                    <tr key={r.id}>
                      <td>
                        {r.driver
                          ? <Link to={`/motoristas/${r.driver.id}`}>{r.driver.name}</Link>
                          : <span className="muted">—</span>}
                        {r.driver && <small className="muted block">{r.driver.phone}</small>}
                      </td>
                      <td>{r.reason_label || r.reason}</td>
                      <td className="muted">{r.note || '—'}</td>
                      <td>
                        {r.latitude != null && r.longitude != null
                          ? <a href={`https://www.google.com/maps?q=${r.latitude},${r.longitude}`} target="_blank" rel="noreferrer" className="mono">{r.latitude.toFixed(4)}, {r.longitude.toFixed(4)}</a>
                          : <span className="muted">—</span>}
                      </td>
                      <td>{ago(r.created_at)}</td>
                      <td><Badge tone={TONE[r.status]}>{LABEL[r.status]}</Badge></td>
                      <td className="row-actions nowrap">
                        {ops && r.status !== 'resolved' && <button className="btn sm primary" disabled={busy} onClick={() => setReport(r, 'resolved')}>Resolver</button>}
                        {ops && r.status !== 'open' && <button className="btn sm" disabled={busy} onClick={() => setReport(r, 'open')}>Reabrir</button>}
                        {ops && r.status !== 'dismissed' && <button className="btn sm" disabled={busy} onClick={() => setReport(r, 'dismissed')}>Ignorar</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty>Sem problemas de mapa {status === 'open' ? 'abertos.' : 'neste estado.'}</Empty>}
        </Gate>
      </Card>
    </Page>
  )
}

import { useState } from 'react'
import { api, authHeaders } from '../api'
import { ago } from '../format'
import { useData } from '../live'
import type { Recording, SafetyIncident } from '../types'
import { Badge, Card, Empty, Gate, Page, Tabs, useRun } from '../ui/kit'

async function openRecording(uuid: string) {
  const r = await fetch(`/api/recordings/${uuid}/file`, { headers: authHeaders() })
  if (!r.ok) throw new Error('gravação indisponível')
  window.open(URL.createObjectURL(await r.blob()), '_blank')
}

export function Safety() {
  const [status, setStatus] = useState<'open' | 'closed' | ''>('open')
  const d = useData<{ items: SafetyIncident[] }>(`/safety${status ? `?status=${status}` : ''}`)
  const rec = useData<{ items: Recording[] }>('/recordings')
  const { run, busy } = useRun()

  const close = (i: SafetyIncident) => {
    if (!confirm(`Fechar o alerta de ${i.subjectName}?`)) return
    run(() => api.patch(`/safety/${i.uuid}`, { status: 'closed' }), 'Alerta fechado').then(() => d.reload())
  }

  return (
    <Page title="Segurança" sub="Alertas SOS e contactos de confiança das apps.">
      <div className="toolbar">
        <Tabs value={status} onChange={setStatus} items={[['open', 'Abertos'], ['closed', 'Fechados'], ['', 'Todos']]} />
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => x.items.length ? (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Conta</th><th>App</th><th>Alerta</th><th>Viagem</th><th>Contactos</th><th>Quando</th><th>Estado</th><th></th></tr></thead>
              <tbody>{x.items.map((i) => (
                <tr key={i.uuid}>
                  <td>{i.subjectName}<small className="muted block">{i.subjectPhone}</small></td>
                  <td>{i.app}</td>
                  <td>{i.kind === 'sos' ? 'SOS' : i.kind}<small className="muted block">{i.note}</small></td>
                  <td>{i.tripUuid ? <code>{i.tripUuid.slice(0, 8)}</code> : '—'}
                    {i.latitude != null && <small className="muted block">{i.latitude.toFixed(4)}, {i.longitude?.toFixed(4)}</small>}</td>
                  <td>{i.contacts.length ? i.contacts.map((c) => <small className="block" key={c.phone}>{c.name} · {c.phone}</small>) : <span className="muted">sem contactos</span>}</td>
                  <td>{ago(i.createdAt)}</td>
                  <td><Badge tone={i.status === 'open' ? 'warn' : 'ok'}>{i.status}</Badge></td>
                  <td>{i.status === 'open' && <button className="btn sm" disabled={busy} onClick={() => close(i)}>Fechar</button>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <Empty>Sem alertas {status === 'open' ? 'abertos.' : '.'}</Empty>}
        </Gate>
      </Card>

      <Card title="Gravações de viagem" pad={false}>
        <Gate d={rec}>
          {(x) => x.items.length ? (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Motorista</th><th>Viagem</th><th>Tipo</th><th>Duração</th><th>Quando</th><th></th></tr></thead>
              <tbody>{x.items.map((r) => (
                <tr key={r.uuid}>
                  <td>{r.driver || '—'}</td>
                  <td><code>{r.trip_uuid.slice(0, 8)}</code></td>
                  <td>{r.kind}</td>
                  <td>{r.duration_s}s</td>
                  <td>{ago(r.started_at)}</td>
                  <td>{r.has_file && <button className="btn sm" onClick={() => run(() => openRecording(r.uuid), 'A abrir gravação')}>Ouvir</button>}</td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <Empty>Sem gravações.</Empty>}
        </Gate>
      </Card>
    </Page>
  )
}

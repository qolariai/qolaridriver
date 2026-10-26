import { useState } from 'react'
import { api, qs } from '../api'
import { ago } from '../format'
import { useData } from '../live'
import type { Adjustment } from '../types'
import { Badge, Card, Empty, Gate, Page, Tabs, useRun } from '../ui/kit'

const money = (cents: number) =>
  new Intl.NumberFormat('pt-PT', { style: 'currency', currency: 'EUR' }).format(cents / 100)

const KIND: Record<string, string> = {
  tolls: 'Portagens',
  manual_fare: 'Tarifa manual',
  other: 'Outro',
}

export function Adjustments() {
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | ''>('pending')
  const d = useData<{ items: Adjustment[] }>(`/adjustments${qs({ status })}`)
  const { run, busy } = useRun()

  const review = (a: Adjustment, value: 'approved' | 'rejected') => {
    if (value === 'rejected' && !confirm(`Recusar o ajuste de ${a.driver}?`)) return
    run(() => api.patch(`/adjustments/${a.uuid}`, { status: value }), value === 'approved' ? 'Ajuste aprovado' : 'Ajuste recusado')
      .then(() => d.reload())
  }

  return (
    <Page title="Ajustes" sub="Portagens, tarifa manual e acertos pedidos pelos motoristas.">
      <div className="toolbar">
        <Tabs value={status} onChange={setStatus} items={[['pending', 'Pendentes'], ['approved', 'Aprovados'], ['rejected', 'Recusados'], ['', 'Todos']]} />
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => x.items.length ? (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Motorista</th><th>Tipo</th><th>Valor</th><th>Viagem</th><th>Nota</th><th>Quando</th><th>Estado</th><th></th></tr></thead>
              <tbody>{x.items.map((a) => (
                <tr key={a.uuid}>
                  <td>{a.driver}</td>
                  <td>{KIND[a.kind] ?? a.kind}</td>
                  <td className="mono">{money(a.amount)}</td>
                  <td>{a.trip_uuid ? <code>{a.trip_uuid.slice(0, 8)}</code> : '—'}</td>
                  <td>{a.note || '—'}</td>
                  <td>{ago(a.created_at)}</td>
                  <td><Badge tone={a.status === 'pending' ? 'warn' : a.status === 'approved' ? 'ok' : 'bad'}>{a.status}</Badge></td>
                  <td className="row-actions nowrap">
                    {a.status === 'pending' && (
                      <>
                        <button className="btn sm primary" disabled={busy} onClick={() => review(a, 'approved')}>Aprovar</button>
                        <button className="btn sm" disabled={busy} onClick={() => review(a, 'rejected')}>Recusar</button>
                      </>
                    )}
                  </td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <Empty>Sem ajustes {status === 'pending' ? 'pendentes.' : '.'}</Empty>}
        </Gate>
      </Card>
    </Page>
  )
}

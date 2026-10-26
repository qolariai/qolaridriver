import { useState } from 'react'
import { api, authHeaders, qs } from '../api'
import { ago } from '../format'
import { useData } from '../live'
import type { SupportMessage, SupportThread } from '../types'
import { Badge, Card, Empty, Gate, Page, Tabs, useRun } from '../ui/kit'

async function openAttachment(name: string) {
  const r = await fetch(`/api/support/attachment/${encodeURIComponent(name)}`, { headers: authHeaders() })
  if (!r.ok) throw new Error('anexo indisponível')
  window.open(URL.createObjectURL(await r.blob()), '_blank')
}

async function openScreenFrame(share: string) {
  const r = await fetch(`/api/support/screen-share/${encodeURIComponent(share)}/frame`, { headers: authHeaders() })
  if (!r.ok) throw new Error('ecrã indisponível')
  window.open(URL.createObjectURL(await r.blob()), '_blank')
}

export function Support() {
  const [status, setStatus] = useState<'open' | 'closed' | ''>('open')
  const [open, setOpen] = useState<SupportThread | null>(null)
  const d = useData<{ items: SupportThread[] }>(`/support${qs({ status })}`)
  return (
    <Page title="Suporte" sub="Conversas das apps com a operação.">
      <div className="toolbar">
        <Tabs value={status} onChange={setStatus} items={[['open', 'Abertas'], ['closed', 'Fechadas'], ['', 'Todas']]} />
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => x.items.length ? (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Conta</th><th>App</th><th>Categoria</th><th>Última</th><th>Estado</th><th></th></tr></thead>
              <tbody>{x.items.map((t) => (
                <tr key={t.uuid}>
                  <td>{t.name}<small className="muted block">{t.phone}</small></td>
                  <td>{t.app}</td><td>{t.category}</td>
                  <td>{t.last_message}<small className="muted block">{ago(t.updated_at)}</small></td>
                  <td><Badge tone={t.status === 'open' ? 'warn' : 'ok'}>{t.status}</Badge>{t.unread > 0 && <small className="block">{t.unread} nova(s)</small>}</td>
                  <td><button className="btn sm" onClick={() => setOpen(t)}>Abrir</button></td>
                </tr>
              ))}</tbody>
            </table></div>
          ) : <Empty>Sem conversas {status === 'open' ? 'abertas.' : '.'}</Empty>}
        </Gate>
      </Card>
      {open && <Thread t={open} onClose={() => { setOpen(null); d.reload() }} />}
    </Page>
  )
}

function Thread({ t, onClose }: { t: SupportThread; onClose: () => void }) {
  const detail = useData<{ thread: unknown; messages: SupportMessage[] }>(`/support/${t.uuid}`, false)
  const share = useData<{ active: boolean; uuid?: string; has_frame?: boolean }>(`/support/${t.uuid}/screen-share`)
  const { run, busy } = useRun()
  const [text, setText] = useState('')
  const send = () => {
    if (!text.trim()) return
    run(() => api.post(`/support/${t.uuid}/reply`, { message: text }), 'Resposta enviada')
      .then(() => { setText(''); detail.reload() })
  }
  return (
    <Card title={`${t.name} · ${t.app}`} actions={
      <>
        {share.data?.active && share.data.has_frame && share.data.uuid &&
          <button className="btn sm" onClick={() => run(() => openScreenFrame(share.data!.uuid!), 'A abrir ecrã')}>Ver ecrã</button>}
        <button className="btn sm" onClick={onClose}>Fechar</button>
      </>
    }>
      <Gate d={detail}>
        {(x) => <div className="chat">{x.messages.map((m) => (
          <div key={m.id} className={`chat-row ${m.sender}`}>
            <span>{m.body}</span>
            {m.fileName && <button className="btn sm" onClick={() => run(() => openAttachment(m.fileName!), 'A abrir anexo')}>Anexo</button>}
            <small>{ago(m.createdAt)}</small>
          </div>
        ))}</div>}
      </Gate>
      <div className="row-actions" style={{ marginTop: 12 }}>
        <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Responder ao utilizador" style={{ flex: 1 }} />
        <button className="btn primary" disabled={busy} onClick={send}>Enviar</button>
      </div>
    </Card>
  )
}

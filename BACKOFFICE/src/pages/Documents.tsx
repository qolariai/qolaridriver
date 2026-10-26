import { useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, authHeaders, qs } from '../api'
import { ago, DOC_KIND } from '../format'
import { can, useAuth, useData } from '../live'
import type { Doc } from '../types'
import { Badge, Card, Empty, Gate, Icon, Page, Tabs, useRun } from '../ui/kit'

const TONE = { pending: 'warn', approved: 'ok', rejected: 'bad' } as const
const LABEL = { pending: 'Pendente', approved: 'Aprovado', rejected: 'Recusado' } as const

async function openFile(id: number) {
  // o ficheiro precisa do token: descarregar com fetch autenticado e abrir como blob
  const r = await fetch(`/api/documents/${id}/file`, { headers: authHeaders() })
  if (!r.ok) throw new Error('ficheiro indisponível')
  window.open(URL.createObjectURL(await r.blob()), '_blank')
}

export function DocRow({ doc, onChange, hideOwner }: { doc: Doc; onChange: () => void; hideOwner?: boolean }) {
  const { user } = useAuth()
  const { run, busy } = useRun()
  const file = useRef<HTMLInputElement>(null)
  const ops = can(user, 'operator')
  const expired = doc.expires_on && doc.expires_on < new Date().toISOString().slice(0, 10)
  const review = (status: string) => {
    const notes = status === 'rejected' ? window.prompt('Motivo da recusa (o motorista vê isto)') ?? '' : undefined
    if (status === 'rejected' && !notes) return
    run(() => api.patch(`/documents/${doc.id}`, { status, notes }), status === 'approved' ? 'Aprovado' : 'Recusado').then(onChange)
  }
  const upload = (f: File) => run(() => api.put(`/documents/${doc.id}/file`, f), 'Ficheiro guardado').then(onChange)

  return (
    <tr>
      {!hideOwner && (
        <td>
          <Link to={doc.owner_type === 'driver' ? `/motoristas/${doc.owner_id}` : '/veiculos'}>{doc.owner_name}</Link>
          <small className="muted block">{doc.owner_type === 'driver' ? 'Motorista' : 'Veículo'}</small>
        </td>
      )}
      <td>{DOC_KIND[doc.kind] ?? doc.kind}{doc.notes && <small className="muted block">{doc.notes}</small>}</td>
      <td className="mono">{doc.number || '—'}</td>
      <td className={expired ? 'neg' : ''}>{doc.expires_on ?? '—'}{expired && ' (expirado)'}</td>
      <td><Badge tone={TONE[doc.status]}>{LABEL[doc.status]}</Badge>{doc.reviewed_by && <small className="muted block">{doc.reviewed_by} · {ago(doc.reviewed_at)}</small>}</td>
      <td className="row-actions nowrap">
        {doc.has_file && <button className="btn sm" onClick={() => run(() => openFile(doc.id))}><Icon name="eye" size={14} /> Ver</button>}
        {ops && (
          <>
            <button className="btn sm" onClick={() => file.current?.click()} title="Enviar ficheiro"><Icon name="upload" size={14} /></button>
            <input ref={file} type="file" accept="image/jpeg,image/png,image/webp,application/pdf" hidden onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            {doc.status !== 'approved' && <button className="btn sm primary" disabled={busy} onClick={() => review('approved')}>Aprovar</button>}
            {doc.status !== 'rejected' && <button className="btn sm" disabled={busy} onClick={() => review('rejected')}>Recusar</button>}
          </>
        )}
      </td>
    </tr>
  )
}

export function Documents() {
  const [status, setStatus] = useState<'pending' | 'approved' | 'rejected' | ''>('pending')
  const [owner, setOwner] = useState('')
  const d = useData<{ items: Doc[] }>(`/documents${qs({ status, owner_type: owner })}`)
  return (
    <Page title="Documentos" sub="Verificação de motoristas e veículos. Motorista novo só fica ativo depois de aprovado.">
      <div className="toolbar">
        <Tabs value={status} onChange={setStatus} items={[['pending', 'Pendentes'], ['approved', 'Aprovados'], ['rejected', 'Recusados'], ['', 'Todos']]} />
        <div className="toolbar-right">
          <select value={owner} onChange={(e) => setOwner(e.target.value)} aria-label="Tipo"><option value="">Motoristas e veículos</option><option value="driver">Motoristas</option><option value="vehicle">Veículos</option></select>
        </div>
      </div>
      <Card pad={false}>
        <Gate d={d}>
          {(x) => x.items.length ? (
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Dono</th><th>Documento</th><th>N.º</th><th>Validade</th><th>Estado</th><th></th></tr></thead>
                <tbody>{x.items.map((doc) => <DocRow key={doc.id} doc={doc} onChange={d.reload} />)}</tbody>
              </table>
            </div>
          ) : <Empty>Nada por aqui{status === 'pending' ? ' — tudo verificado.' : '.'}</Empty>}
        </Gate>
      </Card>
    </Page>
  )
}

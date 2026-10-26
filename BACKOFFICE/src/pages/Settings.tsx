import { useEffect, useState } from 'react'
import { api } from '../api'
import { ago, APP_LABEL, dateTime } from '../format'
import { can, useAuth, useData } from '../live'
import type { Admin, Device, Session } from '../types'
import { Badge, Card, Empty, Field, Gate, Modal, Page, Switch, Tabs, useRun } from '../ui/kit'

type SettingsResp = { values: Record<string, number | boolean | string>; labels: Record<string, string>; otp_code: string; public_host: string; ports: Record<string, number> }

export function Settings() {
  const [tab, setTab] = useState<'params' | 'admins' | 'sessions' | 'devices' | 'push' | 'audit'>('params')
  const { user } = useAuth()
  return (
    <Page title="Definições" sub="Parâmetros da plataforma, acessos à consola e ligação das apps">
      <Tabs value={tab} onChange={setTab} items={[
        ['params', 'Parâmetros'], ...(can(user) ? [['admins', 'Administradores'] as ['admins', string]] : []),
        ['sessions', 'Sessões das apps'], ['devices', 'Dispositivos'], ['push', 'Mensagens para as apps'], ['audit', 'Registo de ações'],
      ]} />
      {tab === 'params' && <Params />}
      {tab === 'admins' && <Admins />}
      {tab === 'sessions' && <Sessions />}
      {tab === 'devices' && <Devices />}
      {tab === 'push' && <Push />}
      {tab === 'audit' && <Audit />}
    </Page>
  )
}

function Params() {
  const d = useData<SettingsResp>('/settings', false)
  const { user } = useAuth()
  const admin = can(user)
  const [vals, setVals] = useState<Record<string, number | boolean | string>>({})
  const { run, busy } = useRun()
  useEffect(() => { if (d.data) setVals(d.data.values) }, [d.data])
  const save = () => run(() => api.patch('/settings', Object.fromEntries(Object.entries(vals).map(([k, v]) => [k, typeof d.data!.values[k] === 'number' ? Number(String(v).replace(',', '.')) : v]))), 'Parâmetros guardados')
  return (
    <Gate d={d}>
      {(x) => (
        <div className="grid-2-1">
          <Card title="Operação" actions={admin && <button className="btn primary sm" disabled={busy} onClick={save}>Guardar</button>}>
            <div className="form-grid">
              {Object.entries(x.labels).map(([k, label]) => {
                const v = vals[k]
                return typeof x.values[k] === 'boolean' ? (
                  <div key={k} className="field switch-field"><span className="field-label">{label}</span><Switch checked={!!v} label={label} disabled={!admin} onChange={(nv) => setVals({ ...vals, [k]: nv })} /></div>
                ) : (
                  <Field key={k} label={label}><input value={String(v ?? '')} disabled={!admin} onChange={(e) => setVals({ ...vals, [k]: e.target.value })} /></Field>
                )
              })}
            </div>
          </Card>
          <Card title="Ligação">
            <dl className="kv">
              <dt>IP nas APKs</dt><dd className="mono">{x.public_host}</dd>
              <dt>Driver</dt><dd className="mono">porta {x.ports.driver}</dd>
              <dt>Rider</dt><dd className="mono">porta {x.ports.rider}</dd>
              <dt>Fleet</dt><dd className="mono">porta {x.ports.fleet}</dd>
              <dt>Consola</dt><dd className="mono">porta {x.ports.console}</dd>
              <dt>Código de login</dt><dd className="mono">{x.otp_code}</dd>
            </dl>
            <p className="muted">Portas e código mudam-se por variáveis de ambiente (BACKEND/config.py).</p>
          </Card>
        </div>
      )}
    </Gate>
  )
}

function Admins() {
  const d = useData<Admin[]>('/admins')
  const { user } = useAuth()
  const { run } = useRun()
  const [open, setOpen] = useState(false)
  const ROLE = { admin: 'Administrador', operator: 'Operador', finance: 'Financeiro' }
  return (
    <Card title="Administradores da consola" actions={<button className="btn sm primary" onClick={() => setOpen(true)}>Adicionar</button>} pad={false}>
      <Gate d={d}>
        {(rows) => (
          <table className="table">
            <thead><tr><th>Utilizador</th><th>Papel</th><th>Último login</th><th>Ativo</th></tr></thead>
            <tbody>{rows.map((a) => (
              <tr key={a.id}><td><strong>{a.name || a.email}</strong><small className="muted block">{a.email}</small></td>
                <td><select value={a.role} disabled={a.id === user?.id} onChange={(e) => run(() => api.patch(`/admins/${a.id}`, { role: e.target.value }), 'Guardado').then(d.reload)}>
                  {Object.entries(ROLE).map(([k, v]) => <option key={k} value={k}>{v}</option>)}</select></td>
                <td className="muted">{ago(a.last_login_at)}</td>
                <td><Switch checked={a.active} label="Ativo" disabled={a.id === user?.id} onChange={(v) => run(() => api.patch(`/admins/${a.id}`, { active: v })).then(d.reload)} /></td></tr>
            ))}</tbody>
          </table>
        )}
      </Gate>
      <p className="muted pad">Operador: viagens, motoristas, frotas, documentos, simulador. Financeiro: leitura + pagamentos. Administrador: tudo.</p>
      {open && <AdminForm onClose={() => setOpen(false)} onSaved={() => { setOpen(false); d.reload() }} />}
    </Card>
  )
}

function AdminForm({ onClose, onSaved }: { onClose: () => void; onSaved: () => void }) {
  const [f, setF] = useState({ email: '', name: '', role: 'operator', password: '' })
  const { run, busy } = useRun()
  return (
    <Modal title="Novo administrador" onClose={onClose}
      footer={<><button className="btn" onClick={onClose}>Cancelar</button><button className="btn primary" disabled={busy || !f.email || f.password.length < 6} onClick={() => run(() => api.post('/admins', f), 'Criado').then((r) => r && onSaved())}>Criar</button></>}>
      <div className="form-grid">
        <Field label="Email"><input type="email" value={f.email} onChange={(e) => setF({ ...f, email: e.target.value })} autoFocus /></Field>
        <Field label="Nome"><input value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} /></Field>
        <Field label="Papel"><select value={f.role} onChange={(e) => setF({ ...f, role: e.target.value })}><option value="operator">Operador</option><option value="finance">Financeiro</option><option value="admin">Administrador</option></select></Field>
        <Field label="Palavra-passe inicial" hint="mín. 6 caracteres"><input type="password" value={f.password} onChange={(e) => setF({ ...f, password: e.target.value })} /></Field>
      </div>
    </Modal>
  )
}

export function SessionTable({ rows, onChange }: { rows: Session[]; onChange: () => void }) {
  const { user } = useAuth()
  const { run } = useRun()
  if (!rows.length) return <Empty>Sem sessões.</Empty>
  return (
    <div className="table-wrap">
      <table className="table compact">
        <thead><tr><th>App</th><th>Utilizador</th><th>Início</th><th>Uso</th><th>IP</th><th></th></tr></thead>
        <tbody>{rows.map((s) => (
          <tr key={s.id}><td><Badge tone={s.app}>{APP_LABEL[s.app]}</Badge></td><td>{s.subject_name ?? s.subject_uuid.slice(0, 8)}</td>
            <td className="nowrap">{dateTime(s.created_at)}</td><td className="muted nowrap">{ago(s.last_used_at)}</td><td className="mono">{s.ip}</td>
            <td>{s.revoked ? <Badge>terminada</Badge> : can(user, 'operator') && <button className="btn sm" onClick={() => run(() => api.post(`/sessions/${s.id}/revoke`), 'Sessão terminada').then(onChange)}>Terminar</button>}</td></tr>
        ))}</tbody>
      </table>
    </div>
  )
}

function Sessions() {
  const [app, setApp] = useState('')
  const d = useData<Session[]>(`/sessions${app ? `?app=${app}` : ''}`)
  return (
    <Card title="Sessões das apps" actions={<select value={app} onChange={(e) => setApp(e.target.value)} aria-label="App"><option value="">Todas</option><option value="rider">Rider</option><option value="driver">Driver</option><option value="fleet">Fleet</option></select>} pad={false}>
      <Gate d={d}>{(rows) => <SessionTable rows={rows} onChange={d.reload} />}</Gate>
    </Card>
  )
}

function Devices() {
  const d = useData<Device[]>('/devices')
  return (
    <Card title="Dispositivos que falaram com o backend" pad={false}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <table className="table compact">
            <thead><tr><th>App</th><th>Aparelho</th><th>Utilizador</th><th>Versões</th><th>Push</th><th>IP</th><th>Visto</th></tr></thead>
            <tbody>{rows.map((v) => (
              <tr key={v.id}><td><Badge tone={v.app}>{APP_LABEL[v.app]}</Badge></td><td>{v.model || <span className="mono">{v.device_key.slice(0, 16)}</span>}</td>
                <td>{v.subject_name || '—'}</td><td className="muted">Android {v.os_version || '?'} · app {v.app_version || '?'}</td>
                <td>{v.has_push_token ? 'sim' : '—'}</td><td className="mono">{v.ip}</td><td className="muted">{ago(v.last_seen_at)}</td></tr>
            ))}</tbody>
          </table>
        ) : <Empty>Nenhum telemóvel registado ainda.</Empty>}
      </Gate>
    </Card>
  )
}

function Push() {
  const d = useData<{ id: number; app: string; subject: string; topic: string; payload: unknown; created_at: number; delivered_at: number | null }[]>('/push')
  return (
    <Card title="Mensagens enviadas às apps (canal ramen)" pad={false}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <table className="table compact">
            <thead><tr><th>Hora</th><th>App</th><th>Para</th><th>Tópico</th><th>Conteúdo</th><th>Entregue</th></tr></thead>
            <tbody>{rows.map((m) => (
              <tr key={m.id}><td className="nowrap">{dateTime(m.created_at)}</td><td>{m.app}</td><td>{m.subject}</td><td className="mono">{m.topic}</td>
                <td className="mono small ellipsis-cell">{JSON.stringify(m.payload)}</td><td>{m.delivered_at ? ago(m.delivered_at) : <Badge tone="warn">por entregar</Badge>}</td></tr>
            ))}</tbody>
          </table>
        ) : <Empty>Sem mensagens.</Empty>}
      </Gate>
    </Card>
  )
}

function Audit() {
  const d = useData<{ id: number; at: number; admin: string; action: string; entity: string; entity_id: string; detail: string }[]>('/audit')
  return (
    <Card title="Registo de ações na consola" pad={false}>
      <Gate d={d}>
        {(rows) => rows.length ? (
          <table className="table compact">
            <thead><tr><th>Hora</th><th>Quem</th><th>Ação</th><th>Alvo</th><th>Detalhe</th></tr></thead>
            <tbody>{rows.map((a) => (
              <tr key={a.id}><td className="nowrap">{dateTime(a.at)}</td><td>{a.admin}</td><td className="mono">{a.action}</td><td>{a.entity} {a.entity_id}</td><td className="mono small ellipsis-cell">{a.detail}</td></tr>
            ))}</tbody>
          </table>
        ) : <Empty>Sem ações registadas.</Empty>}
      </Gate>
    </Card>
  )
}

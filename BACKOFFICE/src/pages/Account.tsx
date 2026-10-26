import { useState } from 'react'
import { api } from '../api'
import { useAuth } from '../live'
import { Card, Field, Page, useRun } from '../ui/kit'

const ROLE = { admin: 'Administrador', operator: 'Operador', finance: 'Financeiro' }

export function Account() {
  const { user, logout } = useAuth()
  const [f, setF] = useState({ current: '', next: '', again: '' })
  const { run, busy } = useRun()
  const save = () => run(async () => {
    if (f.next !== f.again) throw new Error('As palavras-passe novas não coincidem')
    await api.post('/auth/password', { current: f.current, new: f.next })
    setF({ current: '', next: '', again: '' })
  }, 'Palavra-passe alterada')
  return (
    <Page title="Conta" sub={`${user?.email} · ${user ? ROLE[user.role] : ''}`} actions={<button className="btn" onClick={logout}>Sair</button>}>
      <Card title="Mudar palavra-passe" className="narrow">
        <div className="form-grid one">
          <Field label="Atual"><input type="password" value={f.current} onChange={(e) => setF({ ...f, current: e.target.value })} autoComplete="current-password" /></Field>
          <Field label="Nova" hint="mín. 6 caracteres"><input type="password" value={f.next} onChange={(e) => setF({ ...f, next: e.target.value })} autoComplete="new-password" /></Field>
          <Field label="Repetir nova"><input type="password" value={f.again} onChange={(e) => setF({ ...f, again: e.target.value })} autoComplete="new-password" /></Field>
        </div>
        <div className="row-actions"><button className="btn primary" disabled={busy || f.next.length < 6 || !f.current} onClick={save}>Guardar</button></div>
      </Card>
    </Page>
  )
}

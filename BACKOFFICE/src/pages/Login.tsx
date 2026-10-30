import { useState, type FormEvent } from 'react'
import { useAuth } from '../live'

export function Login() {
  const { login } = useAuth()
  const [email, setEmail] = useState('admin@qolari.local')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError('')
    try {
      await login(email.trim(), password)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="login">
      <form className="login-card" onSubmit={submit}>
        <span className="logo lg">Q</span>
        <h1>Qolari Mobility</h1>
        <p className="muted">Consola de operação das apps Rider, Driver e Fleet.</p>
        {error && <div className="error-box">{error}</div>}
        <label className="field">
          <span className="field-label">Email</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" required />
        </label>
        <label className="field">
          <span className="field-label">Palavra-passe</span>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required autoFocus />
        </label>
        <button className="btn primary block" disabled={busy}>{busy ? 'A entrar…' : 'Entrar'}</button>
        <p className="hint">Primeiro acesso: <code>admin@qolari.local</code> / <code>admin</code> — muda em Conta.</p>
      </form>
    </div>
  )
}

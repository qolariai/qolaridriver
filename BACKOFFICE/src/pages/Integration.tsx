import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, qs } from '../api'
import { ago, APP_LABEL, clock } from '../format'
import { useData } from '../live'
import type { AppName } from '../types'
import { Badge, Card, Empty, Gate, Icon, Modal, Page, Tabs, useRun } from '../ui/kit'

type AppInfo = {
  app: AppName; label: string; apk: string; port: number; listening: boolean; base_url: string
  catalog_endpoints: number; catalog_implemented: number; routes: number; called: number; calls: number
  unmapped_called: number; errors: number; last_call_at: number | null; sessions_active: number; devices: number
}
type EP = { method: string; path: string; handler?: string; calls: number; errors?: number; last_status: number | null; last_at: number | null
  implemented: boolean; sink?: boolean; operation?: string; response?: string; in_catalog?: boolean }
type Traffic = { seq: number; ts: number; method: string; path: string; template: string; handler: string; status: number; ms: number; request: string; query: Record<string, string>; response: string }

export function Integration() {
  const d = useData<AppInfo[]>('/integration')
  return (
    <Page title="Integração das apps" sub="O que cada APK pede ao backend, o que já tem resposta própria e o que falta mapear">
      <Gate d={d}>
        {(rows) => (
          <>
            <div className="cards three">
              {rows.map((a) => (
                <Link key={a.app} to={`/integracao/${a.app}`} className={`card app-card app-${a.app}`}>
                  <div className="app-top">
                    <span className={`app-logo app-${a.app}`}>{APP_LABEL[a.app][0]}</span>
                    <div><strong>{a.label}</strong><small className="muted block">{a.apk}</small></div>
                    <Badge tone={a.listening ? 'ok' : 'bad'}>{a.listening ? `porta ${a.port}` : `porta ${a.port} fechada`}</Badge>
                  </div>
                  <code className="base-url">{a.base_url}</code>
                  <div className="meter" title="Endpoints do catálogo com resposta própria">
                    <span style={{ width: `${(100 * a.catalog_implemented) / Math.max(1, a.catalog_endpoints)}%` }} />
                  </div>
                  <small className="muted">{a.catalog_implemented} de {a.catalog_endpoints} endpoints da APK com resposta própria · {a.routes} rotas</small>
                  <div className="fleet-stats">
                    <span><strong>{a.calls}</strong> pedidos</span>
                    <span><strong className={a.unmapped_called ? 'warn-text' : ''}>{a.unmapped_called}</strong> por mapear</span>
                    <span><strong>{a.sessions_active}</strong> sessões</span>
                    <span><strong>{a.devices}</strong> aparelhos</span>
                  </div>
                  <small className="muted">Último pedido: {ago(a.last_call_at)}</small>
                </Link>
              ))}
            </div>
            <Card title="Como ligar os telemóveis">
              <ol className="steps">
                <li>As APKs têm o endereço <code>192.168.1.204</code> gravado: o PC tem de ter este IP na rede onde está o telemóvel (mesmo Wi-Fi ou hotspot).</li>
                <li>O Windows tem de deixar entrar ligações nas portas <code>80</code>, <code>3000</code> e <code>8090</code> (ver README do backend).</li>
                <li>Login nas apps: telemóvel de uma conta (ex.: Rider <code>+351910000001</code>, Driver <code>+351920000001</code>, Fleet <code>+351930000001</code>) e o código <code>0000</code>.</li>
                <li>Abre a app e acompanha aqui os pedidos em tempo real; os “por mapear” mostram o modelo de resposta que a app espera.</li>
              </ol>
            </Card>
          </>
        )}
      </Gate>
    </Page>
  )
}

export function IntegrationApp() {
  const { app = 'rider' } = useParams() as { app: AppName }
  const [tab, setTab] = useState<'traffic' | 'called' | 'unmapped' | 'catalog'>('traffic')
  const [q, setQ] = useState('')
  const [detail, setDetail] = useState<{ method: string; path: string } | null>(null)
  return (
    <Page back={{ to: '/integracao', label: 'Integração' }} title={`Qolari ${APP_LABEL[app]}`} sub="Pedidos reais da app e cobertura do contrato extraído da APK">
      <div className="toolbar">
        <Tabs value={tab} onChange={setTab} items={[['traffic', 'Ao vivo'], ['called', 'Endpoints usados'], ['unmapped', 'Por mapear'], ['catalog', 'Catálogo da APK']]} />
        {tab !== 'traffic' && <div className="search"><Icon name="search" /><input placeholder="Filtrar path" value={q} onChange={(e) => setQ(e.target.value)} /></div>}
      </div>
      {tab === 'traffic' ? <TrafficView app={app} onOpen={setDetail} /> : <EndpointList app={app} filter={tab} q={q} onOpen={setDetail} />}
      {detail && <EndpointModal app={app} {...detail} onClose={() => setDetail(null)} />}
    </Page>
  )
}

function TrafficView({ app, onOpen }: { app: AppName; onOpen: (x: { method: string; path: string }) => void }) {
  const [items, setItems] = useState<Traffic[]>([])
  const [paused, setPaused] = useState(false)
  const [open, setOpen] = useState<number | null>(null)
  const since = useRef(0)
  useEffect(() => {
    since.current = 0
    setItems([])
    let stop = false
    const tick = async () => {
      if (stop) return
      if (!paused) {
        try {
          const r = await api.get<{ items: Traffic[] }>(`/integration/${app}/traffic?since=${since.current}`)
          if (r.items.length) {
            since.current = r.items[r.items.length - 1].seq
            setItems((old) => [...r.items.reverse(), ...old].slice(0, 300))
          }
        } catch { /* backend em baixo: tenta outra vez */ }
      }
      setTimeout(tick, 1500)
    }
    tick()
    return () => { stop = true }
  }, [app, paused])
  return (
    <Card pad={false} title={`${items.length} pedidos`} actions={<button className="btn sm" onClick={() => setPaused(!paused)}>{paused ? 'Retomar' : 'Pausar'}</button>}>
      {items.length ? (
        <div className="traffic">
          {items.map((t) => (
            <div key={t.seq} className={`tr-row ${t.handler ? '' : 'unmapped'} ${t.status >= 400 ? 'err' : ''}`}>
              <button className="tr-head" onClick={() => setOpen(open === t.seq ? null : t.seq)}>
                <time>{clock(t.ts)}</time><span className="method">{t.method}</span>
                <span className="path ellipsis">{t.path}</span>
                <Badge tone={t.status >= 400 ? 'bad' : 'ok'}>{t.status}</Badge>
                {t.handler === 'sink' ? <Badge>telemetria</Badge> : t.handler ? <Badge tone="info">{t.handler}</Badge> : <Badge tone="warn">sem handler</Badge>}
                <span className="muted">{Math.round(t.ms)} ms</span>
              </button>
              {open === t.seq && (
                <div className="tr-body">
                  {t.template !== t.path && <p className="muted">Template: <code>{t.template}</code></p>}
                  {Object.keys(t.query).length > 0 && <><h4>Query</h4><pre>{JSON.stringify(t.query, null, 2)}</pre></>}
                  <h4>Pedido</h4><pre>{pretty(t.request) || '—'}</pre>
                  <h4>Resposta</h4><pre>{pretty(t.response)}</pre>
                  <button className="btn sm" onClick={() => onOpen({ method: t.method, path: t.template })}>Ver endpoint e modelo esperado</button>
                </div>
              )}
            </div>
          ))}
        </div>
      ) : <Empty>À espera de pedidos desta app. Abre a app no telemóvel (mesma rede, IP 192.168.1.204).</Empty>}
    </Card>
  )
}

function pretty(s: string) {
  try {
    return JSON.stringify(JSON.parse(s), null, 2)
  } catch {
    return s
  }
}

function EndpointList({ app, filter, q, onOpen }: { app: AppName; filter: string; q: string; onOpen: (x: { method: string; path: string }) => void }) {
  const d = useData<{ items: EP[]; total: number }>(`/integration/${app}/endpoints${qs({ filter, q })}`)
  return (
    <Card pad={false}>
      <Gate d={d}>
        {(x) => x.items.length ? (
          <div className="table-wrap">
            <table className="table hover compact">
              <thead><tr><th>Método</th><th>Path</th><th>Operação / resposta</th><th>Estado</th><th className="num">Pedidos</th><th>Último</th></tr></thead>
              <tbody>{x.items.map((e) => (
                <tr key={`${e.method} ${e.path}`} onClick={() => onOpen({ method: e.method === '?' ? 'POST' : e.method, path: e.path })}>
                  <td className="method">{e.method}</td>
                  <td className="mono path-cell">{e.path}</td>
                  <td className="muted">{e.operation}{e.response ? ` → ${e.response}` : ''}</td>
                  <td>{e.sink ? <Badge>telemetria</Badge> : e.implemented ? <Badge tone="ok">{e.handler || 'implementado'}</Badge> : <Badge tone="warn">genérico {'{}'}</Badge>}</td>
                  <td className="num">{e.calls}</td>
                  <td className="muted nowrap">{e.last_at ? ago(e.last_at) : '—'}</td>
                </tr>
              ))}</tbody>
            </table>
            {x.total > x.items.length && <p className="muted pad">A mostrar {x.items.length} de {x.total}. Usa o filtro.</p>}
          </div>
        ) : <Empty>{filter === 'unmapped' ? 'Nenhum pedido sem resposta própria — ou a app ainda não foi aberta.' : 'Nada.'}</Empty>}
      </Gate>
    </Card>
  )
}

type Detail = {
  method: string; path: string; implemented: boolean
  catalog: { method: string; path: string; operation: string; response: string } | null
  response_model: { class: string; fields: { name: string; type: string }[] } | null
  stats: { calls: number; errors: number; handler: string; last_status: number; first_at: number; last_at: number; last_request: string; last_response: string } | null
}

function EndpointModal({ app, method, path, onClose }: { app: AppName; method: string; path: string; onClose: () => void }) {
  const d = useData<Detail>(`/integration/${app}/endpoint${qs({ path, method })}`, false)
  const [model, setModel] = useState<Detail['response_model']>(null)
  const { run } = useRun()
  const openType = (t: string) => {
    const name = t.replace(/[<>;]/g, ' ').trim().split(/\s+/).pop() ?? t
    run(async () => setModel(await api.get(`/integration/${app}/model?name=${encodeURIComponent(name)}`)))
  }
  return (
    <Modal title={`${method} ${path}`} onClose={onClose} wide>
      <Gate d={d}>
        {(x) => (
          <div className="stack">
            <p>{x.implemented ? <Badge tone="ok">tem handler no backend</Badge> : <Badge tone="warn">sem handler — responde {'{}'}</Badge>}
              {x.catalog?.operation && <> · operação <code>{x.catalog.operation}</code></>}</p>
            {(model ?? x.response_model) ? (
              <>
                <h4>Modelo de resposta esperado <code>{(model ?? x.response_model)!.class.split('.').slice(-2).join('.')}</code> {model && <button className="btn sm" onClick={() => setModel(null)}>voltar</button>}</h4>
                <table className="table compact"><tbody>{(model ?? x.response_model)!.fields.map((f) => (
                  <tr key={f.name}><td className="mono">{f.name}</td><td><button className="link" onClick={() => openType(f.type)}>{f.type.split('.').slice(-1)[0]}</button></td></tr>
                ))}</tbody></table>
              </>
            ) : <p className="muted">Modelo de resposta não identificado no catálogo desta APK.</p>}
            {x.stats ? (
              <>
                <p className="muted">{x.stats.calls} pedidos · {x.stats.errors} erros · último {ago(x.stats.last_at)} (HTTP {x.stats.last_status})</p>
                <h4>Último pedido</h4><pre>{pretty(x.stats.last_request) || '—'}</pre>
                <h4>Última resposta</h4><pre>{pretty(x.stats.last_response)}</pre>
              </>
            ) : <p className="muted">A app ainda não chamou este endpoint.</p>}
          </div>
        )}
      </Gate>
    </Modal>
  )
}

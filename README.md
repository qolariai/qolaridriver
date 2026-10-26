# Qolari Mobility — clone funcional (Driver + Rider + Fleet + backoffice)

Laboratório de aprendizagem: recriação limpa da experiência das apps de mobilidade,
com marca própria **Qolari**, backend próprio e backoffice de operação. O entregável
é código 100% novo; as APKs originais ficam como **referência e instrumento**, nunca
como produto.

> **Não distribuir.** Não há publicação na Play Store nem operação real. As APKs
> renomeadas (`qolari-*.apk`) são instrumento de laboratório (`repack_suspect`), não
> fazem parte do entregável.

## Publicado

| Endereço | O que serve |
|---|---|
| `https://admin-driver.qolari.com` | Backoffice (React + API) |
| `https://driver.qolari.com` | API da app Driver; `/` abre a consola |
| `https://rider.qolari.com` | API da app Rider |
| `https://qolari.com/pt/marketplace/qolaridriver` | Página do marketplace e APKs |

O estado do deploy, credenciais demo e backups estão em [`DEPLOY.md`](DEPLOY.md) §10.

## O que existe

| Pasta | Conteúdo |
|---|---|
| `ANDOIRD/DRIVER/` | Spec, captura (`ux_capture/`), `ui_spec/`, contrato e **recriação** em `RECRIACAO/` |
| `ANDOIRD/USER_LITE/` | Captura da Rider Lite e **recriação** em `RECRIACAO/` |
| `ANDOIRD/FLEET/` | Contrato e instrumento da Fleet (sem recriação visual) |
| `BACKEND/` | FastAPI + SQLite: 3 apps, consola, `ramen`, despacho, finanças, testes |
| `BACKOFFICE/` | SPA React + Vite (ops, suporte/KYC, financeiro, administração) |
| `tools/` | `spec_check.py` (portões do MEGA) e `gen_coverage.py` (cobertura) |
| `VALIDACAO_HONOR/` | Capturas da validação no dispositivo (app nova; não é spec) |

## Arrancar

```powershell
# Backend (portas 8090 Rider, 8091 Driver, 8300 consola, 3000 Fleet)
cd BACKEND
.\.venv\Scripts\python server.py

# Backoffice (build servido pelo backend em :8300; para desenvolver:)
cd BACKOFFICE
npm install
npm run dev
```

Contas do seed (código `0000`):

| App | Conta |
|---|---|
| Rider | `+351910000001` (Ana) |
| Driver | `+351920000003` (João) ou `+351920000001` (Carlos) |
| Fleet | `+351930000001` |
| Backoffice | `admin@qolari.local` / `admin` |

## Apps Android (recriação)

```powershell
$env:JAVA_HOME = "C:\Program Files\Eclipse Adoptium\jdk-21.0.12.101-hotspot"

cd ANDOIRD\DRIVER\RECRIACAO
.\gradlew.bat assembleDebug testDebugUnitTest    # 74 testes

cd ANDOIRD\USER_LITE\RECRIACAO
.\gradlew.bat assembleDebug testDebugUnitTest    # 11 testes
```

As apps apontam para o backend local em `USB` (`127.0.0.1`, com `adb reverse`):

```powershell
adb reverse tcp:8090 tcp:8090
adb reverse tcp:8091 tcp:8091
adb install -r ANDOIRD\DRIVER\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk
adb install -r ANDOIRD\USER_LITE\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk
```

O host muda **num sítio só**: `config/AppConfig.kt` de cada app.

## Mapas (Google Maps)

As apps usam o **Google Maps SDK** nos ecrãs principais. A chave está em
`google_maps_api_key.txt`; o build lê `MAPS_API_KEY` de `local.properties`:

```properties
# ANDOIRD/DRIVER/RECRIACAO/local.properties
# ANDOIRD/USER_LITE/RECRIACAO/local.properties
MAPS_API_KEY=AIza...
```

Sem a chave o mapa fica cinzento (o logcat mostra `Authorization failure`). As
miniaturas decorativas dos cartões continuam desenhadas e não são interativas.

**Restringir a chave no Google Cloud:** em *APIs & Services → Credentials*, limitar a
`Maps SDK for Android` a:
- `com.qolari.drivereplica` (debug SHA-1 da keystore de debug)
- `com.qolari.userlite` (debug SHA-1 da keystore de debug)

e definir quotas. O `google_maps_api_key.txt` e os `local.properties` estão no
`.gitignore`; não versionar a chave.

O backend usa `ROUTING_URL` para a rota por estrada (por omissão o demo público do
OSRM, definido em `server.py`); se o serviço falhar, devolve uma linha reta e a app
desenha-a na mesma.

## Verificação

```powershell
cd BACKEND; .\.venv\Scripts\python -m pytest -q tests    # 93 passed
cd ..; python tools\spec_check.py                         # 451 PASS
python tools\gen_coverage.py                              # regenera coverage.md
```

## Estado

- **Fases 0-7 do MEGA:** concluídas. **Alvo:** `funcional`.
- **Driver:** 109 ecrãs classificados; 84 implementados, 17 parciais e 8 fora de
  âmbito declarados em `coverage.md`. Inclui suporte, segurança, documentos,
  preferências de condução, transferências, incentivos, fila de aeroporto,
  perfil empresarial, ajustes/faturas, paragens, gravação de áudio e vídeo do ecrã.
- **Rider:** recriação com 11 testes; contrato nativo `designed`; apoio, segurança,
  agendamento, gorjeta/recibo, locais guardados, empresa/família/Uber One,
  paragens, partilha do ecrã completo e offline com fila.
- **Fleet:** operação coberta por contrato + backend + backoffice; sem paridade
  visual.
- **Backoffice:** RBAC (`admin`/`operator`/`finance`), intervenções auditadas,
  suporte, segurança, ajustes, gravações e ecrã partilhado.
- **Veredicto:** pronto para `funcional` (ver `VALIDACAO_MEGA.md` §9, §10, §11 e §12).

## Documentos de trabalho

| Ficheiro | Para quê |
|---|---|
| `plan.md` | declaração inicial, gates, cobertura, tolerância, alvo |
| `access_plan.md` | decisão de acesso por app/role |
| `coverage.md` | ecrã → evidência → integridade → razão de gap |
| `topology.md` | tipo de app, atores, backends, backoffice, máquina de estados |
| `endpoints.json` | contrato do ecossistema (owner, producer, consumers, evidência) |
| `capabilities.md` | matriz ação → endpoint/estado → teste → status |
| `backlog.md` | gaps; zero abertos para `funcional` |
| `VALIDACAO_MEGA.md` | relatório final da FASE 6 + FASE 7 |
| `ADAPTACAO_PROMPTS.md` | o que os prompts mudaram e como foi aplicado |
| `MELHORIAS.md` | fases P0-P3 depois do fecho (estado e prova) |
Os prompts antigos (`PROMPT_SPEC_UIUX`, `PLANO_SPEC_UIUX_*`, `PROMPT_BACKEND_CENTRAL`,
`PROMPT_RIDER_PEDIDO`, `PROMPT_PROXIMO_CHAT`) estão arquivados em
`BACKUPS/prompts_arquivo_2026-10-25/`. Não são usados pelo estado atual.

## Tolerâncias declaradas

Mapas principais em Google Maps (chave em `local.properties`), FCM configurado
(Driver/Rider; `ramen` como fallback), fonte Uber Move ?

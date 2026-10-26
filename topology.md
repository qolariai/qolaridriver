# topology.md — Topologia do ecossistema Qolari

**Versão:** 1.0 · **Data:** 2026-10-25 · **Método:** MEGA §4.5 e §4.6.
**Regra dura:** a topologia é nossa; não espelha a do original. O que se clona é o
comportamento observável, não a arquitetura interna da Uber.

## 1. Classificação

| Campo | Valor | Evidência |
|---|---|---|
| Tipo | **Marketplace de dois lados** (ride-hailing) | oferta só chega com motorista online; despacho por proximidade; estados que só outro ator move; avaliações cruzadas; liquidação com comissão e taxa de frota |
| Modelo de negócio | plataforma que cobra comissão e taxa de frota | `domain/finance.py`, `_settle` em `domain/trips.py` |
| Multi-app | sim (Driver, Rider, Fleet) + backoffice | três pacotes e três contratos |
| Multi-tenant | sim, por frota (`Organization`) | `Fleet` vê só os seus motoristas; `topology.md` §6 |
| Multi-país | não no âmbito atual | seed em Lisboa; `City` e `Product` permitem extensão |
| Multi-idioma | PT-PT na UI e documentação | copy própria; o original é inglês |

## 2. Atores

| Role | App | Como entra | Que estados move |
|---|---|---|---|
| Passageiro | Rider | telefone + código `0000` | cria `requested`; cancela; avalia |
| Motorista | Driver | telefone + código `0000` | online/offline; aceita/recusa; recolha; inicia; termina; avalia |
| Frota | Fleet | telefone + código `0000` | veículos, motoristas, convites; lê operação e ganhos |
| Operação | Backoffice (`operator`) | e-mail + palavra-passe | despacha, força estados, aprova documentos, bloqueia contas |
| Financeiro | Backoffice (`finance`) | e-mail + palavra-passe | pagamentos, acertos, leitura de tudo |
| Administração | Backoffice (`admin`) | e-mail + palavra-passe | configuração, tarifas, promoções, administradores |
| Sistema | backend | relógio de 1 s | expira propostas, re-despacha, move motoristas simulados |
| Peer-bot | testes | script/pytest | simula o ator em falta (Rider ou Driver) |

## 3. Apps

| Nome | Role | Plataforma | Stack | Estado |
|---|---|---|---|---|
| Qolari Driver | motorista | Android | Kotlin, Views + Compose por evidência, Navigation, ViewModel/StateFlow, Retrofit/OkHttp/Gson, DataStore | recriada (lotes 0–5) |
| Qolari Rider | passageiro | Android | Kotlin, Views, Navigation, ViewModel/StateFlow, Retrofit/OkHttp/Gson, DataStore | recriada (`ANDOIRD/USER_LITE/RECRIACAO`, 11 testes) |
| Qolari Fleet | frota | Android | Kotlin (app de laboratório, re-branded) | contrato e backend; sem recriação própria nem captura |
| Qolari Backoffice | ops/suporte/financeiro | Web (React) | React 19, Vite, TypeScript, Leaflet | `designed`, operacional |
| iOS | motorista/passageiro/frota | iOS | — | fora do âmbito atual |

## 4. Backends

**Decisão: 1 backend modular.** `BACKEND/` — FastAPI + SQLite, um processo, uma base de
dados, um deploy. As portas emulam os hosts que as APKs esperam; não são serviços.

| Domínio | Ficheiro | Entidades | Endpoints |
|---|---|---|---|
| Identidade/sessão | `apps/identity.py`, `apps/usl.py` | `AuthSession`, `Device`, `LoginAttempt` | `/v2`, `/rt/identity/*` |
| Viagens/despacho | `domain/trips.py`, `apps/rider.py`, `apps/driver.py` | `Trip`, `Offer`, `TripEvent` | `/rt/riders/*`, `/rt/drivers/*`, `/rt/trips/*` |
| Frota | `apps/fleet.py` | `Organization`, `FleetUser`, `Vehicle` | `/rt/fleet/*`, `/rt/vehicle-supplier/*` |
| Financeiro | `domain/finance.py`, `domain/pricing.py` | `LedgerEntry`, `Payout`, `Promo` | `/api/finance/*`, `/rt/earnings/*` |
| Notificações | `domain/push.py`, `apps/common.py` | mensagens `ramen`, `Notification` | `/ramen/*`, `/rt/inbox/*` |
| Catálogo/geo | `apps/catalog.py`, `apps/geocode.py`, `apps/routing.py` | `City`, `Product`, moradas | `/rt/riders/*`, `/rt/navigation/*` |
| Backoffice | `console/api.py` | `AdminUser`, `AuditLog` | `/api/*` |

**Porquê não separar:** escala de laboratório; um deploy; consistência transacional
simples; a separação pagaria em deploy, observabilidade e consistência sem retorno
medido. Se o projeto crescer, os candidatos naturais são **matching/dispatch** (tempo
real) e **pagamentos/ledger** (isolamento e auditoria).

**Hosts:** as apps apontam para `192.168.1.204` / `driver.qolari.com`; o backend escolhe
a app pela **porta local**, não pelo `Host`. Isto é uma decisão de laboratório, não uma
topologia de produção.

## 5. Backoffices

**Decisão: 1 SPA com quatro áreas funcionais e RBAC.** `BACKOFFICE/` é servido pelo
backend em `/` e fala com `/api/*`. Não é um clone: é `designed`.

| Área | Utilizador | Funções | Estados que move | Ecrãs |
|---|---|---|---|---|
| Ops/Despacho | `operator` | mapa ao vivo, viagens, simulador, forçar estado, cancelar, reatribuir | `requested`, `accepted`, `arrived`, `in_progress`, `completed`, `cancelled` | Painel, Viagens, Ficha da viagem, Simulador |
| Suporte/KYC | `operator` | motoristas, passageiros, frotas, veículos, documentos, bloqueios | `driver.status`, `document.status`, `rider.status` | Motoristas, Passageiros, Frotas, Veículos, Documentos |
| Financeiro | `finance` | comissão, taxas, saldos, pagamentos, acertos | `payout.status`, liquidação | Finanças |
| Administração | `admin` | tarifas, promoções, parâmetros, administradores, integração | configuração | Categorias, Promoções, Definições, Integração, Conta |

**RBAC:** `admin` (tudo), `operator` (operação e suporte), `finance` (leitura + finanças).
Todas as ações passam por `audit()` em `console/auth.py`; o registo está em `/api/audit`.

**Desvio consciente:** o MEGA recomenda separar financeiro/compliance de suporte. Aqui
as duas áreas vivem no mesmo SPA, separadas por papel e auditoria. Para operação real,
recomenda-se separar o deploy e o domínio; no laboratório, a separação por papel é
suficiente e está declarada.

## 6. Modelo de dados partilhado

| Entidade | Dono (quem escreve) | Transições | Visibilidade por role |
|---|---|---|---|
| `Rider` | `apps/identity.py`, `console/api.py` | `active` / `blocked` | Rider (próprio), Backoffice; Driver vê nome e rating na viagem |
| `Driver` | `console/api.py`, `apps/driver.py` | `pending` → `approved` → `suspended`; `offline` → `online` → `on_trip` | Driver (próprio), Fleet (da org), Backoffice; Rider vê na viagem |
| `Vehicle` | `console/api.py`, `apps/fleet.py` | `active` / `inactive` | Fleet (da org), Backoffice; Rider vê categoria |
| `Organization` | `console/api.py` | — | Fleet (própria), Backoffice |
| `Trip` | **`domain/trips.py`** | `requested` → `accepted` → `arrived` → `in_progress` → `completed`; `cancelled`; `no_drivers` | Rider (própria), Driver (atribuído), Fleet (da org), Backoffice |
| `Offer` | `domain/trips.py` | `pending` → `accepted` / `rejected` / `expired` / `withdrawn` | Driver (destinatário), Backoffice |
| `LedgerEntry` | `domain/trips.py` | criado na liquidação | Driver, Fleet, Backoffice (`finance`) |
| `Payout` | `apps/driver.py`, `console/api.py` | `pending` → `paid` / `cancelled` | Driver (próprio), Backoffice (`finance`) |
| `Document` | `apps/driver.py` (upload), `console/api.py` (revisão) | `pending` → `approved` / `rejected` | Driver (próprio), Backoffice |
| `Notification` | `domain/trips.py`, `console/api.py` | `unread` → `read` | Driver (próprio) |
| `SupportThread` / `SupportMessage` | `apps/support.py`, `console/api.py` | `open` ↔ `closed`; mensagens `user`/`support` | Conta (própria), Backoffice |
| `TrustedContact` | `apps/safety.py` | criado/removido | Conta (própria) |
| `SafetyIncident` | `apps/safety.py`, `console/api.py` | `open` → `closed` | Conta (própria), Backoffice |
| `TripShare` | `apps/safety.py` | criado com validade de 4 h | Conta (própria), página pública |
| `DriverPreference` | `apps/driver.py` | modo destino/área, auto-aceitação, pausa | Driver (próprio), `domain/trips.py` |
| `AirportQueue` | `apps/driver.py` | entrada/saída; posição por `joined_at` | Driver (próprio), Backoffice |
| `Quest` / `QuestClaim` | `apps/driver.py` | progresso por viagens; recompensa creditada uma vez | Driver (próprio), Financeiro |
| `Referral` | `apps/driver.py` | convite pendente | Driver (próprio) |
| `AdjustmentRequest` | `apps/driver.py`, `console/api.py` | `pending` → `approved` / `rejected` | Driver (próprio), Backoffice (`finance`) |
| `ScreenShare` | `apps/support.py` | frames JPEG; ativo/inativo | Conta (própria), Backoffice |
| `TripRecording` | `apps/safety.py` | início/fim; ficheiro áudio | Driver (próprio), Backoffice |
| Locais guardados / empresa / família / Uber One | `apps/userlite.py` | `Setting` por rider | Rider (próprio) |

**Regra:** dois escritores no mesmo campo é bug de design. `Trip` só muda em
`domain/trips.py`; o backoffice chama as mesmas funções de domínio, não escreve na BD.

## 7. Tempo real e jobs

| App | Canal | Subscrições | Fallback |
|---|---|---|---|
| Rider | `ramen` long-poll (`GET /ramen/sessions/{id}/messages`) | `trip_status` (estado da viagem), `offer`/`trip` | polling de `/rt/riders/me/status` |
| Driver | `ramen` long-poll | `push_driver_unified_offers_v3` (oferta), `push_drivers_tasks`, `trip_status` | polling de `/rt/drivers/v2/available` a 4 s |
| Fleet | `ramen` long-poll | `driver_trip` em todas as transições da viagem, `driver_status` quando o motorista fica livre | polling de `/rt/fleet/get-fleet-drivers-v2` |
| Backoffice | `/api/changes` long-poll | muda a base de dados → recarrega a página | refresh manual |
**Relógio:** thread de 1 s (`RUN_TICKER=1`) → `trips.tick`: expira propostas, re-despacha,
move motoristas simulados. Viagens agendadas (`scheduled_at`) só entram no despacho à
hora marcada. **FCM:** configurado para Driver/Rider (HTTP v1); o `ramen` continua como
fallback. **Jobs:** liquidação é síncrona no `complete`; pagamentos são pedidos na app
e fechados no backoffice.

## 8. Orquestração — máquina de estados da viagem

Uma linha por transição. `U` = Rider, `D` = Driver, `F` = Fleet, `B` = Backoffice.

| Estado | Quem cria | Quem move adiante | Endpoint | Evento | Vistas |
|---|---|---|---|---|---|
| `requested` | U | D aceita · dispatch atribui · timeout | `POST /rt/riders/me/v2/pickup` | `trip_status` + `push_driver_unified_offers_v3` | D (oferta), B, F (após aceite) |
| `accepted` | — | D a caminho; posição → `arrived` | `POST /rt/drivers/accept-offers` | `trip_status`; `driver_trip` para F | U, D, F, B |
| `arrived` | — | D inicia | `POST /rt/trips/v2/begin` (chegada automática por posição ≤ 80 m) | `trip_status` | U, D, F, B |
| `in_progress` | — | D termina | `POST /rt/trips/v2/end` | `trip_status`; liquidação | U, D, F, B |
| `completed` | — | Job de liquidação (síncrono) + avaliação | interno + `POST /rt/feedback/v2` / `POST /rt/trips/v2/driver-rate` | `trip_status`; `LedgerEntry` | U, D, F, B |
| `cancelled` | U, D, B | — | `POST /rt/trips/{id}/rider-cancel` · `POST /rt/trips/v2/driver-cancel` · `POST /api/trips/{key}/action` | `trip_status`; `offer` retirada | todos |
| `no_drivers` | sistema | — | `trips.tick` / `dispatch` | `trip_status` | U, B |
| `pin_verified` (evento) | D | — | `POST /rt/trips/v2/confirm-pin-is-verified` | `trip_status` | U, D, B |
| `paid` / `cancelled` (payout) | B | B | `POST /api/payouts` · `POST /api/payouts/{id}/paid` | `LedgerEntry` / `Payout` | D, F, B |

**Regras:**

- Cada transição tem **um** endpoint de domínio e **um** evento.
- Um estado sem transição é estado morto; não existe no clone.
- O backoffice intervém por transições de primeira classe, não por `UPDATE` na BD.
- A chegada é decidida pelo servidor pela posição (`_auto_arrive`), porque a app Driver
  4.599 não tem passo "cheguei".

### 8.1 Um escritor por campo

| Campo | Escritor único | Leitores |
|---|---|---|
| `trip.state` | `domain/trips.py` (só via transições) | U, D, F, B |
| `trip.fare` | `pricing` na criação; congelado; `complete` recalcula | U, D, F, B |
| `driver.location` | Driver app (`POST /rt/unifiedlocation/uploadpositions`) | U (só na viagem ativa), F, B; **nunca** outro Driver |
| `driver.availability` | Driver app (online/offline) + `domain/trips.py` (on_trip) | F, matching, B |
| `driver.documents.status` | Backoffice (`PATCH /api/documents/{id}`) | D, F, B |
| `payout.status` | Backoffice (`finance`) | D, F, B |
| `offer.state` | `domain/trips.py` | D, B |

### 8.2 Intervenções do backoffice como transições auditadas

| Intervenção | Endpoint | Evento/efeito | Auditoria |
|---|---|---|---|
| Cancelar viagem | `POST /api/trips/{key}/action` (`cancel`) | `cancelled` + `trip_status` + oferta retirada | `trip.cancel` |
| Forçar estado | `POST /api/trips/{key}/action` (`force` + `state`) | estado forçado + `trip_status` | `trip.force` |
| Propor motorista | `POST /api/trips/{key}/action` (`offer`) | `Offer` + `push_driver_unified_offers_v3` | `trip.offer` |
| Aprovar/rejeitar documento | `PATCH /api/documents/{id}` | `Document.status` | `document.review` |
| Suspender motorista | `PATCH /api/drivers/{id}` | `driver.status` | `driver.update` |
| Pagar/acertar | `POST /api/payouts/{id}/paid` | `Payout.status` + `LedgerEntry` | `payout.paid` |
| Alterar tarifas/promoções | `PATCH /api/settings`, `/api/products`, `/api/promos` | configuração | `*.update` |

### 8.3 Peer-gating e ordem de clonagem

Ordem: **quem cria** (Rider) → **quem move** (Driver) → **quem agrega** (Fleet) → **quem
intervém** (Backoffice).

- `Fleet` é uma role com scope de tenant: vê os seus motoristas, não a frota global.
- Um fluxo só é validado quando observado em **≥2 vistas**.
- Se só se capturou uma app, o estado fica `peer-gated` e o `peer_triggers.md` mapeia
  para as transições desta tabela. O peer-bot simula o ator em falta e é declarado como
  simulado.

### 8.4 Teste dos três espelhos

`BACKEND/tests/test_espelhos.py`:

1. **Cria em U:** Rider pede viagem.
2. **Vê em D e F:** Driver recebe a oferta no `ramen`; Fleet vê o motorista `ONTRIP`
   depois do aceite.
3. **Move em D:** Driver aceita.
4. **Vê em U:** Rider passa a `WaitingForPickup`.
5. **Intervém em B:** Backoffice cancela a viagem.
6. **Vê em U e D:** Rider perde a viagem ativa; Driver recebe `trip_status` cancelled e
   a oferta desaparece; Fleet vê o motorista `ONLINE`; o registo de auditoria tem
   `trip.cancel`.

## 9. Fora de âmbito (declarado)

- **iOS** — as apps iOS existem como laboratório, mas não entram na paridade atual.
- **Páginas web do original** (Ajuda, Documentos, Privacidade, Comfort) — conteúdo
  próprio; não se copia o conteúdo de terceiros.
- **Mapa real / rota real** — Google Maps SDK com chave local + OSRM público (fallback em linha reta).
- **FCM/push do sistema** — configurado para Driver/Rider; o `ramen` continua como fallback.
- **Login social, reCAPTCHA, IAP** — ausentes por decisão.
- **Vídeo de câmara e tradução EN completa** — integrações de sistema/legal; fora do âmbito desta ronda.
- **Marketplace de entregas/comida** — o tipo é ride-hailing; outras verticais não se
  clonam.

## 10. Validação

| Teste | Resultado | Onde |
|---|---|---|
| Ciclo completo pelas 3 apps + consola | ✅ 93 testes | `BACKEND/tests/` |
| Rider recriada (build + unitários) | ✅ `assembleDebug`, 11 testes | `ANDOIRD/USER_LITE/RECRIACAO/` |
| Três espelhos (U→D/F/B→U) | ✅ `test_espelhos.py` | `BACKEND/tests/test_espelhos.py` |
| Um escritor por campo | ✅ por construção (`domain/trips.py`) | revisão |
| Backoffice auditado | ✅ `audit()` em todas as ações | `console/api.py` |
| Sem app a chamar app | ✅ | revisão |
| Sem backoffice a escrever na BD | ✅ chama funções de domínio | revisão |

**Lacunas conhecidas:** nenhuma na propagação de estados. O `ramen` é long-poll, não
socket; a semântica é a mesma (evento por transição) e a latência é a do polling
(4 s na Driver, 4 s na Rider). O FCM está configurado e foi testado no Honor; a
captura do push do sistema não é usada como spec.

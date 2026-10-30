# capabilities.md — matriz de capacidades (FASE 7)

**Alvo:** `funcional` (declarado em `plan.md`). **Regra:** uma entrada só é `ok`
quando tem efeito real (navegação, estado local, endpoint) e teste ou verificação
no telemóvel; caso contrário é `gap` e não pode ficar na UI.

**Fonte de verdade:** [`features.md`](features.md) (FASE 4.7). Este ficheiro é a
**vista de implementação** desse inventário: cada linha aqui existe lá com um
`F-ID`; nenhuma linha existe só aqui.

**Âmbito do clone:** Driver + Rider + backend + backoffice. A Fleet é operação
(contrato + backend), não recriação visual — ver “Exclusões declaradas”.

## 0. Ligação ao inventário (F-ID)

| Documento | Papel | Autoridade |
|---|---|---|
| [`features.md`](features.md) | o que a app Driver **tem** (86 features) | inventário |
| [`ANDOIRD/USER_LITE/features.md`](ANDOIRD/USER_LITE/features.md) | o que a Rider **tem** (52 features) | inventário |
| `capabilities.md` (este) | o que o clone **faz** de cada uma | implementação |
| `backlog.md` | o que **falta** (14 gaps no total) | gaps |
| `rea_evidence/05_close/` | ledger, verify e cobertura | prova |

Contagem por estado:

| App | Features | `ok` | `excluído` | `em falta` | `parcial` |
|---|---|---|---|---|---|
| Driver | 86 | 72 | 8 | 6 | 0 |
| Rider | 52 | 44 | 0 | 8 | 0 |
| **Total** | **138** | **116** | **8** | **14** | **0** |

**Cobertura:** 116 / 130 em âmbito = **89,2 %** (`rea_evidence/05_close/coverage.json`).

### 0.1 Mapa F-ID → secção deste ficheiro

| Domínio | F-ID | Secção |
|---|---|---|
| `auth`, `onboarding` | `F-auth-01..02`, `F-onboarding-01..02` | §1 (Login) |
| `home` | `F-home-01..03` | §1 (Início) |
| `discover` | `F-discover-01..06` | §1 (Descobrir) |
| `earnings` | `F-earnings-01..03` | §1 (Rendimentos) |
| `inbox` | `F-inbox-01..03` | §1 (Caixa de entrada) |
| `menu` | `F-menu-01..05` | §1 (Menu) |
| `settings` | `F-settings-01..11` | §1 (Definições) |
| `safety` | `F-safety-01..10` | §1 (Segurança) |
| `documents` | `F-documents-01..08` | §1 (Documentos) |
| `vehicle` | `F-vehicle-01..03` | §1 (Veículos) |
| `finance` | `F-finance-01..04` | §1/§3 |
| `support` | `F-support-01..04` | §1 (Ajuda) |
| `trip` | `F-trip-01` | §1 (Oferta/viagem) |
| `offline` | `F-offline-01` | §1 (Global) |
| `notifications` | `F-notifications-01..03` | §1 (Definições) |
| `platform` | `F-platform-01..06` | §5 (gaps) |

## 1. Driver — ações visíveis

| Ecrã | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Boas-vindas | começar / entrar | `POST /rt/identity/oauth2/token` | `LoginViewModelTest` | ok |
| Login | telefone + código `0000` | token + sessão DataStore | `LoginViewModelTest` | ok |
| Início | carregar, refresh, retry | `POST /rt/riders/me/app-launch` + `/rt/drivers/*` | `HomeViewModelTest` | ok |
| Início | ficar online/offline | `v2/go-online` / `v2/go-offline` | `HomeViewModelTest`, fluxo no telemóvel | ok |
| Início | abrir menu, notificações, perfil | navegação + `get-profile-hub` | `Lote3Test`, telemóvel | ok |
| Início | mapa, zoom, controles | estado local do mapa | `Lote3Test` | ok |
| Descobrir | filtros, dias, cartões | estado local | `Lote3Test` | ok |
| Rendimentos | dia/semana, gráfico, erro | `/rt/earnings/*` | `Lote3Test` | ok |
| Caixa de entrada | listar, marcar lida | `/rt/inbox/*` | `Lote3Test` | ok |
| Menu | Ajuda, Segurança, Definições | navegação | telemóvel | ok |
| Menu | veículos, documentos, seguro, impostos, pagamentos, sobre | `vehicles`/`documents`/páginas próprias | `Lote5Test` | ok |
| Menu | descobrir, Pro, hub, recomendações | navegação/`infoFragment` | build + revisão | ok |
| Menu | mudar de conta / terminar sessão | `signOut()` + boas-vindas | `Lote1Test` | ok |
| Definições | acessibilidade, audição, comunicação, push, navegação, sons, sobre | estado local + páginas próprias | `Lote1Test` | ok |
| Ajuda | categorias, artigos, pesquisa | conteúdo próprio | `Lote5Test` | ok |
| Veículos | abrir, gerir, sem rede | `/rt/drivers/v2/vehicles` | `Lote5Test` | ok |
| Documentos | lista, estado, detalhe, erro | `/rt/drivers/me/documents` | `Lote5Test` | ok |
| Segurança | ferramentas, centro, PIN, limite de velocidade | sheets + páginas próprias | `Lote5Test` | ok |
| Oferta | aceitar, recusar, expirar | `accept-offers` / `reject-offers` / `expire-offers` | `DriveTest` | ok |
| Viagem | recolher, chegar, PIN, iniciar, terminar | `/rt/trips/v2/*` | `DriveTest` | ok |
| Viagem | cancelar, erro/retry | `driver-cancel` + retry | `DriveTest` | ok |
| Fim | ganhos da viagem, resumo, avaliação | `/rt/earnings/*`, `driver-rate` | `DriveTest` | ok |
| Global | banner offline, back, estados vazios | `NetworkMonitor` + Navigation | telemóvel | ok |

## 2. Rider — ações visíveis

| Ecrã | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Boas-vindas | começar | navegação | build | ok |
| Login | país, telefone, “encontrar conta”, seguinte | validação + `POST /rt/lite/...` token | `ContractTest` | ok |
| Login | usar código do laboratório | preenche `0000` no campo | build | ok |
| Início | carregar, refresh, retry | `GET /rt/lite/home` | backend `test_userlite` | ok |
| Início | pesquisa, sugestão, promoção | navegação para procura/promoções | build | ok |
| Início | localização | permissão + `LocationManager` + `POST /rt/lite/location` | `MapCameraTest`, telemóvel | ok |
| Início | zoom in/out | `MapCamera` (1.0–2.2, passos 1.25) | `MapCameraTest` | ok |
| Pesquisa | procurar, escolher destino | `GET /rt/lite/places` | backend `test_userlite` | ok |
| Pesquisa | usar casa guardada | `GET /rt/lite/home` + `savedPlace` | backend `test_userlite` | ok |
| Pesquisa | vazio, erro, teclado | estados + foco | build | ok |
| Escolher viagem | preços, categorias, retry | `POST /rt/lite/quote` | backend `test_userlite` | ok |
| Escolher viagem | forma de pagamento | `POST /rt/lite/payments/select` | backend `test_userlite` | ok |
| Escolher viagem | pedir | `POST /rt/lite/request` | backend `test_userlite` | ok |
| Viagem ativa | polling de estado, PIN, motorista | `GET /rt/lite/active` a 2 s | backend + telemóvel | ok |
| Viagem ativa | cancelar | `POST /rt/lite/trips/{uuid}/cancel` | backend `test_userlite` | ok |
| Viagem ativa | avaliar, saltar, voltar ao início | `POST /rt/lite/trips/{uuid}/rate` (`stars` 1–5; 0 = agora não) | backend + telemóvel | ok |
| Menu | carteira, atividade, ajuda, promoções, legal, conta | navegação | build | ok |
| Menu | terminar sessão | `signOut()` + confirmação | build | ok |
| Carteira | listar, escolher pagamento | `GET /rt/lite/wallet`, `payments/select` | backend | ok |
| Atividade | histórico, vazio com ação | `GET /rt/lite/history` | backend | ok |
| Ajuda | pesquisa e artigos | conteúdo próprio | build | ok |
| Legal | tópicos e detalhe | conteúdo próprio | build | ok |
| Promoções | aplicar código, ver preços | `GET/POST /rt/lite/promotions*` | backend | ok |
| Conta | escolher/guardar casa | `POST /rt/lite/account/home` | backend `test_userlite` | ok |
| Conta | editar nome/e-mail | `PATCH /rt/lite/account` | backend `test_userlite` | ok |
| Conta | segurança + terminar sessão | `signOut()` | build | ok |
| Conta | privacidade, verificação | `InfoFragment` (conteúdo próprio) | build | ok |
| Global | banner offline, back, estados | `NetworkMonitor` + Navigation | build | ok |

## 3. Backoffice (`designed`)

| Área | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Login/RBAC | entrar como admin/operator/finance | `/api/auth/login`, papéis | pytest consola | ok |
| Painel | mapa, indicadores, top motoristas | `/api/*` | pytest consola | ok |
| Viagens | filtrar, abrir ficha, cancelar/forçar/propor | `/api/trips/{key}/action` | `test_espelhos` | ok |
| Simulador | pedir, online/offline, mover, avançar | mesmas transições | `test_espelhos` | ok |
| Motoristas/Passageiros/Frotas/Veículos | fichas, aprovar, suspender | `/api/drivers`, `/api/riders`, … | pytest consola | ok |
| Documentos | fila, aprovar/recusar | `PATCH /api/documents/{id}` | pytest consola | ok |
| Finanças | saldos, pagamentos, acertos | `/api/payouts` | pytest consola | ok |
| Categorias/Promoções/Definições | tarifas, códigos, parâmetros, admins | `/api/settings`, `/api/products`, `/api/promos` | pytest consola | ok |
| Integração | tráfego, endpoints por mapear | `/api/integration` | revisão | ok |

## 4. Backend e orquestração

| Capacidade | Endpoint / evento | Teste | Status |
|---|---|---|---|
| Login e sessões (3 apps) | `/rt/identity/oauth2/token`, `/rt/lite/session` | `test_userlite`, `test_flow` | ok |
| Viagens: um escritor | `domain/trips.py` | `test_flow`, `test_espelhos` | ok |
| Despacho, expiração, no_drivers | `trip.tick`, `Offers` | `test_flow` | ok |
| Liquidação e saldos | `domain/finance.py` | `test_flow` | ok |
| Tempo real | `ramen` + `/api/changes` | `test_espelhos` | ok |
| Três espelhos U→D/F/B→U | eventos `trip_status`, `driver_trip` | `test_espelhos` | ok |
| Conta Rider (casa, dados) | `PATCH /rt/lite/account`, `POST /rt/lite/account/home` | `test_userlite` | ok |
| Backoffice auditado | `audit()` em todas as ações | pytest consola | ok |

## 5. Exclusões declaradas (não são botões mortos)

| Item | Porque | Equivalente / decisão |
|---|---|---|
| UI própria da Fleet | não há captura; a app do laboratório é instrumento | contrato + operação no backend e backoffice; paridade visual não prometida |
| Entrega/courier, reserva, paragens, cidade, filtro pessoal | fora da vertical ride-hailing do âmbito | entradas removidas da UI |
| Comfort, vídeo, gravação, login por e-mail, adicionar veículo | dependem de SDK/serviços/legal | entradas ausentes; sem placeholder |
| Mapa real / rota real / FCM / 112 / foto de documentos | chave Google, OSRM, FCM, hardware | mapa desenhado, `ramen`, ação removida; declarado em `plan.md` §8 |
| iOS | fora do âmbito | IPAs ficam como laboratório |
| Login social / reCAPTCHA / IAP | decisão do laboratório | login nativo por telefone; sem botões |

## 6. Resumo

| App | Features `ok` | `em falta` | Nota |
|---|---|---|---|
| Driver | 72 | 6 (`F-platform-*`) | 74 testes; validada no device |
| Rider | 44 | 8 (`F-platform-*`/`F-offline`) | 10 testes; validada no device |
| Backoffice | 9 áreas | 0 | RBAC + auditoria |
| Backend | 8 capacidades | 0 | 88 testes |

**Fechado:** a UI de produto das duas apps — 116 features `ok`, zero `parcial`.
**Não fechado:** 14 gaps, todos de plataforma (push do sistema, deep links,
biometria, i18n, dark mode, a11y, contactos, câmera).

**Veredicto honesto:** o alvo `funcional` **não fecha** — 14 gaps abertos,
nenhum de ecrã. Detalhe em `backlog.md` §1 e `rea_evidence/05_close/coverage.json`
(89,2 %).

**Rider:** o inventário FASE 4.7 da Rider ainda não existe. Só depois dele o
`capabilities.md` da Rider pode citar F-ID como a Driver faz.

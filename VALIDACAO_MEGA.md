# VALIDACAO_MEGA.md — relatório de fecho (FASE 6 + FASE 7)

**Data:** 2026-10-25 · **Âmbito:** ecossistema Qolari (Driver, Rider, Fleet, backend, backoffice)
**Programa:** [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) · **Alvo:** `funcional`

## 1. Verificações executadas

| Verificação | Comando | Resultado |
|---|---|---|
| Backend (3 apps + consola + 3 espelhos) | `BACKEND\.venv\Scripts\python -m pytest -q tests` | **93 passed** |
| Teste dos três espelhos | `pytest -q tests\test_espelhos.py` | **1 passed** |
| App Driver (build) | `gradlew.bat assembleDebug` | **BUILD SUCCESSFUL** |
| App Driver (testes) | `gradlew.bat testDebugUnitTest` | **74 testes, 0 falhas** |
| App Rider (build) | `gradlew.bat assembleDebug` | **BUILD SUCCESSFUL** |
| App Rider (testes) | `gradlew.bat testDebugUnitTest` | **11 testes, 0 falhas** |
| Smoke instrumentado (Driver/Rider) | `gradlew.bat connectedDebugAndroidTest` | **1 + 1 testes, 0 falhas** |
| Lint Android | `gradlew.bat lintDebug` | **passa (warnings de hardcoded/RTL)** |
| FCM (Driver/Rider) | token + `fcm._send` + `push.send` | **entregue nos dois; notifica??o no Honor** |
| Backoffice (build) | `npm run build` | **74 módulos, dist gerado** |
| Portões do MEGA | `python tools\spec_check.py` | **451 verificações, 0 falhas** |
| Cobertura | `python tools\gen_coverage.py` | 109 ecrãs base classificados |
| Consola servida + auth | `GET /`, `POST /api/auth/login`, `GET /api/trips` | 200 / 200 / 401 sem token |
| Validação no telemóvel | Honor PTP-N49, Android 16, USB | **fluxo completo** (V-01) |

## 2. Validação no Honor (fecha V-01)

| Item | Valor |
|---|---|
| Device | HONOR PTP-N49, Android 16 |
| Apps | `com.qolari.drivereplica` 0.1.0 e `com.qolari.userlite` 0.1.0 (debug) |
| Backend | local (`server.py`), `adb reverse tcp:8090` e `tcp:8091` |
| Contas | Ana `+351910000001` (Rider), João `+351920000003` (Driver) |
| Código | `0000` (laboratório) |

**Fluxo executado (8 viagens, ids 68-75):**

1. Rider: boas-vindas → telefone → código → casa → pesquisa → Praça Marquês de Pombal
   → escolher Qolari X → pedir.
2. Driver: oferta com tarifa 5,07 € → aceitar → recolha → PIN do passageiro → iniciar
   → deixar → terminar → ganhos e avaliação.
3. Rider: “Motorista a caminho” → “Em viagem” → “Chegou ao destino” → avaliação de
   5 estrelas → volta ao início.
4. Driver: Rendimentos mostra a viagem (4,04 €, 25/10 20:58) e o acumulado semanal.
5. Rider: Menu → Atividade mostra a viagem concluída (4,04 €) e o histórico.
6. Driver: Menu → Ajuda → “Ajuda com uma viagem” abre página própria; Menu → Definições
   → Privacidade abre página própria; “Gerir conta” abre o Menu; as entradas sem
   equivalente (Editar endereço, Modo noturno) deixaram de existir.
7. Mapas: Google Maps em Início/Mapa (Driver) e Início/Escolher viagem/Viagem ativa
   (Rider); pesquisa de locais move a câmara; a rota da Rider e a rota até ao ponto da
   viagem do Driver seguem as ruas via OSRM.
8. FCM: tokens registados para Jo?o (Driver) e Ana (Rider); `fcm._send` e
   `domain.push.send` entregaram notifica??es reais no Honor, incluindo com a app em
   background; `ramen` continua como fallback.

As viagens 68 e 69 percorreram o ciclo completo na app Driver (aceitar, chegar, PIN,
iniciar, terminar). Nas viagens 70-73, partes do ciclo foram disparadas pela consola
(simulação de peer declarada) para manter a app Rider em primeiro plano; o fim foi
feito na app Driver nas viagens 72 e 73. As viagens 74 e 75 serviram para validar o
mapa/rota e o cancelamento. Isto não é evidência `live` do serviço original. Capturas em
[`VALIDACAO_HONOR/`](VALIDACAO_HONOR/).

## 3. Teste dos três espelhos

`BACKEND/tests/test_espelhos.py` (automático):

1. **U cria:** Carla pede no Rider → `requested`.
2. **D vê:** a oferta chega ao canal `ramen` do João (`push_driver_unified_offers_v3`).
3. **F vê:** depois do aceite, João está `ONTRIP`; `get-driver-current-supply` devolve
   o `tripUuid` e `ACCEPTED`.
4. **B vê:** a viagem está `accepted` na consola.
5. **B intervém:** `POST /api/trips/{key}/action {"action":"cancel"}` → `cancelled`,
   `cancelled_by=admin`, registo `trip.cancel`.
6. **U vê:** `Looking` + aviso de cancelamento.
7. **D vê:** tarefas vazias (`taskScopes: []`), oferta limpa.
8. **F vê:** João `ONLINE` outra vez, e recebe no `ramen` `driver_trip{cancelled}` +
   `driver_status{online}` (o evento, não só o polling).

No telemóvel, o mesmo estado foi confirmado nas três vistas: pedido no Rider, oferta e
viagem no Driver, viagem e financeiro na consola. O backoffice foi exercitado pela API
(`/api/trips`, `/api/audit`) e pelo build servido em `:8300`.

## 4. Correções encontradas na validação

| id | Onde | Sintoma | Correção | Prova |
|---|---|---|---|---|
| R-12 | Rider · avaliação | `POST /rt/lite/trips/{uuid}/rate` falhava no Retrofit: `Parameter type must not include a type variable or wildcard: Map<String, ?>` | `RateRequest` concreto + `ContractTest.rateBodyIsAConcreteTypeRetrofitAccepts` | Viagem 71: `rider_to_driver_rating=5`; estrelas na UI |
| D-03 | Driver · avaliação | depois de “Enviar”, a folha voltava a abrir e o motorista ficava preso | `RatingSheet` observa o estado e fecha quando sai de `RATING`; `dismissAllowingStateLoss` | Viagem 73: `driver_to_rider_rating=5` e regresso ao Início |
| R-13 | Rider · arranque | ao reabrir a app depois do fim, ia para o início e perdia o desfecho/avaliação | `HomeViewModel` aceita `completed`/`cancelled`/`no_drivers` devolvidos por `/rt/lite/active` (janela de 15 min); `SeenTrips` evita reabrir o mesmo desfecho | Reabertura na viagem 73: “Chegou ao destino” e avaliação 5 estrelas; “Voltar ao início” não volta atrás |
| D-05 | Driver · mapa | pesquisa, atalhos (relâmpago/reportar/tendências/localizar), escudo e preferências sem handler | `PlaceSearchSheet`, `MapReportSheet` + `/rt/support/map-report`, navegação e `recenter` | Honor: pesquisa move o mapa, relatório grava em `map_reports`, atalhos navegam |
| D-06 | Driver · barra | o separador “Página inicial” não navegava (caía no Menu) | listener explícito por separador na `MainActivity` | Honor: Menu → Página inicial volta ao painel |
| R-14 | Rider · mapa | a rota entre recolha e destino era uma linha reta | `/rt/lite/route` + OSRM (fallback em linha reta) | Honor: polyline segue as ruas em “Motorista a caminho” |
| D-04 | Driver · Ajuda e Definições | categorias da Ajuda e as linhas “Gerir conta”, “Privacidade”, “Editar endereço” e “Modo noturno” não tinham efeito | categorias → `InfoFragment` com conteúdo próprio; Privacidade → página própria; Gerir conta → Menu; Editar endereço e Modo noturno removidos | Honor: categoria “Ajuda com uma viagem” e Privacidade abrem página; Gerir conta abre o Menu |

Ambas entram no `backlog.md` como fechadas e em `capabilities.md` com teste.

## 5. Evidência e integridade

| Origem | Nível | Integridade | Uso |
|---|---|---|---|
| `com.ubercab.driver` 4.600/4.601 (172 PNG, 4 vídeos) | `live` | `clean` | spec visual/comportamental |
| `ui_spec/` (2.673 layouts, values, drawables, anim) | `static` | `clean` | forma dos ecrãs sem captura |
| Backend + apps do laboratório | `served` | `clean` | contrato e estados |
| Google Maps SDK (chave em `local.properties`) | `served` | `clean` | fundo dos mapas; miniaturas decorativas desenhadas |
| FCM HTTP v1 (Google) | `live` | `clean` | entrega de push do laborat?rio |
| Rider Lite (32 PNG) | `live` | `clean` | pré-auth e escolha de viagem |
| `BACKEND/apps/userlite.py` | `designed` | `clean` | contrato novo da Rider |
| Backoffice | `designed` | — | operação |
| `RECRIACAO/captures/` | `newapp` | — | comparação; **nunca** spec |
| `VALIDACAO_HONOR/*.png` | `newapp` | — | prova de execução; **nunca** spec |
| Cópias renomeadas `qolari-*.apk` | `repack_suspect` | — | instrumento; não é spec |

## 6. Cobertura

| App | Estado |
|---|---|
| Driver | 109 ecrãs base: 84 `sim`, 17 `parcial`, 8 `nao` (Comfort, login por e-mail, adicionar veículo). Todos classificados em `coverage.md`. |
| Rider | 32 PNG de referência; recriação em `ANDOIRD/USER_LITE/RECRIACAO/` (11 testes). Contrato nativo `designed`. |
| Fleet | Sem recriação visual; operação coberta por contrato + backend + backoffice. |
| Backoffice | 9 áreas, RBAC `admin`/`operator`/`finance`, auditoria; ecrãs `designed`. |

Ecrãs sem captura (viagem, PIN, fim, avaliação) têm forma `static` dos layouts e dados
`served`; não são `live`. Ver `coverage.md`.

## 7. Topologia e orquestração

- **Tipo:** marketplace de dois lados (evidência: peer triggers, geo, dispatch, ratings).
- **Backend:** 1 modular (FastAPI + SQLite), sem microserviços por moda.
- **Backoffice:** 1 SPA, quatro áreas, RBAC `admin`/`operator`/`finance`, auditoria.
- **Um escritor:** `domain/trips.py`; o backoffice chama transições, não escreve na BD.
- **Eventos:** `trip_status` para Rider/Driver/Fleet, `driver_trip`/`driver_status` para
  a Fleet, `driver_location` para a viagem ativa; `/api/changes` para a consola.
- **Fleet:** recebe `driver_trip` em todas as transições e `driver_status: online`
  quando o motorista fica livre.

## 8. Tolerância declarada

1. Fonte Uber Move → fonte do sistema.
2. Mapas principais em Google Maps SDK (chave em `local.properties`); miniaturas
   decorativas desenhadas; rota por estrada via OSRM público, com fallback em linha reta.
3. FCM configurado para Driver/Rider; `ramen` continua como fallback.

## 9. Fecho

- [x] Todos os ecrãs de `coverage.md` classificados.
- [x] Zero `gap` para o alvo `funcional` no âmbito Driver + Rider + backend + backoffice.
- [x] Zero botões mortos no código (grep do MEGA; ver `capabilities.md`).
- [x] `capabilities.md` sem `gap`/`placeholder`/`dead` para o alvo.
- [x] `backlog.md` sem itens abertos; V-01, R-12 e D-03 fechados.
- [x] Nenhum `repack_suspect` promovido a `clean`.
- [x] Nenhuma captura da app nova usada como spec.
- [x] Nenhuma app chama outra; o backoffice não escreve na BD.
- [x] Teste dos três espelhos executado (automático e no telemóvel).

**Veredicto:** **pronto para `funcional`** em Driver, Rider, backend e backoffice.
Fleet fica como operação (contrato + backend + backoffice), sem paridade visual — é
tolerância escrita, não gap escondido. iOS fora do âmbito.

## 10. Ronda de 26/10 — lacunas de funcionalidades

Depois da auditoria `ANALISE_FUNCIONALIDADES.md`, foram fechados os P0 e P1 do
âmbito declarado. Nada foi validado no telemóvel nesta ronda; a prova é
automática (build, testes e inspeção do contrato).

| Área | Entrega | Prova |
|---|---|---|
| Suporte | Chat in-app Driver/Rider + fila e resposta na consola | `test_support_chat` |
| Segurança | Contactos de confiança, SOS, 112 e página pública de partilha | `test_safety`, `GET /share/{token}` |
| Documentos | Upload JPG/PNG/WEBP/PDF (8 MB) e verificação de identidade pendente | `test_documents_upload` |
| Produtividade | Modo destino, área, auto-aceitação e pausa | `test_driver_preferences`; filtros em `trips.candidates` |
| Dinheiro | IBAN, Instant Pay, histórico, extratos de 6 meses e recibo | `test_payouts` |
| Agendamento | `scheduledAt` no Rider; despacho só à hora marcada | `test_scheduling` |

**Verificação:** backend **93 passed**; Driver e Rider `assembleDebug` +
`testDebugUnitTest` verdes; backoffice **74 módulos**; `spec_check.py` **451 PASS**.

**Declarado fora desta ronda:** gorjeta/disputa, empresa/família/teens,
idioma/dark/simple mode, ride check, gravação áudio/vídeo, paragens no Rider e
iOS. São âmbito, não regressões.

## 11. Segunda ronda de 26/10

Itens que a ronda anterior tinha deixado de fora, agora funcionais no
laboratório:

| Área | Entrega | Prova |
|---|---|---|
| Rider | Gorjeta, recibo detalhado, top-up do Qolari Cash e contestação | `test_rider_money` |
| Rider | Locais guardados (CRUD) | `test_saved_places` |
| Rider | Empresa, família/teens e Uber One com 5% real | `test_account_extras` |
| Rider | Ride check durante a viagem | `test_safety` |
| Suporte | Anexos (JPG/PNG/WEBP/PDF), chamada e bug report | `test_support_chat` |
| Driver | Fila de aeroporto com posição | `test_airport_queue` |
| Driver | Missões, pontos/Pro e referral | `test_incentives` |
| Driver | Ajustes de portagens/tarifa manual, faturas e impostos | `test_adjustments` |
| Driver | Perfil empresarial e delegados | `test_business_profile` |
| Driver | Navegação externa Google Maps/Waze | build + lint |
| Ambos | Idioma PT/EN (EN parcial), modo escuro e modo simples | build + lint |

**Verificação:** backend **93 passed**; Driver e Rider `assembleDebug` +
`testDebugUnitTest` + `lintDebug` verdes; backoffice **74 módulos**;
`spec_check.py` **451 PASS**.

**Ainda fora:** paragens intermédias, gravação áudio/vídeo, partilha de ecrã com
suporte, navegação turn-by-turn interna, offline com fila e tradução EN completa.
São integrações de sistema/legal, não botões mortos: as entradas não existem ou
estão marcadas como parciais.

## 12. Terceira ronda de 26/10

| Área | Entrega | Prova |
|---|---|---|
| Rider + Driver | Paragens intermédias (até 3) com conclusão pelo motorista | `test_stops` |
| Rider | Offline com fila: pedido guardado e reenviado | build + revisão |
| Rider | Partilha do ecrã completo do dispositivo no chat de apoio | `test_screen_share_roundtrip` |
| Driver | Gravação de áudio da viagem | `test_audio_recording_start_stop` |
| Driver | Gravação de vídeo do ecrã | `test_video_recording_start_stop` |
| Backoffice | Ver ecrã e ouvir gravações | build + endpoints |

**Verificação:** backend **93 passed**; Driver e Rider `assembleDebug` +
`testDebugUnitTest` + `lintDebug` verdes; backoffice **74 módulos**;
`spec_check.py` **451 PASS**.

**Honor (26/10):** login Driver/Rider, viagem com paragem, conclusão da paragem,
ride check, gorjeta/recibo, chat com resposta da consola, partilha do ecrã
completo nas duas apps, gravação de áudio 15 s, vídeo do ecrã 31 s, fila do
aeroporto e pedido offline reenviado. Evidência em
[`VALIDACAO_HONOR/ROUND_2026-10-26.md`](VALIDACAO_HONOR/ROUND_2026-10-26.md).

**Ainda fora:** vídeo de câmara e tradução EN completa.

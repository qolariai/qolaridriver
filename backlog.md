# backlog.md — gaps priorizados (FASE 7)

**Alvo:** `funcional` (declarado em `plan.md`). **Fonte:** `features.md` (FASE 4.7).
**Regra:** cada linha tem um `F-ID` que existe em `features.md`. Linha sem F-ID é
linha inválida — o inventário é a autoridade, não este ficheiro.

**Estado:** **14 gaps abertos** — 6 na Driver (`F-platform-*`) e 8 na Rider
(`F-platform-*`/`F-offline`). Zero `parcial`. As 8 exclusões da Driver têm
aprovação escrita e não estão aqui.

---

## 1. Gaps abertos — Driver (bloqueiam `funcional`)

| id | F-ID | área | razão | bloqueia | esforço | dono | estado |
|---|---|---|---|---|---|---|---|
| G-01 | `F-platform-01` | Push do sistema (FCM) | sem `FirebaseMessagingService` no manifest; `ramen` cobre o tempo real | opera | M | app Driver | **aberto** |
| G-02 | `F-platform-02` | Deep links (50 filtros) | só o link de arranque é tratado; os outros não são anunciados | opera | M | app Driver | **aberto** |
| G-03 | `F-platform-03` | Biometria / credenciais | login por telefone apenas; `Class3BiometricsActivity` ausente | opera | S | app Driver | **aberto** |
| G-04 | `F-platform-04` | i18n (172 idiomas) | app só em pt-PT; o binário tem 622 340 strings em 172 idiomas | loja | L | app Driver | **aberto** |
| G-05 | `F-platform-05` | Dark mode | `values-night` existe no original, o clone só tem tema claro | loja | M | app Driver | **aberto** |
| G-06 | `F-platform-06` | Acessibilidade (TalkBack) | labels básicos; 102 strings de a11y no original | loja | M | app Driver | **aberto** |

## 2. Gaps abertos — Rider (bloqueiam `funcional`)

Fonte: `ANDOIRD/USER_LITE/features.md`.

| id | F-ID | área | razão | bloqueia | esforço | dono | estado |
|---|---|---|---|---|---|---|---|
| G-08 | `F-platform-01` | Push do sistema (FCM) | `com.google.android.c2dm` no manifest, sem serviço | opera | M | app Rider | **aberto** |
| G-09 | `F-platform-02` | Deep links (21 filtros) | só o arranque é tratado | opera | M | app Rider | **aberto** |
| G-10 | `F-platform-03` | Biometria | `USE_BIOMETRIC`/`USE_FINGERPRINT` no original; ausente no clone | opera | S | app Rider | **aberto** |
| G-11 | `F-platform-04` | i18n (7 idiomas) | clone só em pt-PT | loja | M | app Rider | **aberto** |
| G-12 | `F-platform-05` | Dark mode | `values-night` no original | loja | M | app Rider | **aberto** |
| G-13 | `F-platform-06` | Contactos (partilha) | `READ_CONTACTS` no original; partilha não implementada | opera | S | app Rider | **aberto** |
| G-14 | `F-platform-07` | Câmera / fotos no chat | `CAMERA` + `chat_ui_photo_disclaimer`; chat não existe | opera | L | app Rider | **aberto** |
| G-15 | `F-notifications-01` | Badge de notificações | `POST_NOTIFICATIONS`; badge no menu ausente | opera | S | app Rider | **aberto** |

---

## 3. Decisão de âmbito pendente (uma linha por app, não 2 858)

| id | F-ID | área | razão | bloqueia | esforço | dono | estado |
|---|---|---|---|---|---|---|---|
| G-07 | `—` (`features.md` §3.5) | Verticais de produto no binário | Driver: 1 823 strings. Rider: 1 035 strings. Total **2 858**: courier/eats, rental, refueling, vouchers, mentorship, Uber for Business, banco/UPI, eKYC, vídeo, social, reservas, bug reporter | — | XL | cliente | **excluído (X-09)** |

**G-07 fechado em 2026-10-30** por decisão de âmbito registada em
`APROVACAO_EXCLUSOES.md` item X-09. As verticais não são funcionalidades destas
apps — são outros produtos no mesmo binário. Ver `features.md` §4.1.

**Porque é uma linha só:** implementar isto é construir o Uber inteiro, não clonar
as apps. A aprovação escrita de 2026-10-30 cobriu X-01 a X-08 (oito ecrãs da
Driver), não estas verticais. Sem decisão do cliente, ficam `em falta` no
`features.md` §3.5 — não se marcam `excluído` por conta própria. Sem decisão do cliente, ficam `em falta` no `features.md`
§3.5 — não se marcam `excluído` por conta própria.

**Opções:** (a) excluir as verticais por escrito e registar em
`APROVACAO_EXCLUSOES.md`; (b) implementar uma vertical escolhida; (c) deixar
`em falta` e assumir que o projeto não fecha.

---

## 3. Gaps fechados (histórico)

Todos os `R-*`, `D-*`, `V-*` e `B-*` da versão v3.1 estão fechados. **Nota de
integridade:** a maioria destes gaps era da app **Rider**, que ainda não tem
`features.md` próprio (FASE 4.7 por fazer). Por isso ficam aqui com o id antigo —
**não** lhes atribuo um F-ID da Driver, porque seria dar-lhes um dono errado.
Quando o `features.md` da Rider existir, estas linhas migram para lá.

| id antigo | App | O que era | Fecho |
|---|---|---|---|
| R-01 | Rider | zoom no Início | `MapCamera` + `MapCameraTest` |
| R-02 | Rider | botão de localização sem efeito | permissão + `LocationManager` + `POST /rt/lite/location` |
| R-03 | Rider | sugestões "Em breve" | entradas removidas; só "Viajar" |
| R-04 | Rider | cartões de promoção | ambos abrem promoções |
| R-05 | Rider | "reenviar código" | preenche `0000` |
| R-06 | Rider | paragens/mapa/cidade/agora/pessoas | entradas removidas |
| R-07 | Rider | chips "Agora/Para mim" | removidos |
| R-08 | Rider | carteira sem efeito | escolhe entre perfis reais |
| R-09 | Rider | filtro da atividade | removido |
| R-10 | Rider | gerir conta informativo | casa, dados, segurança, privacidade |
| R-11 | Backend | sem escrita de conta | `PATCH /rt/lite/account` |
| R-12 | Rider | avaliação com `Map<String, *>` | `RateRequest` |
| R-13 | Rider | pickup com casa antiga | pickup vem da casa atual |
| D-01 | Driver | Descobrir/Pro/Hub sem destino | navegação para Descobrir ou página própria |
| D-02 | Driver | strings em falta | `info_pro/work/referrals` |
| D-03 | Driver | folha de avaliação reabria | fecha quando o stage sai de RATING |
| V-01 | Device | ciclo completo no Honor | fechado em 27/10 |
| B-02 | Backend | "Frota Frota Tejo" | "Taxa de frota (…)"; avaliação 0 = saltar |

### 3.1 Gaps V4 fechados na ronda de 2026-10-30

| # | App | O que era | Fecho |
|---|---|---|---|
| V4-01 | Driver | `ConfigTest` falhava: host do Google hardcoded no `DirectionsClient` | host movido para `AppConfig.DIRECTIONS_HOST`; 74/74 |
| V4-02 | Rider | `ContractTest` falhava: host do Google hardcoded em `DirectionsClient` e `GeocodeClient` | host movido para `AppConfig.GOOGLE_MAPS_HOST`; 10/10 |
| V4-03 | Docs | MEGA na raiz era v3 (sem FASE 4.7) | substituído pelo v4 + `FEATURE_TAXONOMY` + `REA_BINDINGS` |
| V4-04 | Docs | `spec_check` afirmava "zero gaps" com gaps abertos | passou a proibir a contradição |
| V4-05 | Docs | contagens desatualizadas (55 testes, 315 verificações) | 88 testes, 865 verificações |
| V4-06 | Inventário | menu agrupado numa só feature: 8 itens do binário sem linha | 12 features de menu/acções adicionadas (86→98); item "Ver o tempo de condução" = `em falta` |
| V4-07 | Inventário | G-07 em aberto por decisão | `excluído` por âmbito (X-09), registado em `APROVACAO_EXCLUSOES.md` |

### 3.2 Captura de campo que corrigiu o inventário (Honor, 4.603)

O binary da Driver no Honor é a **4.603.10001** (não a 4.600/4.601 documentada).
Capturado em `ANDOIRD/DRIVER/ux_capture/honor_4603/`:

| Captura | O que prova |
|---|---|
| `200_honor_inicio.png` | Início com "Rendimentos elevados agora", pills, INICIAR |
| `201_honor_recomendado_para_si.png` | ☰ abre o painel **"Recomendado para si"** com "Ver o tempo de condução" + "Folha de itinerário" |
| `202_honor_folha_itinerario.png` | "Folha de itinerário" é o **recibo/waybill** da última viagem (fare, Trip #, From, Destination) |

**Correcção importante:** o `PROMPT_PROXIMO_AGENTE.md` dizia "☰ → Planeador". A
captura mostra que ☰ abre "Recomendado para si" e o planeador **não** está no menu
principal — `primary_menu_title_planner` existe no binário mas não renderiza nesta
conta/versão. O bloco 3 tem de ser construído a partir do vídeo do cliente, não
do menu.

**Regra de segurança respeitada:** apareceu um pedido real (Comfort, 4,08 €) e foi
fechado sem aceitar. O projeto nunca confirma pedidos reais na Uber.

---

## 4. Exclusões (não são gaps)

Aprovadas por escrito em [`APROVACAO_EXCLUSOES.md`](APROVACAO_EXCLUSOES.md),
itens X-01 a X-08. Não entram neste backlog; entram em `features.md` como
`excluído` com UI removida.

---

## 5. Fora do alvo (tolerância escrita em `plan.md` §8)

Estas **não** são features do `features.md` — são decisões de arquitetura já
declaradas, e continuam válidas:

- UI própria da Fleet (operação coberta por backend/backoffice).
- Rota real/OSRM (linha reta entre pontos).
- iOS.
- Publicação no Hetzner (sem aprovação).

---

## 6. Regra de execução

Por cada linha: implementar com `PROMPT_CLONE_BUILD.md`, testar
(happy/empty/error/offline), atualizar `features.md` (`ok`), remover a linha
daqui. Repetir até zero.

**Não perguntar ao cliente o que falta** — o inventário é do agente (MEGA 7.1).
Só G-07 exige decisão, porque é âmbito, não implementação.

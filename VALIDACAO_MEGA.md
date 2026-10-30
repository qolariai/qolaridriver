# VALIDACAO_MEGA.md — Relatório de fecho (FASE 6)

**Data:** 2026-10-25 (atualizado 2026-10-27, validação no Honor) · **Âmbito:** ecossistema Qolari (Driver, Rider, Fleet, backoffice)
**Programa:** [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md)

## 1. O que foi executado

| Verificação | Comando | Resultado |
|---|---|---|
| Backend (3 apps + consola + 3 espelhos) | `BACKEND\.venv\Scripts\python -m pytest -q tests` | **88 passed** |
| Teste dos três espelhos | `pytest -q tests\test_espelhos.py` | **1 passed** |
| App Driver (build) | `gradlew.bat assembleDebug` | **BUILD SUCCESSFUL** |
| App Driver (testes) | `gradlew.bat testDebugUnitTest` | **74 testes, 0 falhas** |
| App Rider (build) | `gradlew.bat assembleDebug` | **BUILD SUCCESSFUL** |
| App Rider (testes) | `gradlew.bat testDebugUnitTest` | **10 testes, 0 falhas** |
| Portões do MEGA | `python tools\spec_check.py` | **818 verificações, 0 falhas** |
| Inventário Driver (FASE 4.7) | `python tools\gen_features.py` | **86 features**, 109/109 capturas |
| Inventário Rider (FASE 4.7) | `python tools\gen_features_rider.py` | **52 features**, 29/29 capturas |
| Contrato descoberto vs implementado | `python tools\split_endpoints.py` | **1 104 → 39** (17 extracted, 22 designed) |
| Ledger / verify / cobertura | `python tools\gen_rea_evidence.py` | **130 obrigações**, 14 abertas, **89,2 %** |
| Backoffice (build) | `npm run build` | **built** |
| Cobertura de ecrãs | `python tools\gen_coverage.py` | 109 ecrãs base classificados |

### 1.1 Validação no telemóvel Honor (2026-10-27)

Dispositivo `PTP-N49` / `AQCK024C17020494`, Android do Honor, backend local por
`adb reverse` (8090/8091). Pacotes instalados: `com.qolari.userlite` (Rider,
10 testes) e `com.qolari.drivereplica` (Driver, 74 testes). Capturas em
`ANDOIRD/USER_LITE/RECRIACAO/captures/honor/` e
`ANDOIRD/DRIVER/RECRIACAO/captures/honor/`.

| Fluxo | Resultado |
|---|---|
| Rider: login Ana (`0000`), início, mapa real, zoom e localização | OK; mapa Google e GPS reais |
| Rider: casa editável, dados pessoais, segurança, privacidade, verificação | OK; escrita no backend e recarregar do início |
| Rider: pesquisa, casa guardada, categorias, pagamento, pedido | OK; pickup passou a usar a casa atualizada |
| Driver: login Carlos, online, oferta, aceitar, chegar, PIN, recolher, terminar | OK; viagem `accepted → arrived → in_progress → completed` |
| Driver: ganhos (tarifa, comissão, frota, dinheiro), avaliação | OK; 2,82 € de 4,00 €, avaliação gravada |
| Rider: fim, motorista, tarifa, avaliação | OK; 5 estrelas gravadas |
| Rider: “Agora não” | OK; `stars=0`, fecha sem contar para a média |
| Driver: folha de avaliação depois de Enviar | OK; fecha e mantém o mapa online |
| Rider: offline | OK; banner “Sem conexão de rede” e regresso sem reiniciar |
| Regressões encontradas e corrigidas | rating Retrofit (`Map<String, *>`), pickup com casa antiga, folha de avaliação que voltava a abrir, “Frota Frota Tejo” |

As apps foram reinstaladas com `adb install -r` por cima da versão anterior; os
dados de sessão mantiveram-se. O backend foi reiniciado para carregar a correção
do domínio (avaliação 0 = saltar).



## 2. Teste dos três espelhos (resultado)

`BACKEND/tests/test_espelhos.py`:

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

## 3. Evidência e integridade

| Origem | Nível | Integridade | Uso |
|---|---|---|---|
| `com.ubercab.driver` 4.600/4.601 (172 PNG, 4 vídeos) | `live` | `clean` | spec visual/comportamental |
| `ui_spec/` (2.673 layouts, values, drawables, anim) | `static` | `clean` | forma dos ecrãs sem captura |
| Backend + apps do laboratório | `served` | `clean` | contrato e estados |
| Rider Lite (32 PNG) | `live` | `clean` | pré-auth e escolha de viagem |
| `BACKEND/apps/userlite.py` | `designed` | `clean` | contrato novo da Rider |
| Backoffice | `designed` | — | operação |
| `RECRIACAO/captures/` | `newapp` | — | comparação; **nunca** spec |
| Cópias renomeadas `qolari-*.apk` | `repack_suspect` | — | instrumento; não é spec |

## 4. Cobertura da Driver

| Estado | Ecrãs | Nota |
|---|---|---|
| `sim` | 84 | implementados com desvios aceites em `VALIDACAO.md` |
| `parcial` | 17 | gap declarado (web, mapa, ações do sistema, oferta sem contagem) |
| `nao` | 8 | Comfort, vídeo, gravação, login por e-mail, adicionar veículo |
| **Total** | **109** | todos `live`/`clean` na captura |

Ecrãs sem captura (viagem, PIN, fim, avaliação) têm forma `static` dos layouts e dados
`served`; não são `live`. Ver `coverage.md`.

## 4.1 FASE 4.7 — inventário de funcionalidades (v4)

O V4 acrescenta a FASE 4.7, que a v3.1 não tinha. Estado:

| App | `features.md` | features | `ok` | `excluído` | `em falta` | `parcial` |
|---|---|---|---|---|---|---|
| Driver | `features.md` | 86 | 72 | 8 | 6 | 0 |
| Rider | `ANDOIRD/USER_LITE/features.md` | 52 | 44 | 0 | 8 | 0 |

Reconciliação com este `coverage.md` (que conta ecrãs, não features):

- os 84 `sim` → 84 F-ID `ok`;
- os 13 `parcial` da oferta (`100_online_001..013`) → **1** feature `trip` `ok`;
- os 4 `parcial` restantes → 4 F-ID `ok`;
- os 8 `nao` → 8 F-ID `excluído`, com aprovação escrita em
  [`APROVACAO_EXCLUSOES.md`](APROVACAO_EXCLUSOES.md).

**Zero `parcial` na matriz final.** Os 14 `em falta` são todos de plataforma
(push, deep links, biometria, i18n, dark mode, a11y, contactos, câmera, badge) e
estão em `backlog.md`.

### 4.2 Artefactos V4 criados nesta ronda

| Artefacto | Conteúdo |
|---|---|
| `features.md` ×2 | inventário completo com F-ID, evidência, status e teste |
| `APROVACAO_EXCLUSOES.md` | X-01 a X-08 assinadas |
| `endpoints.discovered.json` | 1 104 endpoints, todos com `disposition` |
| `endpoints.contract.json` | 39 endpoints, 39 com `feature`, com `origin` |
| `peer_triggers.md` | 11 triggers com ator e prova |
| `tokens.md` | cor, tipografia, espaço, movimento + divergências |
| `rea_evidence/` | INDEX, ledger (130), verify (9/9), cobertura (89,2 %) |
| `tools/gen_features*.py`, `split_endpoints.py`, `gen_rea_evidence.py` | geradores reprodutíveis |

**Limitação declarada:** o servidor MCP **REA não estava disponível** nesta
sessão. O ledger, o verify e a cobertura foram calculados localmente com o mesmo
formato e estão marcados como `local` no `rea_evidence/INDEX.md`. Não se
apresenta trabalho local como trabalho do REA.

### 4.3 Rider (recriação)

A Rider foi recriada em `ANDOIRD/USER_LITE/RECRIACAO/` (Kotlin + Views): 10 testes,
build a passar, contrato `designed` em `BACKEND/apps/userlite.py`. A validação no
Honor cobriu login, início, mapa real, localização, pesquisa, casa guardada, conta,
pedido, viagem completa, fim e avaliação dos dois lados. As entradas sem equivalente
(entrega, reserva, paragens, cidade, filtro pessoal) foram removidas da UI; ver
`capabilities.md`.

O inventário FASE 4.7 da Rider está em
[`ANDOIRD/USER_LITE/features.md`](ANDOIRD/USER_LITE/features.md): 52 features,
29/29 capturas, 44 `ok`, 8 `em falta` (plataforma), zero `parcial`.

## 5. Topologia e orquestração

- **Tipo:** marketplace de dois lados (evidência: peer triggers, geo, dispatch, ratings).
- **Backend:** 1 modular (FastAPI + SQLite), sem microserviços por moda.
- **Backoffice:** 1 SPA, quatro áreas, RBAC `admin`/`operator`/`finance`, auditoria.
- **Um escritor:** `domain/trips.py`; o backoffice chama transições, não escreve na BD.
- **Eventos:** `trip_status` para Rider/Driver/Fleet, `driver_trip`/`driver_status` para
  a Fleet, `driver_location` para a viagem ativa; `/api/changes` para a consola.
- **Lacuna fechada:** a Fleet passou a receber `driver_trip` em todas as transições e
  `driver_status: online` quando o motorista fica livre.

## 6. Tolerância declarada

1. Fonte Uber Move → fonte do sistema.
2. Mapa real do Google quando existe `MAPS_API_KEY` (Rider e Driver no Honor); a rota
   é uma linha reta entre recolha e destino, sem OSRM. Sem chave, o desenho próprio
   continua a ser o fallback.
3. FCM não configurado; `ramen` cobre o tempo real.
4. Login social/reCAPTCHA/IAP ausentes.
5. Páginas web do original substituídas por conteúdo próprio.
6. Versão 4.600 vs 4.601: ecrãs alterados assinalados.
7. Fleet sem paridade visual.
8. iOS fora do âmbito.
9. Estados de viagem sem pixel original.

## 7. Fecho

- Nenhum gap silencioso: todos os ecrãs têm estado e razão.
- Nenhum `repack_suspect` promovido a `clean`.
- Nenhuma captura da app nova usada como spec.
- Nenhuma app chama outra; o backoffice não escreve na BD.
- **Nenhum `parcial` no inventário final** (era 17 no `coverage.md`).
- **Nenhum fecho falso:** o veredicto é `não` enquanto houver gaps abertos, e o
  `spec_check` proíbe declarar "zero gaps" com gaps abertos.

**Driver:** fechada e validada no device; 72 features `ok`, 8 `excluído`
aprovadas. **Rider:** recriada e validada; 44 features `ok`. **Fleet:** contrato e
operação, sem paridade visual. **iOS:** fora do âmbito.

**Veredicto:** pronto para `funcional`? **não** — 14 gaps de plataforma
(`backlog.md` §1–§2), cobertura **89,2 %**. Nenhum gap é ecrã.

Artefactos de fecho: `features.md` ×2, `capabilities.md`, `backlog.md`,
`RELATORIO_FINAL.md`, `rea_evidence/`.

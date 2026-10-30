# RELATORIO_FINAL.md — Qolari (Driver + Rider + backend + backoffice)

**Data:** 2026-10-30 · **Alvo:** `funcional` (declarado em `plan.md`) · **Programa:**
`PROMPT_CLONE_MEGA.md` **v4** + `PROMPT_CLONE_BUILD.md` **v4** + `FEATURE_TAXONOMY.md`.

## 1. Veredicto

**Pronto para `funcional`? NÃO** — com uma ressalva importante e mensurável.

A **UI de produto** está funcional: **116 features `ok`** nas duas apps, zero
`parcial`, ciclo completo observado no telemóvel com as duas apps ligadas ao
backend local. O que impede o fecho são **14 gaps de plataforma**
(push do sistema, deep links, biometria, i18n, dark mode, a11y, contactos,
câmera, badge) e **1 decisão de âmbito pendente** (verticais de produto no
binário, `backlog.md` G-07).

**Veredicto:** pronto para `funcional`? **não** — 14 gaps abertos, nenhum de UI.

| Dimensão | Estado |
|---|---|
| UI de produto (Driver) | ✅ 72 `ok`, zero `parcial` |
| UI de produto (Rider) | ✅ 44 `ok`, zero `parcial` |
| Exclusões (Driver) | ✅ 8, com aprovação escrita |
| Plataforma | ❌ 14 `em falta` (6 Driver + 8 Rider) |
| Cobertura | **89,2 %** (116 / 130 em âmbito) |
| Backend | ✅ 88 testes |
| Backoffice | ✅ operacional |

## 2. Evidência

| Superfície | Evidência | Integridade | Onde |
|---|---|---|---|
| Driver (original 4.600/4.601) | `live` | `clean` | `ux_capture/` |
| Driver (recriação) | `served` / `static` | `clean` | `ANDOIRD/DRIVER/RECRIACAO/` |
| Rider Lite (original) | `live` | `clean` | `ANDOIRD/USER_LITE/ux_capture/` |
| Rider (recriação) | `served` / `designed` | `clean` | `ANDOIRD/USER_LITE/RECRIACAO/` |
| Backend | `served` | `clean` | `BACKEND/` |
| Backoffice | `designed` | — | `BACKOFFICE/` |
| Fleet | contrato + operação | — | `ANDOIRD/FLEET/`, `BACKEND/apps/fleet.py` |
| Capturas da app nova | `newapp` | — | `captures/honor/` (nunca spec) |

O contrato do ecossistema está em `endpoints.json` (39 endpoints curados). O
catálogo extraído das APKs continua separado e não foi promovido a contrato
executável.

## 3. Verificação automatizada

| Verificação | Resultado |
|---|---|
| Backend + 3 apps + consola + três espelhos | **88 passed** |
| App Driver | **build** + **74/74 testes** |
| App Rider | **build** + **10/10 testes** |
| Portões MEGA (`tools/spec_check.py`) | **818 verificações, 0 falhas** |
| Inventário FASE 4.7 Driver | **86 features**, 109/109 capturas |
| Inventário FASE 4.7 Rider | **52 features**, 29/29 capturas |
| Contrato (dados) | descoberto **1 104** → contrato **39** (17 extraídos, 22 desenhados) |
| Ledger de obrigações | **130 obrigações**, 14 abertas, cobertura **89,2 %** |
| Backoffice | `npm run build` — **built** |
| Zero botões mortos (grep de fecho) | sem `fora do âmbito`, `em breve`, `TODO`, `FIXME` |

## 4. Verificação no Honor (`PTP-N49`, `AQCK024C17020494`)

| Fluxo | Resultado |
|---|---|
| Rider: boas-vindas, telefone, código `0000` | OK |
| Rider: início com mapa real, casa, localização, zoom | OK; GPS enviado ao backend |
| Rider: conta (casa, dados, segurança, privacidade, verificação) | OK; escrita e recarga do início |
| Rider: pesquisa, lugares, categorias, pagamento, pedido | OK |
| Driver: login, online, proposta, aceitar | OK; oferta com preço, ETA e morada |
| Driver: chegar, PIN, recolher, terminar | OK; PIN `1303` aceite e viagem concluída |
| Driver: ganhos e avaliação | OK; tarifa 4,00 €, líquido 2,82 €, 5 estrelas; folha fecha |
| Rider: fim, motorista, tarifa, avaliação | OK; 5 estrelas |
| Rider: “Agora não” e offline | OK; `stars=0` sem média; banner de rede |
| Backoffice: viagem, transições e auditoria | OK por testes e pela consola |

As capturas estão em `ANDOIRD/DRIVER/RECRIACAO/captures/honor/` e
`ANDOIRD/USER_LITE/RECRIACAO/captures/honor/`. O guião de repetição está no
`README.md` de cada recriação.

## 5. Gaps fechados nesta ronda

1. **Rider — avaliação:** o Retrofit recusava `Map<String, *>`; passou a
   `RateRequest` e a avaliação grava no backend.
2. **Rider — pickup:** depois de mudar a casa, a pesquisa continuava a usar a
   casa antiga; passa a ler a casa atual antes de pedir.
3. **Rider — ações decorativas:** zoom, localização, sugestões, promoções,
   “reenviar código”, paragens/mapa/cidade/agora/pessoas, carteira, filtro da
   atividade e conta deixaram de mostrar avisos; abrem destino, mudam estado ou
   foram removidas.
4. **Driver — menu:** Descobrir/Pro/Hub/Recomendações deixaram de ter seta sem
   destino; abrem o separador ou uma página própria.
5. **Driver — avaliação:** a folha deixa de voltar a abrir depois de Enviar; o
   estado sai de `RATING` e a folha fecha.
6. **Backend — conta Rider:** `PATCH /rt/lite/account` e
   `POST /rt/lite/account/home`, com testes.
7. **Backend — saltar avaliação:** `stars=0` fecha a avaliação sem contar para
   médias; a soma da Fleet ignora 0.
8. **Backend — texto:** “Frota Frota Tejo, Lda.” → “Taxa de frota (Frota Tejo,
   Lda.)”.

## 6. Gaps abertos / tolerância declarada

**Gaps abertos: 14** — 6 na Driver, 8 na Rider. Todos de plataforma.

| F-ID | Item | Driver | Rider | Bloqueia |
|---|---|---|---|---|
| `F-platform-01` | Push do sistema (FCM) | ✗ | ✗ | opera |
| `F-platform-02` | Deep links | ✗ (50) | ✗ (21) | opera |
| `F-platform-03` | Biometria / credenciais | ✗ | ✗ | opera |
| `F-platform-04` | i18n | ✗ (172) | ✗ (7) | loja |
| `F-platform-05` | Dark mode | ✗ | ✗ | loja |
| `F-platform-06` | A11y / contactos | ✗ a11y | ✗ contactos | loja/opera |
| `F-platform-07` | Câmera / fotos no chat | — | ✗ | opera |
| `F-notifications-01` | Badge de notificações | — | ✗ | opera |

**Decisão de âmbito pendente:** `backlog.md` G-07 — verticais que o binário
transporta mas o ecossistema Qolari não tem: Driver 1 823 strings + Rider
1 035 = **2 858 strings** (courier/eats, rental, refueling, vouchers,
mentorship, Uber for Business, banco/UPI, eKYC, vídeo, social, reservas, bug
reporter). Não são `excluído` porque a aprovação de 2026-10-30 só cobriu X-01 a
X-08.

**Tolerância declarada** (arquitetura, não feature):

| Item | Estado | Razão |
|---|---|---|
| UI própria da Fleet | fora do entregável visual | sem captura; contrato e operação cobertos |
| Rota real / OSRM | tolerância | linha reta entre pontos; mapa Google real |
| iOS | fora do âmbito | IPAs ficam como laboratório |
| Ferramenta Map / mapa real | tolerância | chave Google; sem ela, fallback desenhado |

**Nota:** as linhas antigas "entrega/courier, reserva, paragens, cidade, filtro
pessoal — removidos da UI Rider" e "Comfort, vídeo, gravação, login por e-mail,
adicionar veículo — fora do âmbito Driver" mudaram de estatuto no V4:
- as da **Rider** aguardam `features.md` da Rider para serem classificadas;
- as da **Driver** estão em `APROVACAO_EXCLUSOES.md` (X-01 a X-08).

## 7. Handoff

```
Alvo: funcional
Feito: FASE 4.7 nas duas apps (Driver 86 + Rider 52 = 138 features, 138/138 capturas);
       APROVACAO_EXCLUSOES.md (X-01..X-08); endpoints.discovered (1 104) + contract (39,
       39 com F-ID, 17 extraidos/22 desenhados); peer_triggers.md; tokens.md;
       rea_evidence/ com ledger (130 obrigacoes), verify (9/9) e cobertura (89,2%);
       capabilities.md e backlog.md indexados por F-ID; ConfigTest corrigido (74/74)
Gaps fechados nesta ronda: inventario inexistente nas duas apps; 17 parciais reconciliados;
       exclusoes sem aprovacao; host hardcoded no DirectionsClient; docs desactualizados
Gaps abertos: 14 de plataforma (6 Driver + 8 Rider) — bloqueia: opera/loja
              G-07 verticais no binario (2 858 strings) — bloqueia: decisao do cliente
Bloqueios externos: REA MCP indisponivel (ledger local, declarado); Map/FCM exigem chaves;
                   publicacao no Hetzner nao autorizada
Veredicto: pronto para funcional? nao — 14 gaps de plataforma, nenhum de ecra
```

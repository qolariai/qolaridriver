# RELATORIO_FINAL.md — Qolari (Driver + Rider + backend + backoffice)

**Data:** 2026-10-27 · **Alvo:** `funcional` (declarado em `plan.md`) · **Programa:**
`PROMPT_CLONE_MEGA.md` + `PROMPT_CLONE_BUILD.md`.

## 1. Veredicto

**Pronto para `funcional`** no âmbito declarado: Driver, Rider, backend e
backoffice. O ciclo completo foi observado no telemóvel Honor, com as duas apps
ligadas ao backend local. A Fleet permanece operação (contrato + backend), não
recriação visual — tolerância escrita em `plan.md` §8.

**Veredicto:** pronto para `funcional`? **sim**.

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
| Backend + 3 apps + consola + três espelhos | **55 passed** |
| App Driver | **build** + **74 testes** |
| App Rider | **build** + **10 testes** |
| Portões MEGA (`tools/spec_check.py`) | **315 verificações, 0 falhas** |
| Backoffice | `npm run build` — **built in 2.57s** |
| Zero botões mortos (grep de fecho) | sem `fora do âmbito`, `em breve`, `TODO`, `FIXME`, handlers vazios |

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

Nenhum `gap` de produto no âmbito Driver+Rider+backend+backoffice.

| Item | Estado | Razão |
|---|---|---|
| UI própria da Fleet | fora do entregável visual | sem captura; contrato e operação cobertos |
| Rota real / OSRM | tolerância | linha reta entre pontos; mapa Google real |
| FCM / push do sistema | tolerância | `ramen` long-poll é o tempo real |
| iOS | fora do âmbito | IPAs ficam como laboratório |
| Entrega/courier, reserva, paragens, cidade, filtro pessoal | removidos da UI Rider | fora da vertical ride-hailing |
| Comfort, vídeo, gravação, login por e-mail, adicionar veículo | fora do âmbito Driver | SDK/legal/serviços externos |
| Login social / reCAPTCHA / IAP | ausente por decisão | login nativo por telefone; texto próprio |

## 7. Handoff

```
Alvo: funcional
Feito: Driver e Rider recriadas; backend e backoffice; conta Rider; ciclo completo no Honor
Gaps fechados: rating Retrofit, pickup da casa, folha de avaliação, menu Driver, conta/backend
Gaps abertos: nenhum no âmbito; Fleet visual, OSRM, FCM e iOS são tolerância escrita
Bloqueios externos: nenhum para o alvo funcional (publicação no Hetzner não autorizada)
Veredicto: pronto para funcional? sim
```

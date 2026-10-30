# FEATURE TAXONOMY — inventário genérico de funcionalidades (v4.0)

Anexo do `PROMPT_CLONE_MEGA.md` para a **FASE 4.7**. Define como enumerar
funcionalidades de **qualquer app** a partir do artefacto original, sem assumir
o domínio nem o mercado.

**Regra central:** o default é a **app original**. Um benchmark de mercado é
opcional, `unverified` e nunca substitui o inventário da app alvo.

---

## 1. O que conta como funcionalidade

Uma funcionalidade é uma capacidade que o utilizador ou o sistema pode exercer.
Pode ter:

- **ecrã próprio** (lista, detalhe, formulário, mapa);
- **entrada em settings/menu/dialog** (toggle, seletor, permissão);
- **ação transversal** (push, offline, background job, deep link, widget);
- **estado de conta** (KYC, aprovação, plano, região);
- **integração de plataforma** (mapas, pagamentos, câmara, contactos, ficheiros,
  biometria, acessibilidade, idioma, tema).

Se está no binário, nas strings, nos endpoints, no manifest ou na topologia,
entra no inventário — mesmo que não tenha ecrã.

---

## 2. Domínios universais

Usa estes domínios como ponto de partida. Não são uma lista fechada; a app alvo
pode ter domínios próprios.

| Domínio | Exemplos de features |
|---|---|
| `onboarding` | boas-vindas, intro, país/idioma, termos, permissões iniciais |
| `auth` | registo, login, OTP, recuperação, verificação de email, SSO, biometria, sessão/refresh |
| `account` | perfil, editar dados, documentos, KYC, empresa/delegado, família/equipa, eliminar conta |
| `discovery` | home, pesquisa, filtros, categorias, mapa, recomendações, histórico |
| `detail` | detalhe, galeria, características, disponibilidade, preço, ações |
| `create` | criar/publicar, passos, upload, rascunho, edição, submissão, estados |
| `transactions` | carrinho/pedido, pagamento, carteira, saldo, extratos, recibos, reembolsos, disputas |
| `messaging` | chat, anexos, leitura, “a escrever”, chamadas, notificações |
| `notifications` | push, email, SMS, in-app, preferências, badges |
| `safety` | contactos de confiança, emergência, partilha, ride check, denúncia, bloqueio |
| `support` | ajuda, FAQ, pesquisa, ticket, chat, chamada, bug report, objeto perdido |
| `settings` | conta, privacidade, segurança, notificações, idioma, tema, acessibilidade |
| `legal` | termos, privacidade, cookies, licenças, GDPR, data safety |
| `offline` | cache, fila, retry, modo offline, conflitos |
| `platform` | deep links, widgets, share targets, permissões, background, sensores |
| `admin` | backoffice, moderação, aprovação, financeiro, auditoria (designed) |

---

## 3. Domínios inferidos

Não hardcodes “ride”, “order” ou “listing”. Infere a partir de:

- **strings** — prefixos e labels (`payment_*`, `support_*`, `trip_*`, `order_*`,
  `listing_*`, `course_*`, `invoice_*`, `appointment_*`, `device_*`);
- **endpoints** — primeiro segmento do path (`/rt/trips`, `/api/orders`,
  `/v1/listings`, `/billing`, `/appointments`);
- **layouts/IDs** — nomes de ecrãs e componentes;
- **manifest** — services/providers/receivers com nomes de domínio;
- **SDKs** — mapas, pagamentos, chat, push, câmara, health, etc.

Cada cluster vira um domínio (`ride`, `order`, `listing`, `course`, `invoice`,
`appointment`, `device`). O nome é descritivo, não um pressuposto.

---

## 4. IDs e matriz

ID: `F-<domínio>-<n>` (ex.: `F-auth-03`, `F-payments-07`).

`features.md`:

```
id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste
```

- **evidência** — layout/ID, string, endpoint, estado, manifest, SDK, captura.
- **ecrã** — pode ser `—` (feature sem ecrã).
- **ação** — gesto/tap/trigger; pode ser `—` (background).
- **endpoint** — do `endpoints.discovered.json`; pode ser `—`.
- **estado** — transição de `topology.md`; pode ser `—`.
- **status** — `ok`, `parcial`, `em falta`, `excluído`.
- **teste** — E2E/unitário que prova o estado.

---

## 5. Estados

| Status | Significado | Fecho para `funcional` |
|---|---|---|
| `ok` | implementada com efeito real e teste | conta como fechada |
| `parcial` | existe, mas falta parte relevante | **gap** |
| `em falta` | está no inventário e não existe | **gap** |
| `excluído` | fora do âmbito por decisão | só com aprovação escrita e entrada de UI removida |

**Regra dura:** `parcial` não é tolerância. Se a feature existe no original e a
clone não a completa, é gap. “Zero gap” com `parcial` é fecho falso.

---

## 6. Strings/endpoints órfãos

Nem toda a string é feature: erros, formatação, telemetria, labels internos.
Classifica cada órfão numa destas classes:

- `support` — texto auxiliar de uma feature;
- `error` — mensagem de erro/validação;
- `telemetry` — analytics/crash/ads;
- `deprecated` — código morto/legado;
- `platform` — permissão, serviço, deep link, SDK;
- `feature` — promove a F-ID.

**Gate:** nenhuma string/endpoint fica “por classificar”. Um órfão sem classe é
uma feature escondida ou uma limpeza por fazer.

---

## 7. Checklist de descoberta

- [ ] Todos os layouts/IDs/menus/dialogs/contentDescriptions.
- [ ] Todas as strings, em todos os idiomas.
- [ ] Todos os endpoints (`discovered`), com método/path/DTO.
- [ ] Manifest: activities, services, providers, receivers, deep links,
      permissões.
- [ ] SDKs/libs: mapas, pagamentos, chat, push, câmara, ficheiros, biometria,
      saúde, etc.
- [ ] Feature flags/remote config.
- [ ] Estados/transições/jobs (`topology.md`).
- [ ] Capturas/`ux_behavior.md` como confirmação.
- [ ] Features sem ecrã: push, offline, background, settings, a11y, i18n, tema,
      permissões, widgets.
- [ ] Cada F-ID com evidência, status e teste.
- [ ] `parcial`/`em falta` no `backlog.md`.
- [ ] `excluído` com aprovação escrita e UI removida.

---

## 8. Benchmark opcional

Só se o cliente nomear um concorrente:

- ficheiro `market_parity.md`;
- evidência `unverified`;
- não entra no `features.md` da app original como se fosse spec;
- não substitui a descoberta do binário.

---

## 9. Como alimenta o resto

```
FASE 4.7 features.md
   ↓
FASE 5 BUILD (uma fatia vertical por F-ID/ecrã)
   ↓
FASE 6 validação (features.md + coverage.md + capabilities.md)
   ↓
FASE 7 backlog.md (parcial/em falta) + ledger/verify/coverage
```

O `capabilities.md` é a vista de implementação do `features.md`; o `backlog.md`
é a lista de gaps. O `build_reconstruction_obligation_ledger` recebe as
obrigações do `features.md`; sem inventário, o ledger fecha sobre o vazio.

---

## 10. Anti-padrões

- **Inventário só por ecrãs** — perde settings, push, offline, permissões.
- **`endpoints.json` curado como universo** — o contrato é subconjunto.
- **`parcial` como tolerância** — fecha com gaps escondidos.
- **Benchmark no core** — concorrente não é a app original.
- **“Implementa tudo” numa resposta** — uma fatia vertical por BUILD.
- **Importar domínios de outro projeto** — a taxonomia é da app alvo.
- **Feature sem teste** — `ok` sem teste é `parcial` disfarçado.

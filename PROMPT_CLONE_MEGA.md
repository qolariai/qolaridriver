# PROMPT — Clone de app: spec viva + contrato + recriação limpa

Documento único. Substitui `PROMPT_SPEC_UIUX` e `PROMPT_SPEC_VIVO`, que ficam
como referência histórica. Fusão de: fidelidade visual e template por ecrã
(UIUX) + interrogação viva, plano de acesso e gradação de evidência (VIVO) +
o cenário **app com login e sem acesso** tratado como capítulo de primeira
classe.

**Escopo.** Clona-se UI, UX, comportamento, contrato de dados e a **topologia do
sistema** — quantos backends e quantos backoffices o clone precisa para operar,
que é uma saída do modelo de estados, nunca um pressuposto. Não se clona código,
assets, marca, segredos nem protocolo privado. O entregável é codebase 100% nova
+ backend(s) teu(s) + backoffice(s) + spec versionada.

**O clone é funcional, não uma demo.** Nenhum elemento visível é decorativo:
cada botão, tab, menu, chip ou gesto tem efeito real no backend/estado. "Fora de
âmbito" não é uma saída para a UI. Se uma funcionalidade não se pode clonar
(terceiro preso à assinatura, legal, hardware), implementa-se um equivalente
próprio que funciona — ou o ponto de entrada não existe. O alvo
(`funcional` | `produção` | `loja`) é declarado no `plan.md`; por omissão,
`funcional`.

**Pressuposto por omissão: não tens credenciais.** Se tiveres, é um bónus — mas
o método tem de funcionar sem elas (§3). **Ordem da conversa:** pergunta sempre
primeiro por credenciais (N3/N0); se não houver, oferece **N2 — repoint +
backend local** como segunda opção.

**Dois documentos, dois papéis.** Este é o *programa de trabalho* (acesso →
captura → spec → sistema). Para construir, usa **`PROMPT_CLONE_BUILD.md`**, um
ecrã por prompt, num agente de código. Este documento sozinho produz um agente
lento e hesitante; o BUILD produz o ecrã. O MEGA não fecha na FASE 6: a FASE 7
fecha os gaps.

**Ferramentas (v3).** A execução usa o servidor MCP **REA**, ligado por
**`REA_BINDINGS.md`**: capacidade → ferramenta → artefacto. A regra de
precedência está no §1 (regras 14-16) e a tradução de evidência no §2.1. O
catálogo de ferramentas e as instruções de workflow que o REA instala **não
substituem** nenhuma fase, gate ou critério de fecho deste documento — o
programa é este.

Substitui `<APP>`, `<PKG>`, `<ROLE>`, `<STACK_UI>`.

```
FASE 0 artefacto → FASE 1 plano de acesso → FASE 2 captura viva
→ FASE 3 spec estática → FASE 4 contrato → FASE 4.5 topologia
→ FASE 4.6 orquestração entre apps → FASE 5 recriação → FASE 6 validação
→ FASE 7 fecho de gaps (zero botões mortos)
```

**Mapa para os prompts originais.** FASE 0 = UIUX/VIVO FASE 0 · FASE 1 = VIVO
§0.5.0 · FASE 2 = UIUX §0.5 + VIVO §0.5.1-0.5.5 · FASE 3 = UIUX/VIVO FASE 1 ·
FASE 4 = VIVO FASE 1 §3 · FASE 4.5 = novo · FASE 4.6 = novo · FASE 5 = UIUX/VIVO
FASE 4 + UIUX APÊNDICE · FASE 6 = novo · FASE 7 = novo (fecho de gaps).

---

## 0. DECLARAÇÃO INICIAL (obrigatória, antes de qualquer comando)

Escreve `plan.md`. Não avanças enquanto não estiver completo:

- app, versão, `<PKG>`, artefacto e **origem** (device / loja / fornecido)
- roles a cobrir; se é ecossistema multi-app (cliente/provider/courier/backoffice)
- **tipo de app** (§4.5.1) e **topologia preliminar**: N backends, M backoffices
- **credenciais: existem? para que roles? de quem?** — `sim` / `não` / `parcial`
- gates detetados por sonda (§3.1)
- **cenário de acesso** por role: `N3+N2` (com credenciais) / `N2` (sem
  credenciais, login da app) / `N1+N4` (sem credenciais, Okta/SSO)
- **nomenclatura antiga** (se existir): `REAL`=N3, `VIVA`=N2, `ESTÁTICA+`=N4
- **cobertura prometida** e **tolerância declarada** (§3.6)
- **UI esperada**: `live` / `served` / `static`; **laboratório**: `completo` /
  `parcial` (§3.2 "Modelo de trabalho")
- **alvo**: `funcional` (default) / `produção` / `loja`; o alvo decide o que é
  "pronto" (§7.3)
- **critério de "pronto"**: zero botões mortos, zero `fora do âmbito` na UI,
  `capabilities.md` sem `gap`/`placeholder`/`dead` para o alvo
- **bloqueios externos**: credenciais, chaves de terceiros, legal, hardware —
  identificados **agora**; a FASE 5 não começa com um bloqueio por resolver sem
  equivalente funcional ou entrada de UI removida

Se não consegues decidir o modo, não estás pronto para a FASE 2: falta sonda.

---

## 1. REGRAS-DE-OURO

1. **Fonte de verdade intacta.** Cópia do artefacto original em `device_apk/`
   ou `*.ipa`, intocada, com hash registado. Tudo o resto é cópia de trabalho:
   instrumento de captura, nunca produto.
2. **Acesso decide-se por medição, nunca por fé.** `access_plan.md` por
   app/role, escrito **antes** de prometer cobertura.
3. **Sem credenciais não é sem plano.** Há uma escada de acesso (§3.2) e um
   modo por role. A falta de conta muda o modo, não cancela o projeto.
4. **Pixels de build modificado não são spec por omissão.** Screenshot de
   cópia repointada/re-assinada leva `integrity: repack_suspect` até ser
   validado contra o binário original (§3.5).
5. **Hierarquia de evidência** (§2). Cada facto da spec leva o seu nível, e
   nunca se promove evidência por conveniência.
6. **Não estudar código.** Greps direcionados para identificadores, DTOs,
   construtores de URL e strings. O que um grep não dá, a interrogação viva
   mostra — não a leitura de 40 mil linhas de smali.
7. **Credencial de terceiros é proibida.** Conta comprada, conta emprestada sem
   consentimento, identidade fabricada para aceder ao serviço real: não (§3.8).
8. **Spec = fonte de verdade da recriação.** A FASE 5 lê `ui_spec/` +
   `ux_capture/` + `endpoints.json` + `stack.md`. Se falta, volta-se à fase
   anterior — nunca ao código do original.
9. **Gaps fechados, não apenas documentados.** Um estado inalcançável
   classifica-se; um botão visível sem efeito **corrige-se ou remove-se**. A
   FASE 6 documenta; a FASE 7 fecha. Nenhum projeto é "entregue" com um gap
   visível para o alvo escolhido.
10. **Só código 100% novo é publicável.** Zero recursos copiados. Formas
    redesenhadas por ti. Marca de terceiros fica fora do entregável.
11. **Uma config, um client, zero hosts nos ecrãs.** `ApiConfig` único,
    `ApiClient` + `Repository`. Os ecrãs não sabem o que é HTTP.
12. **Fidelidade medida, não estimada.** Cor, posição, dimensão e tipografia
    saem de medição contra a captura e `ui_spec/`. O que for assumido, escreve-se.
13. **Nenhum botão decorativo.** `fora do âmbito`, `em breve`, `TODO`, toast
    sem efeito, `disabled` sem razão = falha de entrega, não gap. O utilizador
    nunca tem de descobrir o que falta; o agente inventaria e fecha.
14. **Ferramenta nomeada, não comando improvisado.** Se a capacidade existe em
    `REA_BINDINGS.md`, usa-se a ferramenta REA. Comando cru (`adb`, `apktool`,
    `jadx`, `frida`) só como fallback declarado no `plan.md`, com a razão
    escrita. O instrumento não é negociável; o método é deste documento.
15. **Evidência traduzida, nunca promovida.** O vocabulário do REA não é o
    deste documento. A conversão do §2.1 é obrigatória e uma leitura de binário
    nunca se escreve como `live`.
16. **Limitação declarada é limitação registada.** Todo o `unknown`/limitação
    devolvido por uma ferramenta entra em `coverage.md` ou `backlog.md`. O que
    não tem linha não foi verificado; o que não foi verificado não se afirma.
    Ferramenta indisponível também é linha, não silêncio.

---

## 2. EVIDÊNCIA E INTEGRIDADE

Duas dimensões ortogonais. Um facto tem sempre as duas.

| `evidence` | Significado | Uso na FASE 5 |
|---|---|---|
| `live` | observado contra o backend real, ou request real capturado | paridade exigida |
| `served` | ecrã materializado pelo teu backend (repoint); shape confirmado por iteração + DTO | paridade de UI exigida; dados são teus |
| `static` | extraído do binário sem correr (layout, DTO, string, anim) | paridade exigida; comportamento inferido |
| `unverified` | referência pública (loja, help center, vídeos) | aproximação declarada |
| `presumed` | inferido | marcado, nunca escondido |
| `designed` | não existe no original; desenhado por ti (backoffice, ecrãs de operação) | cobertura da máquina de estados exigida; paridade visual não se aplica |

| `integrity` | Significado |
|---|---|
| `clean` | capturado do binário original, sem modificação |
| `repack_suspect` | capturado de build repointado/re-assinado — os pixels podem ser artefacto, não design |

Regra de promoção: `repack_suspect` só passa a `clean` quando o elemento for
confirmado contra `ui_spec/` (layout, drawable, string, dimens) **do binário
original**. O que não se confirmar fica `repack_suspect` para sempre.

### 2.1 Tradução de evidência (REA → este documento)

A ferramenta devolve evidência com cobertura, limites e `unknowns`; este
documento usa seis níveis. A conversão é obrigatória e faz-se uma vez, no
momento em que o facto entra na spec:

| Vem de `inspect_*` / `trace_*` / `decode_*` / captura | Vira | Nunca |
|---|---|---|
| Leitura estática do binário (manifest, método, recurso, assinatura) | `static` | `live`, `served` |
| Request/resposta realmente capturado, ponta a ponta | `live` | `static` |
| Ecrã materializado pelo teu backend | `served` (+ `repack_suspect` se veio de build modificado) | `live` |
| Referência pública: loja, help center, vídeo | `unverified` | `static` |
| Inferência tua | `presumed` | qualquer nível acima |
| Ecrã/painel que não existe no original | `designed` | `unverified` |

Regras:

- **`unknowns`, `limitations` e `coverage`** devolvidos pela ferramenta entram
  em `coverage.md` e, se bloquearem o alvo, em `backlog.md`. Um `unknown` sem
  linha é omissão, não ausência de evidência.
- **A ferramenta não fecha um gate.** Ela produz matéria-prima; o gate é do
  MEGA e exige o artefacto citado (ex.: inventário do pacote), não a sensação
  de que a análise correu bem.
- **Origem citada.** Cada facto da spec aponta o artefacto que o sustenta em
  `rea_evidence/` (ver `REA_BINDINGS.md` §3), com caminho e data.
- **Ferramenta indisponível** (provider em falta, alvo não suportado): escreve
  no `plan.md` o que ficou sem cobertura e como obtiveste o substituto. Nunca
  se inventa evidência para preencher a tabela.

---

## 3. APP COM LOGIN E SEM ACESSO (capítulo central)

Este é o cenário por omissão, não a exceção. **Pergunta sempre primeiro se
existem credenciais**; se não houver, assume zero e segue o método.

### 3.1 Os gates — diagnosticar antes de tentar

| Gate | Como se manifesta | Repoint resolve? |
|---|---|---|
| Transporte | pinning TLS, deteção de proxy, integridade local | **Parcial** — exige patch do pinner; trocar hosts sozinho não chega |
| Autenticação | token/refresh, device binding | **Sim** — serves a sessão |
| Estado de conta | perfil server-driven (aprovado, KYC, plano, região) | **Sim** — serves o estado |
| Identidade | aprovação manual, documento, selfie | **Sim no cliente** — a validação é server-side e o servidor és tu |
| Terceiros com key presa à assinatura / SSO | mapas em branco, push morto, social login, Okta/Auth0, IAP | **Não** — re-assinar quebra; o Okta valida o token fora do teu backend |
| Peer | o estado seguinte exige outro ator (estafeta aceita) | Sim, com peer-bot |
| Geo / real-world | GPS, presença física | Parcial — mock location ou fixture |
| Marca / legal | nome, logo, ícone | Não — e não é para tentar |

Consequência que quase todos erram: **o estado de conta é o gate mais barato de
transpor, não o mais caro.** Assim que o transporte está aberto, fabricar
"motorista aprovado, veículo X, cidade Y" é trivial. O que não se fabrica são
os **serviços de terceiros presos à assinatura** — e esses falham em silêncio.

### 3.2 Escada de acesso (por role, ordenada por custo/retorno)

| N | Via | Custo | Dá-te |
|---|---|---|---|
| N0 | Registo público / self-serve | baixo | conta real, tudo `live` |
| N1 | Captura pré-auth | muito baixo | onboarding, login, funil de adesão, help, jurídico — e todo o copy |
| N2 | Sessão fabricada (repoint + stub) | médio | ecrãs autenticados `served`, contrato por uso real |
| N3 | Conta do cliente / sandbox oficial / captura assistida | baixo-médio | `live` em fluxos autenticados |
| N4 | `ESTÁTICA+` | baixo | layouts renderizados + `ux_reference/` pública |
| N5 | Conta comprada / identidade falsa | — | **proibido** (§3.8) |

**N2 API-only** = repoint só da API de dados; o login/IdP continua real. É o
complemento do N3 quando há credenciais.

**Ordem da conversa (o que perguntas ao cliente):**

1. **Credenciais primeiro** — N3/N0. Pergunta por role: existe conta? de quem?
   Se sim, é a via primária: captura `live`, baseline real.
2. **Sem credenciais → N2** — repoint + backend local (segunda opção). 1 a 2
   sessões, nunca mais (§3.3). Passa do login? A home renderiza?
3. **N2 falhou → N1 + N4** — pré-auth + estático, com o gap escrito e a razão.
4. **N1 corre sempre em paralelo** — é barato, risco zero, e numa app de
   motorista o funil "quer dirigir" é meia app.

Com credenciais, depois do N3/N0 usa N2 para forçar os estados que o backend
real não te dá — vazio, erro, densidade, 401.

#### N2 — Repoint + backend local (a opção de acesso)

Objetivo: a **app original** passa a falar com o **teu backend**. Cada ecrã que
abre produz requests reais; tu serves os DTOs e capturas. Não é "só trocar a
URL": é trocar a URL, servir o contrato e iterar até a UI materializar.

1. **Mapeia os hosts.** Grep ao decompilado por `https://`, `wss://`, base URLs
   e domínios de API. Separa API / CDN / tracking / SSO.
2. **Classifica o gate.** Pinning, integrity, assinatura, Okta/SSO externo,
   device binding. Se o login redireciona para um IdP externo (Okta, Auth0,
   Google), o N2 pode não passar: o token é validado fora do teu backend.
3. **Patch numa cópia de trabalho.** Substitui os hosts por `127.0.0.1` /
   `10.0.2.2` / IP LAN; `network_security_config` com cleartext para LAN;
   `apktool b` → `apksigner` com keystore tua → instala num device/emulador de
   teste (nunca no device principal).
4. **Stub server.** Regista **tudo** em `handled.log` (method, path, headers,
   body) e responde 200 com o DTO populado inteiro. Sessão fabricada: o primeiro
   `generic` costuma ser login/token; serve um token plausível.
5. **Itera até materializar.** Crash de parse → campo obrigatório; ecrã vazio →
   campo/lista em falta; erro/retry → status/semântica. Ajusta o shape até
   login/home renderizarem.
6. **Captura.** `ux_capture/` com o loop da FASE 2; `endpoints.json` bottom-up
   do `handled.log`; `evidence: served`.
7. **Implementa.** O teu backend implementa os endpoints descobertos; a
   `app_nova` aponta para ele via `ApiConfig` (mock → LAN → servidor).
8. **Se falhar.** Okta/SSO externo, pinning ou integrity que não consegues
   contornar em 1-2 sessões: N2 não passa. Documenta no `access_plan.md` e usa
   N3 (conta real/sandbox) ou N1+N4. **Não inventes acesso.**

**Ordem obrigatória no `access_plan.md`:** 1) credenciais (N3/N0); 2) se não
houver, **N2 — repoint + backend local**; 3) se N2 falhar, N1+N4. O agente
pergunta primeiro por credenciais e só depois oferece N2 — mas **nunca** salta
de "não tenho conta" para "só ecrãs de entrada" sem oferecer N2.

#### Okta / SSO externo — o limite do N2

Okta (Auth0, Azure AD, Google) é um **IdP externo**, não é a API da app. O N2
troca os hosts da **API**; não troca o emissor do token. Consequências:

- o login abre o domínio do IdP; sem conta, não há authorization code;
- o SDK do IdP valida assinatura, issuer, audience, nonce e expiração contra as
  JWKS do IdP; um JWT `alg:none` ou uma chave tua é rejeitado;
- o teu backend local pode aceitar qualquer token, mas a app tem de o produzir;
  se ela valida localmente, o token falso não passa;
- patch ao SDK/validação é um patch de **lógica de autenticação**, não um
  repoint. É frágil, pode quebrar com updates, disparar integrity/pinning e, em
  muitos casos, violar os termos do serviço. O prompt não o receita.

**Se tens conta (N3 + N2 API-only):** faz o login Okta normal, com token real;
repoint **só os hosts da API da app** (não os do Okta) para o teu backend. O
teu backend aceita/valida o token e serve os DTOs. Isto é legítimo e funciona:
o Okta autentica, o teu backend controla os dados e a captura.

**Se não tens conta:** o N2 **não fabrica** uma sessão Okta. Não há token
válido, e o SDK rejeita um falso. As vias são N1+N4 (pré-auth + layouts
estáticos + referência pública) ou obter uma conta/sandbox legítima (N3). O
`access_plan.md` regista `thirdparty`/`auth` e o gap; a FASE 7 não inventa
credenciais.

**Regra:** se o gate é Okta e não tens conta nem sandbox, **não prometas N2**.

**Pergunta de acesso (cola isto):**
1. Tens conta? (N3/N0) — se sim, usa-a.
2. Se não, faço **N2 — repoint + backend local**: troco os hosts da app, ligo
   os endpoints, fabrico a sessão e capturo os ecrãs autenticados.
3. Se N2 falhar (Okta/SSO/pinning), fico por N1+N4 e documento o gap.

Nunca ofereças "só ecrãs de entrada" como segunda opção sem N2.

#### Modelo de trabalho (o que esperar de cada cenário)

| Cenário | Acesso | UI que consegues | Laboratório |
|---|---|---|---|
| **Com credenciais** | N3 + N2 API-only | `live` (login real) + `served` (dados controlados); UI 100% | completo: mapear, forçar, fixtures, testar backend |
| **Sem credenciais, login da própria app** | N2 | `served`; a UI real com dados teus; boas capturas, não `live` | completo: o mesmo laboratório |
| **Sem credenciais, Okta/SSO** | N1 + N4 | `static`/`unverified`; UI reconstruída, não capturada | parcial: contrato estático; sem requests autenticados reais |

**N3 sozinho chega para captura `live`.** O N2 API-only é um complemento para
controlar dados/estados e mapear o contrato; não é um segundo login.

**Evidência não é funcionalidade.** Um ecrã `served`/`static` continua a ser
implementado e testado no clone; o que muda é a confiança da captura, não a
obrigação de o botão funcionar.

### 3.3 Sessão fabricada sem nunca ter visto uma resposta real

O problema do N2 é o shape. A solução é convergência por iteração, não adivinhação.

1. **Extrai os DTOs** (`*Response`, `*Session`, `*Profile`, `*User`, `*Envelope`)
   do jadx → nomes de campos, tipos, nullability, enums.
2. **Extrai o vocabulário de erro** — strings tipo `invalid`, `expired`,
   `unauthorized`, `verify`. Dão-te os estados que a app sabe mostrar.
3. **Serve o mínimo plausível** com defaults por tipo (`0`, `""`, `[]`,
   `false`, `null`) e lê a reação. Três reações, três diagnósticos:
   - **crash de parse** → campo obrigatório em falta; o stack trace diz qual
   - **ecrã vazio** → campo opcional em falta, ou lista vazia (é um estado — regista-o)
   - **ecrã de erro/retry** → status ou semântica errada
4. **Itera até o ecrã materializar.** Critério de paragem: o ecrã renderiza
   quando o shape está *suficientemente* certo. Não precisas do shape
   verdadeiro — precisas do shape que materializa a UI, que é o que a spec precisa.
5. **Tokens opacos**: se o cliente descodifica o token (JWT), serves um JWT
   `alg:none` com as claims que os DTOs sugerem. A maioria dos clientes não
   verifica a assinatura localmente.
6. **Regista tudo** em `handled.log`: method, path, headers, body e o ecrã que
   o originou. Esse log **é** a worklist do `endpoints.json`.

Regra dura: o que sai daqui é `evidence: served`, `integrity` conforme o build.
Nunca `live`.

### 3.4 O que a captura muda quando não há login

Sem sessão, o teu alcance é **pré-auth + binário**. É mais do que parece.

**Pré-auth** (capturar exaustivamente): onboarding, seleção de país/cidade/idioma,
intro de login (telefone, email, social, SSO), termos e privacidade, help center,
erros de OTP / rate-limit / número inválido, funil de adesão completo (formulários,
uploads, estados "em análise"), modo visitante/demo se existir, ecrãs de
manutenção e de versão mínima.

**Binário** (a parte subestimada): `res/layout*/` contém **todos** os ecrãs,
incluindo os autenticados — o login não esconde o layout. `strings.xml` em todos
os idiomas é o copy deck inteiro. `nav_graph` + manifest + deep links dão o mapa.
Os DTOs dão o contrato. Ou seja: sem login perdes *conteúdo* e *estado*, não
perdes *forma*.

### 3.5 Checklist de superfícies de terceiros (obrigatório em `repack_suspect`)

Antes de aceitar um screenshot de build modificado, verifica por ecrã:

- [ ] **Mapas** — tiles em branco/cinza = key presa à assinatura quebrada. Não é design.
- [ ] **WebViews** — a moldura é spec; o conteúdo de terceiros pode não carregar.
- [ ] **Push/FCM** — silenciosamente morto; estados de notificação não são capturáveis.
- [ ] **Social login / SSO** — os botões existem, o fluxo não.
- [ ] **IAP / pagamentos** — ecrãs de preço podem vir vazios.
- [ ] **Ads** — placeholders e "ad failed" não são design.
- [ ] **Fontes e ícones** — icon font de terceiros → glifos em falta.

O que falhar aqui → `repack_suspect`, validação contra `ui_spec/`, nota no
`coverage.md`. **Falha silenciosa é o pior tipo de falha numa spec.**

### 3.6 Critério de fecho sem credenciais

"Zero nós por visitar" é impossível. O fecho é por **classificação completa**:

- todo o nó alcançável foi visitado
- todo o nó inalcançável tem razão escrita: `auth`, `state`, `peer`, `geo`,
  `flag`, `thirdparty`, `broken`
- cada ecrã autenticado não capturado tem: razão + fonte alternativa usada
  (layout renderizado, `ux_reference` pública) + nível de evidência
- `coverage.md` lista ecrã a ecrã o que é `live` / `served` / `static` /
  `unverified` / `presumed`. Os ecrãs de backoffice são `designed` e vivem no
  `topology.md`, não aqui.

A FASE 6 valida contra esta tabela. Um ecrã `unverified` não é vergonha; um ecrã
`unverified` apresentado como certo é.

**Classificar não é excluir.** `auth`, `state`, `peer`, `geo`, `flag`,
`thirdparty` e `broken` explicam por que um nó não foi capturado — não são
autorização para deixar um botão morto no clone. A FASE 7 decide, por item:
equivalente próprio funcional, ou ponto de entrada removido da UI. Nunca
"fora do âmbito" visível.

### 3.7 Matriz de decisão

| Situação | Modo | Captura | Contrato | Declaração |
|---|---|---|---|---|
| Credenciais + app corre | `N3` (+ `N2` API-only) | exaustiva, `clean` | real + forçado | alta confiança |
| Sem credenciais, repack passa | `N2` | pré-auth `clean` + autenticado `served` | bottom-up do log | UI alta, dados teus |
| Sem credenciais, repack falha / Okta | `N1+N4` | pré-auth `clean` + layouts + público | desenhado, `presumed` | tolerância declarada |
| Pinning, mas conta do cliente | `N3` (+ `N2` API-only) | exaustiva, `clean` | real | alta confiança |
| Multi-role gated | `N2` + peer-bot | por role | único partilhado | peer simulado |

### 3.8 O que nunca se faz

- comprar conta, usar conta de terceiros sem consentimento, ou fabricar
  identidade para **aceder ao serviço real**
- instalar build modificado num dispositivo que não é teu
- distribuir o APK patchado — é instrumento interno, nunca produto
- apresentar `served`/`presumed` como `live`
- copiar assets, marca, nome ou ícone para o entregável
- publicar algo reconhecivelmente da marca de outro
- deixar um botão visível sem efeito real (`fora do âmbito`, `em breve`,
  `TODO`, toast, `disabled` sem razão)
- declarar "fora de âmbito" para passar o checklist
- pedir ao cliente para listar o que falta — o inventário é do agente

### 3.9 Contrato quando não há contrato

Para um clone **não precisas do protocolo do original.** Precisas de *um*
contrato que alimente a UI de forma coerente — o `endpoints.json` é spec para o
**teu** backend.

Sem acesso, o contrato desenha-se: os campos candidatos saem dos DTOs, dos
`strings`, dos bindings de layout (`viewId` ↔ campo) e das mensagens de erro.
Cada campo nasce `presumed` e promove-se quando a interrogação o confirmar.
Perdes fidelidade de protocolo — que nunca terias, porque o backend é teu — e
ganhas um contrato coerente, versionado e implementável.

---

## FASE 0 — Obter e desempacotar o artefacto

**Android**
- `adb devices` → autorizar RSA no telefone
- `adb shell pm list packages | grep -i <nome>` → `adb shell pm path <pkg>`
- `adb pull` do `base.apk` (+ splits) → `device_apk/`
- `.xapk` é ZIP → `base.apk` + splits de config; só o `base.apk` interessa
- hash: `sha256sum device_apk/base.apk` → `plan.md`

**iOS**
- `.ipa` é ZIP → `Payload/<App>.app`; binário Mach-O (idealmente desencriptado)
- nibs/storyboards compilados (`NIBArchive`)

**Decompila sempre uma cópia**
- `apktool d base.apk -o decompiled/` → `res/`, `smali*/`, `AndroidManifest.xml`, `assets/`
- `jadx -d jadx_src/ base.apk` → referência para greps, não para leitura integral

**Manifest** → activities, deep links, permissões, componentes exportados,
`queries`/providers (o que a app consulta fora).

**Ferramentas (obrigatórias).** `pull_adb_package` traz o conjunto completo
(base + todos os splits, como `pm path` os reporta); `inspect_artifact`
classifica e inventaria o que foi extraído, com digest. `adb pull` manual só
como fallback declarado.

**GATE:** `device_apk/` intacto + hash em `plan.md` + `decompiled/` +
`jadx_src/` + inventário do artefacto em `rea_evidence/00_artifact/`.

---

## FASE 1 — Plano de acesso

Sonda barata por role, antes de capturar:

- credenciais: existem? de quem? para que role?
- hardening: grep `CertificatePinner`, `SafetyNet`, `PlayIntegrity`,
  signature/`PackageManager` checks, root/emulator detection
- **teste de repack** (1 a 2 sessões): hosts patch → `apktool b` → `apksigner`
  → `adb install` → passa do login?
- que superfícies de terceiros vão quebrar com re-assinatura (§3.5)
- **device de teste compatível**: minSdk/targetSdk vs Android do device; se o
  device do cliente não corre a app, usa emulador/device de teste
- **classificação rápida do tipo de app** (§4.5.1) — define que roles, backends e
  backoffices vais procurar; a topologia formal fecha na FASE 4.5
- deep links públicos podem abrir ecrãs internos sem sessão — testar antes de
  assumir bloqueio

Escreve `access_plan.md` por role, nesta ordem:
1. **Credenciais** — existe conta? de quem? (N3/N0)
2. **N2 — repoint + backend local** — se não há credenciais
3. **N1 + N4** — fallback, com gap escrito

Para cada role, regista também: **cenário** (`N3+N2`/`N2`/`N1+N4`), **UI
esperada** (`live`/`served`/`static`) e **laboratório** (`completo`/`parcial`).

Inclui cobertura prometida, tolerância declarada e a lista do que fica de fora
**com razão**.

**Ferramentas (obrigatórias).** `inspect_android_package` para manifest, SDK,
permissões e componentes exportados; inspeção de assinatura do artefacto para o
veredicto de re-assinatura. Os dois alimentam a linha de hardening e o teste de
repack — sem eles, o `access_plan.md` é opinião. Para iOS,
`project_apple_application_graph`.

**GATE:** `access_plan.md` fechado + classificação preliminar do tipo de app
(§4.5.1) + evidência de pacote e assinatura em `rea_evidence/01_access/`. Sem
isto não há FASE 2.

---

## FASE 2 — Captura viva (dois canais, um loop)

**Canal A — passivo (binário original).** `screencap` + `uiautomator dump` +
`input tap/swipe/text`. Risco zero, `integrity: clean`. É sempre o primeiro.

**Canal B — interrogativo (cópia repointada + stub backend).** Cada toque produz
um request em `handled.log`; serves o DTO populado **inteiro**; itera até o ecrã
renderizar. Só existe se a sonda de repack da FASE 1 passou.

**Ferramentas (canal A).** `capture_adb_screen` por ecrã (frame único,
content-addressed, digest estável para diff), `start_adb_app` para arranque
reprodutível, `read_adb_logcat` para correlacionar crash/erro com o ecrã. A
travessia e o dump de UI continuam a ser teus: a ferramenta dá o frame, não
decide o próximo nó.

### Preparação (canal A)

Demo mode — status bar limpa, PNGs medíveis e comparáveis:

```bash
adb -s <SERIAL> shell settings put global sysui_demo_allowed 1
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command enter
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 1200
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false
```

No fim da sessão: `... -e command exit`. Datas/horas **dentro** do conteúdo da
app (ex.: "há 2 dias") não se limpam — são dados de exemplo, definidos pelas
fixtures.

Login reproduzível: se houver credenciais, guardar credenciais de teste e
coordenadas em `ux_capture/login.sh`.

### Loop por ecrã

1. `adb exec-out screencap -p > ux_capture/<nome>.png`
2. `uiautomator dump` + pull → nós clicáveis com `bounds`
3. ação: tap / swipe / keyevent / text
4. canal B: o request correspondente entra em `handled.log` e no `endpoints.json`
   (mapping **causal**, não inferido)
5. comportamento → `ux_behavior.md`

**Cobertura exaustiva — travessia em largura.** Em cada ecrã, extrai do dump os
nós clicáveis ainda não visitados e visita-os um a um: ícones, tabs, drawer,
overflow (⋮), FABs, items de lista (tap + long-press + swipe), settings, dialogs,
bottom sheets, onboarding, ajuda/sobre/jurídico. Um tap por explorar = um buraco
que a FASE 5 descobre tarde demais.

**Rolar até ao fim — nos dois eixos.** Ecrãs longos não cabem num PNG: antes de
sair, `input swipe` para baixo até ao fim da lista **e** para o lado em toda a
faixa que mostre conteúdo cortado na margem. Captura cada posição relevante
(topo, meio, fundo; início e fim do carrossel). Um card cortado na borda direita
é o sinal de scroll horizontal — se não o percorreres, a FASE 5 constrói meia
lista. Regista no `ux_behavior.md` o eixo, o encaixe (pager/snap/livre) e o
overscroll.

**Estados fora do happy-path:** lista vazia, sem resultados, skeleton de loading,
offline (`svc wifi disable` + `svc data disable`), 401/sessão expirada, 500,
loading lento, permissão negada, primeiro arranque, toasts/snackbars, dialogs de
confirmação. No canal B força-os por fixture: payload vazio, erro HTTP, fixture
grande (densidade real).

**Animações:** `screenrecord` (máx 3 min) por fluxo-chave. **O modelo não vê
MP4** — extrai frames a 2 fps e uma contact sheet; é com esses frames que se
anotam durações e easings, cruzando com `res/anim`/`interpolator`. Para fluxos
(aceitar → transição → estado), grava em `start`/`stop` à volta das ações.

**Deep links:** `am start -a android.intent.action.VIEW -d "<scheme>://<path>"`.

### Comportamento — `ux_capture/ux_behavior.md`

- **grafo de navegação**: `ecrã origem → trigger → ecrã destino` (observado)
- **gestos por elemento**: swipe revela ações? pull-to-refresh? long-press?
- **scroll por ecrã**: eixo (vertical, horizontal, ambos), encaixe
  (pager/snap/livre), lista horizontal dentro de lista vertical, indicadores
- **animações**: timings + easing
- **feedback**: toast vs snackbar vs dialog, haptics, undo, confirmação destrutiva
- **back** por ecrã: pop / sobe ao pai / confirma / sai
- **formulários**: validação on-blur vs submit, máscaras, foco, teclado

### Peer triggers — `ux_capture/peer_triggers.md`

Estados que só chegam com ator externo: `estado → trigger externo → role`.
Na FASE 5 viram peer-bot.

**GATE:** nós todos visitados **ou** todos classificados (§3.6); `coverage.md`
escrito; `ux_reference/` público marcado `unverified`; frames de captura em
`rea_evidence/02_capture/`.

---

## FASE 3 — Spec estática + stack

**Ferramentas (obrigatórias).** `decode_android_resources` para layouts,
`values/`, drawables, animações e fontes; `inspect_android_package` para o mapa
de manifest/activities/deep links; `search_android_classes` →
`inspect_android_method` → `trace_android_references` para DTOs, enums de
estado e construtores de URL, sempre **por identificador**, nunca por leitura
integral. `inspect_apktool_client` só para diagnosticar o provider.

Tudo por greps direcionados:

- **layouts**: `res/layout*/`, `res/menu*/`, nav graphs, Composables,
  `.storyboard` → hierarquia por ecrã
- **valores**: `colors.xml`, `dimens.xml`, `strings.xml` (todos os idiomas),
  `styles.xml`, `themes.xml`
- **drawables**: vetores, shapes, `color*/` selectors
- **animações**: `anim*/`, `animator*/`, `interpolator*/`
- **tipografia**: `res/font/`, `fontFamily`
- **manifest**: mapa de activities/tabs/deep links/providers

**`stack.md`**: linguagem, toolkit de UI (XML Views vs Compose; UIKit vs
SwiftUI), arquitetura (MVVM/MVI/VIPER pelos nomes de classe), libs maiores
(networking, imagem, DI, persistência, nav). A recriação usa **a mesma stack** —
não se troca XML por Compose nem UIKit por SwiftUI "porque é mais moderno".

**Correlação:** cada ecrã de `ux_capture/` mapeia para um layout de `ui_spec/`.
Os que não mapeiam estão classificados em `coverage.md` (§3.6).

**GATE:** `ui_spec/` + `stack.md` + tabela de correlação sem órfãos + extracto
descodificado e referências citadas em `rea_evidence/03_spec/`.

---

## FASE 4 — Contrato de dados

`endpoints.json` **bottom-up** (canal B da FASE 2) + DTOs estáticos para os
campos que a UI nunca renderizou. O tráfego grava-se e inspeciona-se com
`inspect_web_network_capture` (HAR 1.2, SAZ, mitmproxy) e compara-se
antes/depois com `compare_web_captures`. O shape que entra no contrato é o
observado, não o reconstruído de memória.

Por endpoint:

- `method`, `path`, `role`/`app`
- `owner` — o serviço que possui a escrita do recurso (um só)
- `producer` — app/role que chama · `consumers` — apps que reagem ao resultado
- `emits` — evento publicado quando muda estado · `subscribes` — eventos que o
  ecrã consome (ver FASE 4.6)
- `screens: [...]` — que ecrãs o chamam (causal)
- `request` — shape real observado
- `response` — shape + `evidence: live|served|static|unverified|presumed` — e
  `designed` para os endpoints de backoffice que projetaste por não existirem
  no original
- `peer_trigger` — se o estado seguinte depende de outro role

**Hosts:** `rebuild` (o teu backend implementa) / `substituir` (equivalente
próprio) / `descartar` (telemetria, tracking, ads). Zero não-classificados.
Zero segredos.

**Multi-app:** **um** ficheiro para todo o ecossistema, entidades únicas por
nome, visibilidade por role. Nunca dois `Trip` divergentes.

**O que os greps não apanham** — URLs montadas em runtime, DTOs ofuscados
(`a.b.c`), zero Retrofit → `presumed` até a interrogação ou os construtores de
URL confirmarem.

**GATE:** todo o host classificado, todo o endpoint com pelo menos um ecrã,
`evidence` em cada shape, zero segredos, e a captura de origem de cada shape
citada em `rea_evidence/04_contract/`.

---

## FASE 4.5 — Topologia: que app é esta, quantos backends, quantos backoffices

O número de backends e de backoffices **não é um pressuposto: é uma saída** do
modelo de estados e dos atores. Uma app de entregas, um SaaS multi-tenant e uma
fintech produzem topologias diferentes — e o clone tem de saber qual está a
construir antes de escrever a primeira linha de backend.

**Regra dura: a topologia é tua, não é espelho do original.** O original pode
ter 40 microserviços; tu precisas de 1 ou 2. O que se clona é o comportamento
observável, não a arquitetura interna deles (que nem chegas a ver).

### 4.5.1 Classificar o tipo de app (rápido na FASE 1, formal aqui)

| Tipo | Sinais no binário / na captura | Atores | Backends típicos | Backoffices típicos |
|---|---|---|---|---|
| Marketplace de dois lados (ride, delivery) | peer triggers, geo, "à procura", ratings, dispatch, estados que só outro ator move | cliente, provider/courier | core, matching, geo, pagamentos, notificações | ops/dispatch, suporte, financeiro, aprovação/KYC |
| E-commerce / retalho | catálogo, stock, carrinho, checkout, devoluções | comprador (+ vendedor) | catálogo, stock, pedidos, pagamentos, logística | catálogo/PIM, pedidos, devoluções, financeiro |
| SaaS / B2B | login por organização, convites, RBAC, billing por seat | utilizador, org admin, platform admin | core, auth/SSO, billing | tenants, suporte, billing ops |
| Social / UGC | feed, follow, denúncia, bloqueio | utilizador, moderador | feed, media/CDN, moderação | moderação, trust & safety |
| Fintech / pagamentos | KYC, limites, comprovativos, ledger | utilizador, compliance | ledger, KYC, antifraude | compliance, risco, conciliação |
| Saúde / agendamentos | profissionais, horários, consentimento | paciente, profissional, receção | agenda, registos, notificações | receção, clínico, compliance |
| Educação | turmas, progresso, certificados | aluno, tutor | conteúdo, progresso, avaliação | conteúdo, tutoria |
| IoT / companion | pairing, telemetria, firmware/OTA | utilizador, técnico | device registry, telemetria, OTA | frota, OTA, suporte |
| Super app / multi-vertical | verticais com modelos diferentes na mesma app | vários | **mais de um** | **mais de um** |
| Utilitário single-player | tudo local ou uma API simples | utilizador | 1 | 0 ou 1 |

Escreve a classificação **com a evidência que a sustenta** (que ecrã, que string,
que endpoint, que transição de estado). Sem evidência, é `presumed`.

### 4.5.2 Quantos backends

Default: **1 backend modular**. Só separas quando existe uma razão medida:

- perfil de carga radicalmente diferente (telemetria/geo de alta frequência vs CRUD)
- isolamento obrigatório (pagamentos, PII, compliance)
- ciclo de deploy diferente (matching em tempo real vs catálogo)
- tecnologia diferente necessária (motor de matching, ML, processamento de media)
- multi-app com contrato partilhado mas evolução independente

Nunca: "porque o original tem", "porque microserviços é melhor", "porque sim".
Cada separação paga-se em deploy, observabilidade e consistência — só se faz com
razão escrita.

Candidatos naturais a serviço próprio, quando existem:
**matching/dispatch** (muda de estado por ator externo, tempo real) · **media**
(upload, CDN, transformação) · **pagamentos/ledger** (isolamento e auditoria) ·
**notificações** (push/email/SMS, fan-out).

### 4.5.3 Quantos backoffices

Backoffice ≠ admin. Distingue desde o início:

- **Backoffice** — atua sobre o estado do negócio: dispatch, moderação,
  aprovação, suporte, financeiro
- **Admin** — configura o sistema: flags, preços, catálogo, textos, integrações

Regra de contagem: **um painel por função operacional distinta**, não por role.
Agrupa quando o utilizador e a cadência são os mesmos; separa quando o
utilizador, o risco ou a auditoria são diferentes.

- financeiro/compliance **nunca** no mesmo painel que suporte
- moderação separa-se quando há volume ou risco legal
- dispatch separa-se quando há operação em tempo real
- admin de configuração pode viver no mesmo painel do ops **se** o utilizador for o mesmo

Mínimo para um clone que tenha de **operar**:
1. Ops/Admin (intervenção + configuração)
2. Suporte (read-only + ações de conta)
3. Financeiro/Compliance (se circula dinheiro)
4. Moderação (se há UGC)
5. Dispatch (se há matching em tempo real)

### 4.5.4 Backoffice forensics — inferir o que não está no binário

O backoffice **não existe na app**. Infere-se. A regra central:

> **Todo o estado que a app mostra e nunca cria implica uma ação de backoffice.**

Fontes no binário:
- strings e hosts: `admin`, `backoffice`, `ops`, `internal`, `staff`, `dashboard`, `manage`
- enums de permissão: `ADMIN`, `SUPPORT`, `MODERATOR`, `DISPATCHER`, `FINANCE`
- endpoints com prefixo `/admin`, `/internal`, `/ops`, `/manage`
- feature flags e kill switches → quem os aciona?
- templates de email/push em `assets/` → quem os envia?
- **estados órfãos**: "em análise", "aprovado", "rejeitado", "reembolsado",
  "suspenso", "em disputa", "em revisão"
- ecrãs de contacto, denúncia, disputa → o outro lado existe
- webviews e deep links para painéis
- códigos de erro que implicam revisão manual ("documento ilegível")

Produz a matriz **estado → quem o move → que painel → que endpoint**. Essa
matriz é o requisito funcional do backoffice e entra no `topology.md`.

### 4.5.5 Multi-app, multi-tenant, multi-país

- **Multi-app**: um `endpoints.json`, N apps, M backoffices. Matriz de
  visibilidade por role. Entidades únicas por nome.
- **Multi-tenant**: `tenant_id` em todas as entidades; backoffice de tenant ≠
  backoffice de plataforma. Isolamento testado, não assumido.
- **Multi-país**: `ApiConfig` por país (baseUrl, moeda, pagamentos, legal);
  divergências legais declaradas por mercado.
- **Multi-idioma**: as strings já estão em `ui_spec/` — não inventes copy.

### 4.5.6 `topology.md` — estrutura obrigatória

```
# Topologia — <APP>
1) Classificação
   tipo · modelo de negócio · evidência que o sustenta
2) Atores
   role | app | como entra | que estados move
3) Apps
   nome | role | plataforma | stack
4) Backends
   nome | domínios | porquê separado | entidades que possui | endpoints
5) Backoffices
   nome | utilizador | funções | estados que move | ecrãs
6) Modelo de dados partilhado
   entidade | dono (quem escreve) | transições | visibilidade por role
7) Tempo real e jobs
   canais, filas, agendados
8) Orquestração
   estado | produtor | quem move | apps que veem | endpoint | evento
9) Exclusões de produto (só com aprovação escrita, antes da FASE 5)
   item | porquê | equivalente funcional | entrada de UI removida?
```

**Exclusão não é botão morto.** Se a entrada existe na UI, tem de funcionar. Se
não há equivalente próprio, a entrada não é desenhada. A lista de exclusões é
um contrato assinado, não uma desculpa de última hora.

### 4.5.7 Backoffice é teu — não é clone

O backoffice do original nunca foi visto. O teu é **desenhado**, com design
system próprio e neutro, e a sua fidelidade mede-se por **cobertura da máquina
de estados** (§4.5.4), não por paridade visual. Marca esses ecrãs como
`evidence: designed` — nunca `unverified`, nunca `presumed`, nunca como clonados.

**GATE:** `topology.md` completo; cada estado que a app mostra tem um ator no teu
sistema que o move; cada backend separado tem razão escrita; cada backoffice tem
lista de ecrãs; cada exclusão tem equivalente funcional ou entrada removida, com
aprovação escrita; e cada inferência de backoffice (§4.5.4) cita a string, o
enum, o endpoint ou o estado órfão que a sustenta — sem citação é `presumed` e
vai a `coverage.md`.

---

## FASE 4.6 — Orquestração entre apps: um estado, N vistas

Clonar o Driver implica o User e o Fleet. Não são três produtos independentes:
são **três projeções da mesma máquina de estados**. Esta fase define a
coordenação — que endpoints existem, quem os chama, o que cada app vê e como uma
transição numa app aparece nas outras.

**Ponto de partida que resolve metade das dúvidas:** não existem endpoints "no
backoffice". O backoffice é um **cliente privilegiado do mesmo backend**; os
endpoints `/admin/*` vivem no backend e são autorizados por role. Se o
backoffice tiver endpoints próprios, tens duas fontes de verdade.

### 4.6.1 Princípio: um escritor, N leitores

- cada agregado (`Ride`, `Order`, `Driver`) tem **um** serviço dono da escrita
- cada app é uma **projeção** desse agregado, com campos filtrados por role
- **uma app nunca chama a outra.** A coordenação passa sempre pelo backend:
  leitura do recurso, evento realtime ou push
- o backoffice entra pelo mesmo serviço de domínio e gera o mesmo evento que um
  utilizador geraria

Consequência de desenho: não precisas de sincronização entre apps. Precisas de
uma fonte de verdade e N subscritores.

### 4.6.2 A máquina de estados (entregável central)

Uma tabela por agregado, no `topology.md` §8. Exemplo ride-hailing
(U = User, D = Driver, F = Fleet, B = Backoffice):

| Estado | Quem cria | Quem move adiante | Endpoint | Evento | Vistas |
|---|---|---|---|---|---|
| `requested` | U | D aceita · dispatch atribui · timeout | `POST /rides/{id}/accept` | `ride.requested` | D (oferta), F, B |
| `accepted` | — | D a caminho | `POST /rides/{id}/arriving` | `ride.accepted` | U, F, B |
| `arriving` | — | D chega | `POST /rides/{id}/arrived` | `ride.arriving` | U, F, B |
| `arrived` | — | Início da viagem | `POST /rides/{id}/start` | `ride.arrived` | U, F, B |
| `in_progress` | — | D termina | `POST /rides/{id}/complete` | `ride.started` | U, F, B |
| `completed` | — | Job de pagamento | interno | `ride.completed` | U, D, F, B |
| `cancelled` | U, D, B | — | `POST /rides/{id}/cancel` | `ride.cancelled` | todos |
| `disputed` | U | B resolve | `POST /admin/rides/{id}/resolve` | `ride.disputed` | U, B |
| `paid` / `refunded` | job, B | — | `POST /admin/payments/{id}/refund` | `payment.refunded` | U, D, F, B |

Regras: cada transição tem **um** endpoint e **um** evento. Um estado sem
transição é estado morto — e é assim que o clone "quase funciona".

### 4.6.3 Um escritor por campo

| Campo | Escritor único | Leitores |
|---|---|---|
| `ride.status` | serviço de rides (só via transições) | U, D, F, B |
| `ride.fare` | pricing, na criação, depois congelado | U, D, F, B |
| `driver.location` | Driver app | U (só na viagem ativa), F, B — **nunca** outro Driver |
| `driver.online` | Driver app | F, matching |
| `driver.documents.status` | backoffice (aprovação) | D, F |
| `payout.status` | financeiro / job | D, F, B |

Dois escritores no mesmo campo é bug de design: resolve-se antes de codificar,
não depois de sincronizar.

### 4.6.4 Realtime por app

| App | Canal | Subscrições | Fallback |
|---|---|---|---|
| User | socket | `ride.accepted/arriving/arrived/completed`, `driver.location` | polling do estado 3-5 s |
| Driver | push + socket | `ride.requested` (oferta — crítico), `ride.cancelled` | push é primário; socket para o resto |
| Fleet | socket agregado | `driver.online`, `ride.*` agregado, alertas de frota | polling 10-15 s |
| Backoffice | feed de ops | todas as transições + fila de exceções | refresh manual |

Regra: se o original usa socket, replica a **semântica** (que eventos, com que
latência), não o protocolo. Se não usa, replica o intervalo de polling observado.

### 4.6.5 Backoffice como ator de coordenação

Intervenções manuais são **transições de primeira classe**, não correções na
base de dados: `force_cancel`, `reassign`, `approve_driver`, `suspend`,
`refund`, `resolve_dispute`.

Cada uma exige: endpoint no backend · evento publicado · auditoria (quem,
quando, porquê) · propagação às apps como qualquer outra transição.

Se o backoffice escrever direto na BD, as apps deixam de coordenar no mesmo
instante — e o sintoma aparece semanas depois como "estado inconsistente".

### 4.6.6 Ordem de clonagem e peer-gating

Ordem recomendada: quem **cria** a entidade (User) → quem a **move** (Driver) →
quem a **agrega** (Fleet) → quem **intervém** (Backoffice).

- **Fleet é uma role com scope de tenant** (§4.5.5): vê os seus motoristas, não
  a frota global. Isso é autorização, não um filtro de UI
- um fluxo só é considerado validado quando observado em **≥2 vistas**
- se só podes capturar uma app, o estado fica `peer-gated`: o `peer_triggers.md`
  da FASE 2 mapeia para transições desta tabela e o peer-bot simula o ator
  em falta — sempre declarado como simulado

### 4.6.7 Validação: o teste dos três espelhos

1. cria em **U**
2. vê em **D** (como oferta) e em **F** (agregado)
3. move em **D**
4. vê em **U**
5. intervém em **B**
6. vê em **U** e em **D**

Se qualquer passo falhar, a coordenação não está implementada — pode até estar a
UI. Este teste corre na FASE 6, por agregado.

**GATE:** máquina de estados completa (todo o estado tem produtor e transição);
um escritor por campo; cada app com canal e subscrições declarados; intervenções
de backoffice modeladas como transições auditadas; ordem de clonagem justificada.

---

## FASE 5 — Recriação (`app_nova/`)

- Codebase nova, 100% tua. **Mesma stack** de `stack.md`
- **Implementa a topologia de `topology.md`** — os teus N backends e M
  backoffices, não os do original. Um backend a mais é custo permanente; um
  backoffice a menos é operação impossível
- **Backoffice(s)** com RBAC por função (§4.5.3): design system próprio e
  neutro, ecrãs `designed`, cobertura da máquina de estados exigida
- **Implementa a orquestração de `topology.md` §8** (FASE 4.6): eventos,
  subscrições realtime por app, um escritor por campo, intervenções de
  backoffice como transições auditadas
- Zero recursos copiados: fontes vetoriais originais tuas para cada forma
  (SVG / vector drawable / path nativo), nunca rasterizar nem reutilizar ficheiros
- Por ecrã: corre **`PROMPT_CLONE_BUILD.md`** (não este documento) — um prompt
  por ecrã, com o PNG e o layout anexados
- **Backend teu em estágios**: mock com fixtures → LAN (`0.0.0.0:8080` +
  cleartext no `network_security_config`) → servidor. A app não muda, muda a
  base URL
- **Peer-bot** para os fluxos gated de `peer_triggers.md`: bot scriptado que
  chama os teus endpoints e move o estado. Etiqueta: comportamento simulado,
  nunca observado
- **Networking isolado**: `ApiConfig` único (baseUrl por país/estágio) +
  `ApiClient` + `Repository` por domínio; zero hosts hardcoded nos ecrãs
- A app original (ou a sua versão repointada) continua a ser a referência viva
  para comparar UX
- **Cada ação visível tem efeito real.** O BUILD não aceita placeholders: se o
  endpoint/estado não existe, cria-se antes de marcar o ecrã como pronto.

**GATE:** todos os ecrãs de `coverage.md` implementados **e todas as ações
visíveis funcionam** (endpoint + estado + feedback). Zero `fora do âmbito`,
`em breve`, `TODO`, toast sem efeito ou botão inerte. Item não implementável:
equivalente próprio funcional ou ponto de entrada removido — nunca placeholder.

---

## FASE 6 — Validação e fecho

**Dois níveis, declarados:**

- **Alta confiança** — onde houve `live` / `served` / `static`: paridade exigida
  ecrã a ecrã contra `ux_capture/` + `ui_spec/` (geometria, cor, tipografia,
  estados vazio/erro/loading, gestos, navegação, animações)
- **Tolerância declarada** — onde só há `unverified` / `presumed`: aproximação
  assumida e escrita no relatório final

**Fecho:**
0. **Auditoria de capacidades** — gera `capabilities.md` a partir de todos os
   ecrãs, ações, endpoints e estados. Para cada item: `ok` | `gap` |
   `placeholder` | `missing-endpoint` | `missing-state` | `dead`. Cruza:
   - cada ecrã tem todas as ações visíveis?
   - cada ação tem endpoint/estado e efeito?
   - cada endpoint tem consumidor?
   - cada estado tem transição e vista?
   - cada `peer_trigger` tem peer-bot/job?
   O resultado é `backlog.md`, gerado pelo agente, priorizado. **Não perguntes
   ao cliente o que falta.**
1. valida a máquina de estados contra `topology.md`: todo o estado que a app
   mostra tem um ator no teu sistema que o move (backoffice, peer-bot ou job).
   **Estado órfão = funcionalidade morta no clone**
2. corre o **teste dos três espelhos** (§4.6.7) por agregado, com todas as vistas
   que conseguiste construir
3. percorre `coverage.md` linha a linha — cada ecrã tem veredicto
4. cada `repack_suspect` foi confirmado contra o binário ou continua marcado
5. relatório final: o que é `live`, o que é `served`, o que é `presumed`, e porquê
6. nenhum gap silencioso
7. **zero botão morto** — grep por `fora do âmbito`, `em breve`, `TODO`,
   `FIXME`, `not implemented`, `coming soon`, handlers vazios; corrige ou
   remove a entrada
8. **handoff em chat** — não só ficheiro: alvo, feito, gaps fechados, gaps
   abertos, bloqueios externos, veredicto "pronto para <alvo>? sim/não"
9. **cobertura medida** — `evaluate_reconstruction_coverage` contra o limite
   declarado no `plan.md`; o número entra no `RELATORIO_FINAL.md`. Cobertura
   abaixo do prometido é gap, não tolerância.

---

## FASE 7 — Fecho de gaps (obrigatória; o projeto não fecha na FASE 6)

A FASE 6 diz o que está fiel. A FASE 7 fecha o que está morto. Nenhum projeto é
"entregue" com um botão visível sem efeito.

### 7.1 Inventário automático (o agente faz, não o cliente)

Gera `capabilities.md` a partir de:
- todos os ecrãs de `coverage.md` e do `ux_behavior.md`;
- todos os `unknowns`/limitações registados em `rea_evidence/`;
- todos os elementos interativos (botões, tabs, menus, chips, FABs, gestos,
  deep links, notificações);
- todos os endpoints de `endpoints.json` e do backend;
- todos os estados de `topology.md` §8.

Matriz obrigatória:

```
capacidade | evidência no original | ecrã | ação | endpoint/estado | teste | status
```

`status` só pode ser `ok` ou `gap`. `gap` tem: razão, bloqueia
(`demo`/`opera`/`loja`), esforço, dono.

**Evidência não é funcionalidade.** `live`, `served` e `static` dizem de onde
veio a captura, não se o botão do clone funciona. Um ecrã `static` continua a
ter de implementar todas as ações; um ecrã `served` continua a ter de passar os
testes E2E. A FASE 7 fecha funcionalidade; a evidência mede confiança.

Cruza nos dois sentidos:
- **UI → backend**: cada ação visível tem endpoint/estado e efeito real?
- **backend → UI**: cada endpoint tem consumidor visível? Endpoint sem UI é
  feature morta; UI sem endpoint é botão morto.
- **estado → vista**: cada estado tem transição e vista? Cada vista tem
  transição de saída?
- **peer → bot**: cada `peer_trigger` tem peer-bot/job que o move?

Grep obrigatório no código da app/backoffice:
`fora do âmbito`, `fora de ambito`, `em breve`, `TODO`, `FIXME`,
`not implemented`, `coming soon`, `disabled` sem razão, handlers vazios.
Cada resultado vira linha do `backlog.md` — nunca fica no código.

`backlog.md`:

```
id | área | ecrã/fluxo | razão | bloqueia (demo/opera/loja) | esforço | dono | estado
```

### 7.2 Loop de execução (até zero)

Para cada item do `backlog.md`, por ordem: blocker do alvo > ação visível >
estado > cosmético.

1. Implementa com o `PROMPT_CLONE_BUILD.md` (um ecrã por prompt).
2. Testa ponta a ponta: happy, empty, error, offline/retry.
3. Atualiza `capabilities.md` (`ok`) e remove a linha do `backlog.md`.
4. Se o item não é implementável (terceiro preso à assinatura, legal,
   hardware), decide **agora**: equivalente próprio funcional ou entrada de UI
   removida. Exclusão exige aprovação escrita do cliente; sem isso, o item
   continua `gap` e o projeto não fecha.

Repete até `backlog.md` não ter `gap`/`placeholder`/`dead` para o alvo. **Não
perguntes ao cliente o que falta; o inventário é teu.**

**Autonomia:** não pares para anunciar "falta muito" nem peças aprovação item a
item. Gera o backlog, executa, testa e só voltas ao cliente para exclusões
legais/credenciais/terceiros que não tenhas como resolver. O trabalho continua
até o backlog estar vazio para o alvo.

### 7.3 Definição de "pronto" por alvo

| Alvo | Obrigatório |
|---|---|
| `funcional` (default) | Todos os ecrãs e ações que existem no original funcionam (auth, upload, chat, alertas, favoritos, mapa, offline/cache **quando existirem**); zero botões mortos; testes E2E dos fluxos críticos; backend local com seed; backoffice operacional |
| `produção` | `funcional` + PostgreSQL/migrações, rate limit, HTTPS, backups, logs/métricas, secrets, testes, a11y, i18n, dark mode |
| `loja` | `produção` + release assinado, Play Console, privacidade/termos, GDPR, Data Safety, revisão legal |

Sem alvo declarado, assume `funcional`. "Demo" não é um alvo: se quiseres uma
demo, dizes explicitamente e aceitas os gaps por escrito — mas a UI não mostra
botões mortos mesmo em demo.

O alvo `funcional` não exige que todos os ecrãs sejam `live`; exige que todos
funcionem. A evidência pode ser `served`/`static`; a ação tem de funcionar.

### 7.4 Handoff (chat + ficheiro)

No fim, responde em chat (não só no `RELATORIO_FINAL.md`):

```
Alvo: <funcional|produção|loja>
Feito: <...>
Gaps fechados nesta ronda: <...>
Gaps abertos: <...> (bloqueia: demo/opera/loja)
Bloqueios externos: <...> (pedidos no início, não no fim)
Veredicto: pronto para <alvo>? sim/não
```

Regras:
- não digas "concluído" sem esta mensagem;
- não peças ao cliente para listar o que falta;
- não apresentes um gap como "fora de âmbito" sem aprovação escrita e entrada
  de UI removida;
- se o alvo é `loja` e há um blocker, o veredicto é `não` — mesmo que a UI
  esteja bonita.

### 7.5 Artefactos

`capabilities.md` (matriz), `backlog.md` (gaps priorizados),
`RELATORIO_FINAL.md` (evidência/tolerância), `coverage.md` (captura) e
`plan.md` (alvo/DoD) são a entrega. Sem os cinco, não há fecho.

---

## CHECKLIST FINAL

- [ ] `plan.md` — credenciais (sim/não/parcial), gates, modo por role, cobertura
      prometida, tolerância declarada, **alvo** (`funcional`/`produção`/`loja`) e
      critério de "pronto"
- [ ] `access_plan.md` — decisão por app/role tomada por **sonda**; repack
      testado antes de prometer cobertura
- [ ] `coverage.md` — zero nós por visitar **ou** todos classificados
      (`auth`/`state`/`peer`/`geo`/`flag`/`thirdparty`/`broken`)
- [ ] `rea_evidence/` — artefacto, acesso, captura, spec e contrato com digest e
      ferramenta citada; `unknowns` traduzidos para `coverage.md`/`backlog.md`
- [ ] Precedência respeitada — nenhuma capacidade de `REA_BINDINGS.md` feita por
      comando cru sem razão escrita no `plan.md`
- [ ] `ux_capture/` — screenshots do **binário original** (repointado vale com
      flag); screenshots da app nova **nunca** entram na spec (`newapp_*` à parte)
- [ ] `ux_behavior.md` — grafo de navegação, gestos, animações, feedback, back,
      formulários
- [ ] `peer_triggers.md` — estados gated com trigger externo e role
- [ ] `ux_reference/` — público marcado `unverified`
- [ ] `ui_spec/` — layouts + values + drawables + animações + fontes; layouts
      renderizados para os roles sem execução
- [ ] `stack.md` — stack respeitada na recriação
- [ ] `endpoints.json` — bottom-up do log, não catálogo; `evidence` por shape,
      `screens` causal, `peer_trigger`; hosts todos classificados; zero segredos
- [ ] `topology.md` — tipo de app classificado com evidência; N backends e M
      backoffices justificados; matriz estado → ator → painel completa
- [ ] Backoffice(s) — RBAC por função, ecrãs `designed`, máquina de estados
      coberta, zero estado órfão
- [ ] Orquestração (FASE 4.6) — máquina de estados cross-app completa, um
      escritor por campo, eventos e subscrições por app, intervenções de
      backoffice auditadas, teste dos três espelhos executado
- [ ] `repack_suspect` — todos confirmados contra `ui_spec/` ou assumidamente
      marcados
- [ ] `app_nova/` — código 100% próprio, zero recursos copiados, mesma stack
- [ ] Networking isolado — `ApiConfig` / `ApiClient` / `Repository`, zero hosts
      nos ecrãs
- [ ] Backend(s) teu(s) — mock → LAN → servidor; peer-bots para fluxos gated
- [ ] Validação em dois níveis + relatório de tolerância
- [ ] `capabilities.md` — matriz `capacidade | evidência | ecrã | ação |
      endpoint/estado | teste | status`; zero `gap` para o alvo
- [ ] `backlog.md` — zero itens abertos para o alvo; exclusões só com aprovação
      escrita e entrada de UI removida
- [ ] `app_nova/` — zero botões mortos; zero `fora do âmbito`/`em breve`/`TODO`;
      cada ação visível tem endpoint/estado e teste E2E
- [ ] Backend — todos os endpoints usados pela UI existem e respondem; nenhuma
      ação depende de dados que não existem
- [ ] Handoff em chat — alvo, feito, gaps fechados/abertos, blockers, veredicto
- [ ] Marca de terceiros fora do entregável

---

## ANTI-PADRÕES (STOP RULES)

- **Ler o binário às voltas.** Se três greps direcionados não dão a resposta,
  o problema é de sonda, não de leitura de código.
- **Gastar mais de 1-2 sessões contra hardening.** O `access_plan.md` existe
  para transformar "não deu" em decisão, não em projeto paralelo.
- **Aceitar pixel de build modificado sem flag.** Mapas em branco parecem design.
- **Promover evidência.** `served` não é `live`, `presumed` não é `static`.
- **Preferir comando cru à ferramenta nomeada.** Se a capacidade existe em
  `REA_BINDINGS.md`, o comando improvisado volta a ser o que era: errático e
  sem evidência citável.
- **Engolir um `unknown`.** Limitação que não vira linha em `coverage.md` ou
  `backlog.md` transforma-se em spec inventada duas fases depois.
- **Preencher a spec com "parece que".** Se não mediste, escreve que assumiste.
- **Copiar assets "só para testar".** Contamina o repo e o entregável.
- **Avançar de fase sem o GATE.** Cada fase produz artefactos verificáveis; sem
  eles, a fase seguinte herda o erro.
- **Testar em emulador quando o alvo é device** (ou vice-versa) — deteção de
  emulador muda o comportamento e invalida a captura.
- **Confundir estado vazio com bug do repack** (ou o contrário). Resolve-se
  cruzando com o estático da FASE 3.
- **Espelhar a topologia do original.** Eles têm 40 microserviços; tu não
  precisas de nenhum. A topologia desenha-se, não se copia.
- **Microserviços por moda.** Cada separação paga-se em deploy, observabilidade
  e consistência — só com razão escrita (§4.5.2).
- **Esquecer o backoffice.** Um clone sem painel de operação não opera: os
  estados ficam presos e o produto morre na primeira exceção.
- **App a chamar app.** Se a app A precisa de saber de B, lê o mesmo backend —
  nunca chama o endpoint de B.
- **Backoffice a escrever na base de dados.** Intervenção é transição: serviço
  de domínio + evento + auditoria, ou as apps deixam de coordenar.
- **Dar um fluxo por validado com uma app só.** Um fluxo multi-app só fecha
  quando observado ponta a ponta em ≥2 vistas (§4.6.7).
- **Fabricar identidade para aceder ao serviço real.** É aqui que o projeto
  morre — não na falta de credenciais.
- **Botão decorativo.** `fora do âmbito`, `em breve`, `TODO`, toast sem efeito
  ou `disabled` sem razão = falha, não gap. O ecrã não está pronto.
- **Declarar fora de âmbito para fechar.** Exclusão só com aprovação escrita e
  entrada de UI removida; nunca um botão que diz "não implementado".
- **Pedir ao cliente o inventário.** O agente gera `capabilities.md` e
  `backlog.md`; o cliente só aprova exclusões.
- **Fechar na FASE 6.** A FASE 6 valida; a FASE 7 fecha. Sem FASE 7, o projeto
  está incompleto.
- **Mega-sessão.** Um ecrã por BUILD; sessões de milhares de eventos perdem a
  visão global e otimizam para o marco errado.
- **"Demo" sem dizer.** O alvo é declarado no `plan.md`; demo não é o default.

---

## APÊNDICE A — Template de recriação por ecrã (corre na FASE 5)

**Versão operacional: `PROMPT_CLONE_BUILD.md`.** Este apêndice define o que
"fidelidade" significa; o BUILD é o que se cola no agente, um ecrã de cada vez.
Não uses este documento inteiro como prompt de execução.

Um destes por cada ecrã de `ux_capture/` + `ui_spec/`. Substitui `<STACK_UI>`
pelo toolkit de `stack.md` e `<ECRÃ>` pelo PNG/layout de referência.

---

Recria fielmente o UI de `<ECRÃ>` num único componente autocontido na stack
`<STACK_UI>` — a mesma da app original (`stack.md`). Consulta `ux_behavior.md`
para este ecrã. Declara no topo: `evidence` do ecrã e `integrity` da captura.

**FIDELIDADE VISUAL (prioridade máxima)**
- Extrai a geometria REAL dos elementos gráficos (ilustrações, blobs, ícones,
  logos): traça os contornos a partir da imagem e converte-os em paths
  vetoriais (SVG / vector drawable / Path conforme a stack). NÃO uses caixas +
  corner radius quando a forma é orgânica ou irregular.
- Mede na imagem cores exatas (hex), posições, dimensões e alturas de texto —
  não estimes a olho. Cruza com `ui_spec/` (colors/dimens). Se algo for
  ambíguo, diz o que assumiste.
- Mede a tipografia de cada bloco: fontSize, peso, line-height, cor,
  alinhamento; usa a font de `res/font` se existir.
- Elementos cortados pelas bordas desenham-se completos, continuando offscreen.
- **Scroll nos dois eixos** quando o original os tem: vertical (listas,
  formulários) e horizontal (carrosséis, chips, separadores), incluindo o
  encaixado e o snap/pager. Card cortado na margem = há scroll horizontal.
- Define um espaço de design a partir da imagem e escala com as dimensões do
  dispositivo; formas escalam uniformemente.
- Se a captura for `repack_suspect`, confirma o elemento contra `ui_spec/` antes
  de o tratar como design — e verifica a lista de terceiros (§3.5).

**FIDELIDADE DE COMPORTAMENTO**
- Implementa gestos/animações/estados anotados em `ux_behavior.md` para este
  ecrã (pull-to-refresh, swipe actions, validação, transições) com as
  durações/easings de `res/anim`/`interpolator`.
- Liga cada elemento interativo ao destino certo no grafo de navegação.
- Reproduz o comportamento do back documentado.

**AÇÃO REAL (regra dura)**
- Cada elemento interativo tem efeito real: navega, muta estado, abre fluxo ou
  executa endpoint. Proibido `onClick` vazio, toast "fora do âmbito", `TODO`,
  `em breve` ou `disabled` para esconder falta de backend.
- Se a ação não tem endpoint/estado, o ecrã **não está pronto**: cria o
  contrato/endpoint ou remove a entrada. Não inventes um placeholder.
- Regista cada ação em `capabilities.md` com
  `elemento | ação | endpoint/estado | teste | status`.

**DADOS**
- O componente recebe dados por props/estado — nunca chama HTTP diretamente;
  quem alimenta é o `ApiClient` + `Repository` (`ApiConfig` única).
- Recebe handlers de mutação (`onSubmit`, `onUpload`, `onSend`, `onDelete`) que
  chamam o `Repository`; um handler que só mostra toast não é um handler.
- Mapeia os campos do DTO correspondente (`endpoints.json` → `screens`) 1:1
  para os elementos do ecrã.
- Implementa os estados loading / erro / vazio / offline replicados de
  `ux_capture/`; cada mutação tem idle/loading/success/error/retry.
- Campos sem evidência: usa fixture e marca `presumed` no comentário.
- Nenhuma ação crítica fica sem teste E2E (happy/empty/error/offline).

**ESTRUTURA DE PRODUÇÃO**
- Componente com props para interações (ex.: `onLogin`, `onOpenTerms`), tipos
  fortes na linguagem da stack.
- Camadas decorativas sem captura de toques; overflow escondido no root.
- Elementos interativos com `accessibilityRole`/equivalente; links com o seu
  próprio handler.
- NÃO desenhes réplicas da status bar nem do indicador de gestos — usa
  StatusBar translúcido e safe-area-insets se fizer sentido.
- Dependências mínimas: só as equivalentes às já detetadas em `stack.md`.

---

## APÊNDICE B — Comandos de referência

**Device e artefacto**
```bash
adb devices
adb shell pm list packages | grep -i <nome>
adb shell pm path <pkg>
adb pull /data/app/<dir>/base.apk device_apk/base.apk
adb pull /data/app/<dir>/split_*.apk device_apk/
adb shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1
```

**Decompilação**
```bash
apktool d base.apk -o decompiled/
jadx -d jadx_src/ base.apk
apktool b <dir> -o patched.apk
zipalign -p -f 4 patched.apk aligned.apk
apksigner sign --ks <keystore> --out signed.apk aligned.apk
adb install -r signed.apk
```

**Captura**
```bash
adb exec-out screencap -p > ux_capture/<nome>.png
adb shell uiautomator dump /sdcard/ui.xml && adb pull /sdcard/ui.xml
adb shell input tap X Y
adb shell input swipe x1 y1 x2 y2 300
adb shell input text "user@x.com"
adb shell input keyevent KEYCODE_BACK
adb shell screenrecord /sdcard/flow.mp4   # máx 3 min
```

**Rede**
```bash
adb shell svc wifi disable
adb shell svc data disable
adb shell am start -a android.intent.action.VIEW -d "<scheme>://<path>"
```

**Demo mode** — ver FASE 2 (entrar e `-e command exit` no fim).

**iOS**
```bash
xcrun simctl io booted screenshot <nome>.png
idevicescreenshot <nome>.png
# travessia guiada: XCUITest
```

**Web/SaaS**
- Playwright: login, crawl de DOM + HAR (o HAR é o `handled.log` web)
- repoint = interceptação de requests ou bundle servido localmente

**Interrogação**
- stub que regista tudo em `handled.log` (method, path, headers, body)
- mitmproxy para gravar shapes reais quando há credenciais e backend acessível

---

## APÊNDICE C — Artefactos esperados

```
<APP>/
  plan.md                # declaração inicial, gates, modo, tolerância
  access_plan.md         # decisão por app/role
  coverage.md            # ecrã → evidência → integridade → razão de gap
  rea_evidence/          # artefactos por fase: digest + ferramenta + unknown
  device_apk/            # original intocado + hash
  decompiled/            # apktool
  jadx_src/              # jadx (referência para greps)
  ui_spec/               # layouts, values, drawables, anim, font
  stack.md
  ux_capture/            # PNGs, login.sh, ux_behavior.md, peer_triggers.md
  ux_reference/          # público, unverified
  handled.log            # requests observados (worklist do contrato)
  endpoints.json         # contrato versionado, UM por ecossistema
  topology.md            # tipo de app, atores, N backends, M backoffices
  capabilities.md        # matriz ação → endpoint → estado → UI → status
  backlog.md             # gaps priorizados; zero abertos para o alvo
  app_nova/              # codebase 100% nova (app ou apps)
  backend/               # N serviços, conforme topology.md
  backoffice/            # M painéis, RBAC por função, ecrãs `designed`
```

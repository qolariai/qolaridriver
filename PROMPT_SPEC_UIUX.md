# PROMPT — Spec de UI/UX + contrato de dados → recriação limpa (via slim)

> **Substituído em 2026-10-25.** O programa de trabalho é agora
> [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) e a execução por ecrã é
> [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md). Este documento fica como referência
> histórica das fases P0–P8.

Versão encurtada de `PROMPT_REPLICAR_COMPLETO` (numeração das fases alinhada
para referência cruzada). Pressuposto: **só se clona a UI/UX e o contrato de
dados — todo o resto (backend, lógica, codebase) é feito de raiz.** O
binário original nunca é modificado nem reconstruído — serve apenas para
extração read-only. A app instalada no telefone é a referência viva.

Substitui `<APP>` pelo alvo. Fases ordenadas; cada uma produz artefactos
verificáveis antes de avançar.

```
FASE 0 (unpack) → FASE 0.5 (captura viva) → FASE 1 (UI/UX + contrato) → FASE 4 (recriação)
```

## REGRAS-DE-OURO

1. **Fonte de verdade intacta** — guarda sempre uma cópia do artefacto
   original (`device_apk/`, `*.ipa`); todo o trabalho faz-se numa cópia.
2. **Captura viva primeiro** — FASE 0.5 corre sobre a app original
   *instalada e a funcionar*, antes de descompilar o que quer que seja.
3. **Não estudar código** — o smali/jadx serve para extrair identificadores
   e o contrato de dados, não para perceber lógica de negócio. Se uma
   informação não sai de um grep direcionado, provavelmente não precisas
   dela — a `ux_capture/` e os layouts dizem-te como a app se comporta.
4. **Spec = fonte de verdade da recriação** — tudo o que a FASE 4 precisa
   tem de estar em `ui_spec/` + `ux_capture/` + `endpoints.json`. Se falta,
   volta à FASE 1, não ao código.

---

## FASE 0 — Obter e desempacotar o artefacto

- **Android**: `.xapk` é um ZIP → extrair → `base.apk` + splits de config.
  Só o `base.apk` interessa (splits são recursos por densidade/locale).
- **iOS**: `.ipa` é um ZIP → `Payload/<App>.app`. Nibs/storyboards estão
  compilados (`NIBArchive`), o binário é Mach-O (idealmente desencriptado).

## FASE 0.5 — Ligação ADB + captura viva (o modelo pilota a app real)

### 1. Ligar PC ↔ smartphone

- No telefone: Opções de programador → **Depuração USB** ativa.
- `adb devices` → aceitar o fingerprint RSA no ecrã do telefone (marcar
  "permitir sempre").
- Sem fio (opcional): `adb tcpip 5555` com o cabo ligado → desligar cabo →
  `adb connect <IP-do-telefone>:5555`. Em Android 11+: `adb pair`.
- Fixar `<SERIAL>` = saída de `adb devices` — todos os comandos seguintes
  usam `adb -s <SERIAL>`.
- iOS equivalente: `xcrun simctl io booted screenshot` no simulador /
  `idevicescreenshot` no device + XCUITest para navegação guiada.

### 2. Arrancar a app + login

- `adb -s <SERIAL> shell monkey -p <pkg> -c android.intent.category.LAUNCHER 1`
- **Login uma vez, sessão fica guardada** — o token/cookie persiste em
  `data/data/<pkg>`; nas capturas seguintes a app já entra logada.
- Primeiro login scriptável: `adb shell uiautomator dump /sdcard/ui.xml &&
  adb pull /sdcard/ui.xml` → ler `bounds` dos EditText/botão →
  `input tap X Y`, `input text "user@x.com"`, `input keyevent KEYCODE_ENTER`.
- Guardar credenciais de teste e coordenadas num `ux_capture/login.sh` —
  login reproduzível se a sessão expirar.

### 3. Loop de captura (como o modelo "mexe" na app)

**Antes de capturar — status bar limpa (demo mode):** PNGs consistentes e
sem ruído (relógio, bateria, ícones de notificações de outras apps) que
confundiria a medição de geometria/cores:

```bash
adb -s <SERIAL> shell settings put global sysui_demo_allowed 1
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command enter
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command clock -e hhmm 1200
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command battery -e level 100 -e plugged false
adb -s <SERIAL> shell am broadcast -a com.android.systemui.demo -e command notifications -e visible false
```

No fim da sessão: `... -e command exit` para repor. Datas/horas *dentro* do
conteúdo da app (ex.: "há 2 dias" num anúncio) não se limpam — tratam-se
como dados de exemplo: as fixtures do mock é que definem o conteúdo na
recriação.

Ciclo por ecrã:

1. `adb exec-out screencap -p > ux_capture/<nome>.png` — screenshot direto
   para o PC, sem passar pelo sdcard.
2. `uiautomator dump` + `pull` → árvore de views com `bounds` clicáveis →
   o modelo escolhe o próximo alvo (tab, card, filtro, botão).
3. Ação: `input tap` / `input swipe x1 y1 x2 y2 300` /
   `input keyevent KEYCODE_BACK` / `input text`.
4. **Cobertura exaustiva — regra dura.** Percorrer a app de uma ponta à
   outra: abrir TODOS os ícones, tabs, itens de menu, drawer, overflow (⋮),
   FABs; long-press e swipe sobre items de lista; cada entrada de settings;
   dialogs, bottom sheets, onboarding, ajuda/sobre/jurídico. Cada ecrã ou
   estado alcançável = 1 PNG nomeado. Estratégia: travessia em largura —
   em cada ecrã, extrai do `uiautomator dump` os nós clicáveis ainda não
   visitados e visita-os um a um; a fase só fecha quando não restar
   nenhum. Um tap por explorar = um buraco na spec que a FASE 4 descobre
   tarde demais.

Estados fora do happy-path (não esquecer):
- Lista vazia / sem resultados, skeletons de loading
- Offline e erro: desligar rede (`svc wifi disable` + `svc data disable`)
  e capturar os ecrãs de erro/retry
- Anónimo vs autenticado, sessão expirada
- Toasts/snackbars, dialogs de confirmação, pedidos de permissão

Atalhos e limites:

- Deep links saltam direto a ecrãs internos:
  `am start -a android.intent.action.VIEW -d "<scheme>://<path>"`.
- Animações/transições não saem em PNG → `adb shell screenrecord
  /sdcard/flow.mp4` (máx 3 min) + `adb pull` por cada fluxo-chave.

### 4. Correlacionar com a spec estática

Cada PNG recebe o nome do layout correspondente (`lista.png` ↔
`res/layout/fragment_list.xml`). Resultado: `ux_capture/` = spec viva que
mostra o que o XML estático não mostra — conteúdo real, skeletons de
loading, estados de erro, variações por dados.

### 5. Spec de comportamento (como a app se comporta — não só o que mostra)

Durante a travessia, registar em `ux_capture/ux_behavior.md`:

- **Mapa de navegação**: por cada ação, `ecrã_origem → trigger →
  ecrã_destino` (ex.: `lista → tap card #3 → detalhe`). Resultado: o grafo
  real de navegação, não o deduzido.
- **Gestos por elemento**: swipe revela ações? pull-to-refresh? swipe
  horizontal em galerias? long-press = menu contextual?
- **Animações observadas**: por cada screenrecord, anotar o que se move,
  duração aproximada e easing (slide-up, fade, shared-element) — cruzar com
  `res/anim`/`interpolator` extraídos na FASE 1.
- **Feedback**: snackbar vs dialog vs toast, haptics, confirmação antes de
  ações destrutivas, undo.
- **Back**: comportamento do botão back por ecrã (sai? confirma? sobe?).
- **Formulários**: validação quando (on-blur vs submit), máscaras de input,
  foco, comportamento do teclado.

## FASE 1 — Extração da especificação (read-only sobre o original)

**Android** — duas vistas complementares:
- `apktool d base.apk -o decompiled/` → `res/` (layouts XML legíveis, values,
  drawables), `smali*/` (bytecode em texto), `AndroidManifest.xml`, `assets/`
- `jadx base.apk` → código Java legível (`jadx_src/`) — referência para greps
  direcionados, não para leitura integral

**O que extrair para a spec de UI/UX:**
- `res/layout*/` → hierarquia completa de ecrãs (é literalmente a definição
  visual)
- `res/values*/` → `colors.xml`, `strings.xml` (todos os idiomas),
  `dimens.xml`, `styles.xml`, `themes.xml`
- `res/drawable*/` → vetores/ícones · `res/color*/` → selectors
- `res/anim*/ animator/ interpolator/` → animações · `res/font/` → tipografia
- `AndroidManifest.xml` → mapa de activities/tabs, deep links, providers
- iOS equivalente: `.nib`/`.storyboardc` (decoder NIBArchive),
  `*.lproj/*.strings`, `Assets.car` (cores em records COLR), metadados Swift
  (`__swift5_types`, campos)

**Mapa completo de rede e contrato de dados** — tudo por greps direcionados
(não é leitura de código, é extração de identificadores). Objetivo: TODA a
ligação que a app faz para fora fica classificada — zero hosts sem dono:

- **Endpoints REST**: grep `https://` e annotations Retrofit
  (`@GET/@POST/@PUT/@DELETE`) no smali/jadx → método, path, params, shape
- **Base URLs e ambientes**: hosts em strings/build config — dev vs prod,
  domínios de API vs CDN vs tracking
- **Auth**: esquema completo — grep `Authorization`, `Bearer`, `oauth`,
  `refresh_token`, cookies de sessão, providers de login social
- **Realtime e push**: `wss://`, socket.io, FCM topics/canais → o que
  precisa de canal vivo
- **Uploads e media**: `multipart`, `upload`, hosts de imagens/CDN → onde
  os ficheiros vivem e para onde vão
- **Config remota/feature flags**: `remote_config`, endpoints de
  bootstrap/arranque
- **Serviços de terceiros por ecrã**: maps SDK, pagamentos, analytics,
  crashlytics, ads — tudo o que telefona para casa
- **DTOs**: classes `*Dto/*Response/*Request` — campos = contrato por ecrã
- **Persistência local**: entidades Room/Realm → schema esperado

Cada host sai classificado no `endpoints.json`: **rebuild** (o teu backend
implementa) / **substituir** (equivalente próprio na recriação) /
**descartar** (tracking/telemetria — não se reconstrói). Cada endpoint leva
também `screens: [...]` — que ecrãs alimenta (do cruzamento
PNG ↔ layout ↔ DTO): é o índice que a FASE 4 usa para ligar dados à UI.

**Stack tecnológica** — detetar, porque a codebase nova usa a mesma:
- Linguagem + toolkit de UI: Kotlin/Java + XML Views vs Compose;
  Swift/Obj-C + UIKit vs SwiftUI (presença de `res/layout` XML vs UI
  declarativa no smali; metadados `__swift5_types`)
- Arquitetura visível: activities/fragments vs single-activity; padrão por
  nomes de classes (`*ViewModel`, `*Presenter`, `*Controller`)
- Libs principais por pacotes/imports em smali: Retrofit/OkHttp, Room/Realm,
  Coil/Glide, Hilt/Dagger, Coroutines/RxJava → mapear para equivalentes

Guardar tudo em `ui_spec/` + `endpoints.json` + nota de modelo de dados +
`stack.md`.
Cruza-se com `ux_capture/`: cada ecrã capturado em vivo deve mapear para um
layout extraído.

## FASE 4 — Recriação limpa (o entregável publicável)

- Nova codebase escrita **obrigatoriamente na stack da original** (extraída
  na FASE 1): mesma linguagem, mesmo toolkit de UI, mesmas libs ou
  equivalentes diretos — não trocar XML por Compose nem UIKit por SwiftUI
  "porque é mais moderno"; a paridade de stack é o que torna a spec
  reproduzível 1:1
- Ecrãs reescritos a partir de `ui_spec/` + `ux_capture/` — código 100% novo,
  assets próprios. Corre o **template do APÊNDICE** por ecrã: o PNG dá
  geometria/cores, o layout XML a hierarquia, `ux_behavior.md` os gestos e
  os destinos de navegação
- **Backend teu, contrato versionado** — o `endpoints.json` é a interface
  documentada entre UI e backend (entra no repo): spec para implementares o
  TEU backend, não hosts para a app chamar. Estágios obrigatórios:
  1. mock local que serve o contrato com fixtures (desbloqueia a UI já)
  2. backend real em LAN (`0.0.0.0:8080` + cleartext no
     `network_security_config`)
  3. deploy para o teu servidor — a app não muda, só a base URL
- **Networking isolado + config única** — base URL, keys e ambientes num
  único ficheiro de config; todo o acesso à API atrás de um client/camada
  de dados que espelha o `endpoints.json`; zero hosts hardcoded nos ecrãs.
  Resultado: trocar de backend/estágio = mudar uma linha; uma UI nova
  liga-se ao backend só pelo contrato documentado
- A app original instalada no telefone continua a ser a referência viva para
  comparar UX ecrã a ecrã
- Validação final: percorrer `ux_capture/` + `ux_behavior.md` e confirmar
  paridade de UI **e comportamento** — ecrãs, fluxos, animações, contraste,
  estados vazios/erro, gestos, navegação

---

## Checklist de sucesso

- [ ] `ux_capture/` completa — cobertura exaustiva verificada: zero nós
      clicáveis por visitar, fluxos-chave em screenrecord, correlacionados
      com os layouts
- [ ] `ux_behavior.md` completo — grafo de navegação, gestos, animações,
      feedback, back, formulários
- [ ] Spec estática isolada (layouts + values + drawables + animações +
      mapa do manifest)
- [ ] `endpoints.json` completo — mapa de rede exaustivo, zero hosts sem
      classificar (rebuild/substituir/descartar) + esquema de auth +
      modelo de dados
- [ ] Serviços de terceiros mapeados (o que substituir na recriação)
- [ ] Codebase nova criada — código 100% próprio, assets próprios
- [ ] Networking isolado — base URL/keys num único ficheiro de config,
      zero hosts hardcoded nos ecrãs
- [ ] Backend próprio implementa o contrato (mock → LAN → servidor)
- [ ] UX equivalente validada ecrã a ecrã contra `ux_capture/`

## Nota de contexto

Esta via não produz nenhum APK derivado — extrai spec e recria de raiz. O
que vai para a loja é sempre a codebase nova da FASE 4.

---

## APÊNDICE — Template de recriação por ecrã (corre na FASE 4)

Um prompt destes por cada ecrã de `ux_capture/` + `ui_spec/`. Substitui
`<STACK_UI>` pelo toolkit detetado na FASE 1 (`stack.md`) e `<ECRÃ>` pelo
PNG/layout de referência.

---

Recria fielmente o UI de `<ECRÃ>` num único componente autocontido na stack
`<STACK_UI>` — a mesma da app original (`stack.md`). Consulta
`ux_behavior.md` para este ecrã.

FIDELIDADE VISUAL (prioridade máxima):
- Extrai a geometria REAL dos elementos gráficos (ilustrações, blobs,
  ícones, logos): traça os contornos a partir da imagem e converte-os em
  paths vetoriais (SVG/vector drawable/Path consoante a stack). NÃO uses
  caixas + corner radius quando a forma é orgânica/irregular.
- Mede na imagem cores exatas (hex), posições, tamanhos e altura dos textos
  — não estimes a olho. Cruza com `ui_spec` (colors/dimens). Se algo for
  ambíguo, diz o que assumiste.
- Mede a tipografia de cada bloco: fontSize, peso, line-height, cor,
  alinhamento; usa a font de `res/font` se existir.
- Elementos cortados pelas bordas desenham-se completos, continuando
  offscreen.
- Define um espaço de design a partir da imagem e escala com as dimensões
  do dispositivo; formas escalam uniformemente.

FIDELIDADE DE COMPORTAMENTO:
- Implementa gestos/animações/estados anotados em `ux_behavior.md` para
  este ecrã (pull-to-refresh, swipe actions, validação, transições) com as
  durações/easings de `res/anim`/`interpolator`.
- Liga cada elemento interativo ao destino certo no mapa de navegação.

DADOS (se o ecrã consumir API):
- O componente recebe dados por props/estado — nunca chama HTTP
  diretamente; quem alimenta é o client de API + camada de dados (config
  única).
- Mapeia os campos do DTO correspondente (`endpoints.json` → `screens`)
  1:1 para os elementos do ecrã.
- Implementa os estados loading/erro/vazio replicados de `ux_capture/`.

ESTRUTURA DE PRODUÇÃO:
- Componente com props para interações (ex.: onLogin, onOpenTerms), tipos
  fortes na linguagem da stack.
- Camadas decorativas sem captura de toques; overflow escondido no root.
- Elementos interativos com accessibilityRole/equivalente; links com o seu
  próprio handler.
- NÃO desenhes réplicas da status bar nem do indicador de gestos — usa
  StatusBar translúcido e safe-area-insets se fizer sentido.
- Dependências mínimas: só as equivalentes às já detetadas em `stack.md`.

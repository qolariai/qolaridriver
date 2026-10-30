# PROMPT — Backend central do trio Qolari Mobility (Rider + Driver + Fleet)

Continua este trabalho. Responde em português de Portugal. Raiz: `C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\`

Laboratório **local de aprendizagem**: 3 apps Uber (Android) rebrandeadas para Qolari, ligadas a um backend no PC, a correr no telemóvel via USB. Não distribuir nem operar a sério.

**Objetivo desta fase**: juntar as 3 apps ao backend e ao backoffice **com o mesmo processo do projeto BOLT FOOD** — as apps abrem com os **seus próprios ecrãs** (login incluído) e todo o trabalho é fazer o backend responder ao que cada app espera, endpoint a endpoint, validando no telemóvel.

---

## 1. COMO SE TRABALHA (ler primeiro)

- **As APKs são as originais da Uber**, só rebrandeadas e com os URLs redirecionados. Ecrãs, botões, textos fixos e lógica são da app. **Não se cria nenhum ecrã nosso à frente da app** (o utilizador rejeitou a página de login web que foi feita na sessão anterior — ver §3, passo 2). O que aparece com dados (perfil, categorias, preços, carros no mapa, estados da viagem, ganhos, motoristas da frota) vem das respostas do backend.
- **As APKs só se recompilam uma vez** (§3, passo 1: apontar para `127.0.0.1` + `adb reverse`). Depois disso ficam congeladas; tudo o resto é no backend.
- **Ciclo por endpoint**:
  1. Abrir a app no telemóvel com o logcat a gravar **desde antes** (`adb logcat -c` e `adb logcat -v time > f.txt`).
  2. Consola → **Integração das apps** → app → "Ao vivo" / "Por mapear" (ou `BACKEND\logs\<app>\AAAA-MM-DD.log`): cada pedido, o handler usado e a resposta; os "Por mapear" levaram `{}` e o detalhe mostra a operação e o **modelo de resposta esperado** (campos navegáveis, tirados da APK).
  3. Código descompilado: path → interface Retrofit (`*Api.smali`) → modelo de resposta → quem consome (procurar leituras sem guarda / campos obrigatórios).
  4. Handler em `BACKEND\apps\<app>.py` com `@handles(app, "POST", "/rt/...")` e um comentário a dizer de onde saiu o contrato (classe/campo); teste em `BACKEND\tests\`.
  5. Reiniciar o servidor (ainda **não há recarga a quente**: `netstat -ano | findstr :8300` → `taskkill /PID <pid> /T /F` → `BACKEND\iniciar.bat`; vale a pena acrescentar um `POST /api/dev/reload` para os `apps\*.py`, como no Bolt) e voltar a testar no telemóvel.
- **Apps nativas (Java/Kotlin, não React Native como o Bolt)**: erros aparecem no logcat como `FATAL EXCEPTION` / `AndroidRuntime`, erros de parse Gson/Moshi (`JsonSyntaxException`, `Expected BEGIN_OBJECT…`), ou `OkHttp`/`RxJava` `onError`. Uma resposta `{}` onde a app esperava um campo obrigatório costuma dar erro silencioso + ecrã vazio ou a voltar ao início.
- **Descompilação**:
  - Smali (fonte das recompilações): Rider `USER\work_base\` (+ `USER\work_splits\`), Driver `DRIVER\decoded\`, Fleet `FLEET\qolarifleet_src\`.
  - Contratos já extraídos (copiados em `BACKEND\contracts\`): Rider 1055 endpoints + 1894 modelos (`USER\backend_spec\`), Driver 1053 paths + 2022 modelos, Fleet 647 endpoints + 527 modelos. `BACKEND\tools\extract_models.py` extrai mais modelos de pastas smali.
  - Java legível: `FLEET\tools\jadx\bin\jadx.bat` (ainda não foi corrido em nenhuma das 3; as APKs têm 120–270 MB, correr só sobre as classes necessárias ou com tempo).
  - Os pacotes foram renomeados: Rider `com.ubercab.*`→`com.qolari.*` e `com.uber.*`→`com.qint.*`; Driver e Fleet `com.ubercab.*`/`com.uber.*`→`com.qolari.*`. Headers: Rider/Driver mandam `x-uber-*`; a **Fleet manda `x-qolari-*`** (o rebrand trocou todas as strings `uber`).
- **Conduzir o telemóvel**: `adb shell input tap/swipe`, `adb shell uiautomator dump /sdcard/ui.xml` + `adb shell cat /sdcard/ui.xml` (textos e bounds), capturas `adb shell screencap -p /sdcard/x.png` + `adb pull`. adb: `C:\Users\Miglo\AppData\Local\Microsoft\WinGet\Packages\Google.PlatformTools_Microsoft.Winget.Source_8wekyb3d8bbwe\platform-tools\adb.exe`.
- **Telemóvel partilhado** (HONOR `PTP_N49`, série `AQCK024C17020494`, ligado por USB): o utilizador também o usa para outros projetos (BOLT FOOD usa `adb reverse` 9090/8080/7070 → 8100; o `com.myapp.android` usa `tcp:8080 → 8000`). Antes de mexer: `adb reverse --list` e `adb shell dumpsys activity activities | grep topResumedActivity`; **pedir OK** para instalar APKs, mudar regras `adb reverse` e conduzir o telemóvel. Nunca escrever dados de cartão.
- Ao editar ficheiros no Windows: o `Set-Content -Encoding UTF8` do PowerShell 5.1 mete BOM — usar o Edit ou Python.

---

## 2. PRESENTE (2026-10-05)

### Backend → `BACKEND\` (ler `BACKEND\README.md`)
- FastAPI + SQLite (`data\qolari.db`), **um processo com 4 portas**: Driver **80**, Rider **8090**, Fleet **3000**, consola **8300**. A app é identificada pela **porta local** onde o pedido entra (não pelo `Host`). Arranque: `BACKEND\iniciar.bat` (ou `.venv\Scripts\python server.py`); **não arranca sozinho** depois de reiniciar o PC. Se o Apache do XAMPP estiver ligado, a 80 fica ocupada (o servidor avisa e continua). Testes: `.venv\Scripts\python -m pytest -q tests` → **9 testes, todos a passar** (ciclo completo pelas 3 apps + consola, sem telemóvel).
- Domínio (`domain\`): `trips.py` (**máquina de estados única** `requested → accepted → arrived → in_progress → completed` + `cancelled`/`no_drivers`, **despacho** ao motorista aprovado/online/mais próximo com veículo da categoria, propostas que expiram, liquidação), `pricing.py` (base + km + minuto, mínimo, dinâmica, taxa de reserva, promoções), `finance.py` (ledger por parte: motorista/frota/plataforma, pagamentos), `settings.py` (parâmetros editáveis na consola), `push.py` (fila de mensagens por utilizador para o canal `ramen`), `seed.py`. Relógio de 1 s em `main.py` (expira propostas, refaz despacho, move motoristas **simulados** no mapa).
- Camada das apps (`apps\`): `rtapi.py` (registo `@handles`, token em `x-uber-token`/`x-qolari-token`/Bearer, erros `{"code": "rtapi.xxx", "message"}`, catch-all `{}` + registo em `EndpointStat` e no tráfego ao vivo), `identity.py` (login, `/rt/identity/oauth2/token`, sessões, dispositivos), `rider.py`, `driver.py`, `fleet.py`, `common.py` (`/ramen/sessions/{id}/messages` em long-polling, conta do utilizador), `catalog.py` (catálogo das APKs → templates e modelos esperados). **Sem `STRICT_AUTH`, um pedido sem token válido usa o 1.º utilizador do seed** (útil para a app avançar enquanto o login não está mapeado).
- **Os handlers seguem os nomes de campo dos modelos das APKs mas nunca foram validados com uma app real.** Mais incertos: fluxo de login, `ClientStatus.status` do Rider (`Looking`/`Dispatching`/`WaitingForPickup`/`OnTrip` — palpite), `DriverTasks` do Driver (proposta = `upfrontOfferTaskData` em `blockingTasks`; recolha/entrega = `completionTask` `pickupTaskData`/`dropoffTaskData`; uniões Gson sem campo `type` — palpite), formato das mensagens `ramen`. Enums **confirmados** no smali da Fleet: `DriverStatus` OFFLINE|ONLINE|ONTRIP, `OnboardingStatus` ACTIVE|APPLIED|REJECTED|WAITLISTED|…, `OrganizationOnboardingStatus` COMPLETE|IN_PROGRESS, `ComplianceStatus` ACTIVE|INACTIVE|INVALID.
- Seed: Lisboa; categorias Qolari X, Comfort, XL, Green; frotas "Frota Tejo, Lda." (taxa 12 %) e "Lisboa Drive Partners" (8 %); comissão da plataforma 20 %; ~60 viagens concluídas nos últimos 7 dias; código promocional `BEMVINDO`. Contas: Rider `+351910000001` Ana, `+351910000002` Bruno, `+351910000003` Carla — Driver `+351920000001` Carlos (Tejo), `+351920000004` Diana (independente), `+351920000006` Inês (por aprovar) — Fleet `+351930000001` Rui (Tejo), `+351930000002` Sofia. Código de verificação fixo `0000` (`OTP_CODE`).

### Backoffice → `BACKOFFICE\` (ler `BACKOFFICE\README.md`)
- Vite 7 + React 19 + TS + React Router 7 + Leaflet; `npm run build` → servido em **<http://127.0.0.1:8300>** (login `admin@qolari.local` / `admin`). Tempo real por long-polling (`/api/changes`).
- Secções: Painel (mapa ao vivo), Viagens (detalhe com mapa, tarifa, cronologia, propostas, movimentos, ações/forçar estado), **Simulador** (pedir viagens no mapa e avançar sem telemóvel), Motoristas, Passageiros, Frotas, Veículos, Documentos, Categorias e tarifas, Promoções, Finanças (saldos, pagamentos, acertos), **Integração das apps** (o instrumento principal desta fase), Definições (parâmetros, administradores com papéis, sessões, dispositivos, mensagens, registo de ações). API em `BACKEND\console\`.

### Estado das apps
| App | Pacote | Fonte smali | APK atual | URL gravado | No telemóvel |
|---|---|---|---|---|---|
| **Rider** (Uber 4.650.10003) | `com.qolari.rider` | `USER\work_base` + `work_splits` | `USER\final_apks\*.apk` (splits) / `USER\QOLARI USER.apk` | `http://192.168.1.204:8090` (1141 ocorrências: dex, `resources.arsc`, `assets\parameters.json`, `assets\loginUrlFetch*.html`) | instalada (2026-10-03), nunca falou com este backend |
| **Driver** | `com.qolari.driver` | `DRIVER\decoded` | `DRIVER\qolari-drive.apk` | `http://192.168.1.204` (porta 80; 1482 ocorrências + manifest) | **não instalada** |
| **Fleet** | `com.qolari.fleet` | `FLEET\qolarifleet_src` | `FLEET\QolariFleet.apk` | `http://192.168.1.204:3000` (1026 ocorrências) | **não instalada** |

No telemóvel há também `com.ubercab.driver` e `com.ubercab.fleet` **originais da Play Store** (outros pacotes; não mexer) e apps de outros projetos (`com.qolari.drive`, `com.qolaridriver.*`, `com.qolarifood.app`… — não mexer).
Assinatura: `DRIVER\tools\qolari.keystore` / `USER\qolari.keystore` (alias `qolari`, pass `qolari123`). Ferramentas: `apktool.jar` e `apk-signer.jar` em `DRIVER\tools\`, `FLEET\tools\`, `USER\tools\` (+ `build-tools` com aapt2/zipalign); Java 21 no PATH. `BACKEND\tools\scan_host.py <apk> [host]` lista onde aparece o endereço dentro de um APK.

**Rede**: o PC está agora no Wi-Fi com IP **10.196.82.12** (não 192.168.1.204) e a firewall do Windows bloqueia entradas no Python → **as apps, tal como estão, não chegam ao backend**. Por isso o passo 1 abaixo.

---

## 3. FEITO EM 2026-10-06 (sessão 2) — ler isto antes dos próximos passos

> Nota: a tabela "Estado das apps" e a secção "Rede" do §2 ficaram desatualizadas; o que vale é isto.

- **APKs redirecionadas para `127.0.0.1` + `adb reverse` e instaladas** (`com.qolari.rider`, `com.qolari.driver`, `com.qolari.fleet`):
  - Rider `http://127.0.0.1:8090` → `USER\final_apks_local\*.apk` (29 splits; keystore `USER\qolari.keystore`; instalar com `adb install-multiple -r *.apk` dentro da pasta).
  - Driver `http://127.0.0.1:8091` → `DRIVER\qolari-drive-local.apk` (feita a partir de `qolari-drive-resfix.apk`, a que estava instalada; keystore `DRIVER\tools\qolari.keystore`; `adb install -r` mantém os dados). No PC `DRIVER_PORT=8091` (`config.py`); a 80 fica livre para o Apache.
  - Fleet `http://127.0.0.1:3000` → `FLEET\QolariFleet-local.apk` (keystore do Driver).
  - `adb reverse tcp:8090 tcp:8090`, `tcp:8091 tcp:8091`, `tcp:3000 tcp:3000` — perdem-se quando o USB/adb reinicia.
- **Recompilar sem estragar nada** (nunca `apktool b -f`): `BACKEND\tools\apk_cache.py seed <apk> <fonte>` (põe os dex/recursos da APK atual na cache `build\apk` do apktool) → editar só smali → `java -jar apktool.jar b <fonte> -o x.apk` (incremental: só remonta os `classesN.dex` alterados; verificado byte a byte) → `BACKEND\tools\patch_apk_host.py <apk> <saida> <antigo> <novo> classesN.dex=<fonte>\build\apk\classesN.dex …` (troca só esses dex e reescreve os string pools do `resources.arsc`/XML; o resto fica igual) → `zipalign -p -f 4` → `apksigner sign --v4-signing-enabled false` (ambos em `USER\tools\build-tools\android-14`). `BACKEND\tools\repoint_apks.py` troca o IP nas fontes; `scan_host.py` confirma.
- **Bugs antigos das APKs corrigidos** (o Rider rebentava ao arrancar desde 03-10): pin OkHttp `*192.168.1.204:8090` (rebrand de `*.uber.com`) em `USER\work_base\smali_classes3\up9\h.smali` → `*.qolari.local`; drawables partidos (`@null`) — 42 no Rider, 37 na Fleet (a Driver já tinha o resfix): `BACKEND\tools\fix_null_drawables.py scan|fix <apk>`.
- **Login = o da própria app.** As 3 usam a biblioteca `uauth`/USL da Uber: a app abre `/v2?codeChallenge=…&app_url=…&isEmbedded=true` numa WebView (em produção é a página de `auth.uber.com`; não existe ecrã nativo de telefone). `BACKEND\apps\usl.py` serve essa página — réplica do fluxo original (telemóvel → código de 4 dígitos `0000` → nome se a conta for nova), marca Qolari, sem atalhos nem avisos — e redireciona para `qolarilogin://auth?session=<id>&authCode=<c>` (string `uauth_dl_scheme`; `UAuthWebViewClient.a(Uri)`). A app confirma com `POST /rt/silk-screen/submit-form` (corpo `formContainerAnswer`, ecrã `SESSION_VERIFICATION`, `codeVerifier` PKCE verificado) e recebe `OnboardingFormContainer.oAuthInfo`. O login web antigo foi retirado; modelo novo `LoginAttempt`. **Decisão tomada por mim (o utilizador pediu "faz tu tudo sozinho")** — confirmar com o utilizador se a página está como ele quer.
- **Recarga a quente**: `curl -X POST http://127.0.0.1:8300/api/dev/reload` (só de 127.0.0.1; reimporta `apps\*.py`, inclusive ficheiros novos; tabelas novas exigem reiniciar). O servidor está a correr escondido com saída em `BACKEND\logs\server.out.log` / `server.err.log`.
- Testes: **12 a passar**.

### Estado no telemóvel (06-10, 00:40)
- **Rider**: login OK (Ana `+351910000001`) → **ecrã inicial** ("Introduzir local da recolha", "Obter uma viagem"). Pede `app-launch` em ciclo (~1/s: resposta incompleta?) e há ~15 endpoints "Por mapear" (`cx/homescreen/get-homescreen-layout`, `request-blockers/get-blockers/`, `locations/v3/labeled/all`, `consumer/get-rider-preferences`, …). O logótipo no topo ainda diz "Uber" (resto do rebrand).
- **Driver (atualizado 06-10, 01:40)** — resolvido:
  1. **gRPC**: o canal gRPC (`DRIVER\decoded\smali_classes2\la1\e0.smali` método `a`) foi mudado para grpc-okhttp **HTTP/2 sem TLS em `127.0.0.1:8092`** (o original: Cronet/TLS para `host:443`, que depois do rebrand dava `Invalid host or port: 127.0.0.1:8091 443`); campo `k` de `smali_classes22\io\grpc\okhttp\b.smali` passou a público. No PC: `BACKEND\apps\grpc.py` (hypercorn, registo `@grpc_handles`, framing + trailers, descodificador protobuf para o registo, entra no "Ao vivo" da consola), `config.GRPC_PORTS`, `adb reverse tcp:8092 tcp:8092`. `apps\parameters.py` responde a `GetMobileParameters*` com mensagem vazia → a obtenção de parâmetros passa a SUCCESS.
  2. **Classes perdidas no rebrand**: 470 ficheiros smali com caminho ≥ 260 caracteres nunca entraram no dex (o apktool no Windows ignora-os) e 281 deles nem foram renomeados. Corrigido com `BACKEND\tools\fix_long_smali.py` + compilar a partir de `subst X: DRIVER\decoded` (`java -jar apktool.jar b X:\`). Mais 58 descritores desencontrados `com/uber`↔`com/qolari` → `BACKEND\tools\fix_package_leftovers.py`. Verificação: `BACKEND\tools\dex_classes.py <apk> missing-refs|missing-supers` — a Driver tem agora a mesma linha de base da APK original da Uber (32 referências em falta, todas também no original).
  3. Logger da biblioteca de parâmetros (`smali_classes2\mw2\a.smali`) instrumentado para o logcat (tag `ParametersSDK`) — útil para diagnóstico; o original estava vazio.
  - **Ponto atual**: depois do login a app abre uma WebView de onboarding do parceiro (`RichWebUiView`) que esgota o tempo ("Algo correu mal / Tente novamente mais tarde"). No proxy `BACKEND\tools\tcp_peek.py` vê-se que há ligações **TLS (https)** a `127.0.0.1:8091`, que o servidor HTTP rejeita ("Invalid HTTP request received"). Próximo: descobrir que URL https é essa (provavelmente um host montado como `https://` + host) e mudá-la para `http://`. O servidor está neste momento com `DRIVER_PORT=18091` atrás do proxy na 8091 — para voltar ao normal, reiniciar sem essa variável e parar o `tcp_peek.py`.
- **Driver (estado anterior)**: login OK (Diana `+351920000004`), depois "Algo correu mal / Tentar novamente" (`NetworkErrorRetryView`, sem nenhum pedido). Causa: `DRIVER\decoded\smali_classes3\s75\b.smali` só deixa passar se a obtenção **autenticada** de parâmetros (`ParameterFetchStatusStream`, `LAST_AUTHENTICATED`) acabar em `SUCCESS`; o pedido `/api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParameters` (`ParameterServingPresentationGrpcClientImpl`, via `RealtimeClient`) **nunca chega ao backend** — descobrir quem dispara o fetch e porque não sai; o corpo é protobuf.
- **Fleet**: arranca e mostra o ecrã próprio "Divulgação de acesso à localização" (OK) — login ainda não feito. Corrigidos 2 bugs do rebrand que a impediam de abrir: pins `127.0.0.1:3000` em `FLEET\qolarifleet_src\smali_classes8\d41\i.smali` → `*.qolari.local`; `google_api_key` com 38 caracteres e `google_app_id` fora do formato → marcadores iguais aos do Rider/Driver (no `resources.arsc` e no `strings.xml`). Pede `/v1/projects/qolari-fleet-local/installations` (Firebase) em ciclo — responder ou ignorar.

### Firebase (2026-10-11)
- iOS: só existe a IPA do Driver (`IOS\DRIVER\qolari-driver.ipa`, backend `http://192.168.1.9`) — ligada ao Firebase (plist novo + hosts Firebase repostos; ver `IOS\DRIVER\BACKEND_E_MUDANCAS_IOS.md`). Falta assinar (Sideloadly/Apple ID) e chave APNs no Firebase para push. User/Fleet iOS: sem IPA. Backend: escuta em `0.0.0.0`; a Driver também responde na porta **80** (`EXTRA_APP_PORTS`, para a IPA). No PC falta o IP `192.168.1.9` no Wi-Fi e permitir o python na firewall (rede está como "Pública").
- Projeto `qolari-driver-prod`: só 6 apps — Android e iOS `com.qolari.rider` / `com.qolari.driver` / `com.qolari.fleet` (as antigas `com.qolaridriver.*` e a Web Admin foram removidas, exclusão pendente 30 dias). Configs em `ANDOIRD\<APP>\firebase\google-services.json` e `IOS\<APP>\firebase\GoogleService-Info.plist`.
- Valores metidos nas APKs com `BACKEND\tools\set_firebase_res.py <apk> <saida> <google-services.json> <pacote>` (só as entradas `string/google_app_id`, `google_api_key`, `gcm_defaultSenderId`, `project_id`, …; nada por substring) → zipalign + apksigner. Também nos `res\values\strings.xml` das fontes (`--strings`). Cópias anteriores em `ANDOIRD\<APP>\backup_pre_firebase\`.
- As 3 instaladas em 11-10 com estas APKs (Rider `USER\final_apks_local\*.apk`; Driver `DRIVER\qolari-drive-local.apk`, foi preciso desinstalar uma build das 00:09 assinada com outra chave `1E:08:A9…` — dados da Driver no telemóvel perdidos, refazer login; Fleet `FLEET\QolariFleet-local.apk`).

### Servidor Hetzner (2026-10-11) — substituiu o DriveMond
- `ssh root@128.140.82.32` (Ubuntu 24.04, `nexus-ai`; outros sites no mesmo nginx — não mexer). DriveMond (`/var/www/qolaridriver`, BD `qolaridriver_db`) **apagado**; cópia em `/root/backups/drivemond-20261011/` (BD, código, nginx, APKs do marketplace) e `BACKUPS\drivemond-20261011\` neste PC (BD + nginx).
- Backend em `/opt/qolari-driver/BACKEND` (+ `BACKOFFICE/dist`), venv própria, utilizador `qolari-driver`, serviço `systemctl … qolari-driver`, env `/etc/qolari-driver.env` (só root: `ADMIN_PASSWORD`, `SECRET`; `BIND_HOST=127.0.0.1`, Fleet na **3200** porque a 3000 é de outro site). Atualizar: copiar ficheiros (tar sem `.venv`/`data`/`logs`) → `chown -R qolari-driver:` → `systemctl restart qolari-driver`.
- nginx `/etc/nginx/sites-available/qolari-driver` (+ `snippets/qolari-driver-{proxy,ssl}.conf`), certificado `qolari-driver` (Let's Encrypt, 8 nomes):

  | App | Android (HTTPS) | iOS (HTTP, cabe nos slots da IPA) | porta |
  |---|---|---|---|
  | Driver | `https://driver.qolari.com` | `http://d.qolari.com` | 8091 |
  | Driver gRPC | `grpc-driver.qolari.com:443` (HTTP/2 TLS → `grpc_pass` 8092) | — | 8092 |
  | Rider/User | `https://rider.qolari.com` | `http://r.qolari.com` | 8090 |
  | Fleet | `https://fleet.qolari.com` | `http://f.qolari.com` | 3200 |
  | Consola | `https://admin-driver.qolari.com` | | 8300 |
- **APKs do servidor (11-10, instaladas no telemóvel, já falam com o servidor)**: `FLEET\QolariFleet-server.apk`, `DRIVER\qolari-drive-server.apk`, `USER\final_apks_server\*.apk` (29 splits). Feitas com `BACKEND\tools\repoint_server.py apply <app>` (fontes smali; repõe também as strings Google/Firebase/Tink/protobuf que o rebrand antigo tinha estragado — log em `repoint_<app>_server.json`) → `apk_cache.py seed` antes → `apktool b` incremental (Driver/Rider via `subst X:`/`Y:`) → `finish_apk.sh` (dex + recursos + assinatura) → `restore_entries.py` (`google/*`, `mozilla/*` da APK original). gRPC da Driver: TLS `grpc-driver.qolari.com:443`. As `*-local.apk` / `final_apks_local` continuam a apontar para 127.0.0.1.
- **Google Maps (11-10)**: chave "Qolari Maps Key" (projeto `qolari-driver-prod`, sem restrições de app — restringir por package+SHA-1 / bundle ID) em `ANDOIRD\google_maps_api_key.txt`; posta com `set_firebase_res.py --res` (Rider `ub__config_google_mapsv2key`, Driver `maps_api_key`) e `--manifest` (Fleet: literal `com.google.android.maps.v2.API_KEY`), também nas fontes.
- **Crash do Rider ao obter localização (corrigido 11-10)**: `UnsatisfiedLinkError ... com.qint.h3.NativeMethods.geoToH3` — o rebrand trocou nomes de símbolos dentro de `libh3.so` sem recalcular a tabela `.hash` do ELF (carrega, mas o dlsym não encontra os `Java_com_qint_h3_*`). `BACKEND\tools\fix_elf_hash.py scan|fix <apk>` recalcula a `.hash` SysV no sítio (só `USER\final_apks_server\config.arm64_v8a.apk` tinha o problema; Driver/Fleet limpas; `.gnu.hash` não é tratada). A `final_apks_local` continua com o bug.
- **Ciclo do `app-launch` do Rider (corrigido 11-10)**: a app lia o `City` da resposta e falhava no `vehicleViews[].fare` (`vehicleview.ProductFare` exige `id`, `type` TIME_AND_DISTANCE|TIME_OR_DISTANCE, `baseValue`, `speedThresholdMps`, `distanceUnit` KM|MILE) → tratava como erro de rede e repetia ~1/s (`appLaunchRetryOnNetworkErrorV3`). Corrigido em `apps\rider.py::vehicle_view`; o `metadata` devolve agora `requestPickupLocationSynced`/`targetLocationSynced`. Lição: o Uber constrói os modelos com `Builder.build()` que lança "X is null!" nos campos obrigatórios — ver as `const-string ".. is null!"` em `<Modelo>$Builder.smali`. Bissecção usada: devolver só alguns blocos da resposta e contar pedidos no nginx.
- **BD do servidor = cópia da BD local (11-10, autorizado)** para os UUIDs baterem com as sessões do telemóvel; a anterior em `/root/backups/qolari-driver/`. ⚠️ Com ela veio o admin da consola com a password `admin` — mudar na consola (Conta) ou no servidor.
- `server.py`: `SO_REUSEADDR` fora do Windows (o restart no Linux falhava a porta 8090 com "Address already in use").
- **Falta**: IPA Driver repontar para `http://d.qolari.com` (o utilizador corre os comandos; os binários iOS não podem ser alterados por mim); IPAs User e Fleet não existem (precisa dos IPAs decifrados da Uber e da Uber Fleet); marketplace `qolaridriver/` ainda com as APKs do DriveMond (Rider são 29 splits → precisa de APK única); botão "Demo" da página do marketplace aponta para `driver.qolari.com` (agora é a API) → `admin-driver.qolari.com`.

### Driver online e viagem completa (12–15/10)
- **APK instalada: `DRIVER\qolari-drive-server-v3.apk`** (v2 + recursos do split). Duas correções de APK:
  1. **Colisões de classes do rebrand** (`com.uber.X` e `com.ubercab.X` → ambos `com.qolari.X`): `NavigationManager`,
     `navigation/a|b|c` e 10 de `usnap/camera`. A Driver caía logo depois do login (`NoSuchMethodError` em
     `NavigationManager.D()/g0()`). As versões `com.uber` passaram a `…U` (ex. `NavigationManagerU`), referências
     decididas pela APK original (`DRIVER\source-original.apk`): `BACKEND\tools\fix_class_collisions.py` (lento: ~10 min por
     varrimento; dex remontados 2,5,7,8,13,15,17,19). Atenção: `smali_classes20` da fonte NÃO tem `navigation/a|c` que
     estão no dex da APK — não remontar o 20 sem os repor.
  2. **176 drawables sem entrada no `resources.arsc`** (a base foi rebrandeada sem os splits de densidade): ao ficar online
     caía com `BadForegroundServiceNotificationException ... id=0x7f080cf3` (`ub__ic_carbon_notification`). Fonte: o
     `split_config.xxxhdpi.apk` da Uber Driver da Play Store instalada no telemóvel (4.600; IDs e nomes iguais aos nossos,
     confirmado pelo R `smali\xs\h.smali`) → `BACKEND\tools\merge_split_res.py <apk> <split> <saida> --check-r ...`
     (`--only a,b` para só alguns) → zipalign + apksigner.
- **Contrato validado no telemóvel** (`apps\driver.py`, testes em `tests\test_flow.py`):
  - Posições: `/rt/unifiedlocation/uploadpositions` (`uploadLocationRequest.positions[].point`, a cada 4 s) e
    `/rt/surge/supplyInput` → motorista com posição real (deixa de ser simulado).
  - **Proposta = push ramen `push_driver_unified_offers_v3`** (`UnifiedDriverOffers` → `offers[].driverOfferData`
    `{type: primaryOffer}` → `DriverOffer` `offerType JOB`, `metaData.jobOfferModel.acceptWindow`, `offerView.jobOfferViewV3`
    com `coreInfo.simpleView` de etiquetas + `offerAcceptElement.acceptButton`). O `upfrontOfferTaskData` do DriverTasks
    não é lido por ninguém. Sondagem alternativa `/rt/drivers/unified-offers-v3` → `{data, etag, pollingInterval}`.
  - **Ramen: `interpretType` tem de ser `"FULL"`** (com `x-uber-ramen-diff-mode: v1` qualquer outro valor é tratado como
    patch e a mensagem é descartada). Tradução domínio → PushModel por app em `common.TRANSLATORS`.
  - Viagem aceite = `TaskScope` no `DriverTasks` (respostas de accept/begin/end/app-launch… e push `push_drivers_tasks`):
    uniões com `type` = nome do campo, `completionTask` `source DEMAND_JOB`, `coalescedDataUnion`
    pickup/dropoffCoalescedTaskData (`product`, `info.title`), `taskDataMap {tripUUID: pickup/dropoffTaskData}`; morada e
    mapa = `nonBlockingTask` `locationTaskData`. Deslizar "RECOLHER X" → `/rt/trips/v2/begin` (com `waypointUUID`);
    "DEIXAR X" → `/rt/trips/v2/end`. A app não tem passo "cheguei" (`start-waiting` só no temporizador manual,
    `com.qolari.manual_wait_time`): **a chegada é decidida no servidor** — posição a ≤ `arrive_radius_m` (80 m, consola)
    da recolha passa a viagem a `arrived` (`trips._auto_arrive`); em `arrived` a Driver recebe `waitTimeTaskData`.
  - **Avaliação do passageiro e detalhe da tarifa no fim estão desligados por parâmetro**: `jo7.d` (namespace
    `dp_mobile`) `rate_rider_plugin_switch` (por omissão desligado); `transparent_fare_breakdown_worker_plugin_switch`
    ligado mas só serve o ecrã de avaliação. Para os ligar é preciso responder com parâmetros em `GetMobileParameters`
    (gRPC protobuf; hoje vazio) — por fazer.
  - `driverState.available` = online também durante a viagem; com `false` a app mostra "Os pedidos foram interrompidos" e
    manda `go-offline` ao terminar. `go-offline` a meio da viagem responde 200 sem mudar nada; `expire/reject-offers`
    idempotentes.
  - **PIN: por omissão não há** (só se o passageiro o pedir: `request_trip(pin_required=True)`). A tarefa
    `pinVerificationTaskData` só vai no estado `arrived` (em `accepted` deixava o painel em "A carregar...").
  - O painel da viagem (cartão do passageiro + botão de deslizar) é um cartão da **agenda** e às vezes aparece recolhido
    (puxar a folha para cima). O Glide (painel inferior) cai no layout de recurso porque `/rt/glide/...` responde `{}` →
    barra de estado "A carregar...".
- **Diagnóstico**: os registos internos da Driver vão por gRPC `UflurryV2/PublishMessages` (corpo gzip) e ficam em
  `data/uflurry/*.bin` no servidor (`apps\uflurry.py`); ler com `gzip.decompress` + strings (eventos `DriverTasksPayload`,
  `AgendaMetadata`, `EarnerDashboard*`...). `uiautomator dump` falha com animações (cartão/procura): usar `screencap`.
- Utilitários no servidor (não versionados): `/tmp/dev_trip.py status|request [perto]|cancel` (viagem do Bruno junto à
  Diana) e `/tmp/dev_push.py` (reenvia `trip_status`).

## 4. PRÓXIMOS PASSOS

1. Rider: completar `app-launch` (parar o ciclo) e os "Por mapear" do ecrã inicial; depois destino → `fare-estimate` → pedir → viagem (Simulador da consola como motorista).
2. Driver: desbloquear os parâmetros pós-login (acima); depois online → proposta → viagem → ganhos.
3. Fleet: OK na divulgação → login (`+351930000001`) → mapear.
- Já confirmado no smali do Rider: `RideStatus` serializa como `Looking`/`Dispatching`/`WaitingForPickup`/`OnTrip` (era palpite).
4. Ciclo completo com as 3 apps; ajustar o backoffice; atualizar `BACKEND\README.md`.

Plano original de cada app (continua válido):
- **Rider**: arranque (`/rt/riders/{uuid}/app-launch`, `/rt/riders/me/status`) → home com carros à volta (`eyeball.nearbyVehicles`) → escolher destino → `fare-estimate` (categorias e preços da consola) → pedir (`pickup`) → ver motorista a caminho → em viagem → fim → avaliar → histórico. Usar o **Simulador** da consola como motorista enquanto a app Driver não estiver mapeada.
- **Driver**: login → `app-launch` (estado de onboarding) → ficar online (`v2/go-online`, bloqueios `fetch-online-blockers`, veículos) → receber proposta (DriverTasks / ramen) → aceitar → chegar → PIN → iniciar → terminar → ganhos (`/rt/earnings/*`) e perfil (`/rt/earner-profile/*`). Localizações em `/rt/locations/v1/upload-driver-device-locations` (passa o motorista a "posição da app", deixa de ser simulado).
- **Fleet**: login (só contas `FleetUser`) → `get-is-authorized-fleet-partner-v2`, `get-partner-info-v2`, `get-user-organizations` → motoristas (`get-fleet-drivers-v2`, mapa `get-driver-events`) → veículos (criar/atribuir) → ganhos e extratos.
- **Ciclo completo com as 3 apps** (como o Bolt: cliente pede → motorista aceita/conduz → frota vê → backoffice mostra tudo).

### Pendentes menores
- `BACKEND\README.md` ainda descreve o login web antigo e as portas LAN — atualizar.
- O Leaflet usa mosaicos OpenStreetMap (precisa de internet).
- A consola mostra o seed com motoristas **simulados**; desligar "Simular movimento" em Definições quando houver motoristas reais.

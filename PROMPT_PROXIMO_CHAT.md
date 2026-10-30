# PROMPT — Novo chat: app Driver → volta ao Rider → testes da viagem completa

> **Substituído em 2026-10-25 pelo programa novo.** Para o trabalho de spec/recriação,
> usa [`PROMPT_CLONE_MEGA.md`](PROMPT_CLONE_MEGA.md) e
> [`PROMPT_CLONE_BUILD.md`](PROMPT_CLONE_BUILD.md). Este documento fica como registo do
> laboratório de backend contra as APKs renomeadas.

Cola isto no início do novo chat. Responde em português de Portugal.
Raiz: `C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER\`

## 0. Enquadramento (ler antes de tudo)
Laboratório de aprendizagem: 3 apps Android da Uber (Rider, Driver, Fleet) rebrandeadas para **Qolari**, ligadas a um
backend nosso (FastAPI + SQLite) num servidor Hetzner, com um backoffice React. **Não distribuir nem operar a sério.**

Regras de trabalho (o utilizador insiste nelas):
- **As APKs são as originais.** Não se cria nenhum ecrã nosso à frente da app (o utilizador rejeitou isso). Todo o
  trabalho é **o backend responder ao que cada app espera**, endpoint a endpoint, validando no telemóvel — o mesmo
  processo do projeto BOLT FOOD.
- **Trabalho sequencial**, por esta ordem: (1) app Driver online e a aceitar viagens → (2) voltar ao Rider (ecrãs da
  viagem com motorista) → (3) testes da viagem completa com as duas apps → (4) só depois Fleet/backoffice.
- Tens autorização para usar o telemóvel por adb, ler logs e publicar no servidor. **Não escrever passwords/códigos de
  login** (o login nas apps faz-se com o código fixo `0000` na página da própria app; se for preciso escrevê-lo,
  pede ao utilizador). Se o telemóvel mostrar outra app (é partilhado com outros projetos), pára e espera/avisa.
- Faz tudo sozinho e mostra resultados (capturas do telemóvel) no fim de cada etapa.

Documentos a ler (nesta ordem):
1. `PROMPT_BACKEND_CENTRAL.md` — história completa, arquitetura, **§3 (estado da Driver)**, secção "Servidor Hetzner".
2. `PROMPT_RIDER_PEDIDO.md` — o que ficou feito no Rider em 12-10 e as lições (enums/uniões, viagem ativa).
3. `BACKEND\README.md` (parcialmente desatualizado: ainda fala do login web antigo e de portas LAN).

## 1. Onde estamos (2026-10-12)
- **Servidor**: `ssh root@128.140.82.32`, `/opt/qolari-driver/BACKEND`, serviço systemd `qolari-driver`.
  Hosts: Rider `https://rider.qolari.com` (8090), Driver `https://driver.qolari.com` (8091) + gRPC
  `grpc-driver.qolari.com:443` (8092), Fleet `https://fleet.qolari.com` (3200), consola `https://admin-driver.qolari.com`
  (8300). O nginx é partilhado com outros sites — não mexer neles.
- **Publicar** um ficheiro: `scp BACKEND/apps/<x>.py root@128.140.82.32:/opt/qolari-driver/BACKEND/apps/` →
  `chown qolari-driver:` → recarga a quente (no servidor): `curl -X POST http://127.0.0.1:8300/api/dev/reload`
  (reimporta `apps/*.py`; tabelas novas exigem `systemctl restart qolari-driver`, que faz a app mostrar "Sem internet"
  uma vez). Testes locais: `BACKEND\.venv\Scripts\python -m pytest -q tests` → **14 a passar**; manter a passar.
- **Rider** (`com.qolari.rider`, conta Ana `+351910000001`): fluxo até ao pedido **funciona** — escolher recolha e
  destino (moradas reais), categorias, "Confirmar recolha" → `POST /rt/riders/{uuid}/v2/pickup` → viagem `requested`
  → ecrã da viagem → sem motorista em 90 s → `no_drivers` e aviso. Detalhes em `PROMPT_RIDER_PEDIDO.md`.
- **Driver (atualizado 15-10)**: APK `ANDOIRD\DRIVER\qolari-drive-server-v3.apk` instalada, conta Diana. **Fica online,
  recebe a proposta, aceita, RECOLHER → DEIXAR → fim, e continua online** (ver PROMPT_BACKEND_CENTRAL §3 "Driver online e
  viagem completa"). Chegada automática por posição (80 m) desde 15-10. Falta na Etapa 1: avaliação do passageiro
  (precisa de parâmetros gRPC: `dp_mobile/rate_rider_plugin_switch`), ganhos (painel Glide `/rt/glide/*`, hoje `{}` →
  barra "A carregar..." e cartão da viagem às vezes recolhido), `/rt/navigation/v3/route`. Testes: **17**.
  No servidor `offer_timeout_s` está a 60 s (para testar no telemóvel; por omissão 20).
  O texto abaixo sobre a Driver é o estado ANTIGO (até 12-10).
- **Driver (antigo)** (`com.qolari.driver`, APK `ANDOIRD\DRIVER\qolari-drive-server.apk`, instalada): **nunca ficou online**
  (zero pedidos `go-online` no servidor). Últimos pedidos: 10-11 `/rt/drivers/me/status` (sem handler),
  `/rt/silent-authentication/initiate`; 10-06 `drivers/app-launch`, `v2/vehicles`, `get-onboarding-status`.
  Problemas conhecidos (§3 do PROMPT_BACKEND_CENTRAL): parâmetros pós-login (`ParameterFetchStatusStream`
  LAST_AUTHENTICATED tem de dar SUCCESS — `GetMobileParameters` via gRPC), WebView de onboarding do parceiro
  (`RichWebUiView`) que esgotava o tempo. Os dados da app foram apagados em 11-10 (reinstalação) → refazer login.
  Contas: Diana `+351920000004` (independente, aprovada) ou Carlos `+351920000001` (Frota Tejo).
- **Motoristas no BD**: 4 simulados online em Lisboa (Carlos, Marta, Diana, Paulo) recebem as propostas e nunca
  aceitam. Quando a Driver real ficar online, o motorista da app deixa de ser simulado (`upload-driver-device-locations`).
  Para testes de proposta, pôr os outros offline na consola ou garantir que o real é o mais próximo (raio 8 km).

## 2. Etapa 1 — App Driver (começar aqui)
Objetivo: Driver logada → ecrã principal → **ficar online** → receber a proposta de uma viagem pedida no Rider →
**aceitar** → chegar → PIN → iniciar → terminar → ganhos.
1. Abrir a Driver com o logcat a gravar desde antes; ver o ecrã (`uiautomator dump` + `screencap`) e os pedidos no
   servidor (`logs/driver/AAAA-MM-DD.log`, `endpoint_stats` em `data/qolari.db`, nginx `access.log`, gRPC no
   "Ao vivo" da consola). Fazer o login se for preciso (pedir o código ao utilizador se tiver de ser escrito).
2. Desbloquear o arranque endpoint a endpoint (Retrofit `*Api.smali` → modelo de resposta → campos obrigatórios →
   handler em `BACKEND\apps\driver.py` com comentário de onde saiu o contrato + teste em `BACKEND\tests\`).
3. Online: `v2/go-online`, `fetch-online-blockers`, veículos; proposta = `DriverTasks` (`upfrontOfferTaskData` em
   `blockingTasks` — **palpite, validar**) e/ou mensagem `ramen`; aceitar/chegar/iniciar/terminar
   (`completionTask` `pickupTaskData`/`dropoffTaskData` — palpite). Domínio já existe em `domain/trips.py`
   (máquina de estados `requested → accepted → arrived → in_progress → completed`, despacho, liquidação).
4. Fontes: smali `ANDOIRD\DRIVER\decoded\` (ver `fix_long_smali.py` / `subst X:` no PROMPT_BACKEND_CENTRAL),
   contratos `BACKEND\contracts\driver_*`, `BACKEND\tools\model_tree.py driver <classe>`, jadx sobre os dex da APK.

## 3. Etapa 2 — Voltar ao Rider
Com a Driver a aceitar: o Rider deve passar a EN_ROUTE ("Motorista a caminho") → chegou → em viagem → fim →
avaliação → histórico. A viagem ativa vai em `riderAppOrdersResponse` + `fulfillmentStateData`
(`legacyTripState` DISPATCHING/EN_ROUTE/ON_TRIP; falta tratar POST_TRIP/fim). Pendentes do Rider: cabeçalho do ecrã
de procura vazio, `/rt/navigation/get` (rota a pé, Signal3x v31 — não bloqueia), preço na lista de categorias,
ETA "1221 min", "A recolher opções", pesquisa por texto. Ver `PROMPT_RIDER_PEDIDO.md` §"Próximo passo".

## 4. Etapa 3 — Testes da viagem completa
No telemóvel com as duas apps (alternar entre Rider e Driver): pedir no Rider → aceitar na Driver → chegar → PIN →
iniciar → terminar → avaliar dos dois lados → recibo/histórico no Rider → ganhos na Driver → viagem e finanças na
consola. Repetir cancelamentos (passageiro, motorista) e "sem motoristas". Cada caso confirmado ganha um teste em
`BACKEND\tests\` (os testes não usam o telemóvel). No fim, atualizar `PROMPT_BACKEND_CENTRAL.md` e
`BACKEND\README.md`.

## 5. Lições que poupam horas
- **Campo obrigatório em falta** (`"X is null!"` nos `<Modelo>$Builder.smali`; `model_tree.py` marca com `*`) = a app
  rejeita o objeto pai inteiro **em silêncio** (trata como erro de rede, repete o pedido ou volta ao ecrã anterior).
- **Enums/uniões**: nas uniões Thrift o `type` é o **nome do campo** (`"riderContextData"`, `"singlePersonalTransport"`,
  `"transportJobId"`…); outros enums têm `@SerializedName` próprios (`DefaultDevice`, `Accepted`, `MinutesToPickup`) ou
  o nome Java. Ver sempre no smali; valor errado = UNKNOWN sem erro.
- O rebrand antigo estragou strings de terceiros e libs nativas (ver `fix_elf_hash.py`) — suspeitar disso quando algo
  inexplicável falhar. Nunca `apktool b -f` (receita incremental no PROMPT_BACKEND_CENTRAL).
- jadx: classpath com caminho Windows (`C:/.../ANDOIRD/FLEET/tools/jadx/lib/*`); saber o dex de uma classe com
  `grep -c -a "pacote/Classe;" classes*.dex`; acessores dos modelos ofuscados — ler o `.java`.
- Telemóvel: confirmar `topResumedActivity` antes de cada toque; `MSYS_NO_PATHCONV=1` no `uiautomator dump`; os logs
  da Uber não vão ao logcat (só crashes) — o servidor é a melhor fonte.
- Registos do servidor cortam corpos (4000 caracteres no `endpoint_stats`, 2000 no ficheiro de log).

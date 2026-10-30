# Continuar: pedido de viagem no Rider (QOLARI DRIVER)

Lê primeiro `PROMPT_BACKEND_CENTRAL.md` (secção "Servidor Hetzner" e seguintes). Responde em português de Portugal.
Tens autorização do utilizador para mexer no telemóvel (adb), ler logs e publicar no servidor. Não escrevas
passwords/códigos de login. Se o telemóvel mostrar outra app (o utilizador a usá-lo), pára e avisa.

## Estado (2026-10-12, fim do dia)
- Backend no Hetzner `ssh root@128.140.82.32`, `/opt/qolari-driver/BACKEND`, serviço `qolari-driver`.
  Publicar um ficheiro: `scp apps/rider.py root@...:/opt/qolari-driver/BACKEND/apps/` → `chown qolari-driver:` →
  recarga a quente SEM reiniciar: `curl -X POST http://127.0.0.1:8300/api/dev/reload` (no servidor).
  Reiniciar o serviço faz aparecer "Sem internet" na app (tocar IGNORAR em 1080,2526).
- Rider no telemóvel (`USER\final_apks_server\`) fala com `https://rider.qolari.com`. Testes locais:
  `BACKEND\.venv\Scripts\python -m pytest -q tests` (**14**, todos a passar).
- **Fluxo completo até ao pedido FUNCIONA**: home → "Para onde?" (recolha já com morada real) → "Defina a localização
  no mapa" → arrastar (destino com morada real) → "Confirmar destino" → categorias → "Escolher Qolari X" →
  "Confirme o ponto de recolha" (morada, já não "Localização do pino") → "Confirmar recolha" → `get-blockers` →
  **`POST /rt/riders/{uuid}/v2/pickup`** → viagem criada (`requested`, moradas, tarifa, PIN) → a app mostra o ecrã da
  viagem ("Detalhes da viagem · Encontro no seu local de recolha") e sonda `status` a cada 4 s → sem motorista em 90 s
  → `no_drivers` → volta à lista com o aviso "Sem motoristas disponíveis / Não há motoristas perto de si…".
- **Falta motorista**: as propostas vão para os motoristas *simulados* do seed (Carlos, Marta, Diana, Paulo, online em
  Lisboa a ~7 km), que nunca aceitam. A app Driver (`com.qolari.driver`, instalada) nunca chegou a `go-online`
  (parada no arranque/onboarding desde 06-10, ver `PROMPT_BACKEND_CENTRAL.md` §3) → **próximo grande passo**.

## Feito em 12-10 (apps\rider.py, apps\geocode.py novo, tests\)
- `resolve-location` (`ResolveLocationResponse.resultantLocations` obrigatório): `resultantLocations[0]` com
  `anchorGeolocation` (GeolocationResult: `location.id` não vazio + `provider` + name/addressLine1/2/fullAddress +
  `coordinate`), `locationSource` ecoado (`DefaultDevice`…), `pickups` = o próprio pino com `suggested:false` (o uv2.v só
  mostra pontos de acesso com `suggested:true`). Consumidor principal: `fp6.s` (copia locationSource + anchor para o
  ClientRequestLocation do pedido). Com `{}` a app repetia 1 s, 2 s, 4 s, 9 s…
- `apps\geocode.py`: Google Geocoding (pt-PT) com cache em memória + `data/geocode_cache.json` (4 casas decimais).
  Chave: env `GOOGLE_MAPS_KEY` (vazia = desligado, os testes usam isso) → `data/google_maps_api_key.txt` (no servidor,
  600, dono qolari-driver) → `ANDOIRD\google_maps_api_key.txt` (PC). Sem chave/erro devolve só coordenadas.
- `get-venue` → `{"hasVenue": false}`; `create-route-plan` / `delete-route-plan` (DELETE) → `{}`.
- **`get-blockers` — causa do bloqueio do "Confirmar recolha"**: nas uniões Thrift o campo `type` serializa-se com
  o **nome do campo** (`@SerializedName`): `RIDER_CONTEXT_DATA` → `"riderContextData"`, `REQUEST_BLOCKERS_CONTEXT_DATA`
  → `"requestBlockersContextData"`, `UPDATE_PAYLOAD_CONTEXT_DATA` → `"updatePayloadContextData"`, `RIDER_COMPONENT_KEY`
  → `"riderComponentKey"`. Com os nomes Java o Gson lê UNKNOWN, o `h18.d` não escolhe o construtor de caminhos (`vc6.a`)
  e o contexto fica em `REQUEST_BLOCKERS_CONTEXT` em vez de `REQUEST_BLOCKERS_CONTEXT_<requestUuid>`, onde o `uc6.d`
  espera → spinner ~15 s. Também corrigido no `order_selection` (`fullResponse`, `singleTransport`).
  **Regra geral**: antes de mandar um enum, ver no smali se tem `.annotation ... SerializedName` (uniões: nome do campo;
  alguns enums: `DefaultDevice`, `Accepted`, `MinutesToPickup`…; outros: o nome Java).
- **A viagem ativa nesta versão NÃO vem em `StatusResponse.trip`** (o campo nem existe; o `k7b.b.c` até apaga o Trip
  guardado a cada sondagem). Vem de duas partes que têm de bater pelo mesmo uuid (`l7b.k1` → `ActiveOrder`):
  `riderAppOrdersResponse.orders[]` (RiderAppOrder `id`, `state: ACTIVE`, `jobs.type: singlePersonalTransport`,
  `transport.id` = uuid da viagem, `transport.backwardsCompatibleData.legacyTripState` DISPATCHING/EN_ROUTE/ON_TRIP —
  é daqui que sai o estado do ecrã; `meta.lastModifiedTimeMs` obrigatório) e `fulfillmentStateData.orders[]`
  (`orderPlan.jobs[].jobId.alternatives.transportJobId.uuid` = mesmo uuid, `legacyTripData.trip/tripStatus/vehicleView`).
  Ambos no `status` e no `app-launch`; sem viagem vão com `orders: []` (limpa o ecrã).
- `trip_json`: removidos campos que faziam a app rejeitar o Trip inteiro; agora com os obrigatórios dos Builders:
  `tripStatusMessage` (messageId, title, context.tripUUID, detail.mode `Hidden|MinutesToPickup|…`), `pinVerificationInfo`
  (pin + `pinVerificationType`), `driver` (displayCompany, isAccessibilityTripViewEnabled, isCallButtonEnabled, rating,
  status `Accepted|Arrived|DrivingClient`), `vehicle` (exteriorColor, interiorColor, year, vehicleType id/capacity/make/model).
- Pickup: moradas a partir de `requestPickupLocation.anchorGeolocation.location` (senão geocodificação inversa).
- `clientStatus` após `no_drivers`/cancelamento: título = `lastRequestNote`, texto = `lastRequestMsg`,
  `lastRequestType` = enum `TripCancellationType` (`RequestExpired`, `DriverCanceled`, …).

## Próximo passo
1. **App Driver online** (ver `PROMPT_BACKEND_CENTRAL.md` §3, "Driver"): desbloquear o arranque (parâmetros/onboarding)
   → `go-online` → receber a proposta da viagem do Rider → aceitar. Só então o Rider passa a EN_ROUTE ("Motorista a
   caminho"), chegada, PIN, viagem, fim. Enquanto não houver, dá para testar o Rider fazendo um motorista simulado aceitar
   pelo domínio (`trips.accept`) ou pelo Simulador da consola.
2. Rider, pendentes: cabeçalho do ecrã de procura ainda vazio (já mandamos `tripStatusMessage` + `dispatchStatus`; pode
   precisar de `riderAppOrdersResponse.features[orderId]` — OrderCardFeature, etc.); `/rt/navigation/get` (rota a pé
   até à recolha; o parser `jw3.i0` exige Signal3x v31, `serviceProvider: roadrunner-router`, `routes[]` com `edges`,
   `routeUuid`, `encodedRoute` polilinha 1e-5 — hoje `{}` = erro tratado, não bloqueia); preço não aparece na lista
   (fareDisplays/shoppingFareFeature); ETA "1221 min" (segundos lidos como minutos); cabeçalho "A recolher opções";
   pesquisa por texto (`pudo-presentation-helix/text-search`, SDUI).

## Ferramentas (método que funcionou)
- `BACKEND\tools\model_tree.py rider <classe> [prof]` — campos/tipos/obrigatórios (`*`) dos modelos Uber.
- jadx (classpath com caminho **Windows**, senão "Could not find main class"):
  `java -Xmx3g -cp "C:/xampp/.../ANDOIRD/FLEET/tools/jadx/lib/*" jadx.cli.JadxCLI --show-bad-code -q --no-res -d <dir> classesN.dex`
  (dex extraídos de `USER\final_apks_server\base.apk`; ~1 min por dex; 8 em paralelo cabem). Saber que dex tem uma classe:
  `grep -c -a "pacote/Classe;" classes*.dex`. Os acessores dos modelos estão ofuscados (`g()`, `d()`…): ver o `.java`.
- Contratos: `BACKEND\contracts\rider_endpoints.json` (path → responseType).
- Telemóvel: `uiautomator dump` (com `MSYS_NO_PATHCONV=1`), `screencap`; antes de cada toque confirmar
  `topResumedActivity` = `com.qolari.rider` (o telemóvel é partilhado — hoje esteve com `com.qolari.watermark`).
- Servidor: `endpoint_stats` em `data/qolari.db` (last_request/last_response cortados a 4000 caracteres),
  `logs/rider/AAAA-MM-DD.log` (corpo até 2000), nginx `/var/log/nginx/access.log`.
- Lição: falta de campo obrigatório = a app trata como erro de rede / ignora em silêncio; procurar `"... is null!"`
  nos `$Builder.smali`; enum com nome errado = UNKNOWN em silêncio.

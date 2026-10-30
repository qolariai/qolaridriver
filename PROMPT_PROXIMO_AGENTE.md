# Passagem para o próximo agente — Qolari Driver

**Data:** 30/10/2026 · **Ramo:** `clone-driver-bloco2-3` · **Telefone de teste:** Mi (`18a959c4`)

---

## 1. Estado atual

O ecrã de pedido, a navegação e o **bloco 2** estão concluídos e validados no Mi.

| Área | Estado |
|---|---|
| Cartão de pedido (2 secções, preço 52sp, botão "Aceitar") | ✅ |
| Traço progressivo recolha→destino, duas pernas | ✅ |
| Radar de viagens (Exclusivo vs Radar) | ✅ |
| Navegação 2 fases (TO_PICKUP → recolha, ON_TRIP → destino) | ✅ |
| Painel de 2 secções (manobra + paragem verde/vermelha) | ✅ |
| Modo navegação tipo Google Maps (tilt 66°, zoom 18,3, sem 3D) | ✅ |
| Índice OSM local (`tools/osm_build.py` + `apps/osmgeo.py`) | ✅ |
| Cartão de espera na recolha (contador, barra, contacto, "Começar") | ✅ |
| Chat com o passageiro | ✅ |
| Motivos de cancelamento na recolha | ✅ |

**Simulação completa validada até `completed`, total 10,66 €.**

---

## 2. Testes

```
BACKEND: 88/88 ✅
ANDROID: 73/74  — única falha: ConfigTest.noHostIsHardcodedOutsideAppConfig
```

A falha do `ConfigTest` é **pré-existente** e aponta ao `DirectionsClient.kt` (host do
Google Maps). O teste exige que todos os hosts estejam no `AppConfig.kt`. Ou se move a
constante, ou se acrescenta uma exceção ao teste. **Não é regressão do clone.**

---

## 3. O que ficou por fazer — Bloco 3

O utilizador pediu o "Planeador de viagem". Chegou a ser implementado e foi **revertido**
a pedido dele (apagados `RecommendedFragment`, `TripPlannerFragment`, os layouts, ícones,
strings e listeners). **É para refazer de raiz, um ecrã de cada vez, mostrando antes de
avançar.**

### 3.1 Sem viagem — tocar ☰ → "Recomendado para si"

- Horas trabalhadas nas **últimas 24 h**
- Itinerário da **última viagem**
- Botão **OFFLINE**

### 3.2 Com viagem aceite — tocar ☰ → "Planeador de viagem"

- Linha **Recolha** e linha **Entrega**, cada uma com **⋮**
- Botão **"Parar novos pedidos"**
- Tocar ☰ outra vez **volta atrás**

### 3.3 ⋮ de cada paragem → desistir da corrida

Motivos (print do utilizador):

1. Aceitei por engano
2. Problema com a rota da recolha
3. Enganei-me no caminho
4. A recolha não compensa
5. A recolha não é segura
6. Problema com o veículo

> ⚠️ **Não confundir** com o cancelamento junto ao cliente (esse já está feito no bloco 2,
> abre pelo ícone de pessoa do cartão de espera). Aqui o motorista desiste **antes** de
> chegar ao cliente.

---

## 4. Regras do projeto (não negociáveis)

- **Nunca inventar dados.** Usar sempre Google Maps nativo + Google Directions. Nunca
  desenhar ruas ou rotas à mão.
- **Não inventar ecrãs nem botões.** Se não estiver no print ou no vídeo, perguntar.
  (Houve um caso em que foi acrescentado um botão "A+" que ninguém pediu — o utilizador
  não gostou. **Não repetir.**)
- UI em **português de Portugal**, tom Uber.
- **Não apagar** trabalho do utilizador nem APKs sem confirmar.
- Só testar no **Mi (`18a959c4`)**. O Honor (`AQCK024C170094`) é outro projeto.
- O selo "LIMITE" só aparece com `speedLimitSource == "osm"` (dado real). **Nunca** com
  estimativa.
- Radar: `radar_share_pct = 0`. Só vai ao Radar recolha > 2 km ou viagem que já falhou
  no exclusivo.

---

## 5. Como testar no Mi

```powershell
# base do projeto
cd "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER"

# compilar e instalar
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"
& "ANDOIRD\DRIVER\RECRIACAO\gradlew.bat" -p "ANDOIRD\DRIVER\RECRIACAO" assembleDebug --offline
adb -s 18a959c4 install -r --no-streaming "ANDOIRD\DRIVER\RECRIACAO\app\build\outputs\apk\debug\app-debug.apk"

# o reverse cai com frequência: repor sempre antes de testar
adb -s 18a959c4 reverse tcp:8091 tcp:8091
adb -s 18a959c4 reverse tcp:8090 tcp:8090

# captura de ecrã (o redirecionamento direto do PowerShell corrompe o PNG)
cmd /c "adb -s 18a959c4 exec-out screencap -p > .clone\capture\nome.png"
```

**Backend** (a partir de `BACKEND`):
```powershell
Start-Process .venv\Scripts\python.exe server.py
```
> O arranque em background pela shell é cancelado quando o servidor reinicia. Usar
> `Start-Process`.

**Scripts de simulação** em `C:\Users\Miglo\AppData\Local\Temp\opencode\`:
- `fases.ps1 <device>` — cria viagem, aceita, chega e inicia
- `sim_tudo.ps1` — fluxo completo com capturas em cada fase

---

## 6. Ficheiros-chave

| Ficheiro | O que contém |
|---|---|
| `ANDOIRD/DRIVER/RECRIACAO/app/src/main/java/com/qolari/drivereplica/ui/home/MapFragment.kt` | Ecran principal, navegação, cartão de espera, chat, cancelamento |
| `.../ui/home/RealMapView.kt` | Mapa, traço, pinos, `NAV_STYLE`/`MAP_STYLE`, `PIN_FLATTEN` |
| `.../drive/DriveViewModel.kt` | Estados, `loadNavigation`, `cancelForReason`, `sendMessage` |
| `.../drive/Navigation.kt` | Manobra atual, `NavStop`, formatação |
| `.../ui/home/ChatFragment.kt` | Chat com o passageiro |
| `.../ui/home/CancelReasonsFragment.kt` | Motivos de cancelamento na recolha |
| `res/layout/fragment_map.xml` | Painel, barra inferior, `mapList`, `navButton`, `speedBadge` |
| `res/layout/view_maneuver_panel.xml` | Painel preto de 2 secções |
| `res/layout/view_wait_card.xml` | Cartão de espera na recolha |
| `res/layout/view_pickup_nav_bar.xml` | Barra "A recolher/A deixar" (esquerda = `ic_filter`) |
| `BACKEND/apps/driver.py` | `driver_offer`, `trip_scope`, `tripInfo`, `navigation_route`, `trip_message` |
| `BACKEND/domain/trips.py` | Despacho, Radar, `settle_radar`, `tick`, `candidates` |
| `BACKEND/apps/osmgeo.py` | Limite de velocidade / nome de via por OSM |
| `.qolari/notes.md` | Histórico completo do projeto e limites conhecidos |

---

## 7. Decisões de design já fixadas

- Botão do cartão de proposta = **"Aceitar"** (não "Correspondência").
- Sem barra de contagem no cartão da proposta.
- Traço da proposta = progressivo, recolha→destino, preto com interior cinza.
- Pino do motorista = elipse achatada, `PIN_FLATTEN = 0.50f`, 62 dp de largura.
- Mapa de navegação: inclinação **66°**, zoom **18,3**, alvo **150 m** à frente, estilo
  `NAV_STYLE` próprio, **sem 3D** (`setBuildingsEnabled(false)`).
- Barra "À espera do utilizador": barra enche até **300 s** (5 min = 100%).
- Cartão de espera é mostrado em `AT_PICKUP`. O cartão antigo (`view_trip_card`) só
  aparece se houver **PIN**.

---

## 8. Correções de bugs já feitas (para não voltarem)

- `tick()` expirava a proposta antes do emparelhamento (ordem invertida) — corrigido.
- `featureType: "building"` inválido no `MAP_STYLE` causava `InvalidStyleException` e
  descartava o estilo todo — corrigido.
- `/rt/trips/driver-cancel` não existia (só `v2`) → cancelamento silencioso — corrigido
  com alias.
- Traço ficava no mapa após cancelar (resposta assíncrona do Directions) — corrigido.
- Ícone `ic_list` duplicado na barra de navegação → esquerdo passou a `ic_filter`.
- `FakeDrive` nos testes não implementava `sendMessage`/`cancel` — corrigido.

---

## 9. Último pedido do utilizador, ainda em aberto

No ecrã de espera (o print dele, 30/10 11:34), o utilizador apontou que **faltam coisas**
face ao original:

- A barra **"À espera do passageiro"** (com filtros à esquerda e lista à direita) deve
  ficar **visível** durante a espera — ficou implementado.
- A ordem do cartão deve ser **contador primeiro**, contacto (telefone/nome/pessoa)
  depois — ficou implementado.

O utilizador interrompeu depois com "DEIXA ESTAR ASSIM", por isso **não está confirmado**
que esteja como ele quer. **Antes de continuar o bloco 3, confirmar com ele este ecrã.**

---

## 10. Cuidados com o repositório

- O ramo `main` do GitHub tem **ficheiros que não existem nesta pasta local** (123
  ficheiros, ex.: `AudioRecorder.kt`, `SupportFragment.kt`, `lint.xml`, `.github/`).
  Por isso o envio foi feito para o ramo **`clone-driver-bloco2-3`** e não para `main`.
  **Não fazer merge cego** — avaliar primeiro se esses ficheiros devem ser repostos.
- Ficaram **fora do repositório** por segurança/tamanho: `google_maps_api_key.txt`,
  `*.xapk`, `*.apk`, `.clone/`, `.qolari/`, `TESTE PARALELO/`.
- Existem `google-services.json` e chaves Firebase em `ANDOIRD/*/firebase/`. São
  necessários para o build, mas **não deviam estar num repositório público**. Este
  repositório é privado, mas vale a pena revisitar.

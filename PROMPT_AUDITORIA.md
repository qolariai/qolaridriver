# PROMPT — Auditoria da QOLARI Driver (encontrar falhas e botões que não funcionam)

**Data:** 2026-10-31 · **Ramo:** `clone-driver-bloco2-3` · **Telemóvel:** Mi 9T Pro
`18a959c4` · **Último commit:** `78aedf5`

---

## 0. O que te pedem

**Não é para implementar nada.** É para **auditar**: percorrer a app toda, carregar em tudo o
que é botão e escrever um relatório do que não funciona, do que não faz nada, do que faz a
coisa errada e do que está visualmente fora do sítio.

O objectivo é ter uma lista concreta, com passos para reproduzir, para depois se corrigir.

**Não alteres código sem autorização do cliente.** Primeiro o relatório.

---

## 1. Contexto do projecto

Estamos a recriar a **Uber Driver** para a marca **Qolari**. O trabalho está dividido em fases
por fatia da viagem:

| Fase | O que é | Estado |
|---|---|---|
| 1 | Cartão do pedido (aceitar/recusar) | fechada |
| 2 | Motorista vai buscar o cliente | **fechada nesta sessão** (blocos A-D) |
| 3 | Espera do cliente no ponto de recolha | por fazer |
| 4 | Viagem até ao destino | por fazer |
| 5 | Fim da viagem e avaliação | por fazer |

### O que foi feito nos blocos A-D da Fase 2 (para saberes o que é novo e frágil)

**Bloco A — painel de navegação**
- 1.ª secção com texto rico: via + "em direção a" (cinza) + destino
- distância partida em número grande + unidade pequena (`140` + `m`)
- 2.ª secção alterna entre próxima manobra e paragem
- ponto da paragem quadrado; setas de manobra mais grossas; fundo preto puro
- distâncias arredondadas a 5 m abaixo dos 100 m
- vista geral ~2 s antes de entrar em navegação (`NAV_AUTO_START_MS`)

**Bloco B — desenho do mapa**
- traço de navegação carmim `#E62042`
- chevrons brancos a cada 55 m (só em modo navegação)
- pino do motorista circular (`PIN_FLATTEN = 1.0`)
- haste verde na bolha de recolha

**Bloco C — cromo**
- barra inferior vertical com pílula de arrasto
- disco verde com pessoa branca
- `fmtMin` aceita "0 min"
- coluna do A+ sobe 56 dp quando o botão "Navegar" aparece

**Bloco D — aviso de áudio**
- cartão com microfone durante 7 s (`AUDIO_NOTICE_MS`)

**Ícones e ecrãs novos (prints de 2026-10-30)**
- **A+** → "Adicionar um relatório de mapa" (6 sinais + "As minhas contribuições")
- **Atalho de percurso** → alterna vista geral
- **Escudo** → Conjunto de Ferramentas de Segurança
- **Filtros** → Preferências de serviços
- **Lista** → Planeador de viagem
- **⋮ do planeador** → cancelamento por motivos
- **Folha de itinerário** → comprovativo
- **Parar/Retomar pedidos** → `POST /rt/drivers/v2/pause-dispatch`

---

## 2. Como montar o ambiente

```powershell
# base do projecto
cd "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER"

# backend (8091 = Driver, 8090 = Rider)
cd BACKEND
Start-Process .\.venv\Scripts\python.exe -ArgumentList "server.py" -WindowStyle Hidden

# build e instalar no Mi
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"
cd ..\ANDOIRD\DRIVER\RECRIACAO
.\gradlew.bat assembleDebug --offline
adb -s 18a959c4 install -r --no-streaming app\build\outputs\apk\debug\app-debug.apk

# o reverse cai com frequência — repor SEMPRE
adb -s 18a959c4 reverse tcp:8091 tcp:8091
adb -s 18a959c4 reverse tcp:8090 tcp:8090

# captura (o redirecionamento directo do PowerShell corrompe o PNG)
cmd /c "adb -s 18a959c4 exec-out screencap -p > C:\Users\Miglo\AppData\Local\Temp\opencode\foto.png"
```

**Telemóvel:** só o **Mi 9T Pro** (`18a959c4`), 1080×2340, density 440 (escala 2.75).
O Honor `AQCK024C17020494` é de outra sessão — **não mexer**.

**Coordenadas úteis no Mi** (medidas nesta sessão):

| Elemento | x | y |
|---|---|---|
| A+ | 965 | 1500 |
| Atalho de percurso | 970 | 1678 |
| Escudo | 115 | 1660 |
| Filtros | 115 | 1455 |
| Lista (planeador) | 1180 | 2065 |
| Botão Navegar (vista geral) | 855 | 1620 |
| X do relatório | 88 | 1115 |

### Criar uma viagem de teste

Existe um script pronto:
`C:\Users\Miglo\AppData\Local\Temp\opencode\teste_final_mi.ps1`

Faz: limpa viagens → abre a app → cria viagem no Rider → aceita no Driver → tira capturas.
É o ponto de partida mais rápido.

---

## 3. O que auditar — lista de alvos

### 3.1 Ecrãs e botões conhecidos

Percorre cada um e regista se funciona:

**Mapa / em repouso**
- [ ] Casa (voltar ao painel)
- [ ] INICIAR / Ficar offline
- [ ] Qolari Pro (chip do topo)
- [ ] Pesquisa
- [ ] Os 4 atalhos da direita (raio, pin+, gráfico, localizar)
- [ ] Escudo
- [ ] Radar de viagens

**Cartão do pedido (Fase 1)**
- [ ] Aceitar
- [ ] Recusar (X)
- [ ] O cartão expira sozinho?

**Navegação até à recolha (Fase 2)**
- [ ] A+ → relatórios: os 6 sinais, "As minhas contribuições", X, "?"
- [ ] Atalho de percurso → vista geral; e voltar
- [ ] Botão "Navegar" na vista geral
- [ ] Escudo → Conjunto de Ferramentas (5 linhas, cada uma abre algo?)
- [ ] Filtros → Preferências (6 cartões, alternam? "Ver mais"?)
- [ ] Lista → Planeador → ⋮ → cancelar → escolher motivo → confirmar
- [ ] Planeador → Folha de itinerário (todos os campos preenchidos?)
- [ ] Planeador → "Parar novos pedidos" → "Retomar pedidos"
- [ ] Barra inferior: filtros, lista
- [ ] Selo LIMITE
- [ ] Balão da rua
- [ ] Aviso de áudio (aparece e desaparece?)

**Espera na recolha (Fase 3 — por fazer, mas já tem UI)**
- [ ] Contador
- [ ] Telefone → chat
- [ ] Pessoa → motivos de cancelamento
- [ ] Começar \<produto\>

---

## 4. O que procurar (checklist de falhas)

Para cada ecrã, procura activamente por:

1. **Botões mortos** — carregas e não acontece nada (nem animação, nem ecrã, nem erro).
2. **Botões que fazem a coisa errada** — abrem outro ecrã, navegam para o sítio errado.
3. **Botões tapados** — outro elemento por cima (já aconteceu com o "Navegar").
4. **Texto em falta ou a `null`** — campos vazios, "null", "0,00 €" sem dados.
5. **Texto cortado** — reticências onde devia caber, sobreposição entre linhas.
6. **Ecrãs que não voltam** — o botão de retroceder fecha a app em vez de voltar.
7. **Estados que ficam presos** — a UI mostra uma coisa e o servidor outra.
8. **Cores/formas fora do sítio** — algo que destoa do resto.
9. **Dados inventados** — números que a app mostra mas o servidor não mandou.
10. **Crashs** — `adb -s 18a959c4 logcat -d | Select-String "FATAL|AndroidRuntime"`

---

## 5. Regras do projecto (não negociáveis)

- **Nunca inventar dados.** Google Maps + Directions. Nunca desenhar ruas ou rotas à mão.
- **Não inventar ecrãs nem botões.** Se não está no vídeo ou no print, perguntar.
- **UI em português de Portugal**, tom Uber.
- **Não apagar trabalho do utilizador** nem APKs sem confirmar.
- **O selo LIMITE só com `speedLimitSource == "osm"`** (dado real). Nunca com estimativa.
- **Não enviar para o GitHub sem o cliente aprovar.**
- **Backend não se mexe** nesta auditoria — só se for para reportar.

---

## 6. Formato do relatório que tens de entregar

Escreve um ficheiro `AUDITORIA_2026-10-31.md` na raiz do projecto, com esta estrutura:

```markdown
# Auditoria — QOLARI Driver
Data · Telemóvel · Commit

## Resumo
- N ecrãs percorridos
- N botões testados
- N falhas encontradas (X críticas, Y médias, Z cosméticas)

## Falhas

### F-01 · <título curto>
- **Onde:** <ecrã> → <botão>
- **Esperado:** <o que devia acontecer>
- **Observado:** <o que aconteceu>
- **Passos:** 1. … 2. … 3. …
- **Gravidade:** crítica / média / cosmética
- **Prova:** <caminho da captura>
- **Suspeita:** <ficheiro:linha, se souberes — opcional>

### F-02 · …

## Botões testados que funcionam
<lista, para se saber o que já está validado>

## Não foi possível testar
<o que ficou por testar e porquê>
```

**Uma falha por entrada.** Sem juntar vários problemas na mesma.

---

## 7. Sugestão de ordem de trabalho

1. Ler este prompt e o `PROMPT_FASE2.md`.
2. Confirmar que o ambiente sobe (backend + app + reverses).
3. **Correr o `teste_final_mi.ps1`** e ver o estado de base.
4. Percorrer os ecrãs **sem viagem** (mapa em repouso, menus).
5. Criar viagem → percorrer **tudo** da Fase 2.
6. Chegar ao ponto de recolha → testar a Fase 3 (mesmo por fazer).
7. Escrever o relatório **enquanto testas**, não no fim de memória.
8. Mostrar o relatório ao cliente. **Não corrigir nada ainda.**

---

## 8. Ficheiros-chave

| Ficheiro | O que contém |
|---|---|
| `.../ui/home/MapFragment.kt` | Ecrã principal: cartão, navegação, espera, botões |
| `.../ui/home/RealMapView.kt` | Mapa, traços, chevrons, pinos, câmara |
| `.../ui/home/TripPlannerFragment.kt` | Planeador de viagem |
| `.../ui/home/ItinerarySheetFragment.kt` | Folha de itinerário |
| `.../ui/home/PlannerCancelFragment.kt` | Cancelamento com motivos |
| `.../ui/home/PreferencesServicesFragment.kt` | Preferências de serviços |
| `.../ui/home/MapReportSheet.kt` | Relatórios de mapa (A+) |
| `.../drive/DriveViewModel.kt` | Estados, `setPaused()`, navegação |
| `.../drive/Navigation.kt` | Manobra actual, formatação, `NavStop` |
| `.../state/PreferencesStore.kt` | Preferências locais, relatórios, serviços |
| `BACKEND/apps/driver.py` | Contrato da Driver (`pause-dispatch`, `driver_tasks`) |
| `BACKEND/domain/trips.py` | Despacho, `set_paused()`, `candidates()` |

---

## 9. Estado dos testes (antes de começar)

```
Backend ......... 92 passed
App ............. 85/85 (8 suites)
```

Se algum número estiver diferente, **pára e investiga** antes de continuar.

---

## 10. Um aviso honesto

Na última sessão ficaram **duas coisas por confirmar visualmente**:

1. **Chevrons na vista geral** — numa captura com o mapa ainda a carregar apareceram chevrons
   na vista geral. O código devia escondê-los (`clearChevrons()` no setter de `navigating`).
   **Confirma se reaparecem.** Se sim, é uma falha.

2. **Vista geral vs. navegação** — o toque no atalho de percurso falhou várias vezes por
   coordenadas erradas. **Confirma que os dois modos alternam bem** e que o botão "Navegar"
   volta a aparecer.

Fora isso, o Bloco A (painel), a pausa de pedidos e a barra centrada foram validados com
capturas no Honor e no Mi.

---

**Regra final:** o cliente prefere **uma falha bem descrita** a dez corrigidas à pressa.
Testa com calma e escreve com precisão.

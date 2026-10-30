# PROMPT — Próximo agente: Fase 2 (o motorista vai buscar o cliente)

**Data:** 2026-10-30 · **Ramo:** `clone-driver-bloco2-3` · **Telefone:** Honor
`AQCK024C17020494`

---

## 0. Enquadramento

Estamos a recriar a app **Uber Driver** para a marca **Qolari**. O trabalho está
organizado em **fases**, e cada fase é uma fatia vertical da viagem.

| Fase | O que é | Estado |
|---|---|---|
| **Fase 1** | Cartão do pedido de viagem (o motorista aceita ou recusa) | ✅ **fechada nesta sessão** |
| **Fase 2** | Motorista vai buscar o cliente (navegação até à recolha) | ⬅ **a começar** |
| Fase 3 | Espera do cliente no ponto de recolha | por fazer |
| Fase 4 | Viagem até ao destino | por fazer |
| Fase 5 | Fim da viagem e avaliação | por fazer |

**Regra de ouro:** uma fase de cada vez. Não avanças para a fase seguinte sem o
cliente confirmar que a actual está igual ao original.

---

## 1. O que ficou feito na Fase 1 (não repetir)

O cartão do pedido está igual ao vídeo de 2026-10-29:

- Chip do produto (preto) com o nome do backend ("Qolari X")
- Etiqueta do tipo ("Exclusivo" a azul `#276ef1`)
- Preço a 52sp bold
- Linha tempo · distância ("8 min · 3,9 km")
- Pill "Após dedução de taxa de serviço"
- Divisor de bordo a bordo
- Rail vertical: círculo na recolha, quadrado na entrega
- Recolha: rua em cinza + cidade em linha própria
- Viagem: rua + cidade em linha própria
- **Botão "Aceitar" azul `#246CF0`** (era preto — corrigido)
- **Duas pernas no mapa, em plano amplo** (motorista → cliente → entrega),
  visíveis até o cartão desaparecer

### Bugs corrigidos que não devem voltar

1. **Margem dupla no `reframe()`** — o `setPadding()` já reserva a área do
   cartão; passar a altura outra vez ao `newLatLngBounds` afastava o mapa até
   mostrar o país inteiro. Agora usa só 28dp de margem.
2. **`route` setter a chamar `wideView()`** — desfazia o plano amplo sempre que a
   rota mudava. Agora, com `showOfferMarkers = true`, nada mexe na câmara excepto
   o `reframe()`.
3. **PIN forçado a `True`** no `userlite.py` — contradizia a decisão do cliente.
   O PIN só existe quando o passageiro o pede (`pinRequired` no pedido).

---

## 2. O que é a Fase 2

Depois de o motorista tocar em **Aceitar**, a app passa a mostrar a **navegação
até ao cliente**. Isto já está parcialmente implementado — o objectivo é ficar
**igual ao original**, não reescrever.

### O que o vídeo de 2026-10-30 (13:59) mostra

| Elemento | Comportamento no original |
|---|---|
| Painel preto | 2 secções: manobra (seta + distância + rua) e paragem (ponto **verde** + morada da recolha) |
| Traço no mapa | **Só a perna motorista → recolha**. Sem o destino |
| Cor do traço | Preto, sempre (o vermelho da Uber não significa nada) |
| Marcadores | **Só o pino verde da recolha**. Sem pino de destino |
| Balão da rua | Nome da rua actual, por cima do motorista |
| Selo "LIMITE" | Só quando o OSM tem `maxspeed` real naquela via |
| Barra inferior | "A recolher \<nome\>" + tempo + distância |
| Botão | "Navegar" / "Vista geral" (alterna) |
| Câmara | Entra automaticamente em modo navegação ao aceitar |

### O que já existe e funciona

- `Navigation.kt` — escolha da manobra, formatação de distância
- `view_maneuver_panel.xml` — painel de 2 secções
- `view_pickup_nav_bar.xml` — barra "A recolher"
- `DriveViewModel.loadNavigation()` — **uma perna por fase** (já correcto)
- `RealMapView.setNavStop()` — pino da paragem (verde/vermelho)
- Selo de limite só com dado OSM real
- Botão "Navegar"/"Vista geral" com alternância de câmara

### O que falta verificar/afinar

1. **Balão da rua** — `setStreetLabel()` existe mas só funciona com
   `deviceLocation` não nulo. Confirmar que aparece.
2. **Selo LIMITE** — confirmar que aparece numa via com `maxspeed` no OSM e
   **desaparece** onde não há dado (decisão do cliente: nunca mostrar estimativa).
3. **Câmara ao aceitar** — deve entrar automaticamente em modo navegação.
4. **Ordem do painel** — manobra em cima, paragem em baixo, divisor entre elas.

---

## 3. Regras do projecto (não negociáveis)

- **Nunca inventar dados.** Google Maps nativo + Directions. Nunca desenhar ruas
  ou rotas à mão.
- **Não inventar ecrãs nem botões.** Se não está no vídeo ou no print, perguntar.
- **UI em português de Portugal**, tom Uber.
- **Não apagar trabalho do utilizador** nem APKs sem confirmar.
- **Só testar no Honor** (`AQCK024C17020494`). O Mi é outro projecto.
- **O selo LIMITE só com `speedLimitSource == "osm"`** (dado real). Nunca com
  estimativa.
- **Parar e mostrar** ao cliente antes de avançar de fase.

### Regras de teste (aprendidas à força)

- **Uma fase por teste.** Não encadear fases no mesmo script.
- **Capturar e mostrar** o resultado antes de continuar.
- **Nunca ficar online na conta real da Uber.** Se for preciso capturar o
  original, só leitura — nada de aceitar pedidos reais.

---

## 4. Como testar no Honor

```powershell
# base do projeto
cd "C:\xampp\htdocs\QOLARI\PROJETOS OFICIAIS\QOLARI DRIVER"

# backend (as duas portas)
cd BACKEND
Start-Process .\.venv\Scripts\python.exe -ArgumentList "server.py" -WindowStyle Hidden
# 8091 = Driver, 8090 = Rider

# build e instalar
$env:JAVA_HOME="C:\Program Files\Android\Android Studio\jbr"
cd ..\ANDOIRD\DRIVER\RECRIACAO
.\gradlew.bat assembleDebug --offline
adb -s AQCK024C17020494 install -r --no-streaming app\build\outputs\apk\debug\app-debug.apk

# o reverse cai com frequência — repor sempre
adb -s AQCK024C17020494 reverse tcp:8091 tcp:8091
adb -s AQCK024C17020494 reverse tcp:8090 tcp:8090

# captura (o redirecionamento directo do PowerShell corrompe o PNG)
cmd /c "adb -s AQCK024C17020494 exec-out screencap -p > C:\Users\Miglo\AppData\Local\Temp\opencode\foto.png"
```

### Script de simulação já pronto

`C:\Users\Miglo\AppData\Local\Temp\opencode\fases.ps1 <device>` — cria a viagem,
aceita, e captura as duas fases de navegação.

`C:\Users\Miglo\AppData\Local\Temp\opencode\card_only.py` — cria a viagem e
captura **só o cartão** (não aceita). Útil para a Fase 1.

---

## 5. Ficheiros-chave

| Ficheiro | O que contém |
|---|---|
| `.../ui/home/MapFragment.kt` | Ecrã principal: cartão, navegação, espera, chat |
| `.../ui/home/RealMapView.kt` | Mapa, traços, pinos, `reframe()`, balão da rua |
| `.../drive/DriveViewModel.kt` | Estados, `loadNavigation()`, `stopFor()` |
| `.../drive/Navigation.kt` | Manobra actual, formatação, `NavStop` |
| `res/layout/view_maneuver_panel.xml` | Painel preto de 2 secções |
| `res/layout/view_pickup_nav_bar.xml` | Barra "A recolher / A deixar" |
| `res/layout/view_offer_card.xml` | Cartão do pedido (Fase 1) |
| `BACKEND/apps/driver.py` | Contrato da Driver |
| `BACKEND/apps/osmgeo.py` | Limite de velocidade por OSM |
| `BACKEND/domain/trips.py` | Despacho, estados, liquidação |

---

## 6. Estado dos testes (antes de começar)

```
Backend ......... 89 passed
Driver .......... build + 74/74 testes
Portões MEGA .... 865 verificações, 0 falhas
Rider ........... build + 10/10 testes
```

Se algum destes números estiver diferente no início da sessão, **pára e
investiga** antes de escrever código.

---

## 7. Documentação de referência

| Ficheiro | Para quê |
|---|---|
| `features.md` | Inventário FASE 4.7 da Driver (86 features, F-ID) |
| `capabilities.md` | O que o clone faz de cada feature |
| `backlog.md` | Gaps abertos (14, todos de plataforma) |
| `tokens.md` | Cores, tipografia, espaços medidos |
| `peer_triggers.md` | Estados que dependem de outro ator |
| `plan.md` | Declaração inicial, tolerância |

**Nota:** o programa é o `PROMPT_CLONE_MEGA.md` **v4** (tem a FASE 4.7). Em
conflito, ganha o MEGA.

---

## 8. Primeiro passo concreto

1. Ler este prompt e o `PROMPT_PROXIMO_AGENTE.md`.
2. Confirmar que os testes estão verdes (ver §6).
3. Pedir ao cliente **o vídeo da Fase 2** (se ainda não estiver na pasta
   `ANDOIRD/DRIVER/ux_capture/video_*`).
4. Assistir ao vídeo e **listar ao cliente** as diferenças face ao que já existe.
5. Só depois escrever código — **um bloco de cada vez**, mostrando o resultado.

**Não começar a implementar sem o vídeo.** O cartão da Fase 1 ensinou que
trabalhar sem referência visual leva a três tentativas erradas seguidas.

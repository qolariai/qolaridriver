# Modo Destino (lupa do mapa) — implementação

**Pedido:** print de 2026-10-31 16:24 + duas decisões do cliente:
- **2 filtros por dia**
- **raio máximo de 7 km** à volta do local marcado

---

## O que foi feito

### Servidor (`BACKEND/`)

| Ficheiro | O quê |
|---|---|
| `domain/settings.py` | `destination_mode_radius_km = 7.0` e `destination_mode_daily_filters = 2` (editáveis na consola) |
| `domain/models.py` | 5 colunas no `Driver`: `dest_lat`, `dest_lng`, `dest_label`, `dest_used_today`, `dest_used_day` |
| `core/db.py` | migração `ADD COLUMN` para as 5 colunas novas |
| `domain/trips.py` | `set_destination()` (liga/desliga e conta filtros), `destination_filters_left()` (reinicia à meia-noite) e o filtro em `candidates()` |
| `apps/driver.py` | `POST /rt/drivers/v2/destination-mode` + `destinationMode` dentro de `driverState` |
| `console/api.py` | `POST /api/drivers/reset-destination-filters` (repor) e `/destination-mode-off` |

**A regra do filtro** (`candidates()`): depois do raio de despacho normal, se o motorista tem
destino marcado, a viagem só passa se **o destino da viagem** estiver a menos de 7 km do ponto
marcado. Viagens sem coordenadas de destino ficam de fora — não se pode provar que vão na direção.

### App (`RECRIACAO/`)

| Ficheiro | O quê |
|---|---|
| `ui/home/DestinationModeFragment.kt` | ecrã novo: pesquisa, interruptor, contador de filtros |
| `ui/home/PlacesClient.kt` | Places Autocomplete + Details (IPv4, como o `DirectionsClient`) |
| `res/layout/fragment_destination_mode.xml` | layout fiel ao print |
| `MapFragment.kt` | lupa → abre o ecrã; faixa "Modo Destino ligado: só viagens até 7 km de …" |
| `DriveViewModel.kt` / `DriveModels.kt` / `DriverRepository.kt` | estado `DestinationMode`, `setDestination()`, `destinationState()` |

---

## Provas

| Ficheiro (`modo_destino/`) | O que mostra |
|---|---|
| `01_ecra_2de2_filtros.png` | ecrã igual ao print: "Procurar locais", "Modo Destino", "2/2 filtros restantes" |
| `02_sugestoes_reais.png` | sugestões reais do Places para "Baixa": Baixa da Banheira, Baixa-Chiado, Baixa de Lisboa, Baixa Citadina |
| `03_ligado_no_mapa.png` | mapa com a faixa "Modo Destino ligado: só viagens até 7 km de Baixa da Banheira, Portugal" |
| `04_escolhido.png` | volta ao mapa depois de escolher |

**Teste fim-a-fim do filtro de 7 km** (destino marcado: Baixa-Chiado):

```
Cascais        (24,3 km)  ->  0 ofertas   ✔ bloqueada
Estoril        (17,0 km)  ->  0 ofertas   ✔ bloqueada
Av. Liberdade  ( 2,9 km)  ->  1 oferta    ✔ passa
```

**Limite diário:**

```
1.º filtro -> filtersLeft: 1
2.º filtro -> filtersLeft: 0
3.º filtro -> 400 no_filters_left   ✔
Desligar   -> não gasta filtro      ✔
```

---

## Verificação

```
Backend ......... 95 passed  (+3: tests/test_destination_mode.py)
App ............. 90/90      (+2: marcar destino gasta filtro / desligar não gasta)
```

---

## Dois problemas que apareceram e ficaram resolvidos

1. **Os testes do backend ficaram em 8 falhas** depois de eu acrescentar o módulo novo. Não era
   código partido: o meu teste deixava o Modo Destino **ligado na BD partilhada da sessão**, e os
   testes seguintes deixavam de receber viagens. Também enchia a fila do ramen com propostas que
   ninguém aceitava. O `fixture` agora desliga o modo em todos os motoristas, repõe quem está
   online, cancela as viagens pendentes e drena a fila.

2. **A pesquisa não mostrava nada.** O `PlacesClient` faz I/O bloqueante e estava a correr no main
   thread; a exceção era engolida e a lista ficava vazia. Passou a usar `Dispatchers.IO`.

---

## O que fica por decidir

- **`Casa` e o histórico** do print (Casa / Baixa-Chiado / Mem Martins com o lápis) **não** foram
  feitos: é preciso decidir onde se guardam os favoritos (conta? telemóvel?) e se o lápis edita a
  morada ou só o rótulo. Hoje o ecrã mostra só a pesquisa.
- **`Recomendado para si`** (lista sem viagem) continua por fazer.

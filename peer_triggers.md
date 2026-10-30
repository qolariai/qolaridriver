# peer_triggers.md — estados que dependem de outro ator

**FASE 2 / FASE 4.6** do `PROMPT_CLONE_MEGA.md`. Um `peer_trigger` é um estado que
a app **não consegue** mover sozinha: precisa de outro role, de um job ou do
sistema. Sem esta tabela, o BUILD implementa ecrãs que nunca saem do sítio.

**Regra:** cada linha tem um **ator** que move o estado e uma **prova** de que o
clone tem esse ator (`peer-bot`, job de relógio ou transição de backoffice).

---

## 1. Trigger → ator → prova

| # | F-ID | Estado que precisa de peer | Ator que move | Como o clone tem esse ator | Prova |
|---|---|---|---|---|---|
| P-01 | `F-trip-01` | `requested` → `accepted` | Driver (outra app) | despacho no backend + app Driver a aceitar | `test_espelhos` |
| P-02 | `F-trip-01` | `accepted` → `arrived` | Driver | `POST /rt/drivers/arrive` | `test_flow` |
| P-03 | `F-trip-01` | `arrived` → `in_progress` | Driver (PIN) | PIN gerado no backend, comparado na app | `DriveTest` |
| P-04 | `F-trip-01` | `in_progress` → `completed` | Driver | `POST /rt/drivers/end-trip` | `DriveTest` |
| P-05 | `F-trip-01` | `requested` → `no_drivers` | sistema (relógio) | `trip.tick()` a cada 1 s | `test_flow` |
| P-06 | `F-trip-01` | `offered` → `expired` | sistema (relógio) | `expire-offers` / `tick` | `DriveTest` |
| P-07 | `F-trip-01` | qualquer → `cancelled` | Rider **ou** Driver **ou** backoffice | três caminhos, todos auditados | `test_espelhos` |
| P-08 | `F-trip-01` | avaliação do motorista | Rider | `POST /rt/lite/trips/{uuid}/rate` | `ContractTest` |
| P-09 | `F-trip-01` | avaliação do passageiro | Driver | `driver-rate` | `DriveTest` |
| P-10 | `F-safety-01` | partilha de viagem ativa | sistema (`ACTION_SEND`) | `share-trip` + intent do sistema | `Lote5Test` |
| P-11 | `F-home-01` | oferta só chega se online | Driver + backend | `go-online` + despacho por proximidade | `HomeViewModelTest` |

---

## 2. F-ID sem peer (não precisam de tabela)

Tudo o que é navegação local, leitura ou toggle está fora desta tabela — não
espera por ninguém. Exemplos: menu, definições, documentos (leitura), ajuda,
legal, carteira (leitura).

---

## 3. O que o clone **não** tem

| Trigger | Porque não tem | Consequência |
|---|---|---|
| Push do sistema (FCM) a acordar a app | sem `FirebaseMessagingService` | `F-platform-01` `em falta`; o `ramen` cobre o tempo real |
| SMS real de verificação | laboratório usa `0000` | `F-auth-02` funciona mas não é o canal real |
| Peer humano real (outra pessoa a pedir) | laboratório usa conta de teste | `test_espelhos` simula o peer |

**Regra do MEGA §4.6.7:** um fluxo multi-app só fecha quando observado ponta a
ponta em **≥ 2 vistas**. O `test_espelhos` cobre U→D/F/B→U; o ciclo no telemóvel
cobre Rider + Driver em simultâneo.

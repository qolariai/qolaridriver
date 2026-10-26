# peer_triggers.md — Rider (estados que dependem de outro ator)

**Evidência:** pré-auth e escolha de viagem `live`/`clean` (32 PNG em `ux_capture/`);
pós-pedido `served` pelo backend do laboratório; contrato nativo `designed`. Não é
`live` do serviço original.

| Estado / campo | Trigger externo | Role que dispara | Endpoint / evento | Vistas que reagem |
|---|---|---|---|---|
| `requested` | passageiro pede | Rider | `POST /rt/lite/request` | Backoffice, dispatch |
| `requested` → `accepted` | motorista aceita | Driver | `accept-offers` → `trip_status` | Rider (motorista a caminho) |
| `accepted` → `arrived` | motorista chega | Driver | `arrive` → `trip_status` | Rider (“chegou”) |
| `arrived` → `in_progress` | PIN + início | Driver | `begin` → `trip_status` | Rider (“em viagem”) |
| `in_progress` → `completed` | motorista termina | Driver | `end` → `trip_status` | Rider (fim + avaliação) |
| `completed` → avaliação | passageiro avalia | Rider | `POST /rt/lite/trips/{uuid}/rate` | Driver (rating), Backoffice |
| `cancelled` | passageiro, motorista ou operação | Rider / Driver / Backoffice | `cancel` → `trip_status` | todos |
| `no_drivers` | timeout de procura | sistema (`trips.tick`) | `trip_status` | Rider (aviso + voltar) |
| `driver.location` | posição do motorista | Driver | `driver_location` | Rider (só viagem ativa) |
| `payment` / `wallet` | escolha do passageiro | Rider | `POST /rt/lite/payments/select` | Rider, Backoffice |

**Regra:** a app Rider nunca chama a Driver; lê o mesmo backend e reage a
`trip_status`. O desfecho recente (`completed`/`cancelled`/`no_drivers`) é devolvido por
`/rt/lite/active` durante 15 min para a avaliação não se perder ao reabrir a app.

# peer_triggers.md — Driver (estados que dependem de outro ator)

**Evidência:** transições observadas no laboratório (`served`) e confirmadas em
`BACKEND/tests/test_espelhos.py`; o protocolo do original não foi reproduzido. Não é
`live` do serviço original.

| Estado / campo | Trigger externo | Role que dispara | Endpoint / evento | Vistas que reagem |
|---|---|---|---|---|
| `requested` → oferta ao motorista | passageiro pede viagem | Rider | `POST /rt/riders/me/v2/pickup` → `push_driver_unified_offers_v3` | Driver (oferta), Backoffice |
| `requested` → `accepted` | motorista aceita | Driver | `POST /rt/drivers/accept-offers` | Rider, Fleet, Backoffice |
| `accepted` → `arrived` | motorista chega (slide ou 80 m) | Driver | `POST /rt/trips/v2/arrive` | Rider, Fleet, Backoffice |
| `arrived` → `in_progress` | PIN do passageiro + início | Driver | `POST /rt/trips/v2/begin` | Rider, Fleet, Backoffice |
| `in_progress` → `completed` | motorista termina | Driver | `POST /rt/trips/v2/end` + liquidação | Rider, Driver, Fleet, Backoffice |
| `completed` → avaliação | passageiro avalia | Rider | `POST /rt/lite/trips/{uuid}/rate` | Driver (rating), Backoffice |
| `completed` → avaliação | motorista avalia | Driver | `POST /rt/trips/v2/driver-rate` | Rider (rating), Backoffice |
| `cancelled` | passageiro, motorista ou operação | Rider / Driver / Backoffice | `rider-cancel` · `driver-cancel` · `POST /api/trips/{key}/action` | todos |
| `no_drivers` | timeout de procura | sistema (`trips.tick`) | `trip_status` | Rider, Backoffice |
| `driver.online` | motorista fica online/offline | Driver | `v2/go-online` · `v2/go-offline` | Fleet, dispatch, Backoffice |
| `driver.documents.status` | aprovação/recusa | Backoffice (`operator`) | `PATCH /api/documents/{id}` | Driver, Fleet |
| `payout.status` | fecho/liquidação | Backoffice (`finance`) / job | `/api/payouts` | Driver, Fleet, Backoffice |

**Fluxos gated:** a oferta só chega com o motorista online e dentro do raio; a viagem
só avança com o passageiro (PIN) e com o motorista (chegada/início/fim). Quando só há
uma app disponível, o peer é simulado pela consola — sempre declarado como `served`,
nunca como observação do serviço original.

**Peer-bot:** `BACKEND/tests/test_espelhos.py` faz o papel dos três atores
(Rider/Driver/Fleet/Backoffice) e valida a propagação. Ver `topology.md` §8.

# Honor — evidência da Rider (2026-10-27)

Dispositivo `PTP-N49` (`AQCK024C17020494`), backend local por `adb reverse`
(8090). Pacote `com.qolari.userlite` (0.1.0, 10 testes).

| Ficheiro | Momento |
|---|---|
| `01_welcome` … `05_home` | boas-vindas, telefone, código `0000`, início |
| `06_menu` … `11_account_saved_data` | menu, gerir conta, casa, dados pessoais |
| `12_home_updated` … `14_location_ok` | início com casa nova, permissão e GPS |
| `15_search` … `18_searching` | pesquisa, Rossio, categorias, pedido |
| `19_trip_completed` … `23_rating_sent` | fim da viagem, tarifa, avaliação enviada |
| `24_search_pickup` … `25_search_pickup_ok` | pickup passa a usar a casa atual |
| `26_unrated` … `27_after_skip` | reabrir avaliação e “Agora não” (rating 0) |
| `28_offline` … `29_online_again` | banner “Sem conexão de rede” e regresso |

**Correções confirmadas aqui:** mapa Google real; GPS; casa editável; pickup
com a casa atual; avaliação (Retrofit `RateRequest`); “Agora não” fecha a
avaliação sem contar para a média. As capturas são da app nova (`newapp`),
nunca spec.

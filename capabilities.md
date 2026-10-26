# capabilities.md — matriz de capacidades (FASE 7)

**Alvo:** `funcional` (declarado em `plan.md`). **Regra:** uma entrada só é `ok`
quando tem efeito real (navegação, estado local, endpoint) e teste ou verificação
no telemóvel; caso contrário é `gap` e não pode ficar na UI.

**Âmbito do clone:** Driver + Rider + backend + backoffice. A Fleet é operação
(contrato + backend), não recriação visual — ver “Exclusões declaradas”.

## 1. Driver — ações visíveis

| Ecrã | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Boas-vindas | começar / entrar | `POST /rt/identity/oauth2/token` | `LoginViewModelTest` | ok |
| Login | telefone + código `0000` | token + sessão DataStore | `LoginViewModelTest` | ok |
| Início | carregar, refresh, retry | `POST /rt/riders/me/app-launch` + `/rt/drivers/*` | `HomeViewModelTest` | ok |
| Início | ficar online/offline | `v2/go-online` / `v2/go-offline` | `HomeViewModelTest`, fluxo no telemóvel | ok |
| Início | abrir menu, notificações, perfil | navegação + `get-profile-hub` | `Lote3Test`, telemóvel | ok |
| Início | mapa real, pesquisa, zoom, recentrar | Google Maps SDK + `/rt/support/map-report` | telemóvel (V-01) | ok |
| Mapa | pesquisa de locais, atalhos (relâmpago, reportar, tendências, localizar), preferências, segurança | Google Maps + sheets + navegação | telemóvel (V-01) | ok |
| Descobrir | filtros, dias, cartões | estado local | `Lote3Test` | ok |
| Rendimentos | dia/semana, gráfico, erro | `/rt/earnings/*` | `Lote3Test` | ok |
| Caixa de entrada | listar, marcar lida | `/rt/inbox/*` | `Lote3Test` | ok |
| Menu | Ajuda, Segurança, Definições | navegação | telemóvel | ok |
| Menu | veículos, documentos, seguro, impostos, pagamentos, sobre | `vehicles`/`documents`/páginas próprias | `Lote5Test` | ok |
| Menu | descobrir, Pro, hub, recomendações | navegação/`infoFragment` | build + revisão | ok |
| Menu | mudar de conta / terminar sessão | `signOut()` + boas-vindas | `Lote1Test` | ok |
| Definições | acessibilidade, audição, comunicação, push, navegação, sons, sobre, privacidade, gerir conta | estado local + páginas próprias + Menu | `Lote1Test`, telemóvel (V-01) | ok |
| Ajuda | categorias → página de conteúdo próprio | `InfoFragment` + strings próprias | telemóvel (V-01) | ok |
| Veículos | abrir, gerir, sem rede | `/rt/drivers/v2/vehicles` | `Lote5Test` | ok |
| Documentos | lista, estado, detalhe, upload e verificação de identidade | `/rt/drivers/v2/documents`, `.../upload`, `.../verify-identity` | `test_documents_upload`, `Lote5Test` | ok |
| Segurança | contactos, SOS, 112, partilha da viagem | `/rt/safety/*`, `/share/{token}` | `test_safety`, `Lote5Test` | ok |
| Preferências de condução | modo destino, área, auto-aceitação, pausa | `/rt/drivers/v2/preferences`, `.../break` | `test_driver_preferences` | ok |
| Rendimentos | transferir (IBAN/Instant Pay), histórico, extratos | `/rt/earnings/*payout*`, `.../statements` | `test_payouts` | ok |
| Rendimentos | recibo detalhado da viagem | `/rt/earnings/get-trip` | `test_payouts`, `DriveTest` | ok |
| Apoio | conversa com a operação | `/rt/support/threads` | `test_support_chat` | ok |
| Apoio | anexos, chamada e bug report | `/rt/support/threads`, `.../messages` | `test_support_chat` | ok |
| Segurança | ride check | `/rt/safety/ride-check` | `test_safety` | ok |
| Fila do aeroporto | entrar, sair, posição | `/rt/drivers/v2/airport-queue` | `test_airport_queue` | ok |
| Incentivos | missões, pontos/Pro, referral | `/rt/drivers/v2/incentives`, `.../referrals` | `test_incentives` | ok |
| Ajustes | portagens/tarifa manual, faturas, impostos | `/rt/earnings/*adjustment*`, `.../invoices`, `.../tax-info` | `test_adjustments` | ok |
| Empresa | perfil empresarial e delegados | `/rt/drivers/v2/business-profile` | `test_business_profile` | ok |
| Viagem | navegação externa Google Maps/Waze | `Intent` `google.navigation`/`waze://` | build + lint | ok |
| Viagem | paragens até 3, concluídas pelo motorista | `/rt/trips/v2/complete-stop` | `test_stops` | ok |
| Viagem | gravação de áudio | `/rt/safety/recording/*` | `test_audio_recording_start_stop` | ok |
| Viagem | gravação de vídeo do ecrã | `/rt/safety/recording/*` | `test_video_recording_start_stop` | ok |
| Apoio | partilha do ecrã completo | `/rt/support/threads/{uuid}/screen-share/*` | `test_screen_share_roundtrip` | ok |
| Aparência | idioma, modo escuro, modo simples | `UiPrefs` + `AppearanceFragment` | build/lint | parcial |
| Oferta | aceitar, recusar, expirar | `accept-offers` / `reject-offers` / `expire-offers` | `DriveTest` | ok |
| Viagem | recolher, chegar, PIN, iniciar, terminar | `/rt/trips/v2/*` | `DriveTest` | ok |
| Viagem | cancelar, erro/retry | `driver-cancel` + retry | `DriveTest` | ok |
| Fim | ganhos da viagem, resumo, avaliação | `/rt/earnings/*`, `driver-rate` | `DriveTest`, telemóvel (V-01) | ok |
| Global | banner offline, back, estados vazios | `NetworkMonitor` + Navigation | telemóvel | ok |

## 2. Rider — ações visíveis

| Ecrã | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Boas-vindas | começar | navegação | build | ok |
| Login | país, telefone, “encontrar conta”, seguinte | validação + `POST /rt/lite/...` token | `ContractTest` | ok |
| Login | usar código do laboratório | preenche `0000` no campo | build | ok |
| Início | carregar, refresh, retry | `GET /rt/lite/home` | backend `test_userlite` | ok |
| Início | mapa real, rota, zoom, localização | Google Maps SDK + `/rt/lite/route` | telemóvel (V-01) | ok |
| Início | pesquisa, sugestão, promoção | navegação para procura/promoções | build | ok |
| Início | localização | permissão + `LocationManager` + `POST /rt/lite/location` | `MapCameraTest`, telemóvel | ok |
| Início | zoom in/out | `MapCamera` (1.0–2.2, passos 1.25) | `MapCameraTest` | ok |
| Pesquisa | procurar, escolher destino | `GET /rt/lite/places` | backend `test_userlite` | ok |
| Pesquisa | usar casa guardada | `GET /rt/lite/home` + `savedPlace` | backend `test_userlite` | ok |
| Pesquisa | vazio, erro, teclado | estados + foco | build | ok |
| Escolher viagem | preços, categorias, retry | `POST /rt/lite/quote` | backend `test_userlite` | ok |
| Escolher viagem | forma de pagamento | `POST /rt/lite/payments/select` | backend `test_userlite` | ok |
| Escolher viagem | pedir | `POST /rt/lite/request` | backend `test_userlite` | ok |
| Escolher viagem | agendar data/hora | `POST /rt/lite/request` com `scheduledAt` | `test_scheduling` | ok |
| Viagem ativa | polling de estado, PIN, motorista | `GET /rt/lite/active` a 2 s | backend + telemóvel | ok |
| Viagem ativa | cancelar | `POST /rt/lite/trips/{uuid}/cancel` | backend `test_userlite` | ok |
| Viagem ativa | avaliar, saltar, voltar ao início | `POST /rt/lite/trips/{uuid}/rate` | `ContractTest`, telemóvel (V-01) | ok |
| Menu | carteira, atividade, ajuda, promoções, legal, conta | navegação | build | ok |
| Menu | Apoio e Segurança | `/rt/support/threads`, `/rt/safety/*` | `test_support_chat`, `test_safety` | ok |
| Segurança | contactos, SOS, 112, partilha | `/rt/safety/*`, `/share/{token}` | `test_safety` | ok |
| Segurança | ride check | `/rt/safety/ride-check` | `test_safety` | ok |
| Dinheiro | gorjeta, recibo, disputa, top-up | `/rt/lite/trips/{uuid}/tip|receipt|dispute`, `/rt/lite/wallet/topup` | `test_rider_money` | ok |
| Conta | locais guardados | `/rt/lite/places/saved` | `test_saved_places` | ok |
| Conta | empresa, família/teens, Uber One | `/rt/lite/account/*` | `test_account_extras` | ok |
| Viagem | paragens até 3 e estado por paragem | `stops` no pedido e em `trip_json` | `test_stops` | ok |
| Offline | fila do pedido com reenvio | `PendingTripStore` + `HomeFragment` | build + revisão | ok |
| Apoio | partilha do ecrã completo | `/rt/support/threads/{uuid}/screen-share/*` | `test_screen_share_roundtrip` | ok |
| Aparência | idioma, modo escuro, modo simples | `UiPrefs` + `AppearanceFragment` | build/lint | parcial |
| Menu | terminar sessão | `signOut()` + confirmação | build | ok |
| Carteira | listar, escolher pagamento | `GET /rt/lite/wallet`, `payments/select` | backend | ok |
| Atividade | histórico, vazio com ação | `GET /rt/lite/history` | backend | ok |
| Ajuda | pesquisa e artigos | conteúdo próprio | build | ok |
| Legal | tópicos e detalhe | conteúdo próprio | build | ok |
| Promoções | aplicar código, ver preços | `GET/POST /rt/lite/promotions*` | backend | ok |
| Conta | escolher/guardar casa | `POST /rt/lite/account/home` | backend `test_userlite` | ok |
| Conta | editar nome/e-mail | `PATCH /rt/lite/account` | backend `test_userlite` | ok |
| Conta | segurança + terminar sessão | `signOut()` | build | ok |
| Conta | privacidade, verificação | `InfoFragment` (conteúdo próprio) | build | ok |
| Global | banner offline, back, estados | `NetworkMonitor` + Navigation | build | ok |

## 3. Backoffice (`designed`)

| Área | Ação | Endpoint / estado | Teste | Status |
|---|---|---|---|---|
| Login/RBAC | entrar como admin/operator/finance | `/api/auth/login`, papéis | pytest consola | ok |
| Painel | mapa, indicadores, top motoristas | `/api/*` | pytest consola | ok |
| Viagens | filtrar, abrir ficha, cancelar/forçar/propor | `/api/trips/{key}/action` | `test_espelhos` | ok |
| Simulador | pedir, online/offline, mover, avançar | mesmas transições | `test_espelhos` | ok |
| Motoristas/Passageiros/Frotas/Veículos | fichas, aprovar, suspender | `/api/drivers`, `/api/riders`, … | pytest consola | ok |
| Documentos | fila, aprovar/recusar | `PATCH /api/documents/{id}` | pytest consola | ok |
| Finanças | saldos, pagamentos, acertos | `/api/payouts` | pytest consola | ok |
| Categorias/Promoções/Definições | tarifas, códigos, parâmetros, admins | `/api/settings`, `/api/products`, `/api/promos` | pytest consola | ok |
| Integração | tráfego, endpoints por mapear | `/api/integration` | revisão | ok |
| Problemas de mapa | listar, resolver, reabrir, ignorar | `/api/map-reports` | pytest consola | ok |
| Suporte | listar conversas, responder, fechar | `/api/support*` | `test_support_chat` | ok |
| Segurança | listar SOS, ver contactos, fechar | `/api/safety*` | `test_safety` | ok |
| Ajustes | aprovar/recusar portagens e tarifa manual | `/api/adjustments*` | `test_adjustments` | ok |
| Gravações | ouvir áudio da viagem | `/api/recordings*` | `test_audio_recording_start_stop` | ok |
| Ecrã | ver o ecrã partilhado no chat | `/api/support/*/screen-share` | `test_screen_share_roundtrip` | ok |

## 4. Backend e orquestração

| Capacidade | Endpoint / evento | Teste | Status |
|---|---|---|---|
| Login e sessões (3 apps) | `/rt/identity/oauth2/token`, `/rt/lite/session` | `test_userlite`, `test_flow` | ok |
| Viagens: um escritor | `domain/trips.py` | `test_flow`, `test_espelhos` | ok |
| Despacho, expiração, no_drivers | `trip.tick`, `Offers` | `test_flow` | ok |
| Liquidação e saldos | `domain/finance.py` | `test_flow` | ok |
| Tempo real | `ramen` + `/api/changes` | `test_espelhos` | ok |
| Três espelhos U→D/F/B→U | eventos `trip_status`, `driver_trip` | `test_espelhos` | ok |
| Conta Rider (casa, dados) | `PATCH /rt/lite/account`, `POST /rt/lite/account/home` | `test_userlite` | ok |
| Backoffice auditado | `audit()` em todas as ações | pytest consola | ok |
| Suporte, segurança e documentos | threads, SOS, upload e revisão | `test_support_chat`, `test_safety`, `test_documents_upload` | ok |
| Preferências de despacho | destino, área, auto-aceitação, pausa | `test_driver_preferences` | ok |
| Pagamentos e extratos | IBAN, Instant Pay, histórico, 6 meses | `test_payouts` | ok |
| Agendamento | `scheduledAt` no pedido; despacho só à hora | `test_scheduling` | ok |
| Gorjeta e recibo | tip, linhas e total no recibo | `test_rider_money` | ok |
| Fila de aeroporto | posição por ordem de entrada | `test_airport_queue` | ok |
| Incentivos | missões, pontos, referral | `test_incentives` | ok |
| Ajustes | portagens/tarifa manual com aprovação | `test_adjustments` | ok |
| Locais guardados e conta | CRUD e empresa/família/Uber One | `test_saved_places`, `test_account_extras`, `test_business_profile` | ok |
| Paragens | conclusão por paragem no motorista | `test_stops` | ok |
| Gravação de áudio | início/fim e ficheiro | `test_audio_recording_start_stop` | ok |
| Gravação de vídeo | MP4 do ecrã | `test_video_recording_start_stop` | ok |
| Partilha de ecrã | frames do ecrã completo para o apoio | `test_screen_share_roundtrip` | ok |
| Push FCM | token do dispositivo + envio FCM | `/rt/devices/push-token`, `apps/fcm.py` | pytest + Honor | ok |

## 5. Exclusões declaradas (não são botões mortos)

| Item | Porque | Equivalente / decisão |
|---|---|---|
| UI própria da Fleet | não há captura; a app do laboratório é instrumento | contrato + operação no backend e backoffice; paridade visual não prometida |
| Entrega/courier, reserva, paragens, cidade, filtro pessoal | fora da vertical ride-hailing do âmbito | entradas removidas da UI |
| Comfort, vídeo de boas-vindas/câmara, login por e-mail, adicionar veículo, editar endereço | dependem de SDK/serviços/legal ou são requisito de `produção` | entradas ausentes; sem placeholder |
| Miniaturas de mapa nos cartões | ilustração decorativa, não interativa | mapa real só nos ecrãs principais; miniaturas desenhadas |
| iOS | fora do âmbito | IPAs ficam como laboratório |
| Login social / reCAPTCHA / IAP | decisão do laboratório | login nativo por telefone; sem botões |

## 6. Resumo

| App | Ações `ok` | `gap` | Nota |
|---|---|---|---|
| Driver | 31 grupos de ecrã | 0 | 74 testes de app + 93 de backend; validada no Honor (V-01) |
| Rider | 34 grupos de ecrã | 0 | 11 testes; validada no Honor (V-01) |
| Backoffice | 14 áreas | 0 | RBAC + auditoria + suporte + segurança + ajustes |
| Backend | 22 capacidades | 0 | 93 testes |

**Zero `gap` para o alvo `funcional` no âmbito Driver+Rider+backoffice.** As
exclusões acima são tolerância escrita, não funcionalidade em falta na UI.

**Ronda de 26/10:** entraram suporte (Driver/Rider/consola), segurança (contactos,
SOS, 112 e partilha pública), upload/verificação de documentos, preferências de
condução (destino/área/auto-aceitação/pausa), transferências/extratos/recibo e
agendamento no Rider. Provas: `test_support_chat`, `test_safety`,
`test_documents_upload`, `test_driver_preferences`, `test_payouts`,
`test_scheduling`; backend com **81 testes**.

**Segunda ronda de 26/10:** gorjeta/recibo/top-up/disputa, ride check, anexos e
chamada no apoio, fila de aeroporto, missões/pontos/referral, ajustes/faturas/
impostos, locais guardados, empresa/família/Uber One, perfil empresarial e
aparência/idioma. Backend com **89 testes**.

As falhas encontradas na validação final foram corrigidas e cobertas por teste:
`R-12` (Rider: `@Body` do `rate` era `Map<String, ?>`, rejeitado pelo Retrofit), `R-13`
(Rider: ao reabrir depois do fim ia para o início e perdia a avaliação), `R-14` (Rider:
a rota do mapa era uma linha reta; passou a `/rt/lite/route` com OSRM), `D-03` (Driver:
a folha de avaliação voltava a abrir depois de enviar), `D-04` (Driver: categorias da
Ajuda e linhas das Definições sem efeito), `D-05` (Driver: botões do mapa e atalhos sem
handler) e `D-06` (Driver: o separador Página inicial não navegava). Ver `backlog.md` e
`VALIDACAO_MEGA.md` §4.

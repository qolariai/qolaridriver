# ENDPOINTS.md — contrato de rede da Driver 4.600.10000

Gerado por `spec_tools/endpoints_report.py` a partir de `endpoints.json`. **Não editar à mão.**

Contrato documentado entre a UI e o backend proprio (spec FASE 1/4). Hosts e paths sao identificadores extraidos do original; nao sao para a app nova chamar.

## Resumo

- **Hosts:** 129. rebuild 14, substituir 55, descartar 60. Sem classificação: 0.
- **Endpoints:** 1104. rebuild 1001, substituir 96, descartar 7.
- **Prioridade dos `rebuild`:** essencial 103, secundário 587, por avaliar 219, fora de âmbito 92.
- **Já implementados no backend do laboratório:** 99. Com chamadas no tráfego registado: 26.
- **Por verbo:** POST 915, GET 138, ? 28, PUT 10, DELETE 8, PATCH 3, gRPC 2.
- **Por origem:** retrofit: 1074; string literal (sem anotacao Retrofit): 18; trafego registado no nosso backend (app renomeada): 11; gRPC (MethodDescriptor no smali): 1.
- **Resposta com DTO já mapeado em `BACKEND/contracts`:** 59 de 1074.

**Classes:** `rebuild` (o nosso backend implementa), `substituir` (equivalente próprio), `descartar` (não se reconstrói).
**Prioridade:** essencial = já implementado ou chamado no tráfego; secundário = ligado a um ecrã capturado pelo nome; por avaliar = sem ecrã identificado; fora de âmbito = produto que a Driver capturada não usa.

## Hosts

| Host | Classe | Papel | Motivo |
|---|---|---|---|
| `10.0.2.2` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `alphacephei.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `aomedia.org` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `aomediacodec.github.io` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `app-measurement.com` | descartar | telemetria/atribuicao | analitica, atribuicao ou ads de terceiros |
| `cn-staging.uber.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `code.uberinternal.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `constraintlayout.github.io` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `default.url` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `devbuilds.uber.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `developer.apple.com` | descartar | nao e rede da app | namespace, loja ou documentacao |
| `drive.google.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `earn.sng.link` | descartar | telemetria/atribuicao | analitica, atribuicao ou ads de terceiros |
| `earner-online-staging.uber.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `eats.uber.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `embedded.ifood.com.br` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `eventgw.twilio.com` | descartar | telemetria | gateway de eventos |
| `examp.le` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `facebook.com` | descartar | terceiro: facebook | SDK do Facebook sem funcao nos ecras capturados |
| `github.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `google.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `graph.facebook.com` | descartar | terceiro: facebook | SDK do Facebook sem funcao nos ecras capturados |
| `help.riamoneytransfer.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `hmns.kr` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `ingen.uber.com` | descartar | funcao desconhecida | sem uso observado nas capturas nem no trafego; rever se aparecer em uso |
| `integrations-staging.uber.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `localhost` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `loggi-uber.zendesk.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `merchant.uber.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `merchants-beta.ubereats.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `merchants.ubereats.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `ns.adobe.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `optimistic` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `pagead2.googlesyndication.com` | descartar | ads | publicidade |
| `picsum.photos` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `play.google.com` | descartar | nao e rede da app | namespace, loja ou documentacao |
| `presidio-webview-playground.uber.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `rent-webview.uber.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `s2s.singular.net` | descartar | atribuicao | atribuicao de marketing |
| `schemas.android.com` | descartar | nao e rede da app | namespace, loja ou documentacao |
| `schemas.microsoft.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `supplier.uber.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `support.google.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `tc2.uber.com` | descartar | funcao desconhecida | sem uso observado nas capturas nem no trafego; rever se aparecer em uso |
| `testpurchaseurl.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `ubereats.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `venmo.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `wisdom.uberinternal.com` | descartar | ambiente interno da Uber | staging/dev/ferramentas internas |
| `www.example.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `www.facebook.com` | descartar | terceiro: facebook | SDK do Facebook sem funcao nos ecras capturados |
| `www.google.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `www.googleadservices.com` | descartar | ads | publicidade |
| `www.grab.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `www.irs.gov` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `www.nauto.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `www.placebear.com` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `www.tesla.com` | descartar | ligacao externa | link de parceiro ou de outro mercado, nao usado em PT |
| `www.ubereats.com` | descartar | fora de ambito | produto ou mercado nao usado pela Driver capturada |
| `www.w3.org` | descartar | nao e rede da app | namespace, loja ou documentacao |
| `youtu.be` | descartar | nao e rede da app | documentacao, namespace, exemplo ou teste |
| `auth.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.geixahba.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.naevooda.co` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.oojoovae.org` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.ooshahwa.biz` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.shaipeeg.net` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-dc1.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn-geo1.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `cn.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `earner-online-critical.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `earner-online.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `login.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `platform.uberinternal.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `pusher.uber.com` | rebuild | API da app | edge/API chamado pelos ecras; o nosso backend responde |
| `account.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `accounts.google.com` | substituir | login Google | login social proprio, se mantido |
| `accounts.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `api-m.paypal.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `api.braintreegateway.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `api.sandbox.braintreegateway.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `b.stats.paypal.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `bonjour.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `c.paypal.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `c.sandbox.paypal.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `cards.uber.com` | substituir | pagamentos | fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota |
| `chat-support.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `d183q68ssszldn.cloudfront.net` | substituir | media/CDN | assets proprios |
| `d1goeicueq33a8.cloudfront.net` | substituir | media/CDN | assets proprios |
| `d3ktknrqa34sgg.cloudfront.net` | substituir | media/CDN | assets proprios |
| `d4p17acsd5wyj.cloudfront.net` | substituir | media/CDN | assets proprios |
| `driverinjuryprotection.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `drivers.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `earner-recording-settings.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `ers.twilio.com` | substituir | voz/chat | VoIP/chat proprio entre motorista e passageiro |
| `ewp.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `finprod.uber.com` | substituir | pagamentos | fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota |
| `firebaseinstallations.googleapis.com` | substituir | push (FCM) | projeto Firebase proprio |
| `firebaseremoteconfig.googleapis.com` | substituir | config remota (Firebase) | projeto Firebase proprio ou config do nosso backend |
| `firebaseremoteconfigrealtime.googleapis.com` | substituir | config remota (Firebase) | projeto Firebase proprio ou config do nosso backend |
| `frontier-ivr.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `helix-go-webview.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `help.uber.com` | substituir | paginas web (ajuda/legal) | paginas proprias |
| `img.pngio.com` | substituir | media/CDN | assets proprios |
| `incentives.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `learn.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `m.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `mobile-content.uber.com` | substituir | media/CDN | assets proprios |
| `myprivacy.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `partners.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `pay.hyperwallet.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `payment-providers.uber.com` | substituir | pagamentos | fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota |
| `payment.uber.com` | substituir | pagamentos | fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota |
| `payments.uber.com` | substituir | pagamentos | fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota |
| `privacy.uber.com` | substituir | paginas web (ajuda/legal) | paginas proprias |
| `redeem.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `rewards.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `s3.amazonaws.com` | substituir | media/CDN | assets proprios |
| `static-maps.uber.com` | substituir | mapas | Google Maps SDK com chave propria |
| `survey.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `t.uber.com` | substituir | paginas web (ajuda/legal) | paginas proprias |
| `tb-static.uber.com` | substituir | media/CDN | assets proprios |
| `uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `ubr.to` | substituir | links curtos | links proprios |
| `ui.uber.com` | substituir | media/CDN | assets proprios |
| `vehicles.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |
| `www.googleapis.com` | substituir | APIs Google (login/mapas) | chaves e projeto proprios |
| `www.paypal.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `www.paypalobjects.com` | substituir | pagamentos | fornecedor de pagamento proprio, se necessario |
| `www.uber.com` | substituir | pagina web dentro da app (webview) | pagina propria equivalente |

Falsos positivos da extração (não são hosts): 5.

## Endpoints essenciais (o mínimo para os ecrãs capturados)

| Verbo | Path | Ecrãs | Handler no backend |
|---|---|---|---|
| ? | `/api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParameters` | arranque (todas as sessoes) | — |
| ? | `/api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParametersUnauthenticated` | login/arranque (031-033); arranque (todas as sessoes) | — |
| ? | `/api/grpc/uberdevices.upsert-user-device/UpsertUserDevice` | arranque (todas as sessoes) | identity.grpc_upsert_user_device |
| GET | `/ramen/sessions/{sessionId}/messages` | login/arranque (031-033); caixa de entrada (012, 063); canal em tempo real (todas) | common.ramen_messages |
| POST | `/rt/communications/device-token/create` | login/arranque (031-033); arranque (todas as sessoes); definicoes (043-052) | identity.push_token |
| POST | `/rt/devices/exemption` | arranque (todas as sessoes) | identity.device_exemption |
| POST | `/rt/devices/task` | arranque (todas as sessoes); viagem (nao capturado) | identity.device_task |
| POST | `/rt/devices/upsert` | arranque (todas as sessoes) | identity.device_upsert |
| POST | `/rt/devices/upsert-v2` | arranque (todas as sessoes) | identity.device_upsert |
| POST | `/rt/drivers/accept-offers` | oferta (100_online) | driver.accept |
| POST | `/rt/drivers/ack-offers` | oferta (100_online) | driver.tasks |
| POST | `/rt/drivers/app-launch` | arranque (todas as sessoes) | driver.app_launch |
| GET | `/rt/drivers/driving-hour-limits-clock-v2` | inicio: mapa/estado online (110, 100_online) | driver.empty_lists |
| POST | `/rt/drivers/end-trip` | viagem (nao capturado) | driver.end |
| POST | `/rt/drivers/expire-offers` | oferta (100_online) | driver.reject |
| POST | `/rt/drivers/finalize-offers` | oferta (100_online) | driver.tasks |
| POST | `/rt/drivers/get-checklist-sdui` | inicio: acoes necessarias (035) | driver.checklist_sdui |
| GET | `/rt/drivers/get-driver-feed-push` | caixa de entrada (012, 063); canal em tempo real (todas) | driver.empty_lists |
| GET | `/rt/drivers/get-opportunities` | descobrir (010, 036, 061, 080-081); inicio: oportunidades (060) | driver.empty_lists |
| POST | `/rt/drivers/get-upfront-offer` | oferta (100_online) | driver.get_offer |
| POST | `/rt/drivers/learning/fetch-mobile-alerts` | hub de informacoes/comfort (025-030) | driver.fetch_mobile_alerts |
| ? | `/rt/drivers/me/status` | inicio: mapa/estado online (110, 100_online) | — |
| POST | `/rt/drivers/reject-offers` | oferta (100_online) | driver.reject |
| POST | `/rt/drivers/send-wait-timer-alert` | viagem (nao capturado) | driver.arrived |
| GET | `/rt/drivers/unified-offers-v3` | oferta (100_online) | driver.unified_offers_poll |
| GET | `/rt/drivers/update-driver-feed` | caixa de entrada (012, 063); canal em tempo real (todas) | driver.tasks |
| POST | `/rt/drivers/v2/available` | inicio: mapa/estado online (110, 100_online) | driver.tasks |
| POST | `/rt/drivers/v2/capabilities` | arranque (todas as sessoes) | driver.tasks |
| POST | `/rt/drivers/v2/fetch-online-blockers` | inicio: mapa/estado online (110, 100_online) | driver.online_blockers |
| POST | `/rt/drivers/v2/go-offline` | inicio: mapa/estado online (110, 100_online) | driver.go_offline |
| POST | `/rt/drivers/v2/go-online` | inicio: mapa/estado online (110, 100_online) | driver.go_online |
| POST | `/rt/drivers/v2/pin-accept` | oferta (100_online); viagem (nao capturado) | driver.accept |
| POST | `/rt/drivers/v2/preferences` | definicoes (043-052) | driver.preferences |
| ? | `/rt/drivers/v2/unified-offer` | oferta (100_online) | driver.unified_offers_poll |
| GET | `/rt/drivers/v2/vehicles` | veiculos (070, 080-082) | driver.vehicles |
| POST | `/rt/drivers/{driverUUID}/go-online` | inicio: mapa/estado online (110, 100_online) | driver.go_online |
| GET | `/rt/drivers/{driverUUID}/v2/preferences` | definicoes (043-052) | driver.driver_preferences |
| POST | `/rt/earner-profile/get-profile-detail-screen` | menu/perfil (013, 041, 064); mapa e navegacao (110) | driver.profile_hub |
| POST | `/rt/earner-profile/get-profile-hub` | menu/perfil (013, 041, 064); descobrir (010, 036, 061, 080-081); inicio: oportunidades (060) | driver.profile_hub |
| GET | `/rt/earner/heatmapV2` | descobrir (010, 036, 061, 080-081); inicio: oportunidades (060); mapa e navegacao (110) | driver.empty_lists |
| POST | `/rt/earner/preferences` | definicoes (043-052) | driver.preferences |
| GET | `/rt/earner/preferences/views` | definicoes (043-052) | driver.preferences |
| GET | `/rt/earner/zonesmap` | mapa e navegacao (110) | driver.empty_lists |
| POST | `/rt/earnings/get-activity-feed-v3` | rendimentos (011, 062); informacoes fiscais (074); caixa de entrada (012, 063); canal em tempo real (todas) | driver.activity |
| GET | `/rt/earnings/get-balance-summary` | rendimentos (011, 062); informacoes fiscais (074) | driver.balance |
| GET | `/rt/earnings/get-daily-earnings-view` | rendimentos (011, 062); informacoes fiscais (074) | driver.daily |
| GET | `/rt/earnings/get-performance-hub-view` | rendimentos (011, 062); informacoes fiscais (074); descobrir (010, 036, 061, 080-081); inicio: oportunidades (060) | driver.weekly |
| GET | `/rt/earnings/get-trip` | viagem (nao capturado); rendimentos (011, 062); informacoes fiscais (074) | driver.earnings_trip |
| GET | `/rt/earnings/get-weekly-earnings-view` | rendimentos (011, 062); informacoes fiscais (074) | driver.weekly |
| POST | `/rt/earnings/session-feedback-loop/validate-session-readiness` | inicio: mapa/estado online (110, 100_online); login/arranque (031-033); rendimentos (011, 062); informacoes fiscais (074); caixa de entrada (012, 063); canal em tempo real (todas) | driver.validate_session_readiness |
| GET | `/rt/earnings/v3/trip/{tripUUID}` | viagem (nao capturado); rendimentos (011, 062); informacoes fiscais (074) | driver.earnings_trip |
| POST | `/rt/glide/get-earner-dashboard-sections-content` | inicio: painel (060, 120) | driver.earner_dashboard_sections |
| ? | `/rt/health` | arranque (todas as sessoes) | driver.rt_health |
| POST | `/rt/identity/auth/issue-web-auth-cookies` | login/arranque (031-033); ajuda (042, 065, 090-091) | identity.web_cookies |
| POST | `/rt/identity/oauth2/add-sso-id` | login/arranque (031-033) | identity.add_sso_id |
| POST | `/rt/identity/oauth2/get-apps-not-in-device-session-group` | login/arranque (031-033); arranque (todas as sessoes) | identity.apps_not_in_device_session_group |
| POST | `/rt/identity/oauth2/invalidate-token` | login/arranque (031-033) | identity.revoke |
| POST | `/rt/identity/oauth2/revokesession` | login/arranque (031-033) | identity.revoke |
| POST | `/rt/identity/oauth2/sso-exchange-token` | login/arranque (031-033) | identity.oauth_token |
| POST | `/rt/identity/oauth2/token` | login/arranque (031-033) | identity.oauth_token |
| POST | `/rt/identity/oauth2/user-id-token` | login/arranque (031-033) | identity.user_id_token |
| POST | `/rt/inbox/unread-config` | caixa de entrada (012, 063); canal em tempo real (todas) | common.inbox_unread_config |
| POST | `/rt/locations/v1/upload-driver-device-locations` | arranque (todas as sessoes); mapa e navegacao (110) | common.upload_locations_any |
| ? | `/rt/mobile/recovery-action` | arranque (todas as sessoes) | driver.mobile_recovery_action |
| ? | `/rt/navigation/v3/route` | mapa e navegacao (110); definicoes (043-052) | driver.navigation_route |
| POST | `/rt/offer-experience/upload-earner-experience-state` | oferta (100_online) | driver.upload_earner_experience_state |
| GET | `/rt/onboarding/get-onboarding-status` | documentos (071, 083-089) | driver.onboarding_status_response |
| POST | `/rt/silent-authentication/initiate` | login/arranque (031-033) | identity.silent_initiate |
| POST | `/rt/silent-authentication/submit` | login/arranque (031-033) | identity.silent_submit |
| POST | `/rt/silk-screen/submit-form` | arranque: termos, conformidade e verificacao | usl.submit_form |
| POST | `/rt/surge/supplyInput` | inicio: mapa/estado online (110, 100_online) | driver.upload_positions |
| POST | `/rt/transparent-fare-breakdown/get-transparent-fare-breakdown` | rendimentos (011, 062); viagem (nao capturado) | driver.transparent_fare_breakdown |
| POST | `/rt/trips/v2/begin` | viagem (nao capturado) | driver.begin |
| POST | `/rt/trips/v2/complete-stops` | viagem (nao capturado) | driver.end |
| POST | `/rt/trips/v2/confirm-pin-is-verified` | viagem (nao capturado) | driver.pin_ok |
| POST | `/rt/trips/v2/confirm-pin-is-verified-v2` | viagem (nao capturado) | driver.pin_ok |
| POST | `/rt/trips/v2/driver-cancel` | viagem (nao capturado) | driver.driver_cancel |
| POST | `/rt/trips/v2/driver-rate` | viagem (nao capturado) | driver.driver_rate |
| POST | `/rt/trips/v2/end` | viagem (nao capturado) | driver.end |
| POST | `/rt/trips/v2/start-waiting` | viagem (nao capturado) | driver.arrived |
| POST | `/rt/trips/{tripUUID}/begin` | viagem (nao capturado) | driver.begin |
| POST | `/rt/unifiedlocation/uploadpositions` | inicio: mapa/estado online (110, 100_online); mapa e navegacao (110) | driver.upload_positions |
| POST | `/rt/users/contacts` | ajuda (042, 065, 090-091) | common.contacts |
| GET | `/rt/users/contacts` | ajuda (042, 065, 090-091) | common.contacts |
| GET | `/rt/users/get-compliance` | arranque: termos, conformidade e verificacao | common.compliance |
| GET | `/rt/users/get-compliance-and-copy-for-features` | arranque: termos, conformidade e verificacao | common.compliance |
| POST | `/rt/users/get-security-settings` | definicoes (043-052) | common.security_settings |
| POST | `/rt/users/get-user-info` | menu/perfil (013, 041, 064) | common.user_info |
| POST | `/rt/users/need-verification` | arranque: termos, conformidade e verificacao | common.compliance_post |
| POST | `/rt/users/sync-compliance-and-copy-for-features` | arranque: termos, conformidade e verificacao | common.compliance_post |
| POST | `/rt/users/update-compliance` | arranque: termos, conformidade e verificacao | common.compliance_post |
| POST | `/rt/users/update-compliance-with-task` | arranque: termos, conformidade e verificacao; viagem (nao capturado) | common.compliance_post |
| POST | `/rt/users/update-populous-user-info` | menu/perfil (013, 041, 064) | common.update_user |
| POST | `/rt/users/update-user-identity` | login/arranque (031-033) | common.update_user |
| POST | `/rt/v1/driverretention/mentorship/getmentorshipstate` | menu/perfil (013, 041, 064) | driver.mentorship_state |
| POST | `/rt/vehicle/presentation/driver/vehiclesblocker/set-default-vehicle` | veiculos (070, 080-082) | driver.set_default_vehicle |
| ? | `/status` | inicio: mapa/estado online (110, 100_online) | — |
| gRPC | `/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParameters` | arranque (todas as sessoes) | — |
| gRPC | `/uber.streaming.ramen.RamenService/RamenStreaming` | caixa de entrada (012, 063); canal em tempo real (todas) | — |
| ? | `/v2` | login/arranque (031-033) | usl.login_page |
| ? | `/v2/api/phone` | login/arranque (031-033) | usl.login_phone |
| ? | `/v2/api/verify` | login/arranque (031-033) | usl.login_verify |
| ? | `/v2/login` | login/arranque (031-033) | — |

## Endpoints por ecrã (todas as classes)

| Ecrã | Endpoints |
|---|---|
| (sem ecrã identificado) | 301 |
| viagem (nao capturado) | 217 |
| mapa e navegacao (110) | 102 |
| menu/perfil (013, 041, 064) | 95 |
| seguranca (014-024) | 94 |
| login/arranque (031-033) | 85 |
| descobrir (010, 036, 061, 080-081) | 73 |
| inicio: oportunidades (060) | 73 |
| ajuda (042, 065, 090-091) | 73 |
| definicoes (043-052) | 64 |
| rendimentos (011, 062) | 57 |
| informacoes fiscais (074) | 55 |
| caixa de entrada (012, 063) | 50 |
| canal em tempo real (todas) | 50 |
| oferta (100_online) | 37 |
| arranque (todas as sessoes) | 31 |
| arranque: termos, conformidade e verificacao | 25 |
| documentos (071, 083-089) | 24 |
| veiculos (070, 080-082) | 21 |
| hub de informacoes/comfort (025-030) | 16 |
| inicio: mapa/estado online (110, 100_online) | 15 |
| privacidade (048, 053-054) | 9 |
| inicio: painel (060, 120) | 9 |
| inicio: acoes necessarias (035) | 5 |

Confiança da ligação a ecrãs: inferido pelo nome do path: 704; sem ecra identificado: 301; implementado e validado no laboratorio (app renomeada): 99.

## Autenticação

- Sinais no smali: `Authorization`, `Bearer `, `access_token`, `authorization`, `oauth`, `oauth2`, `oauth2Result`, `oauth2_authentication_handler`, `oauth2_authentication_handler_tnkch8`, `oauthDisabled`, `oauthEnabled`, `oauthFlow`, `oauthInfo`, `oauthResult`, `oauth_1rt_invalidate_token_on_persistence_enabled`.
- Rotas já implementadas no backend: `/oauth/token`, `/oauth/v2/token`, `/rt/communications/device-token/create`, `/rt/identity/auth/issue-web-auth-cookies`, `/rt/identity/oauth2/add-sso-id`, `/rt/identity/oauth2/get-apps-not-in-device-session-group`, `/rt/identity/oauth2/invalidate-token`, `/rt/identity/oauth2/revokesession`, `/rt/identity/oauth2/sso-exchange-token`, `/rt/identity/oauth2/token`, `/rt/identity/oauth2/user-id-token`, `/rt/silent-authentication/initiate`, `/rt/silent-authentication/submit`, `/rt/users/update-user-identity`.
- Esquema validado no laboratório (`TESTE/ui_spec_android/contract_main_flow.md`): OAuth2 com `grant_type` password e refresh, e o token vai no header `x-uber-token` (ou `Authorization: Bearer`). Login social (Google) e conta por e-mail aparecem nos ecrãs 032 e 033.

## Tempo real e push

- Push: `Lcom/google/firebase/messaging/FirebaseM`, `fcm`, `gcm` → `substituir` (projeto Firebase próprio).
- Canal em tempo real: `/ramen/events/ack`, `/ramen/events/recv`, `/ramen/events/v2/ack`, `/ramen/sessions/{sessionId}/messages`, `/rt/external-api-eg/streaming_process_turn`, `/rt/safety-media-platform/close-live-stream-session`, `/rt/safety-media-platform/create-live-stream-session`, `/rt/safety-media-platform/get-live-stream-session`, `/rt/safety-media-platform/update-live-stream-readiness`, `/rt/start_streaming_session` → `rebuild`.

## Uploads

40 sinais (multipart e paths com upload), por exemplo: `"/file-upload/upload/chunks/"`, `"/rt/locations/v1/upload-driver-device-locations"`, `"/rt/offer-experience/upload-earner-experience-state"`, `"/rt/support/upload-ticket-image-v2"`, `"/rt/unifiedlocation/uploadpositions"`, `"/rt/upload/negotiate"`, `"add_entity_state_to_upload_metadata"`, `"app_setup_plugin_switch_language_selector_uploader"`.

## Configuração remota

`app-launch`, `bootstrap`, `experiment`, `flipr`, `mobile-config`, `parameters`, `remote-config`, `remote_config`, `/api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParameters`, `/api/grpc/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParametersUnauthenticated`, `/rt/drivers/app-launch`, `/rt/eats/v1/eater-app-launch`, `/rt/riders/{riderUUID}/app-launch`, `/uber.marketplace.experimentation.parameterservingpresentation.ParameterServingPresentation/GetMobileParameters`.

## Persistência local (Room)

- Bases de dados: 1 (androidx.work.impl.WorkDatabase). Tabelas: 9.
- **Só existe a base interna do WorkManager (biblioteca de tarefas em segundo plano). A app não tem esquema Room próprio, por isso não há modelo de dados local a replicar.**
  - `Dependency`: `work_spec_id` TEXT NOT NULL, `prerequisite_id` TEXT NOT NULL, PRIMARY KEY(`work_spec_id`, `prerequisite_id`
  - `WorkSpec`: `id` TEXT NOT NULL, `state` INTEGER NOT NULL, `worker_class_name` TEXT NOT NULL, `input_merger_class_name` TEXT NOT NULL, `input` BLOB NOT NULL, `output` BLOB N
  - `WorkTag`: `tag` TEXT NOT NULL, `work_spec_id` TEXT NOT NULL, PRIMARY KEY(`tag`, `work_spec_id`
  - `SystemIdInfo`: `work_spec_id` TEXT NOT NULL, `generation` INTEGER NOT NULL DEFAULT 0, `system_id` INTEGER NOT NULL, PRIMARY KEY(`work_spec_id`, `generation`
  - `WorkName`: `name` TEXT NOT NULL, `work_spec_id` TEXT NOT NULL, PRIMARY KEY(`name`, `work_spec_id`
  - `WorkProgress`: `work_spec_id` TEXT NOT NULL, `progress` BLOB NOT NULL, PRIMARY KEY(`work_spec_id`
  - `Preference`: `key` TEXT NOT NULL, `long_value` INTEGER, PRIMARY KEY(`key`)
  - `_new_WorkSpec`: `id` TEXT NOT NULL, `state` INTEGER NOT NULL, `worker_class_name` TEXT NOT NULL, `input_merger_class_name` TEXT, `input` BLOB NOT NULL, `output` BLOB NOT NULL, 
  - `_new_SystemIdInfo`: \n            `work_spec_id` TEXT NOT NULL, \n            `generation` INTEGER NOT NULL DEFAULT 0, \n            `system_id` INTEGER NOT NULL, \n            PRI

## Tráfego real no servidor (agregado)

- Fonte: Hetzner (logs de 11 a 17/10, UTC). 12387 pedidos em 7 ficheiros de log.
- **49 caminhos da app** (5831 chamadas), todos dentro do contrato: 0 fora dele.
- Ruído de rastreadores da internet ignorado: 1681 caminhos (6556 chamadas) — `robots.txt`, `.env`, `.git/config` e afins.
- 0 endpoints `rebuild` foram promovidos a **essencial** por aparecerem em tráfego real.
- Trafego da app renomeada (com.qolari.driver) e da app nova de teste contra o nosso backend; nao e trafego da Uber. Os corpos de pedidos nao foram lidos.

## Lacunas do backend: a app chama e o servidor não tem handler (0)

Só `rebuild`. Ordenadas por número de chamadas.

| Chamadas | Verbo | Path | Ecrã provável |
|---|---|---|---|

## Fluxo de viagem observado no laboratório (15-10, UTC)

Ordem real dos pedidos na viagem completa feita com a app renomeada contra o nosso backend. A chegada e o PIN não geram pedido próprio (a chegada é automática por posição).

| Hora | Verbo | Path | Handler |
|---|---|---|---|
| 16:30:47 | POST | `/rt/trips/v2/begin` | driver.begin |
| 16:32:13 | POST | `/rt/trips/v2/end` | driver.end |
| 16:32:13 | POST | `/rt/drivers/v2/go-offline` | driver.go_offline |
| 16:33:04 | POST | `/rt/drivers/v2/go-online` | driver.go_online |
| 16:34:09 | POST | `/rt/drivers/ack-offers` | driver.tasks |
| 16:34:10 | POST | `/rt/drivers/accept-offers` | driver.accept |
| 16:34:50 | POST | `/rt/trips/v2/begin` | driver.begin |
| 16:35:16 | POST | `/rt/trips/v2/end` | driver.end |
| 17:02:42 | POST | `/rt/drivers/v2/go-offline` | driver.go_offline |
| 17:02:44 | POST | `/rt/drivers/v2/go-online` | driver.go_online |
| 18:09:30 | POST | `/rt/earnings/get-daily-earnings-view` | driver.daily |
| 18:09:30 | POST | `/rt/earnings/get-balance-summary` | driver.balance |
| 18:09:30 | POST | `/rt/earnings/get-activity-feed-v3` | driver.activity |

## Limites

- A ligação endpoint → ecrã é inferida pelo nome do path, exceto nos endpoints já implementados e validados no laboratório.
- O tráfego vem dos logs do servidor e do backend local, agregados (sem corpos de pedidos). É tráfego da app renomeada e da app de teste, e não da Uber.
- As capturas da pasta TESTE são posteriores à viagem do laboratório (a partir das 19:09 locais), por isso **não se consegue ligar ecrãs da viagem a pedidos pela hora**. Essa ligação continua inferida pelo nome.
- Os tipos de resposta saem das assinaturas Retrofit. Os genéricos e os erros podem esconder o DTO real.

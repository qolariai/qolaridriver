# backlog.md — gaps priorizados (FASE 7)

**Alvo:** `funcional`. **Estado:** zero itens abertos no âmbito
Driver + Rider + backend + backoffice. A validação no Honor (V-01) foi executada em
2026-10-25 e está registada em `VALIDACAO_MEGA.md` §2.

| id | área | ecrã/fluxo | razão | bloqueia | esforço | dono | estado |
|---|---|---|---|---|---|---|---|
| R-01 | Rider | Início: zoom | os botões mostravam “Ampliar/Reduzir” sem mudar o mapa | demo/opera | S | app Rider | fechado — `MapCamera` + `MapCameraTest` |
| R-02 | Rider | Início: localização | o botão só mostrava um aviso | demo/opera | M | app Rider | fechado — permissão, `LocationManager`, `POST /rt/lite/location` |
| R-03 | Rider | Início: sugestões | “Entrega/Reserve/Envie” abriam “Em breve” | demo/opera | S | app Rider/backend | fechado — entradas removidas; só “Viajar” |
| R-04 | Rider | Início: promoções | um cartão abria a procura, outro o “Em breve” | demo/opera | S | app Rider | fechado — ambos abrem promoções |
| R-05 | Rider | Login: reenviar | botão só mostrava um aviso | demo/opera | S | app Rider | fechado — preenche `0000` |
| R-06 | Rider | Pesquisa: paragens/mapa/cidade/agora/pessoas | cinco entradas só mostravam avisos | demo/opera | M | app Rider | fechado — entradas removidas; ficou “casa guardada” funcional |
| R-07 | Rider | Escolher viagem: chips | “Agora/Para mim” só mostravam avisos | demo/opera | S | app Rider | fechado — removidos |
| R-08 | Rider | Carteira: adicionar pagamento | simulava um pagamento sem efeito | demo/opera | S | app Rider | fechado — escolhe entre os perfis reais |
| R-09 | Rider | Atividade: filtro | mudava o rótulo mas não filtrava | demo/opera | S | app Rider | fechado — removido (não há perfil empresa) |
| R-10 | Rider | Gerir conta | página “informativa” sem edição | demo/opera | L | app Rider/backend | fechado — casa, dados, segurança, privacidade, verificação |
| R-11 | Backend | Conta Rider | não havia escrita para casa/dados | demo/opera | M | backend | fechado — `PATCH /rt/lite/account`, `POST /rt/lite/account/home`, 2 testes |
| D-01 | Driver | Menu: Descobrir/Pro/Hub/Recomendações | linhas com seta e sem destino | demo/opera | S | app Driver | fechado — navegação para Descobrir ou página própria |
| D-02 | Driver | Strings de páginas próprias | informação em falta para as linhas novas | demo/opera | S | app Driver | fechado — `info_pro/work/referrals` |
| D-03 | Driver | Fim: avaliação do passageiro | a folha voltava a abrir depois de “Enviar” e prendia o motorista | demo/opera | S | app Driver | fechado — `RatingSheet` observa o estado; validado na viagem 73 |
| D-04 | Driver | Ajuda e Definições | categorias da Ajuda e quatro linhas das Definições não tinham efeito | demo/opera | M | app Driver | fechado — categorias abrem `InfoFragment`; Privacidade abre página própria; Gerir conta vai ao Menu; Editar endereço e Modo noturno removidos; validado no Honor |
| D-05 | Driver | Mapa | pesquisa, atalhos (relâmpago/reportar/tendências/localizar), escudo e preferências sem handler | demo/opera | M | app Driver | fechado — `PlaceSearchSheet`, `MapReportSheet` + backend, navegação e `recenter`; validado no Honor |
| D-06 | Driver | Barra de separadores | o separador Página inicial não navegava (caía no Menu) | demo/opera | S | app Driver | fechado — listener explícito por separador; validado no Honor |
| R-12 | Rider | Fim: avaliação do motorista | `@Body Map<String, ?>` rejeitado pelo Retrofit; nenhuma avaliação era gravada | demo/opera | S | app Rider | fechado — `RateRequest` + `ContractTest`; validado na viagem 71 |
| R-13 | Rider | Arranque após fim de viagem | ao reabrir a app, o desfecho recente era filtrado e a avaliação perdia-se | demo/opera | S | app Rider | fechado — `HomeViewModel` aceita os estados terminais de `/rt/lite/active`; `SeenTrips` evita reabrir o mesmo desfecho; validado ao reabrir na viagem 73 |
| R-14 | Rider | Mapa | a rota entre recolha e destino era uma linha reta | demo/opera | M | app Rider/backend | fechado — `/rt/lite/route` + OSRM (fallback em linha reta); validado no Honor |
| V-01 | Telemóvel | Driver + Rider no Honor | faltava correr o ciclo completo no dispositivo final | opera | M | operador | fechado — fluxo completo em 25/10; capturas em `VALIDACAO_HONOR/` |
| S-03 | Rider | Gorjeta/recibo/top-up/disputa | dinheiro do Rider era só total simples | demo/opera | M | app Rider | fechado — `test_rider_money` |
| S-04 | Rider | Ride check | faltava check-in de segurança | demo/opera | S | apps/backend | fechado — `test_safety` |
| S-05 | Suporte | Anexos/chamada/bug report | chat só texto | demo/opera | M | apps/backend | fechado — `test_support_chat` |
| D-10 | Driver | Fila de aeroporto | sem fila nem posição | demo/opera | M | app/backend | fechado — `test_airport_queue` |
| D-11 | Driver | Incentivos | cartões estáticos | demo/opera | L | app/backend | fechado — `test_incentives` |
| D-12 | Driver | Ajustes/faturas/impostos | sem pedido nem documento | demo/opera | M | app/backend | fechado — `test_adjustments` |
| D-13 | Driver | Perfil empresarial/delegado | não existia | demo/opera | M | app/backend | fechado — `test_business_profile` |
| R-16 | Rider | Locais guardados | só casa | demo/opera | S | app/backend | fechado — `test_saved_places` |
| R-17 | Rider | Empresa/família/Uber One | não existia | demo/opera | L | app/backend | fechado — `test_account_extras` |
| X-01 | Ambos | Idioma/dark/simple | só PT e claro | demo/opera | M | apps | parcial — PT/EN, dark experimental, simple |
| S-06 | Rider + Driver | Paragens intermédias | pedido não suportava paragens | demo/opera | L | apps/backend | fechado — `test_stops` |
| S-07 | Rider | Offline com fila | pedido perdia-se sem rede | demo/opera | M | app Rider | fechado — `PendingTripStore` |
| S-08 | Rider | Partilha de ecrã | chat sem ecrã | demo/opera | M | apps/backend | fechado — `test_screen_share_roundtrip` |
| S-09 | Driver | Gravação de áudio | sem gravação na viagem | demo/opera | M | app/backend | fechado — `test_audio_recording_start_stop` |
| S-01 | Driver/Rider/Consola | Suporte in-app | não havia chat entre contas e operação | demo/opera | M | backend/apps | fechado — `test_support_chat` |
| S-02 | Driver/Rider/Consola | Segurança | sem contactos de confiança, SOS ou partilha | demo/opera | M | backend/apps | fechado — `test_safety` |
| D-07 | Driver/Consola | Documentos | só lista/estado, sem upload nem verificação | demo/opera | M | backend/app | fechado — `test_documents_upload` |
| D-08 | Driver | Preferências de condução | sem destino, área, auto-aceitação ou pausa | demo/opera | L | backend/app | fechado — `test_driver_preferences` |
| D-09 | Driver | Dinheiro | sem transferir saldo, extratos ou recibo | demo/opera | L | backend/app | fechado — `test_payouts` |
| R-15 | Rider | Agendamento | só pedido imediato | demo/opera | L | backend/app | fechado — `test_scheduling` |

## Gaps abertos

Nenhum para `funcional` no âmbito declarado.

## Fora do alvo (tolerância escrita)

- UI própria da Fleet (operação coberta por backend/backoffice).
- Vídeo de câmara e tradução EN completa.
- Miniaturas decorativas dos cartões (mapa real só nos ecrãs principais).
- iOS.

Estas linhas não são botões na UI; estão em `capabilities.md` §5 e `plan.md` §8.

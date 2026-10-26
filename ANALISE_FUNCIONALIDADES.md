# ANALISE FUNCIONALIDADES - oficial vs recriacao

**Data:** 2026-10-26. **Ambito:** Uber Driver 4.600/4.601 e Uber Lite 1.248.
**Comparacao:** `ANDOIRD/DRIVER/RECRIACAO` e `ANDOIRD/USER_LITE/RECRIACAO`.
**Metodo:** spec/capturas oficiais + codigo + `capabilities.md`/`coverage.md`.

Auditoria de funcionalidades, nao de pixels. Uma funcao pode existir na UI e estar
incompleta; nesse caso fica `parcial`.

| Estado | Significado |
|---|---|
| `ok` | implementada com efeito real |
| `parcial` | existe, mas falta uma parte relevante |
| `visual` | so UI/estatica |
| `removido` | entrada retirada da UI; declarado |
| `em falta` | esta no ambito, mas nao existe |
| `fora` | excluida por decisao de ambito |

## 1. Driver - acesso e conta

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| D01 | Login telefone + codigo | 031-033 | login nativo | ok |
| D02 | Login por e-mail | 033_login_email | nao existe | fora |
| D03 | Login social/SSO | strings login | nao existe | fora |
| D04 | Alternar conta | 000/032 | seletor + sign out | ok |
| D05 | Onboarding do motorista | 035 | cartao de acoes; sem fluxo | parcial |
| D06 | Verificacao de identidade | identity_verification_*, /rt/drivers/v3/verify-identity | upload do CC + estado pendente | ok |
| D07 | Upload de documentos | 083-089; /rt/driver-compliance/documents | lista + upload JPG/PNG/WEBP/PDF | ok |
| D08 | KYC/aprovacao | docs; driver_auto_approve | backend/consola | parcial |
| D09 | Editar perfil | earner-profile/* | hub; sem edicao | parcial |
| D10 | Perfil empresarial/delegado | delegate_profile_*, /rt/business/* | perfil + delegados | ok |
| D11 | Idioma | ub__language_selector_* | PT/EN (EN parcial) | parcial |
| D12 | Simple mode/easy entrance | accessibility_settings_* | modo simples (texto maior) | ok |
| D13 | Recomendar motoristas | /rt/inviter-dashboard/* | codigo, convites e recompensa | ok |

## 2. Driver - inicio e despacho

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| D14 | Online/offline | 110/120 | implementado | ok |
| D15 | Acoes necessarias | 035; request-blockers | cartao; sem resolucao in-app | parcial |
| D16 | Modo Destino | agenda_section_destination; preferred-destination/* | implementado (filtro no despacho) | ok |
| D17 | Preferencias de area | area_preference_*; zonesmap | implementado (raio por zona) | ok |
| D18 | Aceitacao automatica | notify-auto-accept-progress | implementado (aceita no servidor) | ok |
| D19 | Pausa/fila de espera | fleet_break_* | pausa 15/30 min; sem fila | parcial |
| D20 | Heatmap/surge | heatmapV2; surge | circulos decorativos | parcial |
| D21 | Fila de aeroporto | airport_filter_* | grafico de exemplo | visual |
| D22 | Oferta com som/timer | 100_online_* | timer visual; sem som | parcial |
| D23 | Navegacao externa | nav_*; navigation | Google Maps/Waze a partir da viagem | ok |
| D24 | Pedidos por voz | voice_trip_requests | nao existe | em falta |
| D25 | Modo simples | simple_mode_* | nao existe | em falta |

## 3. Driver - viagem e dinheiro

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| D26 | Aceitar/recusar/expirar | 100_online_* | implementado | ok |
| D27 | Surge/boost no detalhe | offer strings | preco fixo | parcial |
| D28 | Chegada/PIN/inicio/fim | arrive; pin-accept; begin/end | implementado | ok |
| D29 | Paragens/waypoints | set-waypoint-destination | ate 3 paragens, concluidas pelo motorista | ok |
| D30 | Tarifa manual/portagens | manual_fare_entry_*; toll_* | pedido de ajuste + aprovacao | parcial |
| D31 | Cancelar com motivo | driver-cancel | implementado | ok |
| D32 | Avaliar passageiro | driver-rate | implementado | ok |
| D33 | Recibo/waybill | earnings/v3/trip | recibo detalhado na app | ok |
| D34 | Objeto perdido/questao | trip-support | report so de mapa | parcial |
| D35 | Partilha/contactos confianca | trusted contacts | partilha do sistema | parcial |
| D36 | Gravacao audio/video | audio_recording_* | audio + video do ecra; camera fora | ok |
| D37 | Ride check | safety strings | nao existe | em falta |

## 4. Driver - rendimentos e suporte

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| D38 | Diario/semanal/saldo | 011/062 | implementado | ok |
| D39 | Transferir saldo/instant pay | finprod; uber_pro_payout | implementado (IBAN + Instant Pay) | ok |
| D40 | Extratos/faturas/impostos | statements; invoices | extratos, faturas e impostos | ok |
| D41 | Gorjetas/ajustes | tip/toll breakdown | gorjeta no recibo; ajustes | ok |
| D42 | Quests/incentivos | incentives/* | missoes com progresso e recompensa | ok |
| D43 | Pontos/Pro | loyalty_* | pontos, nivel e proximo nivel | ok |
| D44 | Descobrir com filtros reais | 010/061 | exemplos | parcial |
| D45 | Ajuda com pesquisa | 042/065/090 | categorias; sem pesquisa | parcial |
| D46 | Chat/ticket/chamada | chat/v2; customer-obsession | chat, anexos, chamada e bug report | ok |
| D47 | Bug report | bug-reporting/* | nao existe | em falta |
| D48 | 112/contactos/ride check | safety-* | 112, contactos, SOS, ride check e partilha | ok |
| D49 | Veiculos/documentos | 070-089 | implementado | ok |
| D50 | Adicionar veiculo | 081 | removido | fora |
| D51 | Enviar foto documento | uploads; docscan | upload na app (imagem/PDF) | ok |
| D52 | Dark mode/idioma | values-night; language | modo escuro e PT/EN (EN parcial) | parcial |
| D53 | FCM | FCM | implementado/testado | ok |
| D54 | Offline com fila | 110-126 | banner; sem fila | parcial |

## 5. Rider - fluxo principal

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| R01 | Boas-vindas/login telefone | 000-003 | implementado | ok |
| R02 | Seletor pais/idioma | 002; language_selector | pais; idioma so PT | parcial |
| R03 | Inicio/mapa/sugestoes | 010/030 | implementado | ok |
| R04 | Localizacao/zoom | 010 | implementado | ok |
| R05 | Pesquisa/destino | 031 | implementado | ok |
| R06 | Casa/locais salvos | 030; saved_places | casa + locais guardados (CRUD) | ok |
| R07 | Cidade/categoria/empresa | search_city | removido | fora |
| R08 | Categorias/precos | 032 | X/Comfort/XL | ok |
| R09 | Pagamento/Uber Cash | 021/032 | dinheiro/cartao + Qolari Cash (top-up) | ok |
| R10 | Adicionar cartao/top-up | payment_wallet | so escolhe perfis | parcial |
| R11 | Promocoes/codigo | 024 | implementado | ok |
| R12 | Agendar/reservar | schedule strings | agendamento com data/hora | ok |
| R13 | Paragens | ride_stops (string) | ate 3 paragens, estado por paragem | ok |
| R14 | Procurar motorista | trip_searching | implementado | ok |
| R15 | Motorista a caminho/PIN | active | implementado | ok |
| R16 | Partilhar viagem | share_trip | link publico de acompanhamento | ok |
| R17 | Contactar motorista | chat/contact | cartao; sem chat | parcial |
| R18 | Cancelar | cancel | implementado | ok |
| R19 | Em viagem/ETA/rota | 041 | implementado | ok |
| R20 | Recibo detalhado | receipt | recibo com linhas e total | ok |
| R21 | Gorjeta/disputa | custom_tip_* | gorjeta e contestacao | ok |
| R22 | Avaliar motorista | rating | implementado | ok |

## 6. Rider - conta, seguranca e suporte

| # | Oficial | Evidencia | Nossa app | Estado |
|---|---|---|---|---|
| R23 | Seguranca/112 | emergency | SOS + ligacao 112 | ok |
| R24 | Contactos confianca/emergencia | contact_manager_* | contactos geridos na app | ok |
| R25 | Partilha de ecra/ride check | screen_share_* | ride check + partilha do ecra completo | ok |
| R26 | Objeto perdido/suporte | support | chat de apoio; sem fluxo dedicado | parcial |
| R27 | Historico/atividade | 022 | implementado | ok |
| R28 | Repetir/recibo historico | activity | lista; sem detalhe | parcial |
| R29 | Menu/perfil | 011/042 | implementado | ok |
| R30 | Editar conta | profile | nome/email; telefone nao | parcial |
| R31 | Verificacao/privacidade | identity_verification_* | paginas informativas | parcial |
| R32 | Perfil empresarial/despesas | business_* | perfil empresarial ativo | ok |
| R33 | Familia/teens | family_* | membros e teen (perfil) | parcial |
| R34 | Uber One | uber_one | subscricao com 5% real | ok |
| R35 | Ajuda/pesquisa/artigos | 012/020 | implementado | ok |
| R36 | Chat/chamada/ticket | help_conversation_* | chat, anexos, chamada e ticket | ok |
| R37 | Legal | 025 | implementado | ok |
| R38 | Idioma/acessibilidade | language/a11y | so PT; parcial | parcial |
| R39 | FCM | FCM | implementado/testado | ok |
| R40 | Offline | 050-052 | fila local de pedido com reenvio | ok |
| R41 | Entrega/transit/bikes | eats/emobility | removido | fora |
| R42 | Voucher/gift card | voucher_* | nao existe | fora |

## 7. Transversal

| # | Funcionalidade | Nossa app | Estado |
|---|---|---|---|
| X01 | Maps/rota/transito/turn-by-turn | mapa real; sem transito/turn-by-turn | parcial |
| X02 | FCM | implementado | ok |
| X03 | Offline com cache/fila | fila de pedido no Rider | parcial |
| X04 | Idioma/moeda | PT/EN (EN parcial); EUR | parcial |
| X05 | Dark mode | modo escuro (experimental) | parcial |
| X06 | A11y completa | modo simples + acessibilidade do sistema | parcial |
| X07 | Suporte in-app | chat + ticket + consola | ok |
| X08 | Pagamentos reais | laboratorio | fora |
| X09 | Multi-pais/tenant | PT | fora |
| X10 | iOS | ausente | fora |

## 8. Prioridade e estado (2026-10-26)

| P | Item | Impacto | Esforco | Estado |
|---|---|---|---|---|
| P0 | Chat/ticket de suporte (Driver/Rider) | alto | M | ✅ chat + ticket na consola |
| P0 | Contactos confianca/emergencia + partilha | alto | M | ✅ contactos, SOS e link publico |
| P0 | Upload/verificacao de documentos | alto | M | ✅ upload + estado pendente |
| P1 | Modo Destino/area/auto-aceitacao/pausa | alto | L | ✅ filtros no despacho + pausa |
| P1 | Transferir saldo/extratos/recibos | alto | L | ✅ IBAN/Instant Pay, extratos, recibo |
| P1 | Agendar/paragens no Rider | alto | L | ✅ agendar + até 3 paragens |
| P1 | Gravação áudio/vídeo | medio | M | ⚠️ áudio na viagem; vídeo fora |
| P1 | Partilha de ecrã com suporte | medio | M | ✅ ecrã da app no chat |
| P1 | Offline com fila | medio | M | ✅ pedido guardado e reenviado |
| P2 | Gorjeta/disputa/objeto perdido | medio | M | ✅ gorjeta e disputa; objeto perdido via chat |
| P2 | Empresa/familia/teens | medio | L | ✅ empresa; família/teens em perfil |
| P2 | Idioma/dark/simple mode | medio | M | ✅ simple/PT-EN; dark experimental |
| P3 | Gravacao/EV/rental/Comfort | baixo/fora | XL | fora |

## 9. Conclusao

O clone cobre o nucleo ride-hailing: login, inicio, mapa, pedido, oferta, PIN,
viagem, fim, avaliacao, rendimentos, carteira, historico, FCM e backoffice. Com esta
ronda cobre tambem suporte, seguranca relacional, documentos, produtividade do
motorista, dinheiro e agendamento.

Ficam declarados fora do alvo `funcional`: gorjeta/disputa, empresa/familia/teens,
idioma/dark/simple mode, gravacao/video, EV/rental/Comfort, entrega, transito/bikes
e iOS. Estas exclusoes sao decisoes de ambito, nao regressoes.

**Prova:** `BACKEND` 93 testes, Driver e Rider com testes verdes, backoffice
compilado, `tools/spec_check.py` com 451 verificacoes. Os novos testes cobrem
`test_support_chat`, `test_safety`, `test_documents_upload`,
`test_driver_preferences`, `test_payouts`, `test_scheduling`,
`test_rider_money`, `test_airport_queue`, `test_incentives`, `test_adjustments`,
`test_saved_places`, `test_account_extras`, `test_business_profile`,
`test_stops`, `test_screen_share_roundtrip`, `test_audio_recording_start_stop` e
`test_video_recording_start_stop`.

**Segunda ronda (26/10):** gorjeta/recibo/top-up/disputa, ride check, anexos e
chamada no suporte, fila de aeroporto, missoes/pontos/referral, ajustes/faturas/
impostos, locais guardados, empresa/familia/Uber One e aparencia/idioma.

**Terceira ronda (26/10):** paragens intermedias (pedido, motorista e conclusao),
**offline com fila** no Rider, **partilha do ecra completo** com o apoio e
**gravacao de audio + video do ecra** da viagem. Continua fora apenas: video de
camara e traducao EN completa.







# MELHORIAS.md — fases P0–P3 (pós-fecho)

Registo das melhorias pedidas depois do fecho `funcional`. Cada fase foi feita de uma vez;
o objetivo continua a ser o alvo `funcional`, não `produção`/`loja`.

## P0 — pontas soltas (concluída)

| # | Item | Estado | Prova |
|---|---|---|---|
| 1 | Backoffice “Problemas de mapa” | ✅ | `GET/PATCH /api/map-reports`, página `MapReports.tsx`, nav; teste `test_backoffice_lists_and_resolves_map_reports` |
| 2 | Rider “motorista a caminho” com rota motorista→recolha | ✅ | `ActiveTripFragment` escolhe a rota por estado; Honor: Amadora→Campo Grande |
| 3 | Rota do Driver refrescada (15 s / 100 m) | ✅ | `DriveViewModel.ROUTE_REFRESH_MS` + `meters()`; `DriveTest` |
| 4 | Chave e credenciais fora do versionamento | ✅ | `.gitignore` (`local.properties`, `google_maps_api_key.txt`); restrições documentadas no README |
| 5 | Voltar das Definições para Início/mapa | ✅ | `SettingsFragment.ARG_BACK_TO`; Honor: Definições→voltar ao Início e ao mapa |

## P1 ? mapas e opera??o (conclu?da)

| # | Item | Estado | Nota |
|---|---|---|---|
| 6 | Miniaturas dos cartões com mapa real | ✅ | `StaticMapView` (Google Static Maps) + fallback desenhado; Honor mostra miniaturas reais |
| 7 | Pesquisa de locais real | ✅ | Google Places Text Search + Geocoding; fallback seed; Driver e Rider; Honor “Rua Augusta” |
| 8 | Cache/self-host do OSRM | ✅ | cache 600 s (falhas 60 s), `ROUTE_CACHE_TTL_S`; self-host em `BACKEND/README.md` |
| 9 | Marcador do motorista/rotação/clustering | ✅ | carro roda com `heading` do backend; clustering N/A (uma oferta por vez); trânsito não ativado |
| 10 | FCM | ? | Driver/Rider no projeto `qolari-driver-prod`, token no backend, envio HTTP v1 testado no Honor; `ramen` fallback |
| 11 | Rate limit em `map-report`/login | ✅ | `core/ratelimit.py`; 10/min login, 5/min map-report, 300/min restante |

## P2 — produção/loja (executado o que não depende de contas)

| # | Item | Estado | Nota |
|---|---|---|---|
| 12 | PostgreSQL, HTTPS, secrets, backups, métricas, CI | ✅ parcial | guarda `ENVIRONMENT=production`, `/api/health`, `tools/backup.py`, Alembic baseline, `psycopg`, nginx/systemd/env em `deploy/`, CI. HTTPS/certificados e deploy real não executados. |
| 13 | Release assinado, Play Console, privacidade/GDPR, Data Safety | ⛔ | config de assinatura por `local.properties`, `PRIVACIDADE.md` e `DATA_SAFETY.md`; Play/keystore/legal são externos. |
| 14 | i18n, dark mode, a11y | ⚠️ | `lintDebug` passa nas duas apps (warnings de hardcoded/RTL); i18n e dark mode ficam como decisão de design, não foram fingidos. |
| 15 | Testes E2E/Espresso e regressão visual | ✅ parcial | smoke instrumentado em ambas (arranque + NavHost); `tools/visual_diff.py`; fluxos completos continuam manuais no Honor. |
| 16 | Fleet visual | ⛔ | decisão de produto; operação coberta por backend/backoffice. |
| 17 | iOS | ⛔ | fora do âmbito; sem macOS/Xcode. |

## P3 — código

| # | Item | Estado | Nota |
|---|---|---|---|
| 18 | Módulo comum de mapas | ✅ | `ANDOIRD/SHARED/map` incluído pelos dois projetos; `GoogleMapView` duplicado removido. |
| 19 | `SeenTrips` persistido por conta | ✅ | DataStore (`terminal_trip`); sobrevive a morte do processo; limpo no logout. |
| 20 | `MapReport` com enum + testes | ✅ parcial | códigos `address/closed/outdated/other` no backend e rótulos na consola; teste de backend; UI test manual. |

## P4 — lacunas da análise de funcionalidades (2026-10-26)

Ronda pedida depois de `ANALISE_FUNCIONALIDADES.md`. Fecha os P0 e P1 do âmbito;
P2/P3 ficam declarados.

| # | Item | Estado | Prova |
|---|---|---|---|
| 21 | Chat de suporte Driver + Rider + consola | ✅ | `apps/support.py`, `Support.tsx`, `test_support_chat` |
| 22 | Contactos de confiança, SOS/112 e partilha pública | ✅ | `apps/safety.py`, `/share/{token}`, `Safety.tsx`, `test_safety` |
| 23 | Upload e verificação de documentos | ✅ | `/rt/drivers/v2/documents/upload`, `.../verify-identity`, `test_documents_upload` |
| 24 | Modo destino, área, auto-aceitação e pausa | ✅ | preferências + filtros em `domain/trips.candidates`, `test_driver_preferences` |
| 25 | Transferir saldo, Instant Pay, histórico e extratos | ✅ | `/rt/earnings/*payout*`, `.../statements`, `test_payouts` |
| 26 | Recibo detalhado e agendamento no Rider | ✅ | `EarningsFragment`, `scheduledAt` + `test_scheduling` |

## P5 — segunda ronda de funcionalidades (2026-10-26)

| # | Item | Estado | Prova |
|---|---|---|---|
| 27 | Gorjeta, recibo, top-up e disputa (Rider) | ✅ | `test_rider_money` |
| 28 | Ride check nas duas apps | ✅ | `test_safety` |
| 29 | Anexos, chamada e bug report no suporte | ✅ | `test_support_chat` |
| 30 | Fila de aeroporto no Driver | ✅ | `test_airport_queue` |
| 31 | Missões, pontos/Pro e referral | ✅ | `test_incentives` |
| 32 | Ajustes, faturas e impostos | ✅ | `test_adjustments` |
| 33 | Locais guardados (Rider) | ✅ | `test_saved_places` |
| 34 | Empresa, família/teens e Uber One | ✅ | `test_account_extras` |
| 35 | Perfil empresarial/delegado (Driver) | ✅ | `test_business_profile` |
| 36 | Idioma, modo escuro e modo simples | ✅ parcial | build + lint |

## P6 — terceira ronda (2026-10-26)

| # | Item | Estado | Prova |
|---|---|---|---|
| 37 | Paragens intermédias (Rider + Driver) | ✅ | `test_stops` |
| 38 | Offline com fila no Rider | ✅ | `PendingTripStore` + `HomeFragment` |
| 39 | Partilha do ecrã da app com o apoio | ✅ | `test_screen_share_roundtrip` |
| 40 | Gravação de áudio da viagem | ✅ | `test_audio_recording_start_stop` |
| 41 | Gravação de vídeo do ecrã da viagem | ✅ | `test_video_recording_start_stop` |
| 42 | Vídeo de câmara | ⛔ | câmara/legal; declarado |

## Verificação final

- Backend: **93 testes**, 0 falhas
- Driver: **74 testes** + 1 instrumentado, 0 falhas
- Rider: **11 testes** + 1 instrumentado, 0 falhas
- `spec_check.py`: **451 verificações**, 0 falhas
- Backoffice: build OK (74 módulos)
- Lint: passa nas duas apps (warnings de hardcoded/RTL)

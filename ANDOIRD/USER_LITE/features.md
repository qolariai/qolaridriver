# features.md — inventário de funcionalidades da Rider (Uber Lite)

**FASE 4.7** do `PROMPT_CLONE_MEGA.md` · **app original:** `com.ubercab.uberlite`
1.248.10001 · **taxonomia:** `FEATURE_TAXONOMY.md`

**Gerado por `tools/gen_features_rider.py`.** Não editar à mão.

**Nota de evidência:** a Rider original é uma **WebView**. O contrato nativo não
existe no binário — o `endpoints.json` desta app é `designed` (desenhado para a
nossa recriação), não `live`. A UI observada é `live` onde há captura.

---

## 1. Resumo

| Métrica | Valor |
|---|---|
| Features no inventário | 52 |
| `ok` | 44 |
| `parcial` | 0 |
| `em falta` | 8 |
| `excluído` | 0 |
| Domínios | 17 |
| Capturas base cobertas | 29 / 29 |

### Domínios

| Domínio | Features |
|---|---|
| `home` | 7 |
| `platform` | 7 |
| `trip` | 5 |
| `account` | 4 |
| `offline` | 4 |
| `onboarding` | 4 |
| `menu` | 3 |
| `search` | 3 |
| `auth` | 2 |
| `finance` | 2 |
| `legal` | 2 |
| `promotions` | 2 |
| `rides` | 2 |
| `support` | 2 |
| `history` | 1 |
| `notifications` | 1 |
| `payment` | 1 |

---

## 2. Matriz

```
id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste
```

| id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste |
|---|---|---|---|---|---|---|---|---|---|
| `F-onboarding-01` | onboarding | Arranque sem sessao | `000_arranque_logout.png` | `000_arranque_logout` | abrir app | `—` | — | **ok** | ContractTest |
| `F-onboarding-02` | onboarding | Boas-vindas: comecar | `001_apos_comecar.png` | `001_apos_comecar` | tocar Comecar | `—` | — | **ok** | ContractTest |
| `F-onboarding-03` | onboarding | Seletor de pais (indicativo) | `002_pais_seletor.png` | `002_pais_seletor` | escolher pais | `—` | pais -> codigo | **ok** | ContractTest |
| `F-onboarding-04` | onboarding | Seletor de pais fechado | `003_apos_fechar_seletor.png` | `003_apos_fechar_seletor` | fechar seletor | `—` | seletor -> fechado | **ok** | ContractTest |
| `F-home-01` | home | Inicio (mapa, pesquisa, sugestoes) | `010_inicio.png` | `010_inicio` | abrir app | `GET /rt/lite/home` | — | **ok** | ContractTest |
| `F-home-02` | home | Inicio: estado retomado | `011_inicio_retomada.png` | `011_inicio_retomada` | voltar a app | `GET /rt/lite/home` | — | **ok** | ContractTest |
| `F-menu-01` | menu | Menu lateral | `011_menu.png` | `011_menu` | abrir menu | `GET /rt/lite/session` | — | **ok** | ContractTest |
| `F-support-01` | support | Ajuda: lista | `012_ajuda.png` | `012_ajuda` | abrir topico | `—` | — | **ok** | ContractTest |
| `F-support-02` | support | Ajuda: topico completo | `020_ajuda_completa.png` | `020_ajuda_completa` | ler topico | `—` | — | **ok** | ContractTest |
| `F-finance-01` | finance | Carteira | `021_wallet.png` | `021_wallet` | escolher pagamento | `GET /rt/lite/wallet` | — | **ok** | ContractTest |
| `F-history-01` | history | Atividade: historico | `022_atividade.png` | `022_atividade` | abrir viagem | `GET /rt/lite/history` | — | **ok** | ContractTest |
| `F-promotions-01` | promotions | Promocoes | `024_promocoes.png` | `024_promocoes` | aplicar codigo | `GET /rt/lite/promotions` | — | **ok** | ContractTest |
| `F-legal-01` | legal | Legal | `025_legal.png` | `025_legal` | abrir topico | `—` | — | **ok** | ContractTest |
| `F-home-03` | home | Inicio: estado atual | `026_estado_atual.png` | `026_estado_atual` | refresh | `GET /rt/lite/home` | — | **ok** | ContractTest |
| `F-search-01` | search | Inicio antes da pesquisa | `030_inicio_antes_pesquisa.png` | `030_inicio_antes_pesquisa` | abrir pesquisa | `—` | — | **ok** | ContractTest |
| `F-search-02` | search | Pesquisa de destino | `031_pesquisa_aberta.png` | `031_pesquisa_aberta` | escrever destino | `GET /rt/lite/places` | — | **ok** | ContractTest |
| `F-rides-01` | rides | Escolher viagem (produtos e precos) | `032_apos_escolher_destino.png` | `032_apos_escolher_destino` | escolher produto | `POST /rt/lite/quote` | — | **ok** | ContractTest |
| `F-rides-02` | rides | Escolher viagem: fim da lista | `032_apos_escolher_destino_fim.png` | `032_apos_escolher_destino_fim` | ver ultimo produto | `POST /rt/lite/quote` | — | **ok** | ContractTest |
| `F-home-04` | home | Inicio: retomar | `040_estado_ao_retomar.png` | `040_estado_ao_retomar` | voltar a app | `GET /rt/lite/home` | — | **ok** | ContractTest |
| `F-legal-02` | legal | Legal (2. vista) | `040_legal.png` | `040_legal` | abrir topico | `—` | — | **ok** | ContractTest |
| `F-home-05` | home | Inicio: estado | `041_estado.png` | `041_estado` | refresh | `GET /rt/lite/home` | — | **ok** | ContractTest |
| `F-account-01` | account | Gerir conta | `041_gerir_conta.png` | `041_gerir_conta` | abrir conta | `GET /rt/lite/session` | — | **ok** | ContractTest |
| `F-menu-02` | menu | Menu (2. vista) | `042_menu_2.png` | `042_menu_2` | navegar | `—` | — | **ok** | ContractTest |
| `F-finance-02` | finance | Uber Cash | `042_uber_cash.png` | `042_uber_cash` | abrir saldo | `GET /rt/lite/wallet` | — | **ok** | ContractTest |
| `F-menu-03` | menu | Menu (3. vista) | `043_menu_3.png` | `043_menu_3` | navegar | `—` | — | **ok** | ContractTest |
| `F-search-03` | search | Inicio: sugestoes | `044_inicio_sugestoes.png` | `044_inicio_sugestoes` | tocar sugestao | `GET /rt/lite/places` | — | **ok** | ContractTest |
| `F-offline-01` | offline | Offline: inicio | `050_offline_inicio.png` | `050_offline_inicio` | sem rede | `—` | online -> offline | **ok** | ContractTest |
| `F-offline-02` | offline | Offline: pesquisa | `051_offline_pesquisa.png` | `051_offline_pesquisa` | sem rede | `—` | online -> offline | **ok** | ContractTest |
| `F-offline-03` | offline | Offline: regresso | `052_offline_apos_voltar.png` | `052_offline_apos_voltar` | voltar a rede | `—` | offline -> online | **ok** | ContractTest |
| `F-auth-01` | auth | Login por telefone | Tela de telefone + codigo | — | ver acao | `POST /rt/identity/oauth2/token` | — | **ok** — capturado fora da pasta base (000-003) | ContractTest |
| `F-auth-02` | auth | Verificacao por codigo SMS | Codigo `0000` no laboratorio | — | ver acao | `POST /rt/lite/session` | — | **ok** — laboratorio | ContractTest |
| `F-trip-01` | trip | Pedir viagem | Escolher produto -> Pedir | — | ver acao | `POST /rt/lite/request` | — | **ok** — sem captura de viagem real (nunca confirmar na Uber) | ContractTest |
| `F-trip-02` | trip | Viagem ativa (estado, motorista, PIN) | Polling a 2 s | — | ver acao | `GET /rt/lite/active` | — | **ok** — validado no Honor | ContractTest |
| `F-trip-03` | trip | Cancelar viagem | Cancelar na viagem ativa | — | ver acao | `POST /rt/lite/trips/{uuid}/cancel` | — | **ok** — validado no Honor | ContractTest |
| `F-trip-04` | trip | Avaliar motorista | Estrelas + enviar | — | ver acao | `POST /rt/lite/trips/{uuid}/rate` | — | **ok** — validado no Honor | ContractTest |
| `F-trip-05` | trip | Detalhe/recibo da viagem | Abrir viagem do historico | — | ver acao | `GET /rt/lite/trips/{uuid}` | — | **ok** — sem captura | ContractTest |
| `F-account-02` | account | Editar nome e e-mail | Guardar no perfil | — | ver acao | `PATCH /rt/lite/account` | — | **ok** — designed (sem captura da Lite) | ContractTest |
| `F-account-03` | account | Guardar casa | Escolher casa | — | ver acao | `POST /rt/lite/account/home` | — | **ok** — designed | ContractTest |
| `F-account-04` | account | Terminar sessao | Sair | — | ver acao | `POST /rt/identity/logout` | — | **ok** — — | ContractTest |
| `F-home-06` | home | Localizacao atual (GPS) | Permitir + enviar | — | ver acao | `POST /rt/lite/location` | — | **ok** — validado no Honor | MapCameraTest |
| `F-home-07` | home | Zoom do mapa | Botoes +/- | — | ver acao | `—` | — | **ok** — MapCamera 1.0-2.2 | MapCameraTest |
| `F-promotions-02` | promotions | Aplicar codigo promocional | Introduzir + aplicar | — | ver acao | `POST /rt/lite/promotions/apply` | — | **ok** — — | ContractTest |
| `F-payment-01` | payment | Escolher forma de pagamento | Escolher perfil | — | ver acao | `POST /rt/lite/payments/select` | — | **ok** — — | ContractTest |
| `F-platform-01` | platform | Push do sistema (FCM) | receiver `com.google.android.c2dm` + POST_NOTIFICATIONS | — | background / automatico | `—` | — | **em falta** — notificacoes do sistema nao configuradas | — |
| `F-platform-02` | platform | Deep links (21 filtros) | 21 filtros no manifest | — | background / automatico | `—` | — | **em falta** — so o arranque e tratado | — |
| `F-platform-03` | platform | Biometria | `USE_BIOMETRIC`, `USE_FINGERPRINT` | — | background / automatico | `—` | — | **em falta** — login por telefone apenas | — |
| `F-platform-04` | platform | Idiomas (values-ar/en/es/fr/hi/pt) | 7 ficheiros de idioma | — | background / automatico | `—` | — | **em falta** — app so em pt-PT | — |
| `F-platform-05` | platform | Dark mode | `values-night`, `color-night`, `drawable-night` | — | background / automatico | `—` | — | **em falta** — so tema claro | — |
| `F-platform-06` | platform | Contactos (partilha) | `READ_CONTACTS` | — | background / automatico | `—` | — | **em falta** — partilha nao implementada | — |
| `F-platform-07` | platform | Camera / fotos (chat) | `CAMERA`, `chat_ui_photo_disclaimer` | — | background / automatico | `—` | — | **em falta** — chat nao existe na Rider | — |
| `F-offline-04` | offline | Fila de retry offline | `NetworkMonitor` + estados | — | background / automatico | `—` | — | **ok** — banner + retry | ContractTest |
| `F-notifications-01` | notifications | Notificacoes in-app (badge) | `POST_NOTIFICATIONS` | — | background / automatico | `—` | — | **em falta** — badge no menu ausente | — |

---

## 3. Cobertura mínima (§4.7.3)

### 3.1 Strings classificadas

Fonte: `spec_src/decoded_res/base/res/values-pt/strings.xml` — **2807 strings**.
(A Lite usa pt-BR nas strings; a app nova usa pt-PT escrito por nós.)

| Classe | Strings |
|---|---|
| `orfa` | 1185 |
| `atribuida` | 1161 |
| `support` | 310 |
| `platform` | 141 |
| `deprecated` | 8 |
| `error` | 2 |
| **Total** | **2807** |

| Domínio (atribuídas) | Strings |
|---|---|
| `home` | 289 |
| `account` | 263 |
| `finance` | 182 |
| `promotions` | 121 |
| `support` | 114 |
| `trip` | 93 |
| `notifications` | 73 |
| `safety` | 14 |
| `legal` | 12 |

### 3.2 Endpoints

Contrato implementado: **15 endpoints** em
`ANDOIRD/USER_LITE/endpoints.json` (`designed`, porque o original é WebView).

### 3.3 Manifest → feature ou `platform`

| Componente | Quantidade |
|---|---|
| Permissões | 31 |
| Activities | 19 |
| Services | 17 |
| Receivers | 22 |
| Providers | 10 |
| Deep links | 21 |
| Layouts descodificados | 618 |

### 3.4 Features sem ecrã

- `F-auth-01` **Login por telefone** — `ok`
- `F-auth-02` **Verificacao por codigo SMS** — `ok`
- `F-trip-01` **Pedir viagem** — `ok`
- `F-trip-02` **Viagem ativa (estado, motorista, PIN)** — `ok`
- `F-trip-03` **Cancelar viagem** — `ok`
- `F-trip-04` **Avaliar motorista** — `ok`
- `F-trip-05` **Detalhe/recibo da viagem** — `ok`
- `F-account-02` **Editar nome e e-mail** — `ok`
- `F-account-03` **Guardar casa** — `ok`
- `F-account-04` **Terminar sessao** — `ok`
- `F-home-06` **Localizacao atual (GPS)** — `ok`
- `F-home-07` **Zoom do mapa** — `ok`
- `F-promotions-02` **Aplicar codigo promocional** — `ok`
- `F-payment-01` **Escolher forma de pagamento** — `ok`
- `F-platform-01` **Push do sistema (FCM)** — `em falta`
- `F-platform-02` **Deep links (21 filtros)** — `em falta`
- `F-platform-03` **Biometria** — `em falta`
- `F-platform-04` **Idiomas (values-ar/en/es/fr/hi/pt)** — `em falta`
- `F-platform-05` **Dark mode** — `em falta`
- `F-platform-06` **Contactos (partilha)** — `em falta`
- `F-platform-07` **Camera / fotos (chat)** — `em falta`
- `F-offline-04` **Fila de retry offline** — `ok`
- `F-notifications-01` **Notificacoes in-app (badge)** — `em falta`

### 3.5 Verticais no binário, fora do ecossistema Qolari

| Vertical | Strings | Amostra |
|---|---|---|
| eats / entregas | 63 | `checkout_profile_allowance_spend_per_day_balance_eats`, `checkout_profile_allowance_spend_per_month_balance_eats`, `checkout_profile_allowance_spend_per_trip_balance_eats` |
| vouchers / gift cards | 152 | `eats_voucher_error_modal_invalid_with_bundled_order`, `eats_voucher_error_modal_invalid_with_flex_card`, `eats_voucher_error_modal_invalid_with_meal_voucher_title` |
| Uber for Business / delegados | 154 | `business_hub_add_another_business_profile`, `create_new_business_profile_button`, `create_profile_flow_expense_title_v2` |
| verificacao de identidade (selfie, barcode, CPF) | 214 | `barcode_drivers_license_flow_selector_title`, `barcode_scan_camera_control_help_modal_illustration_title`, `barcode_scan_camera_control_help_modal_subtitle` |
| banco / cartoes / checkout | 153 | `bank_card_error_enter_first_6_digits`, `brazil_credit_debit_card`, `bug_reporter_issue_screenshot_discard` |
| video / audio / exo | 113 | `bug_reporter_fab_trigger_options_video`, `bug_reporter_fab_video_coming_soon`, `bug_reporter_fab_video_thanks` |
| bug reporter (interno) | 120 | `bug_reporter_add_more_files_button`, `bug_reporter_close_button_text`, `bug_reporter_default_report_title` |
| comutadores / UberPool | 66 | `barcode_scan_usnap_camera_control_error_text`, `barcode_scan_usnap_camera_control_success_text`, `commuter_benefits_info` |
| **Total** | **1035** | |

**Como ficam:** `em falta`. Não há aprovação escrita para as excluir. São
decisão de âmbito do cliente (`backlog.md` G-07), não trabalho do agente.

---

## 4. Gate da FASE 4.7

- [x] `features.md` gerado a partir do binário + capturas
- [x] Todas as 29 capturas base têm linha
- [x] Strings classificadas
- [x] Manifest classificado
- [x] Features sem ecrã presentes
- [ ] `em falta` resolvidos — **8 em falta**

**Veredicto:** aberto — 44 `ok`, 8 `em falta`.

---

## 5. Diferença face à Driver

| Aspeto | Driver | Rider (Lite) |
|---|---|---|
| Original | app nativa (Views + Compose) | **WebView** |
| Contrato | `discovered` 1 104 + `contract` 39 | **`designed`** 16 (não existe nativo) |
| Capturas | 109 base | 29 base |
| Layouts | 2 693 | 618 |
| Testes | 74 | 10 (2 ficheiros) |
| `features.md` | 86 features | 52 features |

A consequência prática: na Driver a evidência da UI é `live` + `static`;
na Rider é `live` na UI e **`designed`** no contrato. Nunca se promove
`designed` a `served` sem o servidor confirmar.


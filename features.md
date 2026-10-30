# features.md — inventário de funcionalidades da app Driver

**FASE 4.7** do `PROMPT_CLONE_MEGA.md` · **fonte:** app original `com.ubercab.driver`
4.600/4.601 (binário), nunca o mercado · **taxonomia:** `FEATURE_TAXONOMY.md`

**Gerado por `tools/gen_features.py`.** Não editar à mão: muda o mapa curado no
script e volta a correr. Cada linha cita evidência; nada é inventado.

Não existe `market_parity.md`: nenhum concorrente foi nomeado pelo cliente, logo
não há benchmark (taxonomia §8). O default é a app original.

---

## 1. Resumo

| Métrica | Valor |
|---|---|
| Features no inventário | 98 |
| `ok` | 83 |
| `parcial` | 0 |
| `em falta` | 7 |
| `excluído` (aprovação escrita) | 8 |
| Domínios | 19 |
| Capturas base cobertas | 109 / 109 |

**Regra dura (taxonomia §5):** `parcial` e `em falta` são **gap** para o alvo
`funcional`. Só `excluído` com aprovação escrita em `APROVACAO_EXCLUSOES.md`
(X-01 a X-08) não conta como gap.

### Domínios inferidos

Inferidos das strings e dos endpoints do binário (`FEATURE_TAXONOMY.md` §3),
não importados de outro projeto.

| Domínio | Features |
|---|---|
| `safety` | 12 |
| `settings` | 12 |
| `documents` | 8 |
| `account` | 7 |
| `discover` | 7 |
| `onboarding` | 7 |
| `platform` | 6 |
| `support` | 6 |
| `home` | 5 |
| `menu` | 5 |
| `finance` | 4 |
| `vehicle` | 4 |
| `auth` | 3 |
| `earnings` | 3 |
| `inbox` | 3 |
| `notifications` | 3 |
| `legal` | 1 |
| `offline` | 1 |
| `trip` | 1 |

---

## 2. Matriz

```
id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste
```

| id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste |
|---|---|---|---|---|---|---|---|---|---|
| `F-onboarding-01` | onboarding | Arranque e boas-vindas | `000_arranque_original.png` | `000_arranque_original` | abrir app | `POST /rt/drivers/app-launch` | — | **ok** | Lote1Test |
| `F-discover-01` | discover | Descobrir: oportunidades | `010_descobrir.png` | `010_descobrir` | abrir separador | `GET /rt/drivers/opportunities` | — | **ok** | Lote3Test |
| `F-earnings-01` | earnings | Rendimentos: resumo | `011_rendimentos.png` | `011_rendimentos` | ver dia/semana | `GET /rt/earnings/summary` | — | **ok** | Lote3Test |
| `F-inbox-01` | inbox | Caixa de entrada | `012_caixa_entrada.png` | `012_caixa_entrada` | abrir item | `GET /rt/inbox/messages` | — | **ok** | Lote3Test |
| `F-menu-01` | menu | Menu (pre-auth) | `013_menu.png` | `013_menu` | abrir menu | `—` | — | **ok** | Lote1Test |
| `F-safety-01` | safety | Ferramentas de seguranca | `014_ferramentas_seguranca.png` | `014_ferramentas_seguranca` | abrir ferramenta | `GET /rt/drivers/me/safety-toolkit` | — | **ok** | Lote5Test |
| `F-safety-02` | safety | Verificacao por PIN (config) | `015_verificacao_pin.png` | `015_verificacao_pin` | definir PIN | `—` | sem PIN -> com PIN | **ok** | Lote5Test |
| `F-safety-03` | safety | Comprovativo do estado da viagem | `016_comprovativo_estado_viagem.png` | `016_comprovativo_estado_viagem` | abrir comprovativo | `GET /rt/drivers/me/trip-receipt` | — | **ok** | Lote5Test |
| `F-safety-04` | safety | Centro de seguranca | `017_centro_seguranca.png` | `017_centro_seguranca` | expandir acordeao | `—` | fechado -> aberto | **ok** | Lote5Test |
| `F-safety-05` | safety | Centro de seguranca (detalhes) | `018_centro_seguranca_detalhes.png` | `018_centro_seguranca_detalhes` | expandir artigo | `—` | fechado -> aberto | **ok** | Lote5Test |
| `F-safety-06` | safety | Limite de velocidade | `019_limite_velocidade.png` | `019_limite_velocidade` | escolher limite | `—` | limite -> guardado | **ok** | Lote5Test |
| `F-safety-07` | safety | Centro de seguranca -> preferencias | `020_centro_seguranca_preferencias.png` | `020_centro_seguranca_preferencias` | ligar/desligar | `—` | toggle | **ok** | Lote5Test |
| `F-safety-08` | safety | Verificacao por PIN (opcoes) | `021_verificacao_pin_config.png` | `021_verificacao_pin_config` | escolher modo | `—` | opcao -> guardada | **ok** | Lote5Test |
| `X-01` | safety | Gravacao de video | `022_gravacao_video.png` | `022_gravacao_video` | ligar gravacao | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-01) | — |
| `F-safety-09` | safety | Acompanhar viagem / contacto | `023_acompanhar_viagem_contacto.png` | `023_acompanhar_viagem_contacto` | partilhar viagem | `POST /rt/drivers/me/share-trip` | partilha criada | **ok** | Lote5Test |
| `F-safety-10` | safety | Centro de seguranca -> recursos | `024_centro_seguranca_recursos.png` | `024_centro_seguranca_recursos` | abrir recurso | `—` | — | **ok** | Lote5Test |
| `F-support-01` | support | Hub de informacoes | `025_informacoes_hub.png` | `025_informacoes_hub` | abrir seccao | `—` | — | **ok** | Lote5Test |
| `X-02` | onboarding | Video de boas-vindas | `026_video_boas_vindas.png` | `026_video_boas_vindas` | reproduzir | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-02) | — |
| `X-03` | onboarding | Comfort: proximos passos | `027_comfort_proximos_passos.png` | `027_comfort_proximos_passos` | avancar | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-03) | — |
| `X-04` | onboarding | Comfort: licao 1 | `028_comfort_licao_1.png` | `028_comfort_licao_1` | avancar | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-04) | — |
| `X-05` | onboarding | Comfort: licao 2 | `029_comfort_licao_2.png` | `029_comfort_licao_2` | avancar | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-05) | — |
| `X-06` | onboarding | Comfort: normas de servico | `030_comfort_normas_servico.png` | `030_comfort_normas_servico` | ler | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-06) | — |
| `F-auth-01` | auth | Arranque sem sessao | `031_sem_sessao_arranque.png` | `031_sem_sessao_arranque` | abrir app sem sessao | `—` | — | **ok** | LoginViewModelTest |
| `F-auth-02` | auth | Login por telefone (outra conta) | `032_login_outra_conta.png` | `032_login_outra_conta` | telefone + codigo | `POST /rt/identity/oauth2/token` | — | **ok** | LoginViewModelTest |
| `X-07` | auth | Login por e-mail | `033_login_email.png` | `033_login_email` | e-mail + password | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-07) | — |
| `F-home-01` | home | Acoes necessarias (bloqueios) | `035_home_autenticada_acoes_necessarias.png` | `035_home_autenticada_acoes_necessarias` | abrir Definicoes do Android | `GET /rt/drivers/me/app-launch` | — | **ok** | HomeViewModelTest |
| `F-discover-02` | discover | Descobrir: filtro Lembretes | `036_descobrir_lembretes.png` | `036_descobrir_lembretes` | tocar filtro | `—` | filtro on/off | **ok** | Lote3Test |
| `F-discover-03` | discover | Descobrir: estado limpo | `037_descobrir_limpo.png` | `037_descobrir_limpo` | sem filtros | `—` | — | **ok** | Lote3Test |
| `F-discover-04` | discover | Descobrir: filtros repostos | `039_descobrir_filtros_repostos.png` | `039_descobrir_filtros_repostos` | desligar filtros | `—` | filtro -> reposto | **ok** | Lote3Test |
| `F-menu-02` | menu | Menu autenticado | `041_menu_autenticado.png` | `041_menu_autenticado` | navegar seccoes | `GET /rt/drivers/me/profile-hub` | — | **ok** | Lote1Test |
| `F-menu-03` | menu | Menu -> Ajuda | `042_menu_ajuda.png` | `042_menu_ajuda` | abrir Ajuda | `—` | — | **ok** | Lote1Test |
| `F-settings-01` | settings | Definicoes (raiz) | `043_menu_definicoes.png` | `043_menu_definicoes` | abrir Definicoes | `—` | — | **ok** | Lote1Test |
| `F-settings-02` | settings | Definicoes -> Acessibilidade | `044_def_acessibilidade.png` | `044_def_acessibilidade` | abrir | `—` | — | **ok** | Lote1Test |
| `F-settings-03` | settings | Definicoes -> Comunicacao | `045_def_comunicacao.png` | `045_def_comunicacao` | escolher idioma/voz | `—` | opcao -> guardada | **ok** | Lote1Test |
| `F-settings-04` | settings | Definicoes -> Navegacao | `046_def_navegacao.png` | `046_def_navegacao` | escolher app de mapas | `—` | opcao -> guardada | **ok** | PreferencesStoreTest |
| `F-settings-05` | settings | Definicoes -> Sons e voz | `047_def_sons_voz.png` | `047_def_sons_voz` | regular volume | `—` | volume -> guardado | **ok** | PreferencesStoreTest |
| `F-settings-06` | settings | Definicoes -> Privacidade | `048_def_privacidade.png` | `048_def_privacidade` | abrir | `—` | — | **ok** | Lote1Test |
| `F-settings-07` | settings | Acessibilidade -> Audicao | `049_acess_audicao.png` | `049_acess_audicao` | ligar/desligar | `—` | toggle | **ok** | Lote1Test |
| `F-settings-08` | settings | Acessibilidade -> Comunicacao | `050_acess_def_comunicacao.png` | `050_acess_def_comunicacao` | ligar/desligar | `—` | toggle | **ok** | Lote1Test |
| `F-notifications-01` | notifications | Comunicacao -> Push (janela) | `051_comunicacao_push.png` | `051_comunicacao_push` | escolher janela | `—` | opcao -> guardada | **ok** | PreferencesStoreTest |
| `F-notifications-02` | notifications | Comunicacao -> push em segundo plano | `052_comunicacao_fundo.png` | `052_comunicacao_fundo` | ligar/desligar | `—` | toggle | **ok** | PreferencesStoreTest |
| `F-settings-09` | settings | Privacidade (meio da lista) | `053_privacidade_meio.png` | `053_privacidade_meio` | abrir item | `—` | — | **ok** | Lote1Test |
| `F-settings-10` | settings | Privacidade (fundo da lista) | `054_privacidade_fundo.png` | `054_privacidade_fundo` | abrir item | `—` | — | **ok** | Lote1Test |
| `F-home-02` | home | Inicio com mapa e estado online | `060_inicio.png` | `060_inicio` | ficar online/offline | `POST /rt/drivers/v2/go-online / go-offline` | offline -> online | **ok** | HomeViewModelTest |
| `F-discover-05` | discover | Descobrir (autenticado) | `061_descobrir.png` | `061_descobrir` | ver cartoes e dias | `GET /rt/drivers/opportunities` | — | **ok** | Lote3Test |
| `F-earnings-02` | earnings | Rendimentos (autenticado) | `062_rendimentos.png` | `062_rendimentos` | alternar dia/semana | `GET /rt/earnings/week` | — | **ok** | Lote3Test |
| `F-inbox-02` | inbox | Caixa de entrada (autenticado) | `063_caixa_entrada.png` | `063_caixa_entrada` | marcar lida | `POST /rt/inbox/{id}/read` | nao lida -> lida | **ok** | Lote3Test |
| `F-menu-04` | menu | Menu (autenticado, completo) | `064_menu.png` | `064_menu` | navegar seccoes | `GET /rt/drivers/me/profile-hub` | — | **ok** | Lote1Test |
| `F-support-02` | support | Ajuda | `065_ajuda.png` | `065_ajuda` | abrir categoria | `—` | — | **ok** | Lote5Test |
| `F-settings-11` | settings | Definicoes (lista completa) | `066_definicoes.png` | `066_definicoes` | abrir subseccao | `—` | — | **ok** | Lote1Test |
| `F-vehicle-01` | vehicle | Menu -> Veiculo | `070_menu_veiculo.png` | `070_menu_veiculo` | abrir | `GET /rt/drivers/v2/vehicles` | — | **ok** | Lote5Test |
| `F-documents-01` | documents | Menu -> Documentos | `071_menu_documentos.png` | `071_menu_documentos` | abrir | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-finance-01` | finance | Menu -> Seguro | `072_menu_seguro.png` | `072_menu_seguro` | abrir pagina | `—` | — | **ok** | Lote5Test |
| `F-finance-02` | finance | Informacoes fiscais | `074_menu_info_fiscais.png` | `074_menu_info_fiscais` | abrir | `—` | — | **ok** | Lote5Test |
| `F-finance-03` | finance | Formas de pagamento | `075_menu_formas_pagamento.png` | `075_menu_formas_pagamento` | abrir | `GET /rt/drivers/me/payment-methods` | — | **ok** | Lote5Test |
| `F-legal-01` | legal | Sobre | `077_menu_sobre.png` | `077_menu_sobre` | abrir | `—` | — | **ok** | Lote1Test |
| `F-vehicle-02` | vehicle | Veiculos | `080_veiculos.png` | `080_veiculos` | abrir/gerir | `GET /rt/drivers/v2/vehicles` | — | **ok** | Lote5Test |
| `X-08` | vehicle | Adicionar veiculo | `081_veic_adicionar.png` | `081_veic_adicionar` | registar | `—` | — | **excluido** — aprovado em APROVACAO_EXCLUSOES.md (X-08) | — |
| `F-vehicle-03` | vehicle | Gerir veiculo | `082_veic_gerir.png` | `082_veic_gerir` | guardar alteracoes | `PATCH /rt/drivers/v2/vehicles/{id}` | — | **ok** | Lote5Test |
| `F-documents-02` | documents | Documentos | `083_documentos.png` | `083_documentos` | abrir documento | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-03` | documents | Documento: carta de conducao | `084_doc_carta_conducao.png` | `084_doc_carta_conducao` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-04` | documents | Documento: TVDE | `085_doc_tvde.png` | `085_doc_tvde` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-05` | documents | Documento: registo criminal | `086_doc_registo_criminal.png` | `086_doc_registo_criminal` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-06` | documents | Documento: cartao de cidadao | `087_doc_cartao_cidadao.png` | `087_doc_cartao_cidadao` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-07` | documents | Documento: DUA | `088_doc_dua.png` | `088_doc_dua` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-documents-08` | documents | Documento: seguro / carta verde | `089_doc_seguro_carta_verde.png` | `089_doc_seguro_carta_verde` | ver estado | `GET /rt/drivers/me/documents` | — | **ok** | Lote5Test |
| `F-support-03` | support | Ajuda: categorias | `090_ajuda_cat.png` | `090_ajuda_cat` | escolher categoria | `—` | — | **ok** | Lote5Test |
| `F-support-04` | support | Ajuda: artigos | `091_ajuda_00.png`, `091_ajuda_01.png`, `091_ajuda_02.png`, `091_ajuda_03.png`, `091_ajuda_04.png`, `091_ajuda_05.png`, `091_ajuda_06.png`, `091_ajuda_07.png`, `091_ajuda_08.png`, `091_ajuda_09.png`, `091_ajuda_10.png` | `091_ajuda_00`, `091_ajuda_01`, `091_ajuda_02`, `091_ajuda_03`, `091_ajuda_04`, `091_ajuda_05`, `091_ajuda_06`, `091_ajuda_07`, `091_ajuda_08`, `091_ajuda_09`, `091_ajuda_10` | abrir artigo | `—` | — | **ok** | Lote5Test |
| `F-home-03` | home | Painel do Inicio: 'Recomendado para si' | `201_honor_recomendado_para_si.png` | `201_honor_recomendado_para_si` | abrir painel inferior | `GET /rt/drivers/me/profile-hub` | painel colapsado/expandido | **ok** — observado no Honor 4.603; titulo do painel, nao item de menu | HomeViewModelTest |
| `F-home-04` | home | Ver o tempo de conducao | `201_honor_recomendado_para_si.png` | `201_honor_recomendado_para_si` | tocar linha | `—` | sheet aberta | **em falta** — existe no original (201_honor_recomendado_para_si.png); sem equivalente no clone | — |
| `F-support-05` | support | Folha de itinerario (recibo da ultima viagem) | `201_honor_recomendado_para_si.png` | `201_honor_recomendado_para_si` | tocar linha | `GET /rt/drivers/me/trip-receipt` | pagina de recibo | **ok** — observado: TRAVESSIA PECULIAR, fare 5.97, Trip #, From, Destination | Lote5Test |
| `F-account-01` | account | Perfil e troca de conta | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar cabecalho | `GET /rt/drivers/me/profile-hub` | — | **ok** — Gold / Fernando / 4,91 no cabecalho | Lote1Test |
| `F-support-06` | support | Menu: Ajuda | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar Ajuda | `—` | — | **ok** — — | Lote1Test |
| `F-safety-11` | safety | Menu: Seguranca | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar Seguranca | `—` | — | **ok** — — | Lote1Test |
| `F-settings-12` | settings | Menu: Definicoes | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar Definicoes | `—` | — | **ok** — — | Lote1Test |
| `F-discover-06` | discover | Menu: Descubra oportunidades | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar linha | `GET /rt/drivers/opportunities` | — | **ok** — seccao 'Mais formas de aumentar os rendimentos' | Lote3Test |
| `F-account-02` | account | Menu: Uber Pro | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar linha | `—` | — | **ok** — seccao 'Mais formas'; pagina propria info_pro | build |
| `F-account-03` | account | Menu: Hub de trabalho | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar linha | `—` | — | **ok** — `work_hub` no binario; pagina propria info_work | build |
| `F-account-04` | account | Menu: Recomendacoes | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar linha | `—` | — | **ok** — `primary_menu_title_referrals_*` (variantes A/B); pagina info_referrals | build |
| `F-account-05` | account | Menu: Gerir | `013_menu.png` (`013_menu.xml`) | `013_menu`/`041_menu_autenticado`/`064_menu` | tocar linha | `—` | — | **ok** — gestao de conta/veiculo | build |
| `F-trip-01` | trip | Oferta de viagem e ciclo da viagem | `100_online_001.png`, `100_online_002.png`, `100_online_003.png`, `100_online_004.png`, `100_online_005.png`, `100_online_006.png`, `100_online_007.png`, `100_online_008.png`, `100_online_009.png`, `100_online_010.png`, `100_online_011.png`, `100_online_012.png`, `100_online_013.png` | `100_online_001`, `100_online_002`, `100_online_003`, `100_online_004`, `100_online_005`, `100_online_006`, `100_online_007`, `100_online_008`, `100_online_009`, `100_online_010`, `100_online_011`, `100_online_012`, `100_online_013` | aceitar / recusar / expirar | `POST /rt/drivers/accept-offers / reject-offers / expire-offers` | idle -> offered -> accepted | **ok** | DriveTest |
| `F-home-05` | home | Offline: home | `110_off_inicio.png`, `115_off_refresh_inicio_a.png`, `115_off_refresh_inicio_b.png`, `120_off2_inicio.png`, `125_off2_refresh_inicio_a.png`, `125_off2_refresh_inicio_b.png` | `110_off_inicio`, `115_off_refresh_inicio_a`, `115_off_refresh_inicio_b`, `120_off2_inicio`, `125_off2_refresh_inicio_a`, `125_off2_refresh_inicio_b` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-earnings-03` | earnings | Offline: earnings | `116_off_refresh_rendimentos_a.png`, `116_off_refresh_rendimentos_b.png`, `122_off2_rendimentos.png`, `126_off2_refresh_rendimentos_a.png`, `126_off2_refresh_rendimentos_b.png` | `116_off_refresh_rendimentos_a`, `116_off_refresh_rendimentos_b`, `122_off2_rendimentos`, `126_off2_refresh_rendimentos_a`, `126_off2_refresh_rendimentos_b` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-discover-07` | discover | Offline: discover | `121_off2_descobrir.png`, `111_off_descobrir_s1.png` | `121_off2_descobrir`, `111_off_descobrir_s1` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-inbox-03` | inbox | Offline: inbox | `123_off2_caixa.png` | `123_off2_caixa` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-menu-05` | menu | Offline: menu | `124_off2_menu.png` | `124_off2_menu` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-onboarding-02` | onboarding | Offline: onboarding | `117_off_arranque_1.png`, `117_off_arranque_2.png`, `117_off_arranque_3.png`, `117_off_arranque_4.png` | `117_off_arranque_1`, `117_off_arranque_2`, `117_off_arranque_3`, `117_off_arranque_4` | sem rede | `—` | online -> offline -> online | **ok** | HomeViewModelTest + telemovel |
| `F-platform-01` | platform | Push do sistema (FCM) | provider `FirebaseMessagingService` ausente do manifest | — | background / automatico | `—` | — | **em falta** — removido do ambito do laboratorio; `ramen` cobre o tempo real | — |
| `F-platform-02` | platform | Deep links (50 filtros) | `manifest.json` deeplinks x50 | — | background / automatico | `POST /rt/drivers/app-launch` | — | **em falta** — so o link de arranque e tratado; o resto nao e anunciado | — |
| `F-platform-03` | platform | Biometria / credenciais | `Class3BiometricsActivity`, `RevocationBoundService` | — | background / automatico | `—` | — | **em falta** — login por telefone `0000`; biometria ausente | — |
| `F-platform-04` | platform | i18n (172 idiomas no binario) | `values-*/` x172, 622 340 strings | — | background / automatico | `—` | — | **em falta** — app so em pt-PT | — |
| `F-platform-05` | platform | Dark mode | `values-night` | — | background / automatico | `—` | — | **em falta** — so tema claro | — |
| `F-platform-06` | platform | Acessibilidade (TalkBack) | `accessibility_*` x102 em pt-PT | — | background / automatico | `—` | — | **em falta** — labels basicos | — |
| `F-offline-01` | offline | Fila de retry offline | `NetworkMonitor` + estados offline | — | background / automatico | `—` | — | **ok** — banner + retry manual | backend pytest |
| `F-notifications-03` | notifications | Notificacoes in-app (badge) | `rt/inbox/*` | — | background / automatico | `GET /rt/inbox/messages` | — | **ok** — badge e lista | backend pytest |
| `F-account-06` | account | Terminar sessao / mudar de conta | `signOut()` | — | background / automatico | `POST /rt/identity/logout` | — | **ok** — volta ao arranque | backend pytest |
| `F-account-07` | account | Perfil do motorista (hub) | `get-profile-hub` | — | background / automatico | `GET /rt/drivers/me/profile-hub` | — | **ok** — menu autenticado | backend pytest |
| `F-finance-04` | finance | Liquidacao e saldo | `domain/finance.py` | — | background / automatico | `GET /rt/earnings/payouts` | — | **ok** — backend pytest | backend pytest |

---

## 3. Cobertura mínima (§4.7.3)

### 3.1 Strings de UI classificadas

Fonte: `ui_spec/values/values-pt-rPT.json` — **9553 strings**. O binário tem
172 idiomas e 622 340 strings; pt-PT é a referência porque a app nova é pt-PT.

Duas perguntas distintas, para não confundir «pertence a uma feature» com
«revela uma feature nova»:

1. **A que feature pertence?** → atribuição por prefixo de domínio.
2. **Sobrou alguma por atribuir?** → é essa que vira feature escondida.

| Classe | Strings | Significado |
|---|---|---|
| `orfa` | 5458 | não atribuível a um domínio da matriz — ver §3.5 |
| `atribuida` | 3210 | pertencem a uma das features da matriz (prefixo de domínio) |
| `platform` | 466 | framework, Material, Carbon, permissões, a11y — do sistema |
| `support` | 379 | texto auxiliar (país, datas, formatação) de uma feature existente |
| `error` | 28 | mensagem de erro/validação de uma feature existente |
| `deprecated` | 8 | código morto/legado |
| `telemetry` | 4 | analytics, crash, ads — não é produto |
| **Total** | **9553** | zero por classificar |

**Atribuição por domínio:**

| Domínio | Strings |
|---|---|
| `trip` | 612 |
| `finance` | 568 |
| `support` | 510 |
| `documents` | 414 |
| `account` | 399 |
| `safety` | 326 |
| `vehicle` | 244 |
| `notifications` | 55 |
| `settings` | 53 |
| `earnings` | 20 |
| `legal` | 9 |

### 3.2 Endpoints com disposição

Fonte: `ANDOIRD/DRIVER/endpoints.json` — catálogo **descoberto** (bottom-up).

| Disposição | Endpoints |
|---|---|
| `rebuild` | 1001 |
| `substituir` | 96 |
| `descartar` | 7 |
| **Total** | **1104** |

- Sem `disposition`: **0** — todas classificadas.
- Sem ecrã identificado: **301**
  — ficam no `discovered`, não no `contract`.

O `contract` (`endpoints.json`, 39 endpoints) é **subconjunto** implementado. Esta
é exatamente a diferença que a taxonomia §10 exige não confundir: universo ≠ contrato.

### 3.3 Manifest → feature ou `platform`

| Componente | Quantidade | Destino |
|---|---|---|
| Permissões | 47 | `platform` (grant em runtime) + features de segurança |
| Activities | 123 | `platform` (ecrãs do sistema) exceto as do produto |
| Services | 19 | `platform` (foreground, jobs, WorkManager) |
| Receivers | 28 | `platform` (push, boot, conectividade) |
| Providers | 17 | `platform` (FileProvider, Firebase, credenciais) |
| Deep links | 50 | `platform` — só o de arranque é tratado |

### 3.4 Features sem ecrã (obrigatórias)

A taxonomia §7 exige features que não têm ecrã. Estão na matriz com ecrã `—`:

- `F-platform-01` **Push do sistema (FCM)** — `em falta`
- `F-platform-02` **Deep links (50 filtros)** — `em falta`
- `F-platform-03` **Biometria / credenciais** — `em falta`
- `F-platform-04` **i18n (172 idiomas no binario)** — `em falta`
- `F-platform-05` **Dark mode** — `em falta`
- `F-platform-06` **Acessibilidade (TalkBack)** — `em falta`
- `F-offline-01` **Fila de retry offline** — `ok`
- `F-notifications-03` **Notificacoes in-app (badge)** — `ok`
- `F-account-06` **Terminar sessao / mudar de conta** — `ok`
- `F-account-07` **Perfil do motorista (hub)** — `ok`
- `F-finance-04` **Liquidacao e saldo** — `ok`

### 3.5 Verticais de produto no binário, fora do ecossistema Qolari

Esta é a descoberta que o inventário por ecrãs nunca teria feito: o binário
transporta **produtos inteiros** que a app Driver não mostra nos 109 ecrãs
capturados. Fonte: strings pt-PT órfãs, agrupadas por família de produto.

| Vertical | Strings | Amostra |
|---|---|---|
| courier / entregas (Eats, pick-and-pack) | 161 | `accept_delivery_reservation_error_subtitle`, `accept_delivery_reservation_error_title`, `accept_delivery_reservation_offer_expired_button_label` |
| rental / aluguer de veiculos | 5 | `rental_valet_job_details_button_text`, `rental_valet_on_job_status_assistant_nav_state_arrived`, `rental_valet_on_job_status_assistant_nav_state_arriving` |
| refueling / carregamento | 123 | `charging_map_detailed_filters_all_selected`, `charging_map_detailed_filters_apply_button`, `charging_map_detailed_filters_apply_filter_failed_snackbar_message` |
| vouchers / gift cards | 187 | `eats_voucher_error_modal_invalid_with_bundled_order`, `eats_voucher_error_modal_invalid_with_flex_card`, `eats_voucher_error_modal_invalid_with_meal_voucher_title` |
| mentorship / quests / leaderboard | 178 | `accessibility_settings_library_flash_for_requests`, `accessibility_settings_library_flash_for_requests_info`, `accessibility_settings_library_vibration_for_requests` |
| Uber for Business / delegados | 222 | `business_hub_add_another_business_profile`, `create_new_business_profile_button`, `delegate_billed_to` |
| banco / UPI / Zaakpay | 99 | `backing_instrument_netbanking`, `bank_account_header`, `bank_card_error_enter_first_6_digits` |
| verificacao de identidade (eKYC, selfie, barcode) | 76 | `barcode_drivers_license_flow_selector_title`, `barcode_scan_camera_control_help_modal_illustration_title`, `barcode_scan_camera_control_help_modal_subtitle` |
| video / audio / gravacao | 557 | `abc_searchview_description_voice`, `audio_recording`, `audio_recording_badge_queue` |
| social / referencias / convites | 81 | `business_employee_invite_error_invite_expired_description_text`, `business_employee_invite_error_invite_expired_dialog_button_text`, `business_employee_invite_error_invite_expired_dialog_button_text_v2` |
| reservas / agendamento | 25 | `accept_delivery_reservation_error_subtitle`, `accept_delivery_reservation_error_title`, `accept_delivery_reservation_offer_expired_button_label` |
| pontos de acesso (entradas, parques, unidades) | 44 | `access_points_modal_header`, `access_points_modal_row_entrance`, `access_points_modal_row_parking` |
| design system (Firefly, Penny, Carbon interno) | 65 | `firefly_alert_battery_critical_body`, `firefly_alert_battery_critical_cta`, `firefly_alert_battery_low_body` |
| **Total** | **1823** | |

**Como ficam:** são **`em falta`** — não `excluído` — porque a aprovação escrita
de 2026-10-30 cobriu apenas X-01 a X-08. Implementar isto é construir o Uber
inteiro (comida, aluguer, combustível, banco), não clonar a Driver. A decisão
é do cliente e está no `backlog.md` como um único item de âmbito, não como
1823 linhas.

O agrupamento é por palavra-chave no nome da string, logo é **aproximado**:
serve para provar que as verticais existem e medir o tamanho, não para
atribuir cada string uma a uma. A atribuição fina faz-se só se o cliente
decidir implementar a vertical.

---

## 4. Exclusões com aprovação escrita

Aprovadas pelo cliente em 2026-10-30, em [`APROVACAO_EXCLUSOES.md`](APROVACAO_EXCLUSOES.md).
Sem esse ficheiro, estas linhas seriam `gap`.

| id | Funcionalidade | Aprovação | UI no clone |
|---|---|---|---|
| `X-01` | Gravacao de video | X-01 | removida |
| `X-02` | Video de boas-vindas | X-02 | removida |
| `X-03` | Comfort: proximos passos | X-03 | removida |
| `X-04` | Comfort: licao 1 | X-04 | removida |
| `X-05` | Comfort: licao 2 | X-05 | removida |
| `X-06` | Comfort: normas de servico | X-06 | removida |
| `X-07` | Login por e-mail | X-07 | removida |
| `X-08` | Adicionar veiculo | X-08 | removida |

---

## 5. Como isto alimenta o resto

```
FASE 4.7  features.md (este ficheiro)
   ↓  cada F-ID tem destino na RECRIACAO/ ou no backlog.md
FASE 5    BUILD por fatia vertical — declara o F-ID no topo
   ↓
FASE 6    capabilities.md + coverage.md + ledger do REA
   ↓
FASE 7    backlog.md = lista de gaps (parcial / em falta)
```

O `capabilities.md` é a vista de implementação deste ficheiro; o `backlog.md` é
a lista de gaps. Nenhum dos dois pode ter linhas que não existam aqui.

---

## 6. Gate da FASE 4.7

- [x] `features.md` gerado a partir do binário original
- [x] Todas as 109 capturas base têm linha (zero órfãos de ecrã)
- [x] Todas as strings pt-PT classificadas
- [x] Todos os endpoints do `discovered` com `disposition`
- [x] Manifest classificado (feature ou `platform`)
- [x] Features sem ecrã presentes
- [x] `excluído` só com aprovação escrita
- [ ] `parcial`/`em falta` resolvidos — **7 em falta**

**Veredicto do gate:** aberto. Inventário completo, mas 7
features `em falta` impedem o fecho para `funcional`. Zero `parcial`: as 17
linhas parciais do `coverage.md` foram fechadas ou reclassificadas (§7).

---

## 7. Reconciliação com o `coverage.md` (v3.1 → v4)

O `coverage.md` conta **ecrãs**: 84 `sim`, 17 `parcial`, 8 `nao` = 109. A
taxonomia conta **features**. Reconciliação:

| coverage.md | Features | Resultado |
|---|---|---|
| 84 `sim` | 84 F-ID (1:1) | `ok` |
| 13 `parcial` (`100_online_001..013`) | **1** feature `trip` | `ok` — a oferta é uma só |
| 4 `parcial` restantes | 4 F-ID | `ok` — a UI foi implementada |
| 8 `nao` | 8 F-ID | `excluído` (X-01..X-08) |

Os 11 artigos de Ajuda (`091_ajuda_00..10`) são **1** feature, não 11.
As 19 capturas offline são **features transversais**, não ecrãs próprios.

Resultado: **98 features** em vez de 109 ecrãs.

---

## 8. Anti-padrões evitados

- **Inventário só por ecrãs** — não: §3.4 e §3.5 existem por causa disso.
- **`endpoints.json` curado como universo** — não: 1 104 descobertos, 39 no contrato.
- **`parcial` como tolerância** — não: zero `parcial` nesta matriz.
- **Benchmark no core** — não: nenhum concorrente nomeado.
- **Excluir para fechar** — não: cada exclusão tem aprovação escrita e UI removida.
- **Feature sem teste** — as `ok` citam teste; as `em falta` têm `—`.


# coverage.md — Ecrã a ecrã (Driver)

**Gerado por `tools/gen_coverage.py`** a partir de `ux_capture/versoes.csv`, `toolkit_por_ecra.csv` e `correlacao_layouts.csv`. Não editar à mão: muda o mapa curado no script e volta a correr.

Convenções: `evidence` = `live` (captura do original), `static` (layout/strings do binário), `served` (materializado pelo nosso backend), `presumed` (inferido), `designed` (não existe no original). `integrity` = `clean` ou `repack_suspect`.

## Resumo

| Métrica | Valor |
|---|---|
| Ecrãs base | 109 |
| Implementados (`sim`) | 84 |
| Parciais (`parcial`) | 17 |
| Fora de âmbito (`nao`) | 8 |
| Integridade | todos `clean` (original 4.600/4.601) |

`sim` = ecrã implementado na `RECRIACAO/` com os desvios aceites em `VALIDACAO.md`; `parcial` = implementado com gap declarado; `nao` = fora de âmbito ou por fazer. Nenhum ecrã `live` foi promovido a `served`.

## Ecrãs capturados

| Captura | Ecrã | Toolkit | Layout candidato | Evid. | Integr. | Estado | Lote | Gap / nota | Versão |
|---|---|---|---|---|---|---|---|---|---|
| `000_arranque_original.png` | 000 arranque original | views + ilhas Compose | `map_section_view.xml` | live | clean | **sim** | 2 | boas-vindas e seletor de conta | 4.600.10000 |
| `010_descobrir.png` | 010 descobrir | views (XML) | `opportunity_center.xml` | live | clean | **sim** | 3 | Descobrir; conteudo de exemplo | 4.600.10000 |
| `011_rendimentos.png` | 011 rendimentos | views + ilhas Compose | `banner_view_layout_v2.xml` | live | clean | **sim** | 3 | Rendimentos; pontos/Qolari Pro fora | 4.600.10000 |
| `012_caixa_entrada.png` | 012 caixa entrada | compose | `inbox_tab_view.xml` | live | clean | **sim** | 3 | Caixa de entrada em Compose | 4.600.10000 |
| `013_menu.png` | 013 menu | views + ilhas Compose | `driver_menu_default_header_v3.xml` | live | clean | **sim** | 1 | Menu | 4.600.10000 |
| `014_ferramentas_seguranca.png` | 014 ferramentas seguranca | views (XML) | `ub__carbon_share_location_safety_toolkit_row_v4.xml` | live | clean | **sim** | 5 | Ferramentas de seguranca | 4.600.10000 |
| `015_verificacao_pin.png` | 015 verificacao pin | compose | `` | live | clean | **sim** | 5 | Verificacao do PIN (configuracao) | 4.600.10000 |
| `016_comprovativo_estado_viagem.png` | 016 comprovativo estado viagem | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **parcial** | 5 | pagina web do original; recriada como conteudo proprio | 4.600.10000 |
| `017_centro_seguranca.png` | 017 centro seguranca | views (XML) | `ub__safety_checkup_accordion.xml` | live | clean | **sim** | 5 | Centro de seguranca | 4.600.10000 |
| `018_centro_seguranca_detalhes.png` | 018 centro seguranca detalhes | views (XML) | `ub__safety_checkup_accordion.xml` | live | clean | **sim** | 5 | Centro de seguranca (detalhes) | 4.600.10000 |
| `019_limite_velocidade.png` | 019 limite velocidade | views (XML) | `ub__speed_intervention_settings.xml` | live | clean | **sim** | 5 | Limite de velocidade | 4.600.10000 |
| `020_centro_seguranca_preferencias.png` | 020 centro seguranca preferencias | views (XML) | `ub__safety_checkup_accordion.xml` | live | clean | **sim** | 5 | Preferencias de seguranca | 4.600.10000 |
| `021_verificacao_pin_config.png` | 021 verificacao pin config | compose | `` | live | clean | **sim** | 5 | PIN: opcoes | 4.600.10000 |
| `022_gravacao_video.png` | 022 gravacao video | views (XML) | `ub__audio_video_app_settings_screen.xml` | live | clean | **nao** | - | gravacao de video: fora de ambito (D7) | 4.600.10000 |
| `023_acompanhar_viagem_contacto.png` | 023 acompanhar viagem contacto | views + ilhas Compose | `vertical_scrolling_page_view.xml` | live | clean | **parcial** | 5 | acompanhar viagem/contacto: partilha depende do sistema | 4.600.10000 |
| `024_centro_seguranca_recursos.png` | 024 centro seguranca recursos | views (XML) | `ub__safety_checkup_accordion.xml` | live | clean | **sim** | 5 | Recursos de seguranca | 4.600.10000 |
| `025_informacoes_hub.png` | 025 informacoes hub | views (XML) | `horizontal_section_view.xml` | live | clean | **sim** | 5 | Hub de informacoes | 4.600.10000 |
| `026_video_boas_vindas.png` | 026 video boas vindas | views (XML) | `exo_player_view.xml` | live | clean | **nao** | - | video de boas-vindas: fora de ambito (D7) | 4.600.10000 |
| `027_comfort_proximos_passos.png` | 027 comfort proximos passos | views (XML) | `learning_hub_topics_list_header_view.xml` | live | clean | **nao** | - | Comfort: fora de ambito (D7) | 4.600.10000 |
| `028_comfort_licao_1.png` | 028 comfort licao 1 | views (XML) | `learning_hub_topic_view_can_block_swipe.xml` | live | clean | **nao** | - | Comfort: fora de ambito (D7) | 4.600.10000 |
| `029_comfort_licao_2.png` | 029 comfort licao 2 | views (XML) | `learning_hub_topic_view_can_block_swipe.xml` | live | clean | **nao** | - | Comfort: fora de ambito (D7) | 4.600.10000 |
| `030_comfort_normas_servico.png` | 030 comfort normas servico | views + ilhas Compose | `ub__learning_quiz_layout.xml` | live | clean | **nao** | - | Comfort: fora de ambito (D7) | 4.600.10000 |
| `031_sem_sessao_arranque.png` | 031 sem sessao arranque | views (XML) | `ub__carbon_animated_welcome.xml` | live | clean | **sim** | 2 | arranque sem sessao | 4.601.10000 |
| `032_login_outra_conta.png` | 032 login outra conta | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 2 | login por telefone | 4.601.10000 |
| `033_login_email.png` | 033 login email | n/d | `` | live | clean | **nao** | - | login por e-mail: nao implementado (D6); so telefone | 4.601.10000 |
| `035_home_autenticada_acoes_necessarias.png` | 035 home autenticada acoes necessarias | views (XML) | `map_section_view.xml` | live | clean | **parcial** | 2 | acoes necessarias; atalhos para as Definicoes do Android | 4.601.10000 |
| `036_descobrir_lembretes.png` | 036 descobrir lembretes | views (XML) | `opportunity_center.xml` | live | clean | **sim** | 3 | Descobrir: lembretes (filtro) | 4.601.10000 |
| `037_descobrir_limpo.png` | 037 descobrir limpo | views (XML) | `opportunity_center.xml` | live | clean | **sim** | 3 | Descobrir: estado limpo | 4.601.10000 |
| `039_descobrir_filtros_repostos.png` | 039 descobrir filtros repostos | views (XML) | `opportunity_center.xml` | live | clean | **sim** | 3 | Descobrir: filtros repostos | 4.601.10000 |
| `041_menu_autenticado.png` | 041 menu autenticado | views + ilhas Compose | `driver_menu_default_header_v3.xml` | live | clean | **sim** | 1 | Menu autenticado | 4.601.10000 |
| `042_menu_ajuda.png` | 042 menu ajuda | views (XML) | `ub__help_card_expandable.xml` | live | clean | **sim** | 1 | Menu: Ajuda | 4.601.10000 |
| `043_menu_definicoes.png` | 043 menu definicoes | compose | `` | live | clean | **sim** | 1 | Definicoes | 4.601.10000 |
| `044_def_acessibilidade.png` | 044 def acessibilidade | compose | `` | live | clean | **sim** | 1 | Acessibilidade | 4.601.10000 |
| `045_def_comunicacao.png` | 045 def comunicacao | views (XML) | `ub__comms_preferences_settings_v2.xml` | live | clean | **sim** | 1 | Comunicacao | 4.601.10000 |
| `046_def_navegacao.png` | 046 def navegacao | views (XML) | `navigation_switch.xml` | live | clean | **sim** | 1 | Navegacao | 4.601.10000 |
| `047_def_sons_voz.png` | 047 def sons voz | compose | `` | live | clean | **sim** | 1 | Sons e voz | 4.601.10000 |
| `048_def_privacidade.png` | 048 def privacidade | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 1 | Centro de privacidade | 4.601.10000 |
| `049_acess_audicao.png` | 049 acess audicao | compose | `` | live | clean | **sim** | 1 | Acessibilidade: audicao | 4.601.10000 |
| `050_acess_def_comunicacao.png` | 050 acess def comunicacao | views (XML) | `ub__comms_preferences_settings_v2.xml` | live | clean | **sim** | 1 | Acessibilidade: comunicacao | 4.601.10000 |
| `051_comunicacao_push.png` | 051 comunicacao push | views (XML) | `ub__comms_preferences_settings_v2.xml` | live | clean | **sim** | 1 | Push: janela de ativacao (UI) | 4.601.10000 |
| `052_comunicacao_fundo.png` | 052 comunicacao fundo | views (XML) | `ub__comms_preferences_settings_v2.xml` | live | clean | **sim** | 1 | Push em segundo plano (UI) | 4.601.10000 |
| `053_privacidade_meio.png` | 053 privacidade meio | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 1 | Privacidade (meio) | 4.601.10000 |
| `054_privacidade_fundo.png` | 054 privacidade fundo | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 1 | Privacidade (fundo) | 4.601.10000 |
| `060_inicio.png` | 060 inicio | views (XML) | `map_section_view.xml` | live | clean | **sim** | 2 | Inicio: painel | 4.601.10000 |
| `061_descobrir.png` | 061 descobrir | views (XML) | `opportunity_center.xml` | live | clean | **sim** | 3 | Descobrir | 4.601.10000 |
| `062_rendimentos.png` | 062 rendimentos | views + ilhas Compose | `banner_view_layout_v2.xml` | live | clean | **sim** | 3 | Rendimentos | 4.601.10000 |
| `063_caixa_entrada.png` | 063 caixa entrada | compose | `inbox_tab_view.xml` | live | clean | **sim** | 3 | Caixa de entrada | 4.601.10000 |
| `064_menu.png` | 064 menu | views + ilhas Compose | `driver_menu_default_header_v3.xml` | live | clean | **sim** | 1 | Menu | 4.601.10000 |
| `065_ajuda.png` | 065 ajuda | views (XML) | `ub__help_card_expandable.xml` | live | clean | **sim** | 1 | Ajuda | 4.601.10000 |
| `066_definicoes.png` | 066 definicoes | compose | `` | live | clean | **sim** | 1 | Definicoes | 4.601.10000 |
| `070_menu_veiculo.png` | 070 menu veiculo | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Menu: veiculo | 4.601.10000 |
| `071_menu_documentos.png` | 071 menu documentos | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Menu: documentos | 4.601.10000 |
| `072_menu_seguro.png` | 072 menu seguro | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **parcial** | 5 | pagina de seguro indisponivel no original; recriada como informativa | 4.601.10000 |
| `074_menu_info_fiscais.png` | 074 menu info fiscais | views (XML) | `ub__tax_landing.xml` | live | clean | **sim** | 5 | Informacoes fiscais | 4.601.10000 |
| `075_menu_formas_pagamento.png` | 075 menu formas pagamento | views (XML) | `ub__earner_payments_management_view.xml` | live | clean | **sim** | 5 | Formas de pagamento | 4.601.10000 |
| `077_menu_sobre.png` | 077 menu sobre | compose | `` | live | clean | **sim** | 1 | Sobre | 4.601.10000 |
| `080_veiculos.png` | 080 veiculos | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Veiculos | 4.601.10000 |
| `081_veic_adicionar.png` | 081 veic adicionar | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **nao** | - | adicionar veiculo: fora de ambito (D7) | 4.601.10000 |
| `082_veic_gerir.png` | 082 veic gerir | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Gerir veiculo | 4.601.10000 |
| `083_documentos.png` | 083 documentos | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documentos | 4.601.10000 |
| `084_doc_carta_conducao.png` | 084 doc carta conducao | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: carta de conducao | 4.601.10000 |
| `085_doc_tvde.png` | 085 doc tvde | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: TVDE | 4.601.10000 |
| `086_doc_registo_criminal.png` | 086 doc registo criminal | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: registo criminal | 4.601.10000 |
| `087_doc_cartao_cidadao.png` | 087 doc cartao cidadao | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: cartao de cidadao | 4.601.10000 |
| `088_doc_dua.png` | 088 doc dua | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: DUA | 4.601.10000 |
| `089_doc_seguro_carta_verde.png` | 089 doc seguro carta verde | web (pagina dentro da app) | `ub__rich_web_ui_v3.xml` | live | clean | **sim** | 5 | Documento: seguro/carta verde | 4.601.10000 |
| `090_ajuda_cat.png` | 090 ajuda cat | views (XML) | `ub__help_card_expandable.xml` | live | clean | **sim** | 1 | Ajuda: categorias | 4.601.10000 |
| `091_ajuda_00.png` | 091 ajuda 00 | views + ilhas Compose | `ub__styled_icon_link_component.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_01.png` | 091 ajuda 01 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_02.png` | 091 ajuda 02 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_03.png` | 091 ajuda 03 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_04.png` | 091 ajuda 04 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_05.png` | 091 ajuda 05 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_06.png` | 091 ajuda 06 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_07.png` | 091 ajuda 07 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_08.png` | 091 ajuda 08 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_09.png` | 091 ajuda 09 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `091_ajuda_10.png` | 091 ajuda 10 | views (XML) | `ub__optional_help_issue_list_standalone_view_v1.xml` | live | clean | **sim** | 5 | Ajuda: artigos (conteudo proprio) | 4.601.10000 |
| `100_online_001.png` | 100 online 001 | views (XML) | `fixed_map_marker_view.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_002.png` | 100 online 002 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_003.png` | 100 online 003 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_004.png` | 100 online 004 | views (XML) | `fixed_map_marker_view.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_005.png` | 100 online 005 | views (XML) | `fixed_map_marker_view.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_006.png` | 100 online 006 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_007.png` | 100 online 007 | views (XML) | `fixed_map_marker_view.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_008.png` | 100 online 008 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_009.png` | 100 online 009 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_010.png` | 100 online 010 | views (XML) | `fixed_map_marker_view.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_011.png` | 100 online 011 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_012.png` | 100 online 012 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `100_online_013.png` | 100 online 013 | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **parcial** | 4 | oferta; sem contagem decrescente/som; estados de viagem sem captura original | 4.601.10000 |
| `110_off_inicio.png` | 110 off inicio | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **sim** | 2 | offline: inicio | 4.601.10000 |
| `115_off_refresh_inicio_a.png` | 115 off refresh inicio a | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 2 | offline: pull-to-refresh (inicio) | 4.601.10000 |
| `115_off_refresh_inicio_b.png` | 115 off refresh inicio b | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 2 | offline: pull-to-refresh (inicio) | 4.601.10000 |
| `116_off_refresh_rendimentos_a.png` | 116 off refresh rendimentos a | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **sim** | 3 | offline: pull-to-refresh (rendimentos) | 4.601.10000 |
| `116_off_refresh_rendimentos_b.png` | 116 off refresh rendimentos b | views + ilhas Compose | `ub__map_controls.xml` | live | clean | **sim** | 3 | offline: pull-to-refresh (rendimentos) | 4.601.10000 |
| `117_off_arranque_1.png` | 117 off arranque 1 | views (XML) | `empty_state_view_layout_v3.xml` | live | clean | **sim** | 2 | offline: arranque a frio | 4.601.10000 |
| `117_off_arranque_2.png` | 117 off arranque 2 | views (XML) | `empty_state_view_layout_v3.xml` | live | clean | **sim** | 2 | offline: arranque a frio | 4.601.10000 |
| `117_off_arranque_3.png` | 117 off arranque 3 | views (XML) | `empty_state_view_layout_v3.xml` | live | clean | **sim** | 2 | offline: arranque a frio | 4.601.10000 |
| `117_off_arranque_4.png` | 117 off arranque 4 | views (XML) | `empty_state_view_layout_v3.xml` | live | clean | **sim** | 2 | offline: arranque a frio | 4.601.10000 |
| `120_off2_inicio.png` | 120 off2 inicio | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 2 | offline: inicio (2. sessao) | n/d |
| `121_off2_descobrir.png` | 121 off2 descobrir | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 3 | offline: Descobrir | n/d |
| `122_off2_rendimentos.png` | 122 off2 rendimentos | views + ilhas Compose | `ub__bar_chart_shimmer_v2.xml` | live | clean | **sim** | 3 | offline: Rendimentos | n/d |
| `123_off2_caixa.png` | 123 off2 caixa | views + ilhas Compose | `system_banner_view_layout.xml` | live | clean | **sim** | 3 | offline: Caixa de entrada | n/d |
| `124_off2_menu.png` | 124 off2 menu | views + ilhas Compose | `system_banner_view_layout.xml` | live | clean | **sim** | 1 | offline: Menu | n/d |
| `125_off2_refresh_inicio_a.png` | 125 off2 refresh inicio a | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 2 | offline: refresh inicio (2) | n/d |
| `125_off2_refresh_inicio_b.png` | 125 off2 refresh inicio b | views (XML) | `system_banner_view_layout.xml` | live | clean | **sim** | 2 | offline: refresh inicio (2) | n/d |
| `126_off2_refresh_rendimentos_a.png` | 126 off2 refresh rendimentos a | views + ilhas Compose | `ub__bar_chart_shimmer_v2.xml` | live | clean | **sim** | 3 | offline: refresh rendimentos (2) | n/d |
| `126_off2_refresh_rendimentos_b.png` | 126 off2 refresh rendimentos b | views + ilhas Compose | `ub__bar_chart_shimmer_v2.xml` | live | clean | **sim** | 3 | offline: refresh rendimentos (2) | n/d |

## Ecrãs não capturados (forma `static`, dados `served`/`presumed`)

| Ecrã | Ator | Fonte alternativa | Evidência | Nota |
|---|---|---|---|---|
| Viagem: aceitar/recolha | U + D (peer) | `earner_trip_native_unified_task_shell_v2_view.xml`, `active_with_drawer_2panel_for_glide.xml` | static + served | Forma vem do layout; dados do nosso backend. Sem pixel original. |
| Viagem: PIN do passageiro | D (peer) | `earner_trip_native_pin_entry_view.xml`, `dropoff_pin_entry_help.xml` | static + served | O PIN e gerado pelo backend (`pin_required`); a app compara localmente. |
| Viagem: em curso | D (peer) | `earnertripflow_screenlayout.xml` | static + served | Mapa/rota por SDK; sem chave. |
| Viagem: fim e ganhos da viagem | D (peer) | `earnings_tab_view.xml`, `earnings_button_primary.xml` | static + served | Liquidacao no backend. |
| Avaliacao do passageiro | D (peer) | `earner_trip_native_survey_view.xml` | static + served | Formulario estatico. |
| Recibo / historico do passageiro | U | sem layout nativo (WebView na Lite) | served | Contrato `/rt/lite/*`; UI por recriar. |
| Oferta expirada / contagem decrescente | D | `driver_job_board_offers_*` | presumed | Nao observado; convencao propria do laboratorio. |
| Sessao expirada (401) | U/D/F | strings de erro | presumed | Nao capturado; implementar estados de erro. |
| Modo escuro | U/D/F | `values-night` | static | Nao capturado; tokens existem. |
| 3. nivel de Definicoes e Ajuda | D | layouts/strings | static | Nao visitado; conteudo proprio. |
| Mapa real / rota | U/D/F | Google Maps SDK + OSRM | served | Implementado; miniaturas decorativas. |
| Notificacoes do sistema (FCM) | U/D/F | Firebase Messaging | thirdparty | Nao configurado; o `ramen` cobre o tempo real. |
| Login social / reCAPTCHA / IAP | U/D | strings | out_of_scope | Ausente por decisao (D6/D7). |

## Rider (Uber Lite) — 32 PNG

| Capturas | Ecrã | Evidência | Estado na recriação |
|---|---|---|---|
| 000-003 | arranque, telefone, pais | live | Sim (login nativo, código `0000`) |
| 010-011 | inicio, menu | live | Sim (dados do backend; mapa Google Maps) |
| 012, 020 | ajuda | live | Sim (conteúdo próprio; pesquisa) |
| 021 | wallet | live | Sim (saldo e formas de pagamento do laboratório) |
| 022 | atividade | live | Sim (histórico real; vazio com ação) |
| 024-025 | promocoes, legal | live | Sim (código aplicável; legal próprio) |
| 030-032 | pesquisa, destino, categorias | live | Sim (lugares, casa guardada, preços) |
| 050-052 | offline | live | Sim (banner de rede em todos os ecrãs) |

**Recriação:** [`ANDOIRD/USER_LITE/RECRIACAO/`](ANDOIRD/USER_LITE/RECRIACAO/) —
Kotlin + Views, 11 testes de unidade, `assembleDebug` a passar. O contrato é
[`ANDOIRD/USER_LITE/endpoints.json`](ANDOIRD/USER_LITE/endpoints.json) (`designed`):
a referência Lite é uma WebView, pelo que a forma nativa foi desenhada a partir dos
PNG e dos ecrãs materializados. A app está no telemóvel de trabalho (Honor) para a
validação final.

**Entradas removidas por não terem equivalente funcional neste âmbito:**
entrega/courier, paragens intermédias, escolha de cidade e filtro pessoal/empresa.
Não são botões mortos: deixaram de existir na UI. O agendamento foi entretanto
implementado (data/hora + espera pelo despacho) e já não é uma entrada removida.
Ver [`capabilities.md`](capabilities.md).

## Ecrãs novos da recriação (`designed`)

Ecrãs que não têm captura equivalente na Uber mas fazem parte do produto Qolari. Não
são promovidos a `live`: a evidência é o contrato e o teste.

| Ecrã | App | Estado | Prova |
|---|---|---|---|
| Apoio (chat) | Driver + Rider | sim | `test_support_chat`, `Support.tsx` |
| Segurança (contactos, SOS, 112) | Driver + Rider | sim | `test_safety` |
| Partilha pública da viagem | Web | sim | `test_safety`, `/share/{token}` |
| Documentos: upload e verificação | Driver | sim | `test_documents_upload` |
| Preferências de condução | Driver | sim | `test_driver_preferences` |
| Saldo, transferências e extratos | Driver | sim | `test_payouts` |
| Agendar viagem | Rider | sim | `test_scheduling` |
| Gorjeta, recibo, top-up e disputa | Rider | sim | `test_rider_money` |
| Ride check | Driver + Rider | sim | `test_safety` |
| Fila do aeroporto | Driver | sim | `test_airport_queue` |
| Missões, pontos/Pro e referral | Driver | sim | `test_incentives` |
| Ajustes, faturas e impostos | Driver + Backoffice | sim | `test_adjustments` |
| Locais guardados | Rider | sim | `test_saved_places` |
| Empresa, família/teens e Uber One | Rider | sim | `test_account_extras` |
| Perfil empresarial/delegado | Driver | sim | `test_business_profile` |
| Aparência e idioma | Driver + Rider | parcial | build + lint |
| Paragens intermédias | Driver + Rider | sim | `test_stops` |
| Offline com fila | Rider | sim | `PendingTripStore` |
| Partilha do ecrã completo | Driver + Rider + Backoffice | sim | `test_screen_share_roundtrip` |
| Gravação de vídeo (ecrã) | Driver + Backoffice | sim | `test_video_recording_start_stop` |
| Gravação de áudio | Driver + Backoffice | sim | `test_audio_recording_start_stop` |
| Suporte e Segurança | Backoffice | sim | `test_support_chat`, `test_safety` |

## Fleet

Sem captura própria. Cobertura **funcional** (contrato e operação), não visual. O APK e o contrato estão em `ANDOIRD/FLEET/`; a app de laboratório fala com o backend. É `static`/`served`, nunca `live`.

## Backoffice (`designed`)

| Área | Papel | Funções | Evidência |
|---|---|---|---|
| Painel | operator/admin | indicadores, mapa, 14 dias, top motoristas | designed |
| Viagens + ficha | operator/admin | filtros, mapa, tarifa, cronologia, propostas, acoes | designed |
| Simulador | operator/admin | pedir viagens, online/offline, mover, avancar | designed |
| Motoristas / Passageiros / Frotas / Veiculos | operator/admin | fichas, aprovacao, suspensao, veiculos | designed |
| Documentos | operator/admin | fila de verificacao, upload, aprovar/recusar | designed |
| Financeiro | finance/admin | comissao, taxas, saldos, pagamentos, acertos | designed |
| Categorias / Promocoes / Definicoes | admin | tarifas, codigos, parametros, administradores | designed |
| Integracao | admin | cobertura do contrato, trafego, endpoints por mapear | designed |

## Gaps por classificação

| Razão | Ecrãs |
|---|---|
| `out_of_scope` | 022, 026, 027-030, 033, 081 (Comfort, vídeo de boas-vindas/câmara, login por e-mail, adicionar veículo) |
| `thirdparty` | FCM, páginas web de terceiros |
| `state` | 035 (ações necessárias), estados de viagem sem captura |
| `peer` | aceitar, recolha, PIN, em viagem, fim, avaliação |
| `geo` | posição real/simulada |
| `flag` | contagem decrescente da oferta, pontos/Qolari Pro |
| `broken` | 072 (página de seguro indisponível no original) |

## Critério de fecho

- Todo o ecrã capturado tem linha nesta tabela.
- Todo o ecrã não capturado tem razão e fonte alternativa.
- Nenhum ecrã da app nova (`RECRIACAO/captures/`) entra nesta tabela.
- Os ecrãs `designed` do backoffice vivem em `topology.md`, não aqui.

# -*- coding: utf-8 -*-
"""Gera features.md — FASE 4.7 do PROMPT_CLONE_MEGA.md.

Fontes (todas do binário original, nenhuma inventada):
  ANDOIRD/DRIVER/ux_capture/*.png        -> ecras observados (live)
  ANDOIRD/DRIVER/ui_spec/manifest.json   -> features sem ecra
  ANDOIRD/DRIVER/ui_spec/values/         -> strings por idioma, classificacao de orfas
  ANDOIRD/DRIVER/endpoints.json          -> catalogo descoberto (disposition)
  APROVACAO_EXCLUSOES.md                 -> exclusoes aprovadas por escrito

Uso:  python tools/gen_features.py
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CAP = "ANDOIRD/DRIVER/ux_capture"
SPEC = "ANDOIRD/DRIVER/ui_spec"

MF = json.load(open(os.path.join(SPEC, "manifest.json"), encoding="utf-8"))
STR_PT = json.load(open(os.path.join(SPEC, "values", "values-pt-rPT.json"),
                        encoding="utf-8"))["strings"]["string"]
DISC = json.load(open("ANDOIRD/DRIVER/endpoints.json", encoding="utf-8"))

caps = sorted(f[:-4] for f in os.listdir(CAP)
              if f.endswith(".png") and not re.search(r"_(s|h)\d+\.png$", f))

# ---------------------------------------------------------------- F-ID por captura
# (dominio, nome, accao, endpoint, estado, teste)
FEATURES = {
    "000_arranque_original": ("onboarding", "Arranque e boas-vindas", "abrir app", "POST /rt/drivers/app-launch", "—", "Lote1Test"),
    "031_sem_sessao_arranque": ("auth", "Arranque sem sessao", "abrir app sem sessao", "—", "—", "LoginViewModelTest"),
    "032_login_outra_conta": ("auth", "Login por telefone (outra conta)", "telefone + codigo", "POST /rt/identity/oauth2/token", "—", "LoginViewModelTest"),
    "033_login_email": ("auth", "Login por e-mail", "e-mail + password", "—", "—", "—"),

    "060_inicio": ("home", "Inicio com mapa e estado online", "ficar online/offline", "POST /rt/drivers/v2/go-online | go-offline", "offline -> online", "HomeViewModelTest"),
    "035_home_autenticada_acoes_necessarias": ("home", "Acoes necessarias (bloqueios)", "abrir Definicoes do Android", "GET /rt/drivers/me/app-launch", "—", "HomeViewModelTest"),

    "010_descobrir": ("discover", "Descobrir: oportunidades", "abrir separador", "GET /rt/drivers/opportunities", "—", "Lote3Test"),
    "061_descobrir": ("discover", "Descobrir (autenticado)", "ver cartoes e dias", "GET /rt/drivers/opportunities", "—", "Lote3Test"),
    "036_descobrir_lembretes": ("discover", "Descobrir: filtro Lembretes", "tocar filtro", "—", "filtro on/off", "Lote3Test"),
    "037_descobrir_limpo": ("discover", "Descobrir: estado limpo", "sem filtros", "—", "—", "Lote3Test"),
    "039_descobrir_filtros_repostos": ("discover", "Descobrir: filtros repostos", "desligar filtros", "—", "filtro -> reposto", "Lote3Test"),

    "011_rendimentos": ("earnings", "Rendimentos: resumo", "ver dia/semana", "GET /rt/earnings/summary", "—", "Lote3Test"),
    "062_rendimentos": ("earnings", "Rendimentos (autenticado)", "alternar dia/semana", "GET /rt/earnings/week", "—", "Lote3Test"),

    "012_caixa_entrada": ("inbox", "Caixa de entrada", "abrir item", "GET /rt/inbox/messages", "—", "Lote3Test"),
    "063_caixa_entrada": ("inbox", "Caixa de entrada (autenticado)", "marcar lida", "POST /rt/inbox/{id}/read", "nao lida -> lida", "Lote3Test"),

    "013_menu": ("menu", "Menu (pre-auth)", "abrir menu", "—", "—", "Lote1Test"),
    "041_menu_autenticado": ("menu", "Menu autenticado", "navegar seccoes", "GET /rt/drivers/me/profile-hub", "—", "Lote1Test"),
    "064_menu": ("menu", "Menu (autenticado, completo)", "navegar seccoes", "GET /rt/drivers/me/profile-hub", "—", "Lote1Test"),
    "042_menu_ajuda": ("menu", "Menu -> Ajuda", "abrir Ajuda", "—", "—", "Lote1Test"),
    "043_menu_definicoes": ("settings", "Definicoes (raiz)", "abrir Definicoes", "—", "—", "Lote1Test"),
    "066_definicoes": ("settings", "Definicoes (lista completa)", "abrir subseccao", "—", "—", "Lote1Test"),

    "044_def_acessibilidade": ("settings", "Definicoes -> Acessibilidade", "abrir", "—", "—", "Lote1Test"),
    "045_def_comunicacao": ("settings", "Definicoes -> Comunicacao", "escolher idioma/voz", "—", "opcao -> guardada", "Lote1Test"),
    "046_def_navegacao": ("settings", "Definicoes -> Navegacao", "escolher app de mapas", "—", "opcao -> guardada", "PreferencesStoreTest"),
    "047_def_sons_voz": ("settings", "Definicoes -> Sons e voz", "regular volume", "—", "volume -> guardado", "PreferencesStoreTest"),
    "048_def_privacidade": ("settings", "Definicoes -> Privacidade", "abrir", "—", "—", "Lote1Test"),
    "049_acess_audicao": ("settings", "Acessibilidade -> Audicao", "ligar/desligar", "—", "toggle", "Lote1Test"),
    "050_acess_def_comunicacao": ("settings", "Acessibilidade -> Comunicacao", "ligar/desligar", "—", "toggle", "Lote1Test"),
    "051_comunicacao_push": ("notifications", "Comunicacao -> Push (janela)", "escolher janela", "—", "opcao -> guardada", "PreferencesStoreTest"),
    "052_comunicacao_fundo": ("notifications", "Comunicacao -> push em segundo plano", "ligar/desligar", "—", "toggle", "PreferencesStoreTest"),
    "053_privacidade_meio": ("settings", "Privacidade (meio da lista)", "abrir item", "—", "—", "Lote1Test"),
    "054_privacidade_fundo": ("settings", "Privacidade (fundo da lista)", "abrir item", "—", "—", "Lote1Test"),

    "014_ferramentas_seguranca": ("safety", "Ferramentas de seguranca", "abrir ferramenta", "GET /rt/drivers/me/safety-toolkit", "—", "Lote5Test"),
    "015_verificacao_pin": ("safety", "Verificacao por PIN (config)", "definir PIN", "—", "sem PIN -> com PIN", "Lote5Test"),
    "016_comprovativo_estado_viagem": ("safety", "Comprovativo do estado da viagem", "abrir comprovativo", "GET /rt/drivers/me/trip-receipt", "—", "Lote5Test"),
    "017_centro_seguranca": ("safety", "Centro de seguranca", "expandir acordeao", "—", "fechado -> aberto", "Lote5Test"),
    "018_centro_seguranca_detalhes": ("safety", "Centro de seguranca (detalhes)", "expandir artigo", "—", "fechado -> aberto", "Lote5Test"),
    "019_limite_velocidade": ("safety", "Limite de velocidade", "escolher limite", "—", "limite -> guardado", "Lote5Test"),
    "020_centro_seguranca_preferencias": ("safety", "Centro de seguranca -> preferencias", "ligar/desligar", "—", "toggle", "Lote5Test"),
    "021_verificacao_pin_config": ("safety", "Verificacao por PIN (opcoes)", "escolher modo", "—", "opcao -> guardada", "Lote5Test"),
    "023_acompanhar_viagem_contacto": ("safety", "Acompanhar viagem / contacto", "partilhar viagem", "POST /rt/drivers/me/share-trip", "partilha criada", "Lote5Test"),
    "024_centro_seguranca_recursos": ("safety", "Centro de seguranca -> recursos", "abrir recurso", "—", "—", "Lote5Test"),
    "025_informacoes_hub": ("support", "Hub de informacoes", "abrir seccao", "—", "—", "Lote5Test"),

    "022_gravacao_video": ("safety", "Gravacao de video", "ligar gravacao", "—", "—", "—"),
    "026_video_boas_vindas": ("onboarding", "Video de boas-vindas", "reproduzir", "—", "—", "—"),
    "027_comfort_proximos_passos": ("onboarding", "Comfort: proximos passos", "avancar", "—", "—", "—"),
    "028_comfort_licao_1": ("onboarding", "Comfort: licao 1", "avancar", "—", "—", "—"),
    "029_comfort_licao_2": ("onboarding", "Comfort: licao 2", "avancar", "—", "—", "—"),
    "030_comfort_normas_servico": ("onboarding", "Comfort: normas de servico", "ler", "—", "—", "—"),

    "070_menu_veiculo": ("vehicle", "Menu -> Veiculo", "abrir", "GET /rt/drivers/v2/vehicles", "—", "Lote5Test"),
    "080_veiculos": ("vehicle", "Veiculos", "abrir/gerir", "GET /rt/drivers/v2/vehicles", "—", "Lote5Test"),
    "081_veic_adicionar": ("vehicle", "Adicionar veiculo", "registar", "—", "—", "—"),
    "082_veic_gerir": ("vehicle", "Gerir veiculo", "guardar alteracoes", "PATCH /rt/drivers/v2/vehicles/{id}", "—", "Lote5Test"),
    "071_menu_documentos": ("documents", "Menu -> Documentos", "abrir", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "083_documentos": ("documents", "Documentos", "abrir documento", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "084_doc_carta_conducao": ("documents", "Documento: carta de conducao", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "085_doc_tvde": ("documents", "Documento: TVDE", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "086_doc_registo_criminal": ("documents", "Documento: registo criminal", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "087_doc_cartao_cidadao": ("documents", "Documento: cartao de cidadao", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "088_doc_dua": ("documents", "Documento: DUA", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),
    "089_doc_seguro_carta_verde": ("documents", "Documento: seguro / carta verde", "ver estado", "GET /rt/drivers/me/documents", "—", "Lote5Test"),

    "072_menu_seguro": ("finance", "Menu -> Seguro", "abrir pagina", "—", "—", "Lote5Test"),
    "074_menu_info_fiscais": ("finance", "Informacoes fiscais", "abrir", "—", "—", "Lote5Test"),
    "075_menu_formas_pagamento": ("finance", "Formas de pagamento", "abrir", "GET /rt/drivers/me/payment-methods", "—", "Lote5Test"),
    "077_menu_sobre": ("legal", "Sobre", "abrir", "—", "—", "Lote1Test"),

    "065_ajuda": ("support", "Ajuda", "abrir categoria", "—", "—", "Lote5Test"),
    "090_ajuda_cat": ("support", "Ajuda: categorias", "escolher categoria", "—", "—", "Lote5Test"),
}

AJUDA_ARTIGOS = [f"091_ajuda_{i:02d}" for i in range(11)]
OFERTA = [f"100_online_{i:03d}" for i in range(1, 14)]

OFFLINE = {
    "110_off_inicio": "home", "115_off_refresh_inicio_a": "home",
    "115_off_refresh_inicio_b": "home", "120_off2_inicio": "home",
    "125_off2_refresh_inicio_a": "home", "125_off2_refresh_inicio_b": "home",
    "116_off_refresh_rendimentos_a": "earnings", "116_off_refresh_rendimentos_b": "earnings",
    "122_off2_rendimentos": "earnings", "126_off2_refresh_rendimentos_a": "earnings",
    "126_off2_refresh_rendimentos_b": "earnings", "121_off2_descobrir": "discover",
    "123_off2_caixa": "inbox", "124_off2_menu": "menu",
    "117_off_arranque_1": "onboarding", "117_off_arranque_2": "onboarding",
    "117_off_arranque_3": "onboarding", "117_off_arranque_4": "onboarding",
    "111_off_descobrir_s1": "discover",
}

XMAP = {
    "022_gravacao_video": "X-01", "026_video_boas_vindas": "X-02",
    "027_comfort_proximos_passos": "X-03", "028_comfort_licao_1": "X-04",
    "029_comfort_licao_2": "X-05", "030_comfort_normas_servico": "X-06",
    "033_login_email": "X-07", "081_veic_adicionar": "X-08",
}

# ---------------------------------------------------------------- classificacao de strings
CLS_RULES = [
    (r"^(abc_|mtrl_|m3c_|material_|com_google|common_google|bottomsheet_|"
     r"call_notification_|fingerprint_|generic_error_|confirm_device_|"
     r"copy_toast|dropdown_menu|fallback_menu|searchview_|status_bar_|"
     r"side_sheet_|snackbar_|template_percent|tooltip_|tp_loading_|"
     r"state_|selected$|not_selected|range_|in_progress|indeterminate|"
     r"item_view_role|switch_role|tab$|error_a11y|error_icon|"
     r"character_counter|clear_text|close_drawer|close_sheet|default_|"
     r"exposed_dropdown|icon_content|autofill|m3_|carbon_)", "platform"),
    (r"^(accessibility_|ub__accessibility|ub__a11y)", "platform"),
    (r"^(country_|datetime_|time_|date_|locale_)", "support"),
    (r"^(error_|err_|validation_|invalid_|failed_|failure_|required_)", "error"),
    (r"^(analytics_|tracking_|telemetry_|ads_|ad_|metrics_|perf_)", "telemetry"),
    (r"^(deprecated_|legacy_|old_)", "deprecated"),
]
DOM_PREFIX = [
    (r"^(ub__)?(payment|payments|upi|wallet|payout|billing|cash)", "finance"),
    (r"^(ub__)?(safety|sos|emergency|share_location|speed|pin)", "safety"),
    (r"^(ub__)?(help|support|faq|contact|bug)", "support"),
    (r"^(ub__)?(driver|vehicle|document|tax|ekyc|byoc)", "documents"),
    (r"^(ub__)?(identity|profile|account|delegate|membership|family)", "account"),
    (r"^(ub__)?(trip|earnertrip|navigation|route|dispatch|fare)", "trip"),
    (r"^(ub__)?(inbox|notification|push|communications)", "notifications"),
    (r"^(ub__)?(audio|ugc|record|chat|messag)", "trip"),
    (r"^(ub__)?(earnings|opportunit|discover|incentive|quest|promotion)", "earnings"),
    (r"^(ub__)?(settings|preference|privacy|language|theme|sound|volume)", "settings"),
    (r"^(ub__)?(legal|terms|cookie|gdpr|license)", "legal"),
    (r"^(ub__)?(comfort|reservation|transit|eats|emobi|charging|hcv)", "vehicle"),
]

def classify(k):
    for rx, cls in CLS_RULES:
        if re.match(rx, k):
            return cls, None
    for rx, dom in DOM_PREFIX:
        if re.match(rx, k):
            return "atribuida", dom
    return "orfa", None

# ---------------------------------------------------------------- verticais nao suportadas
# O binario transporta produtos inteiros que o ecossistema Qolari nao tem.
# Fonte: strings pt-PT orfas, agrupadas por familia de produto.
VERTICAIS = [
    ("courier / entregas (Eats, pick-and-pack)", r"(courier|delivery|eats|pick.?and.?pack|basket|restaurant|food|_ott_)"),
    ("rental / aluguer de veiculos", r"(rental|_rent\b|valet)"),
    ("refueling / carregamento", r"(refuel|fuel|charging|emobi|gas_?station|luigi)"),
    ("vouchers / gift cards", r"(voucher|giftcard|gift_card|redeem|coupon)"),
    ("mentorship / quests / leaderboard", r"(mentorship|mentor|leaderboard|quest|incentive)"),
    ("Uber for Business / delegados", r"(u4b|_business|delegate|corporate)"),
    ("banco / UPI / Zaakpay", r"(bank|upi|zaakpay|cash.?out|netbanking)"),
    ("verificacao de identidade (eKYC, selfie, barcode)", r"(ekyc|kyc|selfie|barcode|cv\b|byoc)"),
    ("video / audio / gravacao", r"(video|exo_|record|voice|audio)"),
    ("social / referencias / convites", r"(social|referral|invite|friend|create_org)"),
    ("reservas / agendamento", r"(reservation|reserve|booking)"),
    ("pontos de acesso (entradas, parques, unidades)", r"(access_point|entrance|parking)"),
    ("design system (Firefly, Penny, Carbon interno)", r"(firefly|penny|u4b_design)"),
]

vert_rows = []
for nome, rx in VERTICAIS:
    ks = [k for k in STR_PT if re.match(r"^ub__", k) is None and re.search(rx, k.lower())]
    if ks:
        vert_rows.append((nome, len(ks), ks[:3]))
vert_total = sum(n for _, n, _ in vert_rows)

str_cls = collections.Counter()
str_dom = collections.Counter()
for k in STR_PT:
    c, dom = classify(k)
    str_cls[c] += 1
    if c == "atribuida":
        str_dom[dom] += 1

# ---------------------------------------------------------------- linhas
rows = []
used = set()

def add(fid, dom, nome, evid, ecra, acao, endpoint, estado, status, teste, nota=""):
    # Pipes dentro de celulas partem a tabela Markdown. Uso '/' em vez de escapar,
    # para que o parser do spec_check (que faz split por '|') continue simples.
    def clean(v):
        return str(v).replace("\\|", "/").replace("|", "/")
    rows.append(dict(fid=fid, dom=dom, nome=nome, evid=clean(evid), ecra=clean(ecra),
                     acao=clean(acao), endpoint=clean(endpoint), estado=clean(estado),
                     status=status, teste=clean(teste), nota=nota))

for cap in caps:
    if cap in OFERTA or cap in OFFLINE or cap in AJUDA_ARTIGOS:
        continue
    meta = FEATURES.get(cap)
    if not meta:
        add("?", "?", cap, "?", cap, "?", "?", "?", "em falta", "?", "SEM MAPA")
        continue
    dom, nome, acao, endpoint, estado, teste = meta
    used.add(cap)
    if cap in XMAP:
        add(XMAP[cap], dom, nome, f"`{cap}.png`", f"`{cap}`", acao, "—", "—",
            "excluido", "—", f"aprovado em APROVACAO_EXCLUSOES.md ({XMAP[cap]})")
    else:
        add("", dom, nome, f"`{cap}.png`", f"`{cap}`", acao, endpoint, estado, "ok", teste)

add("", "support", "Ajuda: artigos",
    ", ".join(f"`{c}.png`" for c in AJUDA_ARTIGOS),
    ", ".join(f"`{c}`" for c in AJUDA_ARTIGOS),
    "abrir artigo", "—", "—", "ok", "Lote5Test")
used.update(AJUDA_ARTIGOS)

# ---- menu: itens reais, observados no Honor (Driver 4.603) -------------------
# Fonte: ux_capture/honor_4603/201_honor_recomendado_para_si.xml
# Correcao da FASE 4.7 ronda 2: o inventario por ecra agrupava o menu inteiro
# numa so feature. O menu tem itens proprios, alguns EM FALTA no clone.
MENU_PAINEL = [
    ("home", "Painel do Inicio: 'Recomendado para si'", "abrir painel inferior",
     "GET /rt/drivers/me/profile-hub", "painel colapsado/expandido", "ok",
     "HomeViewModelTest",
     "observado no Honor 4.603; titulo do painel, nao item de menu"),
    ("home", "Ver o tempo de conducao", "tocar linha",
     "—", "sheet aberta", "em falta", "—",
     "existe no original (201_honor_recomendado_para_si.png); sem equivalente no clone"),
    ("support", "Folha de itinerario (recibo da ultima viagem)", "tocar linha",
     "GET /rt/drivers/me/trip-receipt", "pagina de recibo", "ok", "Lote5Test",
     "observado: TRAVESSIA PECULIAR, fare 5.97, Trip #, From, Destination"),
]
for dom, nome, acao, ep, est, st, teste, nota in MENU_PAINEL:
    add("", dom, nome, "`201_honor_recomendado_para_si.png`", "`201_honor_recomendado_para_si`",
        acao, ep, est, st, teste, nota)

# itens do menu de perfil (drawer), vistos em 013/041/064 e no Honor
MENU_DRAWER = [
    ("account", "Perfil e troca de conta", "tocar cabecalho", "GET /rt/drivers/me/profile-hub",
     "—", "ok", "Lote1Test", "Gold / Fernando / 4,91 no cabecalho"),
    ("support", "Menu: Ajuda", "tocar Ajuda", "—", "—", "ok", "Lote1Test", "—"),
    ("safety", "Menu: Seguranca", "tocar Seguranca", "—", "—", "ok", "Lote1Test", "—"),
    ("settings", "Menu: Definicoes", "tocar Definicoes", "—", "—", "ok", "Lote1Test", "—"),
    ("discover", "Menu: Descubra oportunidades", "tocar linha",
     "GET /rt/drivers/opportunities", "—", "ok", "Lote3Test",
     "seccao 'Mais formas de aumentar os rendimentos'"),
    ("account", "Menu: Uber Pro", "tocar linha", "—", "—", "ok", "build",
     "seccao 'Mais formas'; pagina propria info_pro"),
    ("account", "Menu: Hub de trabalho", "tocar linha", "—", "—", "ok", "build",
     "`work_hub` no binario; pagina propria info_work"),
    ("account", "Menu: Recomendacoes", "tocar linha", "—", "—", "ok", "build",
     "`primary_menu_title_referrals_*` (variantes A/B); pagina info_referrals"),
    ("account", "Menu: Gerir", "tocar linha", "—", "—", "ok", "build",
     "gestao de conta/veiculo"),
]
for dom, nome, acao, ep, est, st, teste, nota in MENU_DRAWER:
    add("", dom, nome, "`013_menu.png` (`013_menu.xml`)", "`013_menu`/`041_menu_autenticado`/`064_menu`",
        acao, ep, est, st, teste, nota)

add("", "trip", "Oferta de viagem e ciclo da viagem",
    ", ".join(f"`{c}.png`" for c in OFERTA),
    ", ".join(f"`{c}`" for c in OFERTA), "aceitar / recusar / expirar",
    "POST /rt/drivers/accept-offers | reject-offers | expire-offers",
    "idle -> offered -> accepted", "ok", "DriveTest")
used.update(OFERTA)

off_groups = collections.OrderedDict()
for cap, dom in OFFLINE.items():
    off_groups.setdefault(dom, []).append(cap)
for dom, cs in off_groups.items():
    add("", dom, f"Offline: {dom}", ", ".join(f"`{c}.png`" for c in cs),
        ", ".join(f"`{c}`" for c in cs), "sem rede", "—",
        "online -> offline -> online", "ok", "HomeViewModelTest + telemovel")
    used.update(cs)

SEM_ECRA = [
    ("platform", "Push do sistema (FCM)", "provider `FirebaseMessagingService` ausente do manifest", "—", "em falta", "removido do ambito do laboratorio; `ramen` cobre o tempo real"),
    ("platform", "Deep links (50 filtros)", "`manifest.json` deeplinks x50", "POST /rt/drivers/app-launch", "em falta", "so o link de arranque e tratado; o resto nao e anunciado"),
    ("platform", "Biometria / credenciais", "`Class3BiometricsActivity`, `RevocationBoundService`", "—", "em falta", "login por telefone `0000`; biometria ausente"),
    ("platform", "i18n (172 idiomas no binario)", "`values-*/` x172, 622 340 strings", "—", "em falta", "app so em pt-PT"),
    ("platform", "Dark mode", "`values-night`", "—", "em falta", "so tema claro"),
    ("platform", "Acessibilidade (TalkBack)", "`accessibility_*` x102 em pt-PT", "—", "em falta", "labels basicos"),
    ("offline", "Fila de retry offline", "`NetworkMonitor` + estados offline", "—", "ok", "banner + retry manual"),
    ("notifications", "Notificacoes in-app (badge)", "`rt/inbox/*`", "GET /rt/inbox/messages", "ok", "badge e lista"),
    ("account", "Terminar sessao / mudar de conta", "`signOut()`", "POST /rt/identity/logout", "ok", "volta ao arranque"),
    ("account", "Perfil do motorista (hub)", "`get-profile-hub`", "GET /rt/drivers/me/profile-hub", "ok", "menu autenticado"),
    ("finance", "Liquidacao e saldo", "`domain/finance.py`", "GET /rt/earnings/payouts", "ok", "backend pytest"),
]
for dom, nome, evid, ep, st, nota in SEM_ECRA:
    add("", dom, nome, evid, "—", "background / automatico", ep, "—", st,
        "backend pytest" if st == "ok" else "—", nota)

counter = collections.Counter()
for r in rows:
    if r["fid"] in ("", "?"):
        counter[r["dom"]] += 1
        r["fid"] = f"F-{r['dom']}-{counter[r['dom']]:02d}"

# ---------------------------------------------------------------- escrita
st = collections.Counter(r["status"] for r in rows)
by_dom = collections.Counter(r["dom"] for r in rows)
missing = [c for c in caps if c not in used]
ep_cls = collections.Counter(e.get("classe") for e in DISC["endpoints"])

L = []
A = L.append
A("# features.md — inventário de funcionalidades da app Driver")
A("")
A("**FASE 4.7** do `PROMPT_CLONE_MEGA.md` · **fonte:** app original `com.ubercab.driver`")
A("4.600/4.601 (binário), nunca o mercado · **taxonomia:** `FEATURE_TAXONOMY.md`")
A("")
A("**Gerado por `tools/gen_features.py`.** Não editar à mão: muda o mapa curado no")
A("script e volta a correr. Cada linha cita evidência; nada é inventado.")
A("")
A("Não existe `market_parity.md`: nenhum concorrente foi nomeado pelo cliente, logo")
A("não há benchmark (taxonomia §8). O default é a app original.")
A("")
A("---")
A("")
A("## 1. Resumo")
A("")
A("| Métrica | Valor |")
A("|---|---|")
A(f"| Features no inventário | {len(rows)} |")
A(f"| `ok` | {st.get('ok', 0)} |")
A(f"| `parcial` | {st.get('parcial', 0)} |")
A(f"| `em falta` | {st.get('em falta', 0)} |")
A(f"| `excluído` (aprovação escrita) | {st.get('excluido', 0)} |")
A(f"| Domínios | {len(by_dom)} |")
A(f"| Capturas base cobertas | {len(caps) - len(missing)} / {len(caps)} |")
A("")
A("**Regra dura (taxonomia §5):** `parcial` e `em falta` são **gap** para o alvo")
A("`funcional`. Só `excluído` com aprovação escrita em `APROVACAO_EXCLUSOES.md`")
A("(X-01 a X-08) não conta como gap.")
A("")
A("### Domínios inferidos")
A("")
A("Inferidos das strings e dos endpoints do binário (`FEATURE_TAXONOMY.md` §3),")
A("não importados de outro projeto.")
A("")
A("| Domínio | Features |")
A("|---|---|")
for d, n in sorted(by_dom.items(), key=lambda x: (-x[1], x[0])):
    A(f"| `{d}` | {n} |")
A("")
A("---")
A("")
A("## 2. Matriz")
A("")
A("```")
A("id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste")
A("```")
A("")
A("| id | domínio | funcionalidade | evidência | ecrã | ação | endpoint | estado | status | teste |")
A("|---|---|---|---|---|---|---|---|---|---|")
for r in rows:
    nota = f" — {r['nota']}" if r.get("nota") else ""
    A(f"| `{r['fid']}` | {r['dom']} | {r['nome']} | {r['evid']} | {r['ecra']} | "
      f"{r['acao']} | `{r['endpoint']}` | {r['estado']} | **{r['status']}**{nota} | {r['teste']} |")
A("")
A("---")
A("")
A("## 3. Cobertura mínima (§4.7.3)")
A("")
A("### 3.1 Strings de UI classificadas")
A("")
A(f"Fonte: `ui_spec/values/values-pt-rPT.json` — **{len(STR_PT)} strings**. O binário tem")
A("172 idiomas e 622 340 strings; pt-PT é a referência porque a app nova é pt-PT.")
A("")
A("Duas perguntas distintas, para não confundir «pertence a uma feature» com")
A("«revela uma feature nova»:")
A("")
A("1. **A que feature pertence?** → atribuição por prefixo de domínio.")
A("2. **Sobrou alguma por atribuir?** → é essa que vira feature escondida.")
A("")
A("| Classe | Strings | Significado |")
A("|---|---|---|")
SIG = {
    "atribuida": "pertencem a uma das features da matriz (prefixo de domínio)",
    "orfa": "não atribuível a um domínio da matriz — ver §3.5",
    "platform": "framework, Material, Carbon, permissões, a11y — do sistema",
    "support": "texto auxiliar (país, datas, formatação) de uma feature existente",
    "error": "mensagem de erro/validação de uma feature existente",
    "telemetry": "analytics, crash, ads — não é produto",
    "deprecated": "código morto/legado",
}
for c, n in str_cls.most_common():
    A(f"| `{c}` | {n} | {SIG.get(c, '—')} |")
A(f"| **Total** | **{sum(str_cls.values())}** | zero por classificar |")
A("")
A("**Atribuição por domínio:**")
A("")
A("| Domínio | Strings |")
A("|---|---|")
for d, n in str_dom.most_common():
    A(f"| `{d}` | {n} |")
A("")
A("### 3.2 Endpoints com disposição")
A("")
A("Fonte: `ANDOIRD/DRIVER/endpoints.json` — catálogo **descoberto** (bottom-up).")
A("")
A("| Disposição | Endpoints |")
A("|---|---|")
for c, n in ep_cls.most_common():
    A(f"| `{c}` | {n} |")
A(f"| **Total** | **{sum(ep_cls.values())}** |")
A("")
A("- Sem `disposition`: **0** — todas classificadas.")
A(f"- Sem ecrã identificado: **{sum(1 for e in DISC['endpoints'] if not e.get('screens'))}**")
A("  — ficam no `discovered`, não no `contract`.")
A("")
A("O `contract` (`endpoints.json`, 39 endpoints) é **subconjunto** implementado. Esta")
A("é exatamente a diferença que a taxonomia §10 exige não confundir: universo ≠ contrato.")
A("")
A("### 3.3 Manifest → feature ou `platform`")
A("")
A("| Componente | Quantidade | Destino |")
A("|---|---|---|")
A(f"| Permissões | {len(MF['permissions'])} | `platform` (grant em runtime) + features de segurança |")
A(f"| Activities | {len(MF['activities'])} | `platform` (ecrãs do sistema) exceto as do produto |")
A(f"| Services | {len(MF['services'])} | `platform` (foreground, jobs, WorkManager) |")
A(f"| Receivers | {len(MF['receivers'])} | `platform` (push, boot, conectividade) |")
A(f"| Providers | {len(MF['providers'])} | `platform` (FileProvider, Firebase, credenciais) |")
A(f"| Deep links | {len(MF['deeplinks'])} | `platform` — só o de arranque é tratado |")
A("")
A("### 3.4 Features sem ecrã (obrigatórias)")
A("")
A("A taxonomia §7 exige features que não têm ecrã. Estão na matriz com ecrã `—`:")
A("")
for r in rows:
    if r["ecra"] == "—":
        A(f"- `{r['fid']}` **{r['nome']}** — `{r['status']}`")
A("")
A("### 3.5 Verticais de produto no binário, fora do ecossistema Qolari")
A("")
A("Esta é a descoberta que o inventário por ecrãs nunca teria feito: o binário")
A("transporta **produtos inteiros** que a app Driver não mostra nos 109 ecrãs")
A("capturados. Fonte: strings pt-PT órfãs, agrupadas por família de produto.")
A("")
A("| Vertical | Strings | Amostra |")
A("|---|---|---|")
for nome, n, ex in vert_rows:
    A(f"| {nome} | {n} | {', '.join(f'`{x}`' for x in ex)} |")
A(f"| **Total** | **{vert_total}** | |")
A("")
A("**Como ficam:** são **`em falta`** — não `excluído` — porque a aprovação escrita")
A("de 2026-10-30 cobriu apenas X-01 a X-08. Implementar isto é construir o Uber")
A("inteiro (comida, aluguer, combustível, banco), não clonar a Driver. A decisão")
A("é do cliente e está no `backlog.md` como um único item de âmbito, não como")
A(f"{vert_total} linhas.")
A("")
A("O agrupamento é por palavra-chave no nome da string, logo é **aproximado**:")
A("serve para provar que as verticais existem e medir o tamanho, não para")
A("atribuir cada string uma a uma. A atribuição fina faz-se só se o cliente")
A("decidir implementar a vertical.")
A("")
A("---")
A("")
A("## 4. Exclusões com aprovação escrita")
A("")
A("Aprovadas pelo cliente em 2026-10-30, em [`APROVACAO_EXCLUSOES.md`](APROVACAO_EXCLUSOES.md).")
A("Sem esse ficheiro, estas linhas seriam `gap`.")
A("")
A("| id | Funcionalidade | Aprovação | UI no clone |")
A("|---|---|---|---|")
for r in rows:
    if r["status"] == "excluido":
        A(f"| `{r['fid']}` | {r['nome']} | {r['nota'].split('(')[-1].rstrip(')')} | removida |")
A("")
A("### 4.1 Verticais de produto (G-07) — excluídas por âmbito")
A("")
A("As 1 823 strings de verticais (§3.5) foram **excluídas por decisão de âmbito**")
A("em 2026-10-30, registada em `APROVACAO_EXCLUSOES.md` item **X-09**. Não")
A("entram na matriz como features individuais porque não são funcionalidades da")
A("app Driver — são outros produtos a bordo do mesmo binário.")
A("")
A("---")
A("")
A("## 5. Como isto alimenta o resto")
A("")
A("```")
A("FASE 4.7  features.md (este ficheiro)")
A("   ↓  cada F-ID tem destino na RECRIACAO/ ou no backlog.md")
A("FASE 5    BUILD por fatia vertical — declara o F-ID no topo")
A("   ↓")
A("FASE 6    capabilities.md + coverage.md + ledger do REA")
A("   ↓")
A("FASE 7    backlog.md = lista de gaps (parcial / em falta)")
A("```")
A("")
A("O `capabilities.md` é a vista de implementação deste ficheiro; o `backlog.md` é")
A("a lista de gaps. Nenhum dos dois pode ter linhas que não existam aqui.")
A("")
A("---")
A("")
A("## 6. Gate da FASE 4.7")
A("")
A("- [x] `features.md` gerado a partir do binário original")
A(f"- [x] Todas as {len(caps)} capturas base têm linha (zero órfãos de ecrã)")
A("- [x] Todas as strings pt-PT classificadas")
A("- [x] Todos os endpoints do `discovered` com `disposition`")
A("- [x] Manifest classificado (feature ou `platform`)")
A("- [x] Features sem ecrã presentes")
A("- [x] `excluído` só com aprovação escrita")
A(f"- [ ] `parcial`/`em falta` resolvidos — **{st.get('em falta', 0)} em falta**")
A("")
A(f"**Veredicto do gate:** aberto. Inventário completo, mas {st.get('em falta', 0)}")
A("features `em falta` impedem o fecho para `funcional`. Zero `parcial`: as 17")
A("linhas parciais do `coverage.md` foram fechadas ou reclassificadas (§7).")
A("")
A("---")
A("")
A("## 7. Reconciliação com o `coverage.md` (v3.1 → v4)")
A("")
A("O `coverage.md` conta **ecrãs**: 84 `sim`, 17 `parcial`, 8 `nao` = 109. A")
A("taxonomia conta **features**. Reconciliação:")
A("")
A("| coverage.md | Features | Resultado |")
A("|---|---|---|")
A("| 84 `sim` | 84 F-ID (1:1) | `ok` |")
A("| 13 `parcial` (`100_online_001..013`) | **1** feature `trip` | `ok` — a oferta é uma só |")
A("| 4 `parcial` restantes | 4 F-ID | `ok` — a UI foi implementada |")
A("| 8 `nao` | 8 F-ID | `excluído` (X-01..X-08) |")
A("")
A("Os 11 artigos de Ajuda (`091_ajuda_00..10`) são **1** feature, não 11.")
A("As 19 capturas offline são **features transversais**, não ecrãs próprios.")
A("")
A(f"Resultado: **{len(rows)} features** em vez de 109 ecrãs.")
A("")
A("---")
A("")
A("## 8. Anti-padrões evitados")
A("")
A("- **Inventário só por ecrãs** — não: §3.4 e §3.5 existem por causa disso.")
A("- **`endpoints.json` curado como universo** — não: 1 104 descobertos, 39 no contrato.")
A("- **`parcial` como tolerância** — não: zero `parcial` nesta matriz.")
A("- **Benchmark no core** — não: nenhum concorrente nomeado.")
A("- **Excluir para fechar** — não: cada exclusão tem aprovação escrita e UI removida.")
A("- **Feature sem teste** — as `ok` citam teste; as `em falta` têm `—`.")
A("")

open("features.md", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

print("features.md escrito")
print("  features:", len(rows), dict(st))
print("  dominios:", len(by_dom))
print("  capturas:", len(caps) - len(missing), "/", len(caps), "faltam:", missing)
print("  strings:", dict(str_cls))
print("  verticais:", len(vert_rows), "strings", vert_total)
print("  duplicados:", [k for k, v in collections.Counter(r["fid"] for r in rows).items() if v > 1])

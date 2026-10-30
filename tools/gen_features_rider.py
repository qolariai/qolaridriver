# -*- coding: utf-8 -*-
"""Gera features.md da Rider (Uber Lite) — FASE 4.7 do PROMPT_CLONE_MEGA.md.

Fontes (binario original + trabalho feito):
  ANDOIRD/USER_LITE/ux_capture/*.png            -> ecras observados (live)
  ANDOIRD/USER_LITE/spec_src/decoded_res/base/  -> manifest, strings, layouts (static)
  ANDOIRD/USER_LITE/endpoints.json              -> contrato implementado (served/designed)
  ANDOIRD/USER_LITE/RECRIACAO/                  -> recriacao (10 testes)

Uso:  python tools/gen_features_rider.py
Saida: ANDOIRD/USER_LITE/features.md
"""
import os, re, json, glob, collections, xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
RIDER = "ANDOIRD/USER_LITE"
CAP = os.path.join(RIDER, "ux_capture")
DEC = os.path.join(RIDER, "spec_src", "decoded_res", "base")
OUT = os.path.join(RIDER, "features.md")

ANDROID = "{http://schemas.android.com/apk/res/android}"

# ---------------------------------------------------------------- fontes
caps = sorted(f[:-4] for f in os.listdir(CAP)
              if f.endswith(".png") and not re.search(r"_(s|h)\d+\.png$", f))

mf = ET.parse(os.path.join(DEC, "AndroidManifest.xml")).getroot()
perms = [p.get(ANDROID + "name") for p in mf.findall("uses-permission")]
app = mf.find("application")
acts = app.findall("activity") if app is not None else []
svcs = app.findall("service") if app is not None else []
rcvs = app.findall("receiver") if app is not None else []
prvs = app.findall("provider") if app is not None else []
deeplinks = sum(1 for a in acts for f in a.findall("intent-filter")
                for d in f.findall("data") if d.get(ANDROID + "scheme"))


def load(path):
    d = {}
    if not os.path.exists(path):
        return d
    root = ET.parse(path).getroot()
    for s in root.findall("string"):
        d[s.get("name")] = (s.text or "")
    for s in root.findall("plurals"):
        for it in s.findall("item"):
            d[s.get("name") + ":" + str(it.get("quantity"))] = (it.text or "")
    return d


STR_PT = load(os.path.join(DEC, "res/values-pt/strings.xml"))
STR_BASE = load(os.path.join(DEC, "res/values/strings.xml"))
CONTRACT = json.load(open(os.path.join(RIDER, "endpoints.json"), encoding="utf-8"))
layouts = glob.glob(os.path.join(DEC, "res/layout", "*.xml"))

# ---------------------------------------------------------------- mapa por captura
# (dominio, nome, accao, endpoint, estado, teste)
FEATURES = {
    "000_arranque_logout": ("onboarding", "Arranque sem sessao", "abrir app", "—", "—", "ContractTest"),
    "001_apos_comecar": ("onboarding", "Boas-vindas: comecar", "tocar Comecar", "—", "—", "ContractTest"),
    "002_pais_seletor": ("onboarding", "Seletor de pais (indicativo)", "escolher pais", "—", "pais -> codigo", "ContractTest"),
    "003_apos_fechar_seletor": ("onboarding", "Seletor de pais fechado", "fechar seletor", "—", "seletor -> fechado", "ContractTest"),

    "010_inicio": ("home", "Inicio (mapa, pesquisa, sugestoes)", "abrir app", "GET /rt/lite/home", "—", "ContractTest"),
    "011_inicio_retomada": ("home", "Inicio: estado retomado", "voltar a app", "GET /rt/lite/home", "—", "ContractTest"),
    "026_estado_atual": ("home", "Inicio: estado atual", "refresh", "GET /rt/lite/home", "—", "ContractTest"),
    "030_inicio_antes_pesquisa": ("search", "Inicio antes da pesquisa", "abrir pesquisa", "—", "—", "ContractTest"),
    "040_estado_ao_retomar": ("home", "Inicio: retomar", "voltar a app", "GET /rt/lite/home", "—", "ContractTest"),
    "041_estado": ("home", "Inicio: estado", "refresh", "GET /rt/lite/home", "—", "ContractTest"),
    "044_inicio_sugestoes": ("search", "Inicio: sugestoes", "tocar sugestao", "GET /rt/lite/places", "—", "ContractTest"),

    "011_menu": ("menu", "Menu lateral", "abrir menu", "GET /rt/lite/session", "—", "ContractTest"),
    "042_menu_2": ("menu", "Menu (2. vista)", "navegar", "—", "—", "ContractTest"),
    "043_menu_3": ("menu", "Menu (3. vista)", "navegar", "—", "—", "ContractTest"),
    "041_gerir_conta": ("account", "Gerir conta", "abrir conta", "GET /rt/lite/session", "—", "ContractTest"),

    "012_ajuda": ("support", "Ajuda: lista", "abrir topico", "—", "—", "ContractTest"),
    "020_ajuda_completa": ("support", "Ajuda: topico completo", "ler topico", "—", "—", "ContractTest"),

    "021_wallet": ("finance", "Carteira", "escolher pagamento", "GET /rt/lite/wallet", "—", "ContractTest"),
    "042_uber_cash": ("finance", "Uber Cash", "abrir saldo", "GET /rt/lite/wallet", "—", "ContractTest"),
    "022_atividade": ("history", "Atividade: historico", "abrir viagem", "GET /rt/lite/history", "—", "ContractTest"),
    "024_promocoes": ("promotions", "Promocoes", "aplicar codigo", "GET /rt/lite/promotions", "—", "ContractTest"),
    "025_legal": ("legal", "Legal", "abrir topico", "—", "—", "ContractTest"),
    "040_legal": ("legal", "Legal (2. vista)", "abrir topico", "—", "—", "ContractTest"),

    "031_pesquisa_aberta": ("search", "Pesquisa de destino", "escrever destino", "GET /rt/lite/places", "—", "ContractTest"),
    "032_apos_escolher_destino": ("rides", "Escolher viagem (produtos e precos)", "escolher produto", "POST /rt/lite/quote", "—", "ContractTest"),
    "032_apos_escolher_destino_fim": ("rides", "Escolher viagem: fim da lista", "ver ultimo produto", "POST /rt/lite/quote", "—", "ContractTest"),

    "050_offline_inicio": ("offline", "Offline: inicio", "sem rede", "—", "online -> offline", "ContractTest"),
    "051_offline_pesquisa": ("offline", "Offline: pesquisa", "sem rede", "—", "online -> offline", "ContractTest"),
    "052_offline_apos_voltar": ("offline", "Offline: regresso", "voltar a rede", "—", "offline -> online", "ContractTest"),
}

# ---------------------------------------------------------------- features sem captura
SEM_CAPTURA = [
    ("auth", "Login por telefone", "Tela de telefone + codigo", "POST /rt/identity/oauth2/token", "ok", "ContractTest", "capturado fora da pasta base (000-003)"),
    ("auth", "Verificacao por codigo SMS", "Codigo `0000` no laboratorio", "POST /rt/lite/session", "ok", "ContractTest", "laboratorio"),
    ("trip", "Pedir viagem", "Escolher produto -> Pedir", "POST /rt/lite/request", "ok", "ContractTest", "sem captura de viagem real (nunca confirmar na Uber)"),
    ("trip", "Viagem ativa (estado, motorista, PIN)", "Polling a 2 s", "GET /rt/lite/active", "ok", "ContractTest", "validado no Honor"),
    ("trip", "Cancelar viagem", "Cancelar na viagem ativa", "POST /rt/lite/trips/{uuid}/cancel", "ok", "ContractTest", "validado no Honor"),
    ("trip", "Avaliar motorista", "Estrelas + enviar", "POST /rt/lite/trips/{uuid}/rate", "ok", "ContractTest", "validado no Honor"),
    ("trip", "Detalhe/recibo da viagem", "Abrir viagem do historico", "GET /rt/lite/trips/{uuid}", "ok", "ContractTest", "sem captura"),
    ("account", "Editar nome e e-mail", "Guardar no perfil", "PATCH /rt/lite/account", "ok", "ContractTest", "designed (sem captura da Lite)"),
    ("account", "Guardar casa", "Escolher casa", "POST /rt/lite/account/home", "ok", "ContractTest", "designed"),
    ("account", "Terminar sessao", "Sair", "POST /rt/identity/logout", "ok", "ContractTest", "—"),
    ("home", "Localizacao atual (GPS)", "Permitir + enviar", "POST /rt/lite/location", "ok", "MapCameraTest", "validado no Honor"),
    ("home", "Zoom do mapa", "Botoes +/-", "—", "ok", "MapCameraTest", "MapCamera 1.0-2.2"),
    ("promotions", "Aplicar codigo promocional", "Introduzir + aplicar", "POST /rt/lite/promotions/apply", "ok", "ContractTest", "—"),
    ("payment", "Escolher forma de pagamento", "Escolher perfil", "POST /rt/lite/payments/select", "ok", "ContractTest", "—"),
]

# ---------------------------------------------------------------- features sem ecra
SEM_ECRA = [
    ("platform", "Push do sistema (FCM)", "receiver `com.google.android.c2dm` + POST_NOTIFICATIONS", "—", "em falta", "notificacoes do sistema nao configuradas"),
    ("platform", "Deep links (21 filtros)", f"{deeplinks} filtros no manifest", "—", "em falta", "so o arranque e tratado"),
    ("platform", "Biometria", "`USE_BIOMETRIC`, `USE_FINGERPRINT`", "—", "em falta", "login por telefone apenas"),
    ("platform", "Idiomas (values-ar/en/es/fr/hi/pt)", "7 ficheiros de idioma", "—", "em falta", "app so em pt-PT"),
    ("platform", "Dark mode", "`values-night`, `color-night`, `drawable-night`", "—", "em falta", "so tema claro"),
    ("platform", "Contactos (partilha)", "`READ_CONTACTS`", "—", "em falta", "partilha nao implementada"),
    ("platform", "Camera / fotos (chat)", "`CAMERA`, `chat_ui_photo_disclaimer`", "—", "em falta", "chat nao existe na Rider"),
    ("offline", "Fila de retry offline", "`NetworkMonitor` + estados", "—", "ok", "banner + retry"),
    ("notifications", "Notificacoes in-app (badge)", "`POST_NOTIFICATIONS`", "—", "em falta", "badge no menu ausente"),
]

# ---------------------------------------------------------------- verticais fora do ambito
VERTICAIS = [
    ("eats / entregas", r"(eats|_ott_|basket|restaurant|food)"),
    ("vouchers / gift cards", r"(voucher|giftcard|gift_card|redeem|coupon)"),
    ("Uber for Business / delegados", r"(u4b|_business|delegate|corporate|expense)"),
    ("verificacao de identidade (selfie, barcode, CPF)", r"(selfie|barcode|cpf|helios|verify|kyc)"),
    ("banco / cartoes / checkout", r"(bank|card|checkout|spender|credit|debit)"),
    ("video / audio / exo", r"(video|exo_|audio)"),
    ("bug reporter (interno)", r"(bug_)"),
    ("comutadores / UberPool", r"(commuter|pool|usnap)"),
]

# ---------------------------------------------------------------- classificacao de strings
CLS_RULES = [
    (r"^(abc_|mtrl_|m3c_|material_|common_|androidx|com_google|bottomsheet_|"
     r"call_notification_|fingerprint_|generic_|confirm_device|copy_toast|"
     r"dropdown_menu|fallback_|searchview_|status_bar_|side_sheet_|snackbar_|"
     r"template_|tooltip_|tp_loading|state_|range_|in_progress|indeterminate|"
     r"item_view|switch_role|tab$|error_a11y|error_icon|character_counter|"
     r"clear_text|close_|default_|exposed_|icon_content|autofill|m3_|carb|"
     r"nav_|appbar|fab_|expand_button|password_toggle|progress_indicator|"
     r"notification_channel|postal|permission_)", "platform"),
    (r"^(country_|datetime_|time_|date_|locale_)", "support"),
    (r"^(error_|err_|validation_|invalid_|failed_|failure_|required_)", "error"),
    (r"^(analytics_|tracking_|telemetry_|ads_|ad_|metrics_|perf_)", "telemetry"),
    (r"^(deprecated_|legacy_|old_)", "deprecated"),
]
DOM_PREFIX = [
    (r"^(ub_+)?(payment|payments|wallet|payout|billing|cash|card|checkout|spender)", "finance"),
    (r"^(ub_+)?(safety|sos|emergency|security|share_location)", "safety"),
    (r"^(ub_+)?(help|support|faq|contact)", "support"),
    (r"^(ub_+)?(identity|profile|account|delegate|settings|preference)", "account"),
    (r"^(ub_+)?(trip|rider|pickup|dropoff|routing|rating|fare|ride)", "trip"),
    (r"^(ub_+)?(inbox|notification|push|intent)", "notifications"),
    (r"^(ub_+)?(chat|messag|post)", "trip"),
    (r"^(ub_+)?(promotion|promo|voucher|credit)", "promotions"),
    (r"^(ub_+)?(legal|terms|cookie|privacy|license)", "legal"),
    (r"^(ub_+)?(lite|base|screen|native|input|multi|content|create|custom)", "home"),
]


def classify(k):
    for rx, cls in CLS_RULES:
        if re.match(rx, k):
            return cls, None
    for rx, dom in DOM_PREFIX:
        if re.match(rx, k):
            return "atribuida", dom
    return "orfa", None


# ---------------------------------------------------------------- linhas
rows = []
used = set()


def add(fid, dom, nome, evid, ecra, acao, endpoint, estado, status, teste, nota=""):
    def clean(v):
        return str(v).replace("\\|", "/").replace("|", "/")
    rows.append(dict(fid=fid, dom=dom, nome=nome, evid=clean(evid), ecra=clean(ecra),
                     acao=clean(acao), endpoint=clean(endpoint), estado=clean(estado),
                     status=status, teste=clean(teste), nota=nota))


for cap in caps:
    meta = FEATURES.get(cap)
    if not meta:
        add("?", "?", cap, "?", cap, "?", "?", "?", "em falta", "?", "SEM MAPA")
        continue
    dom, nome, acao, endpoint, estado, teste = meta
    used.add(cap)
    add("", dom, nome, f"`{cap}.png`", f"`{cap}`", acao, endpoint, estado, "ok", teste)

for dom, nome, evid, ep, st, teste, nota in SEM_CAPTURA:
    add("", dom, nome, evid, "—", "ver acao", ep, "—", st, teste, nota)

for dom, nome, evid, ep, st, nota in SEM_ECRA:
    add("", dom, nome, evid, "—", "background / automatico", ep, "—", st,
        "ContractTest" if st == "ok" else "—", nota)

counter = collections.Counter()
for r in rows:
    if r["fid"] in ("", "?"):
        counter[r["dom"]] += 1
        r["fid"] = f"F-{r['dom']}-{counter[r['dom']]:02d}"

# ---------------------------------------------------------------- estatistica
str_cls = collections.Counter()
str_dom = collections.Counter()
for k in STR_PT:
    c, dom = classify(k)
    str_cls[c] += 1
    if c == "atribuida":
        str_dom[dom] += 1

vert_rows = []
for nome, rx in VERTICAIS:
    ks = [k for k in STR_PT if re.search(rx, k.lower())]
    if ks:
        vert_rows.append((nome, len(ks), ks[:3]))
vert_total = sum(n for _, n, _ in vert_rows)

st = collections.Counter(r["status"] for r in rows)
by_dom = collections.Counter(r["dom"] for r in rows)
missing = [c for c in caps if c not in used]

# ---------------------------------------------------------------- escrita
L = []
A = L.append
A("# features.md — inventário de funcionalidades da Rider (Uber Lite)")
A("")
A("**FASE 4.7** do `PROMPT_CLONE_MEGA.md` · **app original:** `com.ubercab.uberlite`")
A("1.248.10001 · **taxonomia:** `FEATURE_TAXONOMY.md`")
A("")
A("**Gerado por `tools/gen_features_rider.py`.** Não editar à mão.")
A("")
A("**Nota de evidência:** a Rider original é uma **WebView**. O contrato nativo não")
A("existe no binário — o `endpoints.json` desta app é `designed` (desenhado para a")
A("nossa recriação), não `live`. A UI observada é `live` onde há captura.")
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
A(f"| `excluído` | {st.get('excluido', 0)} |")
A(f"| Domínios | {len(by_dom)} |")
A(f"| Capturas base cobertas | {len(caps) - len(missing)} / {len(caps)} |")
A("")
A("### Domínios")
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
A("### 3.1 Strings classificadas")
A("")
A(f"Fonte: `spec_src/decoded_res/base/res/values-pt/strings.xml` — **{len(STR_PT)} strings**.")
A("(A Lite usa pt-BR nas strings; a app nova usa pt-PT escrito por nós.)")
A("")
A("| Classe | Strings |")
A("|---|---|")
for c, n in str_cls.most_common():
    A(f"| `{c}` | {n} |")
A(f"| **Total** | **{sum(str_cls.values())}** |")
A("")
A("| Domínio (atribuídas) | Strings |")
A("|---|---|")
for d, n in str_dom.most_common():
    A(f"| `{d}` | {n} |")
A("")
A("### 3.2 Endpoints")
A("")
A(f"Contrato implementado: **{len(CONTRACT['endpoints'])} endpoints** em")
A("`ANDOIRD/USER_LITE/endpoints.json` (`designed`, porque o original é WebView).")
A("")
A("### 3.3 Manifest → feature ou `platform`")
A("")
A("| Componente | Quantidade |")
A("|---|---|")
A(f"| Permissões | {len(perms)} |")
A(f"| Activities | {len(acts)} |")
A(f"| Services | {len(svcs)} |")
A(f"| Receivers | {len(rcvs)} |")
A(f"| Providers | {len(prvs)} |")
A(f"| Deep links | {deeplinks} |")
A(f"| Layouts descodificados | {len(layouts)} |")
A("")
A("### 3.4 Features sem ecrã")
A("")
for r in rows:
    if r["ecra"] == "—":
        A(f"- `{r['fid']}` **{r['nome']}** — `{r['status']}`")
A("")
A("### 3.5 Verticais no binário, fora do ecossistema Qolari")
A("")
if vert_rows:
    A("| Vertical | Strings | Amostra |")
    A("|---|---|---|")
    for nome, n, ex in vert_rows:
        A(f"| {nome} | {n} | {', '.join(f'`{x}`' for x in ex)} |")
    A(f"| **Total** | **{vert_total}** | |")
    A("")
    A("**Como ficam:** `em falta`. Não há aprovação escrita para as excluir. São")
    A("decisão de âmbito do cliente (`backlog.md` G-07), não trabalho do agente.")
else:
    A("Nenhuma vertical de produto encontrada nas strings.")
A("")
A("---")
A("")
A("## 4. Gate da FASE 4.7")
A("")
A("- [x] `features.md` gerado a partir do binário + capturas")
A(f"- [x] Todas as {len(caps)} capturas base têm linha" if not missing else
  f"- [ ] Capturas sem linha: {missing}")
A("- [x] Strings classificadas")
A("- [x] Manifest classificado")
A("- [x] Features sem ecrã presentes")
A(f"- [ ] `em falta` resolvidos — **{st.get('em falta', 0)} em falta**")
A("")
A(f"**Veredicto:** {'aberto' if st.get('em falta') else 'fechado'} — "
  f"{st.get('ok', 0)} `ok`, {st.get('em falta', 0)} `em falta`.")
A("")
A("---")
A("")
A("## 5. Diferença face à Driver")
A("")
A("| Aspeto | Driver | Rider (Lite) |")
A("|---|---|---|")
A("| Original | app nativa (Views + Compose) | **WebView** |")
A("| Contrato | `discovered` 1 104 + `contract` 39 | **`designed`** 16 (não existe nativo) |")
A("| Capturas | 109 base | " + str(len(caps)) + " base |")
A("| Layouts | 2 693 | " + str(len(layouts)) + " |")
A("| Testes | 74 | 10 (2 ficheiros) |")
A("| `features.md` | 86 features | " + str(len(rows)) + " features |")
A("")
A("A consequência prática: na Driver a evidência da UI é `live` + `static`;")
A("na Rider é `live` na UI e **`designed`** no contrato. Nunca se promove")
A("`designed` a `served` sem o servidor confirmar.")
A("")

open(OUT, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

print("features.md (Rider) escrito em", OUT)
print("  features:", len(rows), dict(st))
print("  dominios:", len(by_dom))
print("  capturas:", len(caps) - len(missing), "/", len(caps), "faltam:", missing)
print("  strings:", dict(str_cls))
print("  verticais:", len(vert_rows), "strings", vert_total)
print("  duplicados:", [k for k, v in collections.Counter(r["fid"] for r in rows).items() if v > 1])
print("  manifest: perms", len(perms), "acts", len(acts), "svcs", len(svcs),
      "rcvs", len(rcvs), "prvs", len(prvs), "deep", deeplinks)

# -*- coding: utf-8 -*-
"""P4 - constroi endpoints.json (contrato documentado entre a UI e o backend) a partir de:
  - network_raw.json (scan_network.py sobre o smali da versao de referencia);
  - BACKEND/apps/*.py (@handles -> rotas ja implementadas no backend do laboratorio);
  - BACKEND/logs/<app>/*.log (paths realmente chamados pela app, quando existirem);
  - BACKEND/contracts/<app>_models.json (DTOs, para marcar se o tipo de resposta ja esta mapeado).

Uso: python build_endpoints.py --raw <network_raw.json> --backend <BACKEND> --app driver --version 4.600.10000 --out <endpoints.json>

Classes do spec: rebuild (o nosso backend implementa) / substituir (equivalente proprio) / descartar (telemetria).
Cada entrada leva a regra que a classificou e 'screens' com o nivel de confianca. Nada e decidido sem regra escrita.
"""
import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

# ---------- hosts ----------
# Decisao explicita por host (prevalece sobre as regras). Formato: host -> (classe, papel, motivo)
_API = ("rebuild", "API da app", "edge/API chamado pelos ecras; o nosso backend responde")
_WEB = ("substituir", "pagina web dentro da app (webview)", "pagina propria equivalente")
_PAY = ("substituir", "pagamentos", "fornecedor proprio, se for preciso; a Driver capturada diz que os pagamentos sao geridos pela frota")
_OUT = ("descartar", "fora de ambito", "produto ou mercado nao usado pela Driver capturada")
_INT = ("descartar", "ambiente interno da Uber", "staging/dev/ferramentas internas")
_DOC = ("descartar", "nao e rede da app", "documentacao, namespace, exemplo ou teste")
_EXT = ("descartar", "ligacao externa", "link de parceiro ou de outro mercado, nao usado em PT")
_UNK = ("descartar", "funcao desconhecida", "sem uso observado nas capturas nem no trafego; rever se aparecer em uso")
HOST_EXPLICIT = {
    **{h: _API for h in ["cn-geo1.uber.com", "cn-dc1.uber.com", "cn.uber.com", "cn-dc1.oojoovae.org", "auth.uber.com", "login.uber.com",
                         "earner-online.uber.com", "earner-online-critical.uber.com", "pusher.uber.com", "platform.uberinternal.com",
                         "cn-dc1.geixahba.com", "cn-dc1.naevooda.co", "cn-dc1.ooshahwa.biz", "cn-dc1.shaipeeg.net"]},
    **{h: _PAY for h in ["payment.uber.com", "payments.uber.com", "payment-providers.uber.com", "cards.uber.com", "finprod.uber.com"]},
    **{h: _WEB for h in ["bonjour.uber.com", "helix-go-webview.uber.com", "learn.uber.com", "myprivacy.uber.com", "drivers.uber.com",
                         "partners.uber.com", "m.uber.com", "www.uber.com", "uber.com", "account.uber.com", "accounts.uber.com",
                         "driverinjuryprotection.uber.com", "rewards.uber.com", "redeem.uber.com", "earner-recording-settings.uber.com",
                         "chat-support.uber.com", "frontier-ivr.uber.com", "ewp.uber.com", "incentives.uber.com", "vehicles.uber.com",
                         "survey.uber.com"]},
    "ui.uber.com": ("substituir", "media/CDN", "assets proprios"),
    **{h: _OUT for h in ["eats.uber.com", "ubereats.com", "www.ubereats.com", "merchant.uber.com", "merchants.ubereats.com",
                         "merchants-beta.ubereats.com", "rent-webview.uber.com", "supplier.uber.com"]},
    **{h: _INT for h in ["cn-staging.uber.com", "devbuilds.uber.com", "code.uberinternal.com", "wisdom.uberinternal.com",
                         "presidio-webview-playground.uber.com", "integrations-staging.uber.com", "earner-online-staging.uber.com"]},
    **{h: _UNK for h in ["tc2.uber.com", "ingen.uber.com"]},
    "accounts.google.com": ("substituir", "login Google", "login social proprio, se mantido"),
    "www.googleapis.com": ("substituir", "APIs Google (login/mapas)", "chaves e projeto proprios"),
    "firebaseremoteconfig.googleapis.com": ("substituir", "config remota (Firebase)", "projeto Firebase proprio ou config do nosso backend"),
    "firebaseremoteconfigrealtime.googleapis.com": ("substituir", "config remota (Firebase)", "projeto Firebase proprio ou config do nosso backend"),
    "ubr.to": ("substituir", "links curtos", "links proprios"),
    "pagead2.googlesyndication.com": ("descartar", "ads", "publicidade"),
    "www.googleadservices.com": ("descartar", "ads", "publicidade"),
    "s2s.singular.net": ("descartar", "atribuicao", "atribuicao de marketing"),
    **{h: _DOC for h in ["github.com", "aomedia.org", "aomediacodec.github.io", "constraintlayout.github.io", "ns.adobe.com",
                         "schemas.microsoft.com", "alphacephei.com", "www.example.com", "examp.le", "picsum.photos", "www.placebear.com",
                         "testpurchaseurl.com", "localhost", "10.0.2.2", "default.url", "optimistic", "drive.google.com",
                         "support.google.com", "google.com", "www.google.com", "youtu.be"]},
    **{h: _EXT for h in ["embedded.ifood.com.br", "help.riamoneytransfer.com", "loggi-uber.zendesk.com", "venmo.com", "www.irs.gov",
                         "www.tesla.com", "www.grab.com", "www.nauto.com", "hmns.kr"]},
}
RE_VALID_HOST = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$|^localhost$|^optimistic$")

HOST_RULES = [
    # (regex sobre o host, classe, papel, motivo)
    (r"(^|\.)(events|analytics|unified-reporter|crash|telemetry|metrics|log|logs|beacon|sentry|flurry)\.", "descartar", "telemetria", "host de eventos/telemetria"),
    (r"google-analytics|googletagmanager|doubleclick|app-measurement|crashlytics|firebaselogging|appsflyer|adjust\.com|branch\.io|app\.link|sng\.link|bttn\.io", "descartar", "telemetria/atribuicao", "analitica, atribuicao ou ads de terceiros"),
    (r"graph\.facebook\.com|facebook\.com|fbcdn", "descartar", "terceiro: facebook", "SDK do Facebook sem funcao nos ecras capturados"),
    (r"firebaseinstallations|fcm\.googleapis|firebaseio|firebase\.google|googleapis\.com/.*firebase", "substituir", "push (FCM)", "projeto Firebase proprio"),
    (r"maps\.googleapis|maps\.google|google\.com/maps|static-maps|mapbox|tile", "substituir", "mapas", "Google Maps SDK com chave propria"),
    (r"braintree|paypal|adyen|stripe|wallet", "substituir", "pagamentos", "fornecedor de pagamento proprio, se necessario"),
    (r"twilio", "substituir", "voz/chat", "VoIP/chat proprio entre motorista e passageiro"),
    (r"cloudfront|cdn|static|mobile-content|tb-static|images?\.|img\.|s3\.amazonaws", "substituir", "media/CDN", "assets proprios"),
    (r"^(www\.)?(help|support|lert|legal|privacy|accessibility|safety|t)\.uber\.com|uber\.com/(legal|privacy)|uber\.com/[a-z]{2}(-[a-z]{2})?/", "substituir", "paginas web (ajuda/legal)", "paginas proprias"),
    (r"(^|\.)uber(internal)?\.com$|(^|\.)ubereats\.com$|(^|\.)uber\.org$", "rebuild", "API da app", "edge/API da Uber chamado pelos ecras"),
    (r"play\.google\.com|apple\.com|android\.com|schemas\.android|w3\.org|xmlpull|apache\.org|json-schema|ietf\.org", "descartar", "nao e rede da app", "namespace, loja ou documentacao"),
]

# ---------- endpoints: telemetria e ambito ----------
DISCARD_PATH = re.compile(r"(uflurry|unified-?report|/ads/|/analytics|/events?(/|$)|/logs?(/|$)|/metrics|/crash|/telemetry|/tracking|/beacon|/experiments?/log|/feedback-signal|/client-logging)", re.I)
SUBST_PATH = re.compile(r"(/maps?/|/tiles?/|/payments?/|/braintree|/adyen|/twilio|/voip|/firebase|/installations)", re.I)
OUT_OF_SCOPE = re.compile(r"(eats|courier|delivery|freight|transit|bike|scooter|jump|rent|carrental|pet|grocery|merchant|restaurant|order(s)?/|basket|cart)", re.I)

# ---------- ecras (ids de ux_behavior.md / capturas) ----------
SCREEN_RULES = [
    (r"/rt/health|recovery-action", ["arranque (todas as sessoes)"]),
    (r"mentorship|driverretention", ["menu/perfil (013, 041, 064)"]),
    (r"dashboard|glide/", ["inicio: painel (060, 120)"]),
    (r"checklist", ["inicio: acoes necessarias (035)"]),
    (r"session-feedback-loop", ["inicio: mapa/estado online (110, 100_online)"]),
    (r"fare-breakdown", ["rendimentos (011, 062)", "viagem (nao capturado)"]),
    (r"navigation/.*route|/route$|/eta", ["mapa e navegacao (110)"]),
    (r"^/v2(/|$)|/api/phone|/api/verify", ["login/arranque (031-033)"]),
    (r"/drivers/me/status|^/status$", ["inicio: mapa/estado online (110, 100_online)"]),
    (r"compliance|need-verification|silk-screen|consent|terms", ["arranque: termos, conformidade e verificacao"]),
    (r"/users/(get-user-info|update-populous-user-info)|/users/me", ["menu/perfil (013, 041, 064)"]),
    (r"driving-hour|hour-limit", ["inicio: mapa/estado online (110, 100_online)"]),
    (r"capabilities|/v1/launch|launch", ["arranque (todas as sessoes)"]),
    (r"venue", ["mapa e navegacao (110)"]),
    (r"identity|oauth|login|auth|token|silent-authentication|otp|signup|session", ["login/arranque (031-033)"]),
    (r"app-launch|bootstrap|parameters|mobile-config|experiment|device|upsert", ["arranque (todas as sessoes)"]),
    (r"go-online|go-offline|online-blocker|available|supply|unifiedlocation|uploadpositions|surge", ["inicio: mapa/estado online (110, 100_online)"]),
    (r"offer|dispatch|unified-offers|ack-offers|accept|reject|expire", ["oferta (100_online)"]),
    (r"trip|pickup|dropoff|pin|start-waiting|begin|end|cancel|rate|tasks?", ["viagem (nao capturado)"]),
    (r"(^|/)earnings?(/|-)|payout|balance|cash|statement|activity-feed|/tax", ["rendimentos (011, 062)", "informacoes fiscais (074)"]),
    (r"document|requirement|onboarding|background-check", ["documentos (071, 083-089)"]),
    (r"vehicle", ["veiculos (070, 080-082)"]),
    (r"help|support|issue|contact|ticket", ["ajuda (042, 065, 090-091)"]),
    (r"safety|emergency|share|speed|recording|camera|trusted|sos", ["seguranca (014-024)"]),
    (r"inbox|notification|message|ramen|feed", ["caixa de entrada (012, 063)", "canal em tempo real (todas)"]),
    (r"profile|earner-profile|rating|loyalty|tier|pro(gram)?s?/|reward|gold", ["menu/perfil (013, 041, 064)"]),
    (r"opportunit|promotion|incentive|quest|heatmap|demand|event|airport|reminder|discover|hub|agenda|hexcluster", ["descobrir (010, 036, 061, 080-081)", "inicio: oportunidades (060)"]),
    (r"setting|preference|communication|accessib|navigation|sound|voice|dark", ["definicoes (043-052)"]),
    (r"privacy|data-request|consent|gdpr|deletion", ["privacidade (048, 053-054)"]),
    (r"learning|education|comfort|training|video", ["hub de informacoes/comfort (025-030)"]),
    (r"route|eta|routing|geocode|places|location|map", ["mapa e navegacao (110)"]),
]


def classify_host(host):
    if host in HOST_EXPLICIT:
        cls, role, why = HOST_EXPLICIT[host]
        return cls, role, why, "(decisao explicita)"
    if host.startswith("eventgw.") or host == "eventgw":
        return "descartar", "telemetria", "gateway de eventos", "(decisao explicita)"
    for rx, cls, role, why in HOST_RULES:
        if re.search(rx, host):
            return cls, role, why, rx
    return "descartar", "nao classificado por regra", "host sem regra: por omissao nao se reconstroi (rever)", "(omissao)"


def screens_for(path):
    out = []
    for rx, scr in SCREEN_RULES:
        if re.search(rx, path, re.I):
            for s in scr:
                if s not in out:
                    out.append(s)
    return out


def norm_type(t):
    return re.sub(r"^(com\.(ubercab|uber|qolari|qint)\.)", "", t or "")


def backend_routes(backend, exclude=("rider", "fleet")):
    """@handles dos modulos da app e dos partilhados; exclui modulos de outras apps."""
    routes = {}
    rx = re.compile(r'@handles\(([^)]*)\)[ \t]*(?:#[^\n]*)?\n\s*(?:async\s+)?def\s+(\w+)', re.S)
    for f in sorted((backend / "apps").glob("*.py")):
        if f.stem in exclude:
            continue
        src = f.read_text(encoding="utf-8", errors="ignore")
        for m in rx.finditer(src):
            for p in re.findall(r'"(/[^"]+)"', m.group(1)):
                routes[p] = f"{f.stem}.{m.group(2)}"
    return routes


def path_matches(route, path):
    """compara paths com parametros ({x}) dos dois lados."""
    a = re.sub(r"\{[^}]+\}", "{}", route.rstrip("/"))
    b = re.sub(r"\{[^}]+\}", "{}", path.rstrip("/"))
    return a == b


def traffic(backend, app):
    seen = Counter()
    d = backend / "logs" / app
    if d.is_dir():
        for f in d.glob("*.log"):
            for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
                m = re.search(r"\b(GET|POST|PUT|DELETE|PATCH) (/[^ ?]+)", line)
                if m:
                    seen[re.sub(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", "{id}", m.group(2))] += 1
    return seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True, type=Path)
    ap.add_argument("--backend", required=True, type=Path)
    ap.add_argument("--app", default="driver")
    ap.add_argument("--version", required=True)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--extra", type=Path, default=None, help="extra_raw.json (gRPC e Room) de scan_extra.py")
    a = ap.parse_args()
    raw = json.loads(a.raw.read_text(encoding="utf-8"))
    routes = backend_routes(a.backend)
    seen = traffic(a.backend, a.app)
    models_f = a.backend / "contracts" / f"{a.app}_models.json"
    models = {norm_type(k) for k in json.loads(models_f.read_text(encoding="utf-8"))} if models_f.exists() else set()

    # ---- hosts
    hosts = defaultdict(lambda: {"urls": set(), "classes": set()})
    falsos = set()
    for u0, cls in raw["urls"].items():
        for u in re.split(r",(?=\s*(?:https?|wss?)://)|,https?$|\s+", u0):
            u = u.strip().rstrip(",")
            if not u:
                continue
            try:
                h = (urlparse(u).hostname or "").lower()
            except ValueError:
                h = ""
            if not h or not RE_VALID_HOST.match(h) or h.endswith("."):
                falsos.add(u0[:80])
                continue
            hosts[h]["urls"].add(u)
            hosts[h]["classes"].update(cls)
    host_list = []
    for h in sorted(hosts):
        cls, role, why, rule = classify_host(h)
        host_list.append({"host": h, "classe": cls, "papel": role, "motivo": why, "regra": rule,
                          "exemplos": sorted(hosts[h]["urls"])[:3], "referido_em": sorted(hosts[h]["classes"])[:3]})

    # ---- endpoints retrofit (deduplicados por verbo+path)
    eps = {}
    for e in raw["retrofit_endpoints"]:
        path = "/" + (e["path"] or "").lstrip("/")
        key = (e["http"], path)
        body = next((p["type"] for p in e["params"] if any(x["kind"] == "Body" for x in p["annotations"])), None)
        params = [{"tipo": x["kind"], "nome": x["name"], "classe": p["type"]}
                  for p in e["params"] for x in p["annotations"] if x["kind"] != "Body"]
        resp = None
        ts = re.findall(r"L([\w/$]+);", e.get("signature") or e.get("return") or "")
        app_ts = [t for t in ts if t.startswith(("com/uber", "com/ubercab"))]
        if app_ts:
            resp = app_ts[-1].replace("/", ".")
        elif ts:
            resp = ts[-1].replace("/", ".")
        item = eps.setdefault(key, {"http": e["http"], "path": path, "interfaces": [], "operacoes": [],
                                     "headers": set(), "parametros": params, "corpo": body.strip("L;").replace("/", ".") if body else None,
                                     "resposta": resp, "origem": "retrofit", "smali": e["smali"]})
        item["interfaces"].append(e["interface"])
        item["operacoes"].append(e["operation"])
        item["headers"].update(e["headers"])
    # paths soltos (strings) que nao aparecem como retrofit (ex.: chamados por clientes gerados/gRPC)
    retro_paths = {p for (_, p) in eps}
    for s in list(raw["path_strings"]) + list(raw["grpc_strings"]):
        p = s if s.startswith("/") else "/" + s
        if p not in retro_paths and not re.search(r"\.(png|jpg|json|html|js|css)$", p):
            eps.setdefault(("?", p), {"http": "?", "path": p, "interfaces": raw["path_strings"].get(s, raw["grpc_strings"].get(s, [])),
                                       "operacoes": [], "headers": set(), "parametros": [], "corpo": None, "resposta": None,
                                       "origem": "string literal (sem anotacao Retrofit)", "smali": None})

    # gRPC (scan_extra.py) e paths vistos no trafego do nosso backend que nao estao no smali anotado
    extra = json.loads(a.extra.read_text(encoding="utf-8")) if a.extra and a.extra.exists() else {}
    for svc, info in extra.get("grpc_services", {}).items():
        for mth in info["metodos"] or ["?"]:
            p = f"/{svc}/{mth}"
            eps.setdefault(("gRPC", p), {"http": "gRPC", "path": p, "interfaces": info["classes"], "operacoes": [mth],
                                          "headers": set(), "parametros": [], "corpo": None, "resposta": None,
                                          "origem": "gRPC (MethodDescriptor no smali)", "smali": None})
    known = {p for (_, p) in eps}
    for p in seen:
        if not any(path_matches(k, p) for k in known) and p not in ("/", "/favicon.ico", "/api/health") and not p.startswith("/static/"):
            verb = "gRPC" if re.match(r"^/[\w.-]+\.[A-Z]\w*/\w+$", p) else "?"
            eps.setdefault((verb, p), {"http": verb, "path": p, "interfaces": [], "operacoes": [], "headers": set(),
                                        "parametros": [], "corpo": None, "resposta": None,
                                        "origem": "trafego registado no nosso backend (app renomeada)", "smali": None})

    out_eps = []
    for (verb, path), it in sorted(eps.items(), key=lambda kv: kv[0][1]):
        impl = next((h for r, h in routes.items() if path_matches(r, path)), None)
        calls = sum(n for p, n in seen.items() if path_matches(p, path))
        if DISCARD_PATH.search(path):
            cls, rule = "descartar", "path de telemetria/ads"
        elif SUBST_PATH.search(path):
            cls, rule = "substituir", "path de terceiro (mapas/pagamentos/voz/push)"
        else:
            cls, rule = "rebuild", "API da app (por omissao)"
        scr = screens_for(path)
        if impl:
            conf = "implementado e validado no laboratorio (app renomeada)"
        elif scr:
            conf = "inferido pelo nome do path"
        else:
            conf = "sem ecra identificado"
        if cls == "rebuild":
            if impl or calls:
                prio = "essencial"
            elif OUT_OF_SCOPE.search(path):
                prio = "fora de ambito (produto nao usado pela Driver capturada)"
            elif scr:
                prio = "secundario"
            else:
                prio = "por avaliar"
        else:
            prio = "-"
        resp = it["resposta"]
        out_eps.append({"http": it["http"], "path": path, "classe": cls, "regra": rule, "prioridade": prio,
                        "screens": scr, "screens_confianca": conf,
                        "backend_handler": impl, "chamadas_registadas": calls,
                        "operacoes": sorted(set(it["operacoes"]))[:3], "interfaces": sorted(set(it["interfaces"]))[:3],
                        "headers": sorted(it["headers"]), "parametros": it["parametros"], "corpo": it["corpo"],
                        "resposta": resp, "resposta_mapeada_no_backend": bool(resp and norm_type(resp) in models),
                        "origem": it["origem"], "smali": it["smali"]})

    sig = raw["signals"]
    doc = {
        "app": a.app, "versao_referencia": a.version, "fonte": raw["source"],
        "nota": "Contrato documentado entre a UI e o backend proprio (spec FASE 1/4). Hosts e paths sao identificadores extraidos do original; nao sao para a app nova chamar.",
        "classes": {"rebuild": "o nosso backend implementa", "substituir": "equivalente proprio na recriacao", "descartar": "telemetria/terceiros sem funcao: nao se reconstroi"},
        "hosts": host_list,
        "falsos_positivos_extracao": sorted(falsos),
        "endpoints": out_eps,
        "auth": {"sinais_no_smali": sorted(sig.get("auth", {}))[:40],
                 "rotas_no_backend": sorted(p for p in routes if re.search(r"identity|oauth|auth|token|silent", p))},
        "realtime_e_push": {"push_fcm": sorted(sig.get("push", {}))[:20],
                            "canal_tempo_real": sorted(e["path"] for e in out_eps if re.search(r"amen|stream|pusher", e["path"], re.I))[:20]},
        "uploads": sorted(sig.get("upload", {}))[:40],
        "config_remota": sorted(sig.get("remote_config", {}))[:40] + sorted(e["path"] for e in out_eps if re.search(r"Parameter|mobile-config|app-launch", e["path"]))[:10],
        "persistencia_local_room": {"tabelas": extra.get("room_tables", {}), "bases_de_dados": extra.get("room_databases", []),
                                    "anotacoes_runtime": raw["room"]},
    }
    a.out.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    c_h = Counter(h["classe"] for h in host_list)
    c_e = Counter(e["classe"] for e in out_eps)
    c_p = Counter(e["prioridade"] for e in out_eps if e["classe"] == "rebuild")
    sem = sum(1 for e in out_eps if e["classe"] == "rebuild" and e["prioridade"] == "essencial" and not e["screens"])
    print(f"hosts: {len(host_list)} {dict(c_h)}")
    print(f"endpoints: {len(out_eps)} {dict(c_e)}")
    print(f"prioridade (rebuild): {dict(c_p)}")
    print(f"implementados no backend: {sum(1 for e in out_eps if e['backend_handler'])} | com chamadas registadas: {sum(1 for e in out_eps if e['chamadas_registadas'])}")
    print(f"essenciais sem ecra: {sem} | sem regra de host: {sum(1 for h in host_list if h['regra'] == '(omissao)')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

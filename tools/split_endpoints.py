# -*- coding: utf-8 -*-
"""Gera endpoints.discovered.json + endpoints.contract.json (FASE 4).

O V4 exige dois ficheiros, nao um:
  endpoints.discovered.json = catalogo COMPLETO (bottom-up do binario)
  endpoints.contract.json   = SUBCONJUNTO que o clone implementa, com `feature` (F-ID)

O `endpoints.json` curado existente passa a ser a origem do contract; este script
acrescenta o campo `feature` (F-ID de features.md) e separa os dois ficheiros.

Uso:  python tools/split_endpoints.py
"""
import json, os, re, collections

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

DISC_SRC = "ANDOIRD/DRIVER/endpoints.json"
CONTRACT_SRC = "endpoints.json"
FEATURES = "features.md"

# ---------------------------------------------------------------- F-ID por endpoint
# Dominio do endpoint -> dominio da feature. O F-ID concreto e resolvido por
# correspondencia de `screens` com as linhas de features.md quando possivel.
EP_TO_FEATURE_DOM = {
    "identity": "auth",
    "session": "auth",
    "driver": "home",
    "drivers": "home",
    "trip": "trip",
    "trips": "trip",
    "earnings": "earnings",
    "inbox": "inbox",
    "communications": "notifications",
    "support": "support",
    "safety": "safety",
    "documents": "documents",
    "vehicles": "vehicle",
    "finance": "finance",
    "payment": "finance",
    "payments": "finance",
    "common": "platform",
    "backoffice": "platform",
    "lite": "trip",
}

# Mapa manual: endpoint id -> F-ID. Curado a mao porque o contrato tem 39 linhas
# e cada uma tem um dono claro; um regex daria atribuicoes erradas.
EP_FEATURE = {
    "identity.token": "F-auth-01",
    "identity.oauth2_token": "F-auth-01",
    "identity.logout": "F-account-02",
    "identity.push_token": "F-platform-01",
    "identity.device_upsert": "F-platform-01",
    "identity.device_task": "F-platform-01",
    "identity.device_exemption": "F-platform-01",
    "identity.grpc_upsert_user_device": "F-platform-01",
    "common.ramen_ack": "F-platform-01",
    "common.ramen_messages": "F-platform-01",
    "common.health": "F-platform-01",
    "driver.app_launch": "F-onboarding-01",
    "driver.accept": "F-trip-01",
    "driver.reject": "F-trip-01",
    "driver.expire": "F-trip-01",
    "driver.tasks": "F-trip-01",
    "driver.arrive": "F-trip-01",
    "driver.begin": "F-trip-01",
    "driver.end": "F-trip-01",
    "driver.cancel": "F-trip-01",
    "driver.rate": "F-trip-01",
    "driver.offers": "F-trip-01",
    "driver.empty_lists": "F-home-01",
    "driver.profile_hub": "F-menu-02",
    "driver.documents": "F-documents-01",
    "driver.vehicles": "F-vehicle-01",
    "driver.safety_toolkit": "F-safety-01",
    "driver.share_trip": "F-safety-09",
    "driver.trip_receipt": "F-safety-03",
    "driver.payment_methods": "F-finance-01",
    "earnings.summary": "F-earnings-01",
    "earnings.week": "F-earnings-02",
    "earnings.payouts": "F-finance-03",
    "earnings.opportunities": "F-discover-01",
    "inbox.messages": "F-inbox-01",
    "inbox.read": "F-inbox-02",
    "backoffice.trips": "F-platform-01",
    "backoffice.changes": "F-platform-01",
    "lite.session": "F-auth-01",
    "lite.active": "F-trip-01",
    # --- restantes do contrato (mapeamento por dono, ver EP_TO_FEATURE_DOM)
    "rider.app-launch": "F-onboarding-01",
    "rider.status": "F-home-01",
    "rider.lite-home": "F-home-01",
    "rider.lite-quote": "F-trip-01",
    "rider.lite-active": "F-trip-01",
    "rider.lite-account-home": "F-account-03",
    "rider.lite-location": "F-home-03",
    "driver.positions": "F-home-01",
    "driver.route": "F-trip-01",
    "realtime.ramen": "F-platform-01",
    "fleet.drivers": "F-platform-01",
    "fleet.vehicle-create": "F-vehicle-01",
    "backoffice.settings": "F-platform-01",
}


def load_fids(path):
    fids = {}
    if not os.path.exists(path):
        return fids
    for ln in open(path, encoding="utf-8"):
        if ln.startswith("| `F-"):
            cols = [c.strip() for c in ln.strip("|").split("|")]
            fids[cols[0].strip("`")] = (cols[1], cols[2])
    return fids


fids_driver = load_fids("features.md")
fids_rider = load_fids("ANDOIRD/USER_LITE/features.md")
all_fids = {**fids_driver, **fids_rider}

# ---------------------------------------------------------------- discovered
disc = json.load(open(DISC_SRC, encoding="utf-8"))
out_disc = {
    "schema": "qolari.endpoints.discovered/1",
    "app": disc.get("app"),
    "versao": disc.get("versao_referencia"),
    "fonte": DISC_SRC,
    "nota": (
        "Catalogo COMPLETO extraido do binario (bottom-up). Nao e o contrato: "
        "o contrato e endpoints.contract.json. O universo de endpoints nao se "
        "confunde com o subconjunto implementado (FEATURE_TAXONOMY §10)."
    ),
    "disposicao": {},
    "hosts": disc.get("hosts", []),
    "endpoints": [],
}

disp = collections.Counter()
contratados = set()
for e in json.load(open(CONTRACT_SRC, encoding="utf-8"))["endpoints"]:
    contratados.add((e.get("method"), e.get("path")))

for e in disc["endpoints"]:
    classe = e.get("classe")
    # `rebuild` = o nosso backend implementa (vira contrato).
    # `substituir` = equivalente proprio (o nosso backend tambem implementa).
    # `descartar` = telemetria/ads/tracking, nunca entra no contrato.
    disposition = {
        "rebuild": "contract",
        "substituir": "substituir",
        "descartar": "descartar",
    }.get(classe, "por_classificar")
    disp[disposition] += 1
    out_disc["endpoints"].append({
        "http": e.get("http"),
        "path": e.get("path"),
        "origin": e.get("origem"),
        "disposition": disposition,
        "classe_binario": classe,
        "screens": e.get("screens") or [],
        "screens_confianca": e.get("screens_confianca"),
        "prioridade": e.get("prioridade"),
        "backend_handler": e.get("backend_handler"),
        "is_contract": (e.get("http"), e.get("path")) in contratados,
        "request_hint": e.get("corpo"),
        "response_hint": e.get("resposta"),
    })

out_disc["disposicao"] = dict(disp)
out_disc["total"] = len(out_disc["endpoints"])
out_disc["no_contract"] = sum(1 for e in out_disc["endpoints"] if e["is_contract"])

with open("endpoints.discovered.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(out_disc, f, ensure_ascii=False, indent=1)

# ---------------------------------------------------------------- contract
contract = json.load(open(CONTRACT_SRC, encoding="utf-8"))

# Um endpoint do contrato pode vir de dois sitios, e a diferenca importa:
#   extracted -> observado/extraido do binario (o discovered tem a linha)
#   designed  -> desenhado por nos (Lite e WebView; backoffice nao existe no original)
disc_index = {(e["http"], e["path"]) for e in out_disc["endpoints"]}
disc_paths = {e["path"] for e in out_disc["endpoints"]}

sem_feature = []
for e in contract["endpoints"]:
    fid = EP_FEATURE.get(e.get("id"))
    if not fid:
        # tentar por dominio do owner
        dom = EP_TO_FEATURE_DOM.get(e.get("owner"), None)
        if dom:
            cand = [f for f, (d, _) in fids_driver.items() if d == dom]
            fid = cand[0] if cand else None
    e["feature"] = fid
    if not fid:
        sem_feature.append(e.get("id"))

    met = str(e.get("method") or "")
    key = (met, e.get("path"))
    if key in disc_index:
        e["origin"] = "extracted"
    elif e.get("path") in disc_paths:
        e["origin"] = "extracted"      # metodo difere (GET|POST no contrato)
    else:
        e["origin"] = "designed"

contract["schema"] = "qolari.endpoints.contract/1"
contract["nota"] = (
    "SUBCONJUNTO implementado do catalogo descoberto. Cada endpoint tem `feature` "
    "(F-ID de features.md) e `origin` — o gate da FASE 4 exige ambos. "
    "`extracted` = veio do binario; `designed` = desenhado por nos (a Rider Lite e "
    "WebView, o backoffice nao existe no original). O universo esta em "
    "endpoints.discovered.json."
)
contract["fonte_discovered"] = "endpoints.discovered.json"
contract["total"] = len(contract["endpoints"])
contract["com_feature"] = sum(1 for e in contract["endpoints"] if e.get("feature"))
contract["por_origem"] = {
    "extracted": sum(1 for e in contract["endpoints"] if e.get("origin") == "extracted"),
    "designed": sum(1 for e in contract["endpoints"] if e.get("origin") == "designed"),
}

with open("endpoints.contract.json", "w", encoding="utf-8", newline="\n") as f:
    json.dump(contract, f, ensure_ascii=False, indent=1)

print("endpoints.discovered.json:", out_disc["total"], "endpoints", dict(disp))
print("  ligados ao contrato:", out_disc["no_contract"])
print("endpoints.contract.json:", contract["total"], "endpoints",
      "com feature:", contract["com_feature"], contract["por_origem"])
if sem_feature:
    print("  SEM FEATURE:", sem_feature)

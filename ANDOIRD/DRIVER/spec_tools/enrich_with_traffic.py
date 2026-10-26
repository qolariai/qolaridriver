# -*- coding: utf-8 -*-
"""P4 (afinacao) - enriquece endpoints.json com trafego real do servidor (agregado, sem corpos de pedidos).

Uso: python enrich_with_traffic.py --endpoints endpoints.json --traffic hetzner_traffic.json [--timeline hetzner_timeline.json] --source "Hetzner (logs 11-17/10)"

Para cada endpoint: chamadas, estados, dias e handler visto no servidor; 'lacuna_backend' quando a app o chama e o backend nao tem handler.
Promove a 'essencial' os 'rebuild' vistos em trafego real. Ignora o ruido de rastreadores da internet.
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

APP = re.compile(r"^/(rt|api/grpc|ramen|oauth|uber\.|v1/projects|v1/launch|status)")
NOISE = re.compile(r"\.env|_catalog|login\.action|credentials")
POLL = ("uploadpositions", "supplyInput", "/ramen/", "UflurryV2", "RamenStreaming", "upload-earner-experience-state")
FLOW = re.compile(r"go-online|go-offline|ack-offers|accept-offers|reject-offers|start-waiting|confirm-pin|trips/v2/(begin|end|driver-)|get-daily-earnings|get-balance|get-activity-feed")


def norm(p):
    return re.sub(r"\{[^}]+\}", "{}", p.rstrip("/"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoints", required=True, type=Path)
    ap.add_argument("--traffic", required=True, type=Path)
    ap.add_argument("--timeline", type=Path, default=None)
    ap.add_argument("--source", default="servidor")
    a = ap.parse_args()
    doc = json.loads(a.endpoints.read_text(encoding="utf-8"))
    tr = json.loads(a.traffic.read_text(encoding="utf-8"))
    app = [p for p in tr["paths"] if APP.match(p["path"]) and not NOISE.search(p["path"])]
    ruido = [p for p in tr["paths"] if p not in app]
    by = {}
    for p in app:
        by.setdefault(norm(p["path"]), []).append(p)
    promovidos = 0
    lacunas = []
    vistos = set()
    for e in doc["endpoints"]:
        hits = by.get(norm(e["path"]), [])
        e["chamadas_servidor"] = sum(h["chamadas"] for h in hits)
        if hits:
            vistos.add(norm(e["path"]))
            est = Counter()
            dias = Counter()
            for h in hits:
                est.update(h["estados"]); dias.update(h["dias"])
            e["estados_servidor"] = dict(est)
            e["dias_servidor"] = dict(sorted(dias.items()))
            handlers = {h["handler"] for h in hits}
            e["handler_servidor"] = sorted(handlers)[0] if len(handlers) == 1 else sorted(handlers)
            sem = all("SEM HANDLER" in (h["handler"] or "") for h in hits)
            e["lacuna_backend"] = bool(sem and not e["backend_handler"] and e["classe"] == "rebuild")
            if e["classe"] == "rebuild" and e["prioridade"] != "essencial":
                e["prioridade"] = "essencial"; e["regra"] += " | promovido: visto em trafego real"; promovidos += 1
            if e["lacuna_backend"]:
                lacunas.append({"http": e["http"], "path": e["path"], "chamadas": e["chamadas_servidor"], "classe": e["classe"], "screens": e["screens"]})
        else:
            e["lacuna_backend"] = False
    lacunas.sort(key=lambda x: -x["chamadas"])
    fluxo = []
    if a.timeline and a.timeline.exists():
        last = None
        for t, mt, p, st, h in json.loads(a.timeline.read_text(encoding="utf-8")):
            if FLOW.search(p) and not any(x in p for x in POLL) and p != last:
                fluxo.append({"hora_utc": t, "http": mt, "path": p, "estado": st, "handler": h}); last = p
    doc["trafego_servidor"] = {
        "fonte": a.source, "linhas_de_pedido": tr["linhas_de_pedido"], "ficheiros": tr["ficheiros"],
        "paths_da_app": len(app), "chamadas_da_app": sum(p["chamadas"] for p in app),
        "paths_de_ruido_ignorados": len(ruido), "chamadas_de_ruido_ignoradas": sum(p["chamadas"] for p in ruido),
        "paths_da_app_fora_do_contrato": sorted(p["path"] for p in app if norm(p["path"]) not in {norm(e["path"]) for e in doc["endpoints"]}),
        "promovidos_a_essencial": promovidos,
        "nota": "Trafego da app renomeada (com.qolari.driver) e da app nova de teste contra o nosso backend; nao e trafego da Uber. Os corpos de pedidos nao foram lidos.",
    }
    doc["lacunas_backend"] = lacunas
    doc["fluxo_viagem_observado_no_laboratorio"] = fluxo[:60]
    a.endpoints.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"paths da app: {len(app)} ({sum(p['chamadas'] for p in app)} chamadas) | ruido ignorado: {len(ruido)} paths")
    print(f"endpoints vistos no servidor: {sum(1 for e in doc['endpoints'] if e['chamadas_servidor'])} | promovidos a essencial: {promovidos} | lacunas do backend: {len(lacunas)}")
    print(f"fluxo de viagem observado: {len(fluxo)} passos")
    return 0


if __name__ == "__main__":
    sys.exit(main())

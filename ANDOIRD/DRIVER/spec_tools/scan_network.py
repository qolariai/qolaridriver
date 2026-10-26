# -*- coding: utf-8 -*-
"""P4 (esqueleto) - varre o smali de uma pasta apktool e extrai identificadores de rede e de dados (so leitura).

Uso: python scan_network.py --decoded <pasta_apktool> --out <network_raw.json>

Recolhe, sem interpretar logica de negocio:
  - endpoints Retrofit (interface, metodo, verbo, path, headers, parametros anotados, corpo, retorno);
  - URLs literais (const-string com http/https/ws/wss) -> hosts;
  - strings de paths soltos (/rt/, /api/grpc/, /ramen/ ...), servicos gRPC;
  - sinais de auth, push (FCM), uploads (multipart), config remota, entidades/queries Room.
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

RE_METHOD = re.compile(r"^\.method (?P<flags>[^\n]*?)(?P<name>[\w$<>]+)\((?P<args>[^)]*)\)(?P<ret>\S+)\n(?P<body>.*?)^\.end method", re.M | re.S)
RE_HTTP = re.compile(r"\.annotation runtime Lretrofit2/http/(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS);\s*(?:value = \"([^\"]*)\")?", re.S)
RE_HTTP_GENERIC = re.compile(r"\.annotation runtime Lretrofit2/http/HTTP;(.*?)\.end annotation", re.S)
RE_HEADERS = re.compile(r"\.annotation runtime Lretrofit2/http/Headers;\s*value = \{(.*?)\}", re.S)
RE_SIG = re.compile(r"\.annotation system Ldalvik/annotation/Signature;\s*value = \{(.*?)\}\s*\.end annotation", re.S)
RE_PARAM = re.compile(r"\.param (p\d+)(?:,\s*\"[^\"]*\")?\s*(?:#\s*(\S+))?(.*?)\.end param", re.S)
RE_PARAM_ANN = re.compile(r"\.annotation runtime Lretrofit2/http/(\w+);\s*(?:(?:value|name) = \"([^\"]*)\")?", re.S)
RE_URL = re.compile(r"const-string(?:/jumbo)? [vp]\d+, \"((?:https?|wss?)://[^\"]+)\"")
RE_PATHSTR = re.compile(r"const-string(?:/jumbo)? [vp]\d+, \"(/(?:rt|api|ramen|v\d+|oauth|login|gw|grpc)/[^\" ]{2,200})\"")
RE_GRPC = re.compile(r"\"(/?(?:uber|com\.uber)\.[\w.]+/\w+)\"")
SIGNALS = {
    "auth": re.compile(r"\"(x-uber-token|[Aa]uthorization|Bearer |refresh_token|access_token|grant_type|oauth[\w/-]*|x-uber-[\w-]*session[\w-]*)\""),
    "push": re.compile(r"Lcom/google/firebase/messaging/FirebaseMessagingService;|\"(gcm|fcm)[\w.-]*\""),
    "upload": re.compile(r"Lretrofit2/http/Multipart;|Lretrofit2/http/Part;|\"multipart/form-data\"|\"[\w/-]*upload[\w/-]*\""),
    "remote_config": re.compile(r"\"[\w/.-]*(mobile-config|remote[-_]config|flipr|bootstrap|app-launch|parameters|experiment)[\w/.-]*\""),
}
RE_ROOM_ENTITY = re.compile(r"\.annotation runtime Landroidx/room/Entity;(.*?)\.end annotation", re.S)
RE_ROOM_QUERY = re.compile(r"\.annotation runtime Landroidx/room/Query;\s*value = \"([^\"]*)\"", re.S)
RE_CLASS = re.compile(r"^\.class [^\n]*?(L[^;\s]+;)", re.M)


def strs(block):
    return re.findall(r"\"((?:[^\"\\]|\\.)*)\"", block or "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decoded", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    dec = a.decoded.resolve()
    roots = sorted(p for p in dec.iterdir() if p.is_dir() and p.name.startswith("smali"))
    endpoints, urls, paths, grpc = [], defaultdict(set), defaultdict(set), defaultdict(set)
    signals = {k: defaultdict(set) for k in SIGNALS}
    room = {"entities": [], "queries": []}
    nfiles = 0
    for r in roots:
        for dirpath, _, fs in os.walk(r):
            for f in fs:
                if not f.endswith(".smali"):
                    continue
                nfiles += 1
                p = os.path.join(dirpath, f)
                try:
                    s = open(p, encoding="utf-8", errors="ignore").read()
                except OSError:
                    continue
                rel = os.path.relpath(p, dec).replace(os.sep, "/")
                m = RE_CLASS.search(s)
                cls = m.group(1)[1:-1].replace("/", ".") if m else rel
                if "Lretrofit2/http/" in s:
                    for mm in RE_METHOD.finditer(s):
                        body = mm.group("body")
                        verb, path = None, None
                        h = RE_HTTP.search(body)
                        if h:
                            verb, path = h.group(1), h.group(2) or ""
                        else:
                            g = RE_HTTP_GENERIC.search(body)
                            if g:
                                kv = dict(re.findall(r"(\w+) = \"([^\"]*)\"", g.group(1)))
                                verb, path = kv.get("method"), kv.get("path", "")
                        if not verb:
                            continue
                        hdr = RE_HEADERS.search(body)
                        sig = RE_SIG.search(body)
                        params = []
                        for pm in RE_PARAM.finditer(body):
                            anns = RE_PARAM_ANN.findall(pm.group(3))
                            params.append({"reg": pm.group(1), "type": pm.group(2),
                                           "annotations": [{"kind": k, "name": v or None} for k, v in anns]})
                        endpoints.append({"interface": cls, "operation": mm.group("name"), "http": verb,
                                          "path": path, "headers": strs(hdr.group(1)) if hdr else [],
                                          "args": mm.group("args"), "return": mm.group("ret"),
                                          "signature": "".join(strs(sig.group(1))) if sig else None,
                                          "params": params, "smali": rel})
                if "://" in s:
                    for u in RE_URL.findall(s):
                        urls[u].add(cls)
                if "\"/" in s:
                    for u in RE_PATHSTR.findall(s):
                        paths[u].add(cls)
                    for u in RE_GRPC.findall(s):
                        grpc[u].add(cls)
                for k, rx in SIGNALS.items():
                    for x in rx.findall(s):
                        val = x if isinstance(x, str) and x else rx.pattern[:40]
                        signals[k][val].add(cls)
                if "Landroidx/room/" in s:
                    for e in RE_ROOM_ENTITY.finditer(s):
                        kv = dict(re.findall(r"(\w+) = \"([^\"]*)\"", e.group(1)))
                        room["entities"].append({"class": cls, "tableName": kv.get("tableName"), "smali": rel})
                    for q in RE_ROOM_QUERY.findall(s):
                        room["queries"].append({"class": cls, "sql": q[:300]})
    out = {"source": str(dec), "smali_files": nfiles, "retrofit_endpoints": endpoints,
           "urls": {u: sorted(c)[:5] for u, c in sorted(urls.items())},
           "path_strings": {u: sorted(c)[:5] for u, c in sorted(paths.items())},
           "grpc_strings": {u: sorted(c)[:5] for u, c in sorted(grpc.items())},
           "signals": {k: {v: sorted(c)[:5] for v, c in sorted(d.items())} for k, d in signals.items()},
           "room": room}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"smali: {nfiles} | retrofit: {len(endpoints)} | urls: {len(urls)} | paths soltos: {len(paths)} | grpc: {len(grpc)} | "
          f"room: {len(room['entities'])} entidades, {len(room['queries'])} queries | "
          + " | ".join(f"{k}: {len(v)}" for k, v in signals.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

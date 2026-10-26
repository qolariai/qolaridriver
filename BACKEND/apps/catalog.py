# -*- coding: utf-8 -*-
"""Catalogo de endpoints de cada APK (extraido do smali; ficheiros em contracts/).

    rider  contracts/rider_endpoints.json  (1055: metodo, path, operacao, tipo de resposta)
           contracts/rider_models.json     (1894 modelos: classe -> campos)
    driver contracts/driver_paths.txt      (1053 paths, sem metodo)
    fleet  contracts/fleet_endpoints.json  (647: metodo, path, servico)
           contracts/fleet_models.json     (527 modelos)

Serve para: normalizar paths reais em templates (/rt/riders/<uuid>/status ->
/rt/riders/{riderUUID}/status), medir a cobertura na consola e mostrar o modelo de resposta
esperado de cada endpoint por mapear.
"""
import functools, json, re
from dataclasses import dataclass

import config

APPS = ("rider", "driver", "fleet")


@dataclass
class Entry:
    app: str
    method: str          # "" = desconhecido (driver)
    path: str
    operation: str = ""
    response: str = ""   # classe do modelo de resposta (se conhecida)
    regex: re.Pattern | None = None


def _compile(path: str) -> re.Pattern:
    out = ""
    for part in re.split(r"(\{[^}]+\})", path):
        out += "[^/]+" if part.startswith("{") else re.escape(part)
    return re.compile(f"^{out}/?$")


@functools.lru_cache(maxsize=None)
def entries(app: str) -> tuple[Entry, ...]:
    d = config.CONTRACTS_DIR
    out = []
    if app == "rider":
        for e in json.loads((d / "rider_endpoints.json").read_text(encoding="utf-8")):
            resp = (e.get("responseType") or "").replace("/", ".")
            out.append(Entry(app, e["http"], e["path"], e.get("operation", ""), resp))
    elif app == "driver":
        for line in (d / "driver_paths.txt").read_text(encoding="utf-8").splitlines():
            if line.strip():
                out.append(Entry(app, "", line.strip()))
    elif app == "fleet":
        for e in json.loads((d / "fleet_endpoints.json").read_text(encoding="utf-8")):
            out.append(Entry(app, e["http"], e["path"], e["service"].split("/")[-1]))
    for e in out:
        e.regex = _compile(e.path)
    return tuple(out)


@functools.lru_cache(maxsize=None)
def models(app: str) -> dict:
    f = config.CONTRACTS_DIR / f"{app}_models.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.is_file() else {}


def match(app: str, method: str, path: str) -> Entry | None:
    """Endpoint do catalogo que corresponde ao pedido (templates com {var} aceitam qualquer segmento)."""
    best = None
    for e in entries(app):
        if e.method and e.method != method:
            continue
        if e.regex.match(path):
            # preferir o mais especifico (menos variaveis)
            if best is None or e.path.count("{") < best.path.count("{"):
                best = e
    return best


def model_fields(app: str, cls: str, depth: int = 0) -> dict | None:
    """Campos de um modelo (1 nivel, + os tipos dos campos) para a consola."""
    m = models(app).get(cls)
    if not m:
        # sufixo (o JSON da Fleet usa FQN com com.qolari; o do Rider com com.qint)
        short = cls.split(".")[-1]
        cands = [k for k in models(app) if k.endswith("." + short)]
        m = models(app).get(cands[0]) if len(cands) == 1 else None
        cls = cands[0] if len(cands) == 1 else cls
    if not m:
        return None
    return {"class": cls, "fields": [{"name": f["name"], "type": f["type"]} for f in m["fields"]]}

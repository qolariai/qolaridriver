# -*- coding: utf-8 -*-
"""Camada de protocolo das 3 apps (API "realtime" da Uber: /rt/..., /ramen/..., login web).

Registo:   @handles("rider", "POST", "/rt/riders/{riderUUID}/status")   (app pode ser tuple)
Handler:   fn(call: Call) -> dict (JSON 200)  |  raise RtError(...)  |  Response (HTML, redirect...)
Sem handler: 200 {} e o pedido fica em EndpointStat com handler="" (a consola lista-os em
"Integracao" com o modelo de resposta esperado, tirado do catalogo das APKs).

Autenticacao: as APKs mandam o token em `x-uber-token` (Driver/Rider) ou `x-qolari-token`
(Fleet: o rebrand trocou 'uber' por 'qolari' em todas as strings) ou `Authorization: Bearer`.
"""
import gzip, json, re, threading, time, traceback
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response
from starlette.concurrency import run_in_threadpool

import config
from apps import catalog
from core.db import session_scope
from core.security import verify
from domain.models import AuthSession, Driver, EndpointStat, FleetUser, Rider, jset, now

TOKEN_HEADERS = ("x-uber-token", "x-qolari-token")
SUBJECT_MODEL = {"rider": Rider, "driver": Driver, "fleet": FleetUser}

# Telemetria/analytics: respondem {} sem contar como "por mapear"
SINK_PREFIXES = (
    "/api/grpc/", "/rt/ads/", "/rt/unified-reporter", "/rt/wisdom-autocapture", "/rt/analytics",
    "/rt/communications/device-token", "/rt/devices/results", "/rt/devices/error-handling",
    "/rt/bug-reporting/", "/rt/apphealth", "/events/", "/rt/presidio", "/rt/flywheel",
)


class RtError(Exception):
    """Erro no formato da edge Uber: HTTP status + {"code": "rtapi.xxx", "message": ...}."""
    def __init__(self, status: int, code: str, message: str, data: dict | None = None):
        super().__init__(message)
        self.status, self.code, self.message, self.data = status, code, message, data

    def body(self):
        out = {"code": self.code if "." in self.code else f"rtapi.{self.code}", "message": self.message}
        if self.data:
            out["data"] = self.data
        return out


@dataclass
class Call:
    app: str
    method: str
    path: str
    vars: dict
    query: dict
    body: dict
    headers: dict
    ip: str
    db: object = None
    _subject: object = field(default=None, repr=False)
    session: AuthSession | None = None

    def get(self, *keys, default=None):
        """Procura a 1.a chave presente no body, depois na query (aceita camelCase e snake_case)."""
        for k in keys:
            if k in self.body and self.body[k] is not None:
                return self.body[k]
            if k in self.query:
                return self.query[k]
        return default

    def token(self) -> str | None:
        for h in TOKEN_HEADERS:
            if self.headers.get(h):
                return self.headers[h]
        scheme, _, tok = self.headers.get("authorization", "").partition(" ")
        if scheme.lower() == "bearer" and tok:
            return tok
        return None

    def subject(self, required: bool = True):
        """Utilizador da sessao (Rider/Driver/FleetUser conforme a app)."""
        if self._subject is not None:
            return self._subject
        model = SUBJECT_MODEL[self.app]
        tok = self.token()
        claims = verify(tok) if tok else None
        subj = None
        if claims and claims.get("app") == self.app and claims.get("typ") == "access":
            sess = self.db.get(AuthSession, claims.get("sid", ""))
            if sess and not sess.revoked:
                self.session = sess
                sess.last_used_at = now()
                subj = self.db.query(model).filter(model.uuid == claims["sub"]).first()
        if subj is None and not config.STRICT_AUTH:
            # laboratorio: sem token valido usa o 1.o utilizador ativo da app (ver domain/seed.py)
            subj = self.db.query(model).order_by(model.id).first()
        if subj is None and required:
            raise RtError(401, "unauthorized", "sessao invalida ou expirada")
        if subj is not None:
            subj.last_seen_at = now()
        self._subject = subj
        return subj


@dataclass
class Route:
    apps: tuple
    method: str
    path: str
    fn: Callable
    regex: re.Pattern
    names: tuple

    @property
    def name(self):
        return f"{self.fn.__module__.split('.')[-1]}.{self.fn.__name__}"


ROUTES: list[Route] = []


def handles(apps, method: str, *paths: str):
    apps = (apps,) if isinstance(apps, str) else tuple(apps)

    def deco(fn):
        for path in paths:
            names = tuple(re.findall(r"\{(\w+)\}", path))
            rx = re.compile("^" + re.sub(r"\\\{\w+\\\}", "([^/]+)", re.escape(path)) + "/?$")
            for m in method.split("|"):
                ROUTES.append(Route(apps, m, path, fn, rx, names))
        return fn
    return deco


def reload_handlers() -> dict:
    """Recarga a quente dos apps/*.py (POST /api/dev/reload): tira as rotas de cada modulo e reimporta-o
    (ficheiros novos em apps/ tambem sao importados). Se um modulo falhar a importar, as rotas dele ficam
    de fora ate a proxima recarga sem erro."""
    import importlib, sys
    from pathlib import Path
    names = sorted(f"apps.{p.stem}" for p in Path(__file__).parent.glob("*.py")
                   if p.stem not in ("__init__", "rtapi", "catalog", "present", "grpc"))
    out = {}
    for name in ["apps.present", *names]:
        ROUTES[:] = [r for r in ROUTES if r.fn.__module__ != name]
        try:
            mod = sys.modules.get(name)
            importlib.reload(mod) if mod else importlib.import_module(name)
            out[name] = sum(1 for r in ROUTES if r.fn.__module__ == name)
        except Exception as e:
            traceback.print_exc()
            out[name] = f"ERRO {type(e).__name__}: {e}"
    return out


def find_route(app: str, method: str, path: str):
    best = None
    for r in ROUTES:
        if app in r.apps and r.method in (method, "*"):
            m = r.regex.match(path)
            if m and (best is None or r.path.count("{") < best[0].path.count("{")):
                best = (r, dict(zip(r.names, m.groups())))
    return best


# ---- trafego em memoria (consola) e em ficheiro ---------------------------------------------
_lock = threading.Lock()
TRAFFIC = {a: deque(maxlen=400) for a in catalog.APPS}
_seq = 0


def _clip(obj, n=6000):
    try:
        s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, default=str)
    except Exception:
        s = str(obj)
    return s if len(s) <= n else s[:n] + "…"


def _record(app, method, path, template, handler, status, ms, call: Call | None, out, raw_len, ctype):
    global _seq
    t = time.time()
    with _lock:
        _seq += 1
        TRAFFIC[app].append({
            "seq": _seq, "ts": t, "method": method, "path": path, "template": template,
            "handler": handler, "status": status, "ms": round(ms, 1),
            "request": _clip(call.body) if call and call.body else ("" if not raw_len else f"<{raw_len} bytes {ctype}>"),
            "query": call.query if call else {}, "response": _clip(out, 3000)})
        d = config.LOG_DIR / app
        d.mkdir(parents=True, exist_ok=True)
        with open(d / time.strftime("%Y-%m-%d.log"), "a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {status} {method} {path} -> {handler or 'SEM HANDLER'}"
                    f" ({ms:.0f} ms)\n")
            if call and call.body:
                f.write(f"    body: {_clip(call.body, 2000)}\n")
    try:
        with session_scope() as db:
            st = (db.query(EndpointStat)
                  .filter_by(app=app, method=method, path=template).first())
            if not st:
                st = EndpointStat(app=app, method=method, path=template, calls=0, errors=0)
                db.add(st)
            st.calls += 1
            st.errors += 1 if status >= 400 else 0
            st.handler, st.last_status, st.last_at = handler, status, int(t)
            st.last_request = _clip(call.body if call else "", 4000)
            st.last_response = _clip(out, 4000)
    except Exception:
        traceback.print_exc()


def recent(app: str, since: int = 0) -> list[dict]:
    with _lock:
        return [x for x in TRAFFIC[app] if x["seq"] > since]


# ---- despacho -------------------------------------------------------------------------------
def _decode_body(raw: bytes, headers: dict) -> tuple[dict, str]:
    ctype = headers.get("content-type", "")
    if raw[:2] == b"\x1f\x8b" or "gzip" in headers.get("content-encoding", ""):
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
    if not raw:
        return {}, ctype
    if "json" in ctype or raw[:1] in (b"{", b"["):
        try:
            data = json.loads(raw)
            return (data if isinstance(data, dict) else {"_": data}), ctype
        except ValueError:
            pass
    if "x-www-form-urlencoded" in ctype:
        from urllib.parse import parse_qsl
        return dict(parse_qsl(raw.decode("utf-8", "replace"))), ctype
    return {}, ctype


def _run(route: Route | None, call: Call):
    with session_scope() as db:
        call.db = db
        out = route.fn(call) if route else {}
        if isinstance(out, dict) or isinstance(out, list):
            # serializar dentro da sessao (os handlers podem devolver dados lazy)
            return json.loads(jset(out))
        return out


async def dispatch(request: Request, app: str) -> Response:
    t0 = time.perf_counter()
    path = request.url.path
    method = request.method
    headers = {k.lower(): v for k, v in request.headers.items()}
    raw = await request.body()
    body, ctype = _decode_body(raw, headers)
    query = dict(request.query_params)
    if method == "OPTIONS":
        return Response(status_code=204, headers={"Access-Control-Allow-Origin": "*",
                                                  "Access-Control-Allow-Headers": "*",
                                                  "Access-Control-Allow-Methods": "*"})
    found = find_route(app, method, path)
    route, vars_ = found if found else (None, {})
    entry = None if route else catalog.match(app, method, path)
    template = route.path if route else (entry.path if entry else path)
    sink = not route and path.startswith(SINK_PREFIXES)
    handler = route.name if route else ("sink" if sink else "")
    call = Call(app, method, path, vars_, query, body, headers,
                request.client.host if request.client else "")
    status = 200
    try:
        out = await run_in_threadpool(_run, route, call)
    except RtError as e:
        status, out = e.status, e.body()
    except Exception as e:  # bug num handler: 500 no formato Uber (e o traceback na consola)
        traceback.print_exc()
        status, out = 500, {"code": "rtapi.internal_error", "message": f"{type(e).__name__}: {e}"}
    ms = (time.perf_counter() - t0) * 1000
    if isinstance(out, Response):
        _record(app, method, path, template, handler, out.status_code, ms, call,
                f"<{out.media_type or 'resposta'}>", len(raw), ctype)
        return out
    await run_in_threadpool(_record, app, method, path, template, handler, status, ms, call, out,
                            len(raw), ctype)
    return JSONResponse(out, status_code=status)

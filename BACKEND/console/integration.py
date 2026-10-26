# -*- coding: utf-8 -*-
"""Pagina 'Integracao' da consola: estado de cada app, cobertura do contrato, trafego ao vivo.

Junta 3 fontes: o catalogo das APKs (apps/catalog.py), as rotas implementadas (apps/rtapi.ROUTES)
e o uso real (EndpointStat + trafego em memoria). O objetivo e ver depressa o que a app pediu e
ainda nao tem resposta propria (handler vazio) e qual o modelo de resposta que ela espera.
"""
import socket

from fastapi import APIRouter, Depends, HTTPException

import config
from apps import catalog, rtapi
from console.auth import current
from core.db import session_scope
from domain.models import AuthSession, Device, EndpointStat, now

router = APIRouter(prefix="/api/integration", dependencies=[Depends(current)])

LABEL = {"rider": "Qolari Rider", "driver": "Qolari Driver", "fleet": "Qolari Fleet"}
APK = {"rider": "USER/final_apks (com.qolari.rider)", "driver": "DRIVER/qolari-drive.apk (com.qolari.driver)",
       "fleet": "FLEET/QolariFleet.apk (com.qolari.fleet)"}


def _listening(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def _app_or_404(app: str):
    if app not in catalog.APPS:
        raise HTTPException(404, "app desconhecida")


def _implemented(app: str) -> set[tuple[str, str]]:
    return {(r.method, r.path) for r in rtapi.ROUTES if app in r.apps}


@router.get("")
def overview():
    out = []
    with session_scope() as db:
        for app in catalog.APPS:
            stats = db.query(EndpointStat).filter(EndpointStat.app == app).all()
            entries = catalog.entries(app)
            impl_paths = {p for _, p in _implemented(app)}
            port = config.APP_PORTS[app]
            out.append({
                "app": app, "label": LABEL[app], "apk": APK[app], "port": port, "listening": _listening(port),
                "base_url": f"http://{config.PUBLIC_HOST}" + ("" if port == 80 else f":{port}"),
                "catalog_endpoints": len(entries),
                "catalog_implemented": sum(1 for e in entries if e.path in impl_paths),
                "routes": len(_implemented(app)),
                "called": len(stats), "calls": sum(s.calls for s in stats),
                "unmapped_called": sum(1 for s in stats if not s.handler),
                "errors": sum(s.errors for s in stats),
                "last_call_at": max((s.last_at for s in stats), default=None),
                "sessions_active": db.query(AuthSession).filter(AuthSession.app == app,
                                                                AuthSession.revoked.is_(False),
                                                                AuthSession.last_used_at >= now() - 86400).count(),
                "devices": db.query(Device).filter(Device.app == app).count()})
    return out


@router.get("/{app}/endpoints")
def endpoints(app: str, filter: str = "called", q: str = ""):
    """filter: called (pedidos reais) | unmapped (pedidos sem handler) | catalog (tudo o que a APK conhece)."""
    _app_or_404(app)
    impl = _implemented(app)
    impl_paths = {p for _, p in impl}
    with session_scope() as db:
        stats = {(s.method, s.path): s for s in db.query(EndpointStat).filter(EndpointStat.app == app).all()}
        rows = []
        if filter == "catalog":
            for e in catalog.entries(app):
                st = next((s for (m, p), s in stats.items() if p == e.path and (not e.method or m == e.method)), None)
                rows.append({"method": e.method or "?", "path": e.path, "operation": e.operation,
                             "response": e.response.split(".")[-1] if e.response else "",
                             "implemented": e.path in impl_paths, "calls": st.calls if st else 0,
                             "last_at": st.last_at if st else None, "last_status": st.last_status if st else None})
        else:
            for (m, p), s in stats.items():
                if filter == "unmapped" and (s.handler or s.handler == "sink"):
                    continue
                e = catalog.match(app, m, p) if not s.handler else None
                rows.append({"method": m, "path": p, "handler": s.handler, "calls": s.calls, "errors": s.errors,
                             "last_status": s.last_status, "last_at": s.last_at, "first_at": s.first_at,
                             "implemented": bool(s.handler) and s.handler != "sink", "sink": s.handler == "sink",
                             "in_catalog": bool(e) or bool(s.handler),
                             "operation": e.operation if e else "",
                             "response": e.response.split(".")[-1] if e and e.response else ""})
            rows.sort(key=lambda r: -(r["last_at"] or 0))
        if q:
            rows = [r for r in rows if q.lower() in r["path"].lower() or q.lower() in r.get("operation", "").lower()]
        return {"items": rows[:1500], "total": len(rows)}


@router.get("/{app}/endpoint")
def endpoint_detail(app: str, path: str, method: str = "POST"):
    _app_or_404(app)
    with session_scope() as db:
        st = db.query(EndpointStat).filter_by(app=app, method=method, path=path).first()
        e = catalog.match(app, method, path) or next((x for x in catalog.entries(app) if x.path == path), None)
        model = catalog.model_fields(app, e.response) if e and e.response else None
        if not model and app != "rider" and e and e.operation:
            # Driver/Fleet: tentar <Operacao>Response pelos nomes do catalogo
            op = e.path.rstrip("/").split("/")[-1].replace("-", " ").title().replace(" ", "") + "Response"
            model = catalog.model_fields(app, op)
        return {"method": method, "path": path,
                "catalog": {"method": e.method, "path": e.path, "operation": e.operation,
                            "response": e.response} if e else None,
                "response_model": model,
                "stats": {"calls": st.calls, "errors": st.errors, "handler": st.handler,
                          "last_status": st.last_status, "first_at": st.first_at, "last_at": st.last_at,
                          "last_request": st.last_request, "last_response": st.last_response} if st else None,
                "implemented": any(r.path == path and app in r.apps for r in rtapi.ROUTES)}


@router.get("/{app}/traffic")
def traffic(app: str, since: int = 0):
    _app_or_404(app)
    return {"items": rtapi.recent(app, since)[-200:]}


@router.get("/{app}/model")
def model(app: str, name: str):
    _app_or_404(app)
    m = catalog.model_fields(app, name)
    if not m:
        raise HTTPException(404, "modelo nao encontrado")
    return m


@router.post("/reset-stats")
def reset_stats(user: dict = Depends(current)):
    with session_scope() as db:
        db.query(EndpointStat).delete()
    for q in rtapi.TRAFFIC.values():
        q.clear()
    return {"ok": True}

# -*- coding: utf-8 -*-
"""Aplicacao ASGI unica para as 4 portas.

    porta 80   -> app Driver   (tudo -> apps/rtapi.dispatch)
    porta 8090 -> app Rider
    porta 3000 -> app Fleet
    porta 8300 -> consola: /api/* (console/), / (backoffice React de ../BACKOFFICE/dist)

A app e escolhida pela porta LOCAL onde o pedido entrou (scope["server"]), nao pelo Host.
Para testes/ferramentas: o header `X-Qolari-App: rider|driver|fleet` na porta da consola
encaminha o pedido para essa app (e o que o botao "Testar" da pagina Integracao usa).
"""
import threading, time, traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from sqlalchemy import text

import config
from apps import common, driver, fleet, identity, parameters, rider, rtapi, safety, support, usl, userlite  # noqa: F401  registam as rotas
from console import api as console_api, integration
from core.db import init_db, session_scope
from domain import trips
from domain.models import Trip, TripShare, now
from domain.seed import seed

PORT_APP = {**config.EXTRA_APP_PORTS, **{port: app for app, port in config.APP_PORTS.items()}}
_STARTED_AT = time.time()
_stop = threading.Event()


def _ticker():
    """Relogio do dominio: expira propostas, refaz o despacho, move motoristas simulados."""
    while not _stop.wait(1.0):
        try:
            with session_scope() as db:
                trips.tick(db)
        except Exception:
            traceback.print_exc()
            time.sleep(2)


@asynccontextmanager
async def lifespan(_app):
    init_db()
    with session_scope() as db:
        seed(db)
    t = threading.Thread(target=_ticker, name="ticker", daemon=True)
    if config.RUN_TICKER:
        t.start()
    yield
    _stop.set()


app = FastAPI(title="Qolari Mobility — backend", lifespan=lifespan, docs_url="/api/docs",
              openapi_url="/api/openapi.json")
app.include_router(console_api.router)
app.include_router(integration.router)


@app.middleware("http")
async def route_by_port(request: Request, call_next):
    server = request.scope.get("server") or ("", 0)
    target = PORT_APP.get(server[1])
    forced = request.headers.get("x-qolari-app")
    if target is None and forced in config.APP_PORTS:
        target = forced
    if target and request.url.path.startswith("/static/"):  # imagens dos produtos (seletor da app Rider)
        f = (config.STATIC_DIR / request.url.path[len("/static/"):]).resolve()
        if config.STATIC_DIR.resolve() in f.parents and f.is_file():
            return FileResponse(f, headers={"Cache-Control": "public, max-age=86400"})
    if target:
        return await rtapi.dispatch(request, target)
    return await call_next(request)


@app.get("/share/{token}", include_in_schema=False)
def share_page(token: str):
    """Pagina publica de acompanhamento de uma viagem partilhada (sem login)."""
    import html as _html

    with session_scope() as db:
        share = db.query(TripShare).filter_by(token=token).first()
        if not share or share.expires_at < now():
            return HTMLResponse(
                "<h1>Ligação inválida ou expirada</h1>", status_code=404
            )
        trip = db.query(Trip).filter_by(uuid=share.trip_uuid).first()
        if not trip:
            return HTMLResponse("<h1>Viagem indisponível</h1>", status_code=404)
        labels = {
            "requested": "À procura de motorista",
            "accepted": "Motorista a caminho",
            "arrived": "Motorista no local",
            "in_progress": "Em viagem",
            "completed": "Viagem concluída",
            "cancelled": "Viagem cancelada",
            "no_drivers": "Sem motoristas",
        }
        state = labels.get(trip.state, trip.state)
        driver = trip.driver
        driver_name = getattr(driver, "name", "") or "—"
        plate = getattr(trip.vehicle, "plate", "") if trip.vehicle else ""
        pickup = _html.escape(trip.pickup_address or "Recolha")
        dropoff = _html.escape(trip.dropoff_address or "Destino")
        body = f"""<!doctype html><html lang="pt"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Qolari — viagem partilhada</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f6f6f6;color:#111}}
main{{max-width:520px;margin:0 auto;padding:24px}}h1{{font-size:22px}}
.card{{background:#fff;border-radius:14px;padding:20px;margin-top:16px}}
.state{{font-size:26px;font-weight:700;margin:4px 0 16px}}
.row{{padding:10px 0;border-bottom:1px solid #eee}}.row:last-child{{border:0}}
.label{{color:#6b6b6b;font-size:13px}}.value{{font-size:16px;margin-top:2px}}
.muted{{color:#6b6b6b;font-size:13px;margin-top:18px}}</style></head><body><main>
<h1>Qolari</h1><div class="card"><div class="label">Estado</div>
<div class="state">{_html.escape(state)}</div>
<div class="row"><div class="label">Recolha</div><div class="value">{pickup}</div></div>
<div class="row"><div class="label">Destino</div><div class="value">{dropoff}</div></div>
<div class="row"><div class="label">Motorista</div><div class="value">{_html.escape(driver_name)}</div></div>
<div class="row"><div class="label">Veículo</div><div class="value">{_html.escape(plate or "—")}</div></div>
</div><p class="muted">Ligação válida até {share.expires_at}. Esta página é apenas de leitura.</p>
</main></body></html>"""
        return HTMLResponse(body)


@app.get("/api/health", include_in_schema=False)
def health():
    db_ok, error = True, None
    try:
        with session_scope() as db:
            db.execute(text("select 1"))
    except Exception as e:  # DB em baixo: o probe deve ver ok=false
        db_ok, error = False, f"{type(e).__name__}: {e}"
    return {
        "ok": db_ok,
        "db": "ok" if db_ok else "error",
        "error": error,
        "environment": config.ENVIRONMENT,
        "uptime_s": round(time.time() - _STARTED_AT),
        "ports": {**config.APP_PORTS, "console": config.CONSOLE_PORT},
    }


@app.post("/api/dev/reload", include_in_schema=False)
def dev_reload(request: Request):
    """Recarrega os handlers das apps (apps/*.py) sem reiniciar o servidor. So a partir deste PC."""
    if not request.client or request.client.host not in ("127.0.0.1", "::1"):
        raise HTTPException(403, "so a partir de 127.0.0.1")
    return {"routes": rtapi.reload_handlers()}


@app.get("/{path:path}", include_in_schema=False)
def backoffice(path: str):
    """Build do React (assets) ou index.html (rotas do React Router)."""
    if path.startswith("api/"):
        raise HTTPException(404, "endpoint inexistente")
    dist = config.BACKOFFICE_DIST.resolve()
    target = (dist / path).resolve()
    if path and target.is_file() and dist in target.parents:
        return FileResponse(target)
    index = dist / "index.html"
    if not index.is_file():
        return JSONResponse({"detail": "backoffice por compilar: cd ../BACKOFFICE && npm install && npm run build"},
                            status_code=503)
    return FileResponse(index, headers={"Cache-Control": "no-cache"})

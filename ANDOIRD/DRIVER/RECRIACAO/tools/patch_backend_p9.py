# -*- coding: utf-8 -*-
"""Correcoes do backend pedidas depois do lote 5 (documentos, horas online, semana, acentos, rota, notificacoes).
Uso (na pasta BACKEND): python ..\\ANDOIRD\\DRIVER\\RECRIACAO\\tools\\patch_backend_p9.py   Nao publica nada."""
from pathlib import Path

root = Path.cwd()


def rep(rel, a, b, count=1):
    p = root / rel
    s = p.read_text(encoding="utf-8")
    assert a in s, (rel, a[:70])
    p.write_text(s.replace(a, b, count), encoding="utf-8")


# ---- modelos: sessoes online e notificacoes ----
models = root / "domain/models.py"
m = models.read_text(encoding="utf-8")
if "class DriverSession" not in m:
    m += '''

class DriverSession(Base):
    """Periodo em que o motorista esteve online (para as horas online de Rendimentos). ended_at vazio = aberta."""
    __tablename__ = "driver_sessions"
    id: Mapped[int] = mapped_column(primary_key=True)
    driver_id: Mapped[int] = mapped_column(ForeignKey("drivers.id"), index=True)
    started_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    ended_at: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Notification(Base):
    """Notificacao da Caixa de entrada de um motorista."""
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    uuid: Mapped[str] = mapped_column(String(36), unique=True, default=new_uuid)
    owner_type: Mapped[str] = mapped_column(String(10), default="driver")
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    title: Mapped[str] = mapped_column(String(160))
    body: Mapped[str] = mapped_column(String(400), default="")
    created_at: Mapped[int] = mapped_column(Integer, default=now, index=True)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
'''
    models.write_text(m, encoding="utf-8")

# ---- acentos nos lancamentos novos ----
rep("domain/trips.py", '"tarifa"),', '"Tarifa"),')
rep("domain/trips.py", 'f"comissao {pct:g}%"', 'f"Comissão {pct:g}%"')
rep("domain/trips.py", 'f"frota {org.name}"', 'f"Frota {org.name}"')
rep("domain/trips.py", '"desconto promocional"', '"Desconto promocional"')
rep("domain/trips.py", '"recebido em dinheiro"', '"Recebido em dinheiro"')

# ---- sessoes online em go_online / go_offline ----
rep("domain/trips.py", '''    if driver.availability == "offline":
        driver.availability = "online"
        driver.online_since = now()
''', '''    if driver.availability == "offline":
        driver.availability = "online"
        driver.online_since = now()
        open_session(db, driver)
''')
rep("domain/trips.py", '''    driver.availability = "offline"
    driver.online_since = None
''', '''    driver.availability = "offline"
    driver.online_since = None
    close_sessions(db, driver)
''')
rep("domain/trips.py", "def go_online(db, driver: Driver, lat", '''def open_session(db, driver: Driver) -> None:
    """Abre um periodo online (se ja houver um aberto, nao duplica)."""
    from domain.models import DriverSession
    if not db.query(DriverSession).filter_by(driver_id=driver.id, ended_at=None).first():
        db.add(DriverSession(driver_id=driver.id, started_at=now()))


def close_sessions(db, driver: Driver) -> None:
    from domain.models import DriverSession
    for s in db.query(DriverSession).filter_by(driver_id=driver.id, ended_at=None).all():
        s.ended_at = now()


def online_seconds(db, driver_id: int, start: int, end: int) -> int:
    """Segundos online dentro de [start, end), incluindo a sessao em curso."""
    from domain.models import DriverSession
    t = now()
    total = 0
    for s in db.query(DriverSession).filter(DriverSession.driver_id == driver_id, DriverSession.started_at < end).all():
        stop = s.ended_at if s.ended_at is not None else t
        lo, hi = max(s.started_at, start), min(stop, end)
        if hi > lo:
            total += hi - lo
    return total


def go_online(db, driver: Driver, lat''')

# ---- driver.py: semana por data, horas online, documentos, rota, notificacoes ----
rep("apps/driver.py", "from domain.models import Document, LedgerEntry, Offer, Trip, Vehicle, jget, now",
    "from domain.models import Document, LedgerEntry, Notification, Offer, Trip, Vehicle, jget, now")
rep("apps/driver.py", '''    import time as _t
    d = call.subject()
    today = _day_start(now())
    start = today - _t.localtime(today).tm_wday * 86400
    return earnings_period(call.db, d, start, start + 7 * 86400)''', '''    d = call.subject()
    start, end = week_bounds(now())
    return earnings_period(call.db, d, start, end)''')
rep("apps/driver.py", "def earnings_period(db, d, start: int, end: int) -> dict:", '''def week_bounds(ts: int) -> tuple[int, int]:
    """Segunda 00:00 e a segunda seguinte 00:00 (hora local), por data de calendario: nao soma 7x86400 s, que
    erra na semana da mudanca de hora."""
    import datetime as _dt
    import time as _t
    day = _dt.date.fromtimestamp(ts)
    monday = day - _dt.timedelta(days=day.weekday())
    nxt = monday + _dt.timedelta(days=7)
    mk = lambda x: int(_t.mktime((x.year, x.month, x.day, 0, 0, 0, 0, 0, -1)))
    return mk(monday), mk(nxt)


def earnings_period(db, d, start: int, end: int) -> dict:''')
rep("apps/driver.py", '''            "tripCount": len(rows),''', '''            "tripCount": len(rows),
            "onlineSeconds": trips.online_seconds(db, d.id, start, end),''')

p = root / "apps/driver.py"
s = p.read_text(encoding="utf-8")
if "/rt/drivers/v2/documents" not in s:
    s += '''

# ---- documentos, notificacoes e rota (pedidos depois do lote 5) --------------------------------------
DOC_TITLES = {"carta_conducao": "Carta de condução", "certificado_tvde": "Certificado de motorista TVDE",
              "registo_criminal": "Certificado de registo criminal", "cartao_cidadao": "Cartão de cidadão",
              "dua": "DUA", "seguro": "Seguro", "inspecao": "Inspeção"}


def _doc_json(doc: Document) -> dict:
    return {"uuid": doc.uuid, "kind": doc.kind, "title": DOC_TITLES.get(doc.kind, doc.kind.replace("_", " ").capitalize()),
            "status": doc.status, "expiresOn": doc.expires_on, "note": doc.notes or "", "hasFile": bool(doc.file_name)}


@handles(APP, "GET|POST", "/rt/drivers/v2/documents")
def documents(call: Call):
    """Documentos do motorista e do veiculo atual: tipo, estado (pending|approved|rejected), validade e nota."""
    db = call.db
    d = call.subject()
    mine = db.query(Document).filter(Document.owner_type == "driver", Document.owner_id == d.id).order_by(Document.id).all()
    vehicle = []
    if d.vehicle_id:
        vehicle = db.query(Document).filter(Document.owner_type == "vehicle", Document.owner_id == d.vehicle_id).order_by(Document.id).all()
    return {"driverDocuments": [_doc_json(x) for x in mine], "vehicleDocuments": [_doc_json(x) for x in vehicle]}


@handles(APP, "GET|POST", "/rt/inbox/notifications")
def inbox_notifications(call: Call):
    db = call.db
    d = call.subject()
    rows = (db.query(Notification).filter(Notification.owner_type == "driver", Notification.owner_id == d.id)
            .order_by(Notification.created_at.desc()).limit(100).all())
    return {"notifications": [{"uuid": n.uuid, "title": n.title, "body": n.body, "createdAt": present.ms(n.created_at),
                               "read": n.read} for n in rows],
            "unreadCount": sum(1 for n in rows if not n.read)}


@handles(APP, "POST", "/rt/inbox/mark-read")
def inbox_mark_read(call: Call):
    d = call.subject()
    ids = call.get("uuids", "notificationUUIDs", default=[]) or []
    q = call.db.query(Notification).filter(Notification.owner_type == "driver", Notification.owner_id == d.id)
    for n in q.all():
        if not ids or n.uuid in ids:
            n.read = True
    return {}
'''
    s = s.replace('''def navigation_route(call: Call):
    return {}''', '''def navigation_route(call: Call):
    """Rota entre dois pontos (polilinha, distancia e duracao). Sem coordenadas devolve {} como antes."""
    from apps import routing
    b = call.body or {}
    pts = routing.points_from(b, call.query if hasattr(call, "query") else {})
    if not pts:
        return {}
    return routing.route(*pts)''')
    p.write_text(s, encoding="utf-8")

# ---- routing.py novo ----
(root / "apps/routing.py").write_text('''# -*- coding: utf-8 -*-
"""Rota entre dois pontos. Sem chave nem rede, usa a linha reta com a velocidade media da cidade (30 km/h);
com `ROUTING_URL` (um servidor OSRM, ex.: http://127.0.0.1:5000) pede a rota real. Nunca levanta: se o servico falhar, cai na linha reta."""
import json
import math
import os
import urllib.request

AVG_KMH = 30.0


def haversine_m(a: tuple, b: tuple) -> float:
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def points_from(body: dict, query: dict | None = None):
    """((lat, lng), (lat, lng)) a partir de {origin, destination}, {start, end} ou dos parametros da query."""
    src = dict(query or {})
    src.update(body or {})
    for a, b in (("origin", "destination"), ("start", "end"), ("from", "to")):
        o, d = src.get(a), src.get(b)
        if isinstance(o, dict) and isinstance(d, dict):
            p = (_num(o.get("latitude", o.get("lat"))), _num(o.get("longitude", o.get("lng"))))
            q = (_num(d.get("latitude", d.get("lat"))), _num(d.get("longitude", d.get("lng"))))
            if None not in p and None not in q:
                return p, q
    return None


def _straight(a: tuple, b: tuple) -> dict:
    dist = haversine_m(a, b)
    return {"source": "straight_line", "distanceMeters": round(dist), "durationSeconds": round(dist / (AVG_KMH / 3.6)),
            "polyline": [{"latitude": a[0], "longitude": a[1]}, {"latitude": b[0], "longitude": b[1]}]}


def route(a: tuple, b: tuple) -> dict:
    url = os.environ.get("ROUTING_URL", "").rstrip("/")
    if url:
        try:
            req = f"{url}/route/v1/driving/{a[1]},{a[0]};{b[1]},{b[0]}?overview=full&geometries=geojson"
            with urllib.request.urlopen(req, timeout=4) as r:
                data = json.load(r)
            rt = data["routes"][0]
            return {"source": "osrm", "distanceMeters": round(rt["distance"]), "durationSeconds": round(rt["duration"]),
                    "polyline": [{"latitude": lat, "longitude": lng} for lng, lat in rt["geometry"]["coordinates"]]}
        except Exception:
            pass
    return _straight(a, b)
''', encoding="utf-8")
print("ok")

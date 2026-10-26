# -*- coding: utf-8 -*-
"""App Qolari Lite (recriacao da Uber Lite) -> dominio do laboratorio.

Contrato desenhado para a app nova (FASE 4/5 do PROMPT_CLONE_MEGA): a Uber Lite desenha o
conteudo numa WebView e nao expoe um contrato nativo utilizavel. Estes endpoints sao a
"spec do nosso backend" e nao uma copia do protocolo da Uber. Evidencia: designed/static;
ver ANDOIRD/USER_LITE/endpoints.json.

Autenticacao: a mesma das outras apps (`POST /rt/identity/oauth2/token`, grant_type=password,
codigo fixo do laboratorio). O sujeito e um Rider.
"""
from datetime import datetime
import uuid

from apps import geocode, present, routing
from apps.rtapi import Call, RtError, handles
from domain import geo, pricing, settings, trips
from domain.models import (City, Driver, LedgerEntry, Product, Promo, RiderPromo, Setting,
                           SupportMessage, SupportThread, Trip, jget, jset, now)
from domain.trips import TripError

APP = "rider"

# Moradas de exemplo (Lisboa). A morada real do utilizador nunca entra na spec nem na app.
PLACES = [
    {"id": "pombal", "name": "Praça Marquês de Pombal", "line1": "Praça Marquês de Pombal", "line2": "Lisboa",
     "lat": 38.72553, "lng": -9.14997},
    {"id": "rossio", "name": "Praça do Rossio", "line1": "Praça do Rossio", "line2": "Lisboa",
     "lat": 38.71391, "lng": -9.13940},
    {"id": "cordoaria", "name": "Cordoaria Nacional", "line1": "Av. da Índia", "line2": "Lisboa",
     "lat": 38.70251, "lng": -9.20190},
    {"id": "odivelas", "name": "R. Júlio Dinis 16", "line1": "R. Júlio Dinis 16", "line2": "Odivelas",
     "lat": 38.79490, "lng": -9.17980},
    {"id": "aeroporto", "name": "Aeroporto Humberto Delgado", "line1": "Alameda das Comunidades Portuguesas",
     "line2": "Lisboa", "lat": 38.77425, "lng": -9.13422},
    {"id": "oriente", "name": "Gare do Oriente", "line1": "Av. Dom João II", "line2": "Lisboa",
     "lat": 38.76797, "lng": -9.09900},
    {"id": "timeout", "name": "Time Out Market", "line1": "Av. 24 de Julho 49", "line2": "Lisboa",
     "lat": 38.70705, "lng": -9.14590},
    {"id": "lxfactory", "name": "LX Factory", "line1": "R. Rodrigues de Faria 103", "line2": "Lisboa",
     "lat": 38.70350, "lng": -9.17860},
    {"id": "nacoes", "name": "Parque das Nações", "line1": "Alameda dos Oceanos", "line2": "Lisboa",
     "lat": 38.76500, "lng": -9.09500},
    {"id": "belem", "name": "Mosteiro dos Jerónimos", "line1": "Praça do Império", "line2": "Belém, Lisboa",
     "lat": 38.69790, "lng": -9.20650},
    {"id": "luz", "name": "Estádio da Luz", "line1": "Av. Eusébio da Silva Ferreira", "line2": "Lisboa",
     "lat": 38.75270, "lng": -9.18470},
    {"id": "colombo", "name": "Centro Comercial Colombo", "line1": "Av. Lusíada", "line2": "Lisboa",
     "lat": 38.75400, "lng": -9.18800},
]

# Casa do passageiro: fixture neutra, marcada `presumed` na spec. Nao e a morada da conta capturada.
HOME_PLACE = {"id": "home", "name": "Casa", "line1": "R. José Gomes Ferreira", "line2": "Lisboa",
              "lat": 38.75300, "lng": -9.14500}

PAYMENTS = {
    "cash": {"id": "cash", "label": "Dinheiro", "detail": "Pague ao motorista no fim da viagem"},
    "card": {"id": "card", "label": "Cartão •••• 4242", "detail": "Cartão simulado do laboratório"},
}


def _err(e: TripError) -> RtError:
    return RtError(400, e.code, str(e), {"title": "Qolari", "message": str(e)})


def _point(obj) -> tuple[float, float] | None:
    if not isinstance(obj, dict):
        return None
    lat, lng = obj.get("lat", obj.get("latitude")), obj.get("lng", obj.get("longitude"))
    try:
        return (float(lat), float(lng)) if lat is not None and lng is not None else None
    except (TypeError, ValueError):
        return None


def _city(db, lat: float | None = None, lng: float | None = None) -> City:
    cities = db.query(City).filter(City.active.is_(True)).all()
    if not cities:
        raise RtError(503, "no_city", "sem cidades ativas")
    if lat is None or lng is None:
        return cities[0]
    return min(cities, key=lambda c: geo.haversine_m(c.center_lat, c.center_lng, lat, lng))


def _place(p: dict, lat: float | None = None, lng: float | None = None) -> dict:
    out = {"id": p["id"], "name": p["name"], "line1": p.get("line1", ""), "line2": p.get("line2", ""),
           "full": ", ".join(x for x in (p.get("name"), p.get("line2")) if x),
           "lat": p["lat"], "lng": p["lng"]}
    if lat is not None and lng is not None:
        out["distance_m"] = int(geo.haversine_m(lat, lng, p["lat"], p["lng"]))
    return out


def _money(cents: int, currency: str = "EUR") -> str:
    return present.money(cents, currency)


def _nearest_eta(db, lat: float, lng: float, product=None) -> int:
    """ETA (min) do motorista elegivel mais proximo; 1 min se nao houver nenhum (estado da captura)."""
    best = None
    for d in db.query(Driver).filter(Driver.status == "approved", Driver.availability == "online",
                                     Driver.lat.is_not(None)).all():
        v = d.vehicle
        if not v or v.status != "active":
            continue
        if product is not None and (v.product_ids and product.id not in v.product_ids):
            continue
        if product is not None and (v.seats < product.capacity or v.year < product.min_vehicle_year):
            continue
        dist = geo.haversine_m(lat, lng, d.lat, d.lng) * settings.get(db, "road_factor")
        eta = dist / (settings.get(db, "avg_speed_kmh") / 3.6)
        best = eta if best is None else min(best, eta)
    return max(1, round((best or 60) / 60))


def _driver_json(t: Trip) -> dict | None:
    if not t.driver:
        return None
    d, v = t.driver, t.vehicle
    return {
        "uuid": d.uuid,
        "name": d.first_name,
        "rating": d.rating,
        "phone": d.phone,
        "lat": d.lat,
        "lng": d.lng,
        "heading": d.heading or 0.0,
        "vehicle": None if not v else {
            "make": v.make, "model": v.model, "color": v.color, "colorHex": v.color_hex,
            "plate": v.plate, "label": f"{v.make} {v.model}",
        },
    }


def _fare_json(t: Trip) -> dict:
    cur = t.city.currency
    cents = t.fare if t.fare is not None else t.est_fare
    return {"cents": cents, "label": _money(cents, cur), "currency": cur,
            "discount": _money(t.discount, cur) if t.discount else None}


def trip_json(db, t: Trip) -> dict:
    """Estado da viagem para a app Lite. Um so formato para todos os estados."""
    cur = t.city.currency
    eta = None
    if t.state == "accepted" and t.driver and t.driver.lat is not None:
        dist = geo.haversine_m(t.driver.lat, t.driver.lng, t.pickup_lat, t.pickup_lng) * settings.get(db, "road_factor")
        eta = max(1, round(dist / (settings.get(db, "avg_speed_kmh") / 3.6) / 60))
    if t.state == "arrived":
        eta = 0
    trip_eta = None
    if t.state == "in_progress":
        left = max(0, (t.est_duration_s or 0) - (now() - (t.started_at or now())))
        trip_eta = max(1, round(left / 60))
    return {
        "uuid": t.uuid,
        "state": t.state,
        "createdAt": t.requested_at,
        "scheduledAt": present.ms(t.scheduled_at) if t.scheduled_at else None,
        "product": {"id": t.product.id, "name": t.product.name},
        "pickup": {"lat": t.pickup_lat, "lng": t.pickup_lng, "address": t.pickup_address},
        "stops": [{"lat": s.get("lat"), "lng": s.get("lng"), "address": s.get("address", ""),
                   "done": bool(s.get("done"))} for s in jget(t.stops, [])],
        "nextStopIndex": next((i for i, s in enumerate(jget(t.stops, [])) if not s.get("done")), None),
        "dropoff": {"lat": t.dropoff_lat, "lng": t.dropoff_lng, "address": t.dropoff_address},
        "pin": t.pin or None,
        "driver": _driver_json(t),
        "driverEtaMin": eta,
        "tripEtaMin": trip_eta,
        "fare": _fare_json(t),
        "tipCents": t.tip_cents or 0,
        "totalCents": (t.fare if t.fare is not None else t.est_fare) + (t.tip_cents or 0),
        "canTip": t.state == "completed" and not t.tip_cents,
        "payment": t.payment_method,
        "canCancel": t.state in ("requested", "accepted", "arrived"),
        "canRate": t.state == "completed" and t.rider_to_driver_rating is None,
        "myRating": t.rider_to_driver_rating,
        "cancelledBy": t.cancelled_by or None,
        "cancelReason": t.cancel_reason or None,
        "distanceKm": round((t.distance_m or t.est_distance_m or 0) / 1000, 1),
        "durationMin": round((t.duration_s or t.est_duration_s or 0) / 60),
    }


def _trip_for(call: Call, uuid: str | None = None) -> Trip:
    rider = call.subject()
    q = call.db.query(Trip).filter(Trip.rider_id == rider.id)
    t = q.filter_by(uuid=uuid).first() if uuid else q.filter(Trip.state.in_(("requested", "accepted", "arrived",
                                                                             "in_progress"))).first()
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente")
    return t


def _active_or_recent(db, rider) -> Trip | None:
    t = (db.query(Trip).filter(Trip.rider_id == rider.id,
                               Trip.state.in_(("requested", "accepted", "arrived", "in_progress")))
         .order_by(Trip.id.desc()).first())
    if t:
        return t
    # Depois de terminar/cancelar, a app precisa de ver o desfecho antes de voltar ao inicio.
    t = (db.query(Trip).filter(Trip.rider_id == rider.id,
                               Trip.state.in_(("completed", "cancelled", "no_drivers")),
                               Trip.requested_at >= now() - 900)
         .order_by(Trip.id.desc()).first())
    if t and (t.state != "completed" or t.rider_to_driver_rating is None):
        return t
    return None


# ---- sessao e perfil -------------------------------------------------------------------------
def _session_payload(db, rider) -> dict:
    city = _city(db)
    return {"riderUUID": rider.uuid, "firstName": rider.first_name or "Passageiro", "name": rider.name,
            "phone": rider.phone, "email": rider.email, "rating": rider.rating,
            "city": {"name": city.name, "currency": city.currency},
            "memberSince": rider.created_at,
            "payment": PAYMENTS.get(rider.default_payment, PAYMENTS["cash"])}


@handles(APP, "GET", "/rt/lite/session")
def session(call: Call):
    return _session_payload(call.db, call.subject())


@handles(APP, "PATCH", "/rt/lite/account")
def update_account(call: Call):
    """Dados pessoais editaveis na app (nome e e-mail). O telefone e a identidade da conta."""
    db, rider = call.db, call.subject()
    first = str(call.body.get("firstName", rider.first_name) or "").strip()
    last = str(call.body.get("lastName", rider.last_name) or "").strip()
    email = str(call.body.get("email", rider.email) or "").strip()
    if not first:
        raise RtError(400, "missing_name", "indique o nome")
    if len(first) > 60 or len(last) > 60:
        raise RtError(400, "invalid_name", "nome demasiado longo")
    if email and ("@" not in email or email.startswith("@") or email.endswith("@")):
        raise RtError(400, "invalid_email", "e-mail invalido")
    if len(email) > 120:
        raise RtError(400, "invalid_email", "e-mail demasiado longo")
    rider.first_name, rider.last_name, rider.email = first, last, email
    return _session_payload(db, rider)


# ---- inicio e lugares ------------------------------------------------------------------------
def _home_place(db, rider) -> dict:
    """Casa do passageiro: guardada nas preferencias do laboratorio; fixture propria por omissao."""
    row = db.get(Setting, f"rider_home:{rider.id}")
    return jget(row.value, HOME_PLACE) if row else HOME_PLACE


@handles(APP, "POST", "/rt/lite/account/home")
def set_home(call: Call):
    db, rider = call.db, call.subject()
    place_id = str(call.body.get("placeId") or "").strip()
    place = next((p for p in PLACES if p["id"] == place_id), None)
    if place is None and place_id == HOME_PLACE["id"]:
        place = HOME_PLACE
    if place is None:
        raise RtError(404, "place_not_found", "morada desconhecida")
    row = db.get(Setting, f"rider_home:{rider.id}")
    if row:
        row.value = jset(place)
    else:
        db.add(Setting(key=f"rider_home:{rider.id}", value=jset(place)))
    db.flush()
    return {"savedPlace": _place(place)}


@handles(APP, "POST", "/rt/lite/location")
def location(call: Call):
    rider = call.subject()
    p = _point(call.body)
    if not p:
        raise RtError(400, "missing_location", "sem coordenadas")
    rider.lat, rider.lng = p
    return {"ok": True}


# ---- inicio e lugares ------------------------------------------------------------------------
def _acct_get(db, rider, key: str, default):
    row = db.get(Setting, f"rider_{key}:{rider.id}")
    return jget(row.value, default) if row else default


def _acct_set(db, rider, key: str, value):
    row = db.get(Setting, f"rider_{key}:{rider.id}")
    if row:
        row.value = jset(value)
    else:
        db.add(Setting(key=f"rider_{key}:{rider.id}", value=jset(value)))
    db.flush()


def _uber_one_active(db, rider) -> dict:
    data = _acct_get(db, rider, "uber_one", {"active": False, "until": None})
    if data.get("until") and data["until"] < now():
        data["active"] = False
    return data


def _ensure_uber_one_promo(db, rider):
    """Membros Uber One recebem 5% na proxima viagem (promo renovada a cada viagem)."""
    if not _uber_one_active(db, rider).get("active"):
        return
    promo = db.query(Promo).filter_by(code="UBERONE").first()
    if not promo:
        promo = Promo(code="UBERONE", description="Uber One: 5% na viagem",
                      kind="percent", value=5, max_discount=200, per_rider=999)
        db.add(promo)
        db.flush()
    has = (db.query(RiderPromo)
           .filter(RiderPromo.rider_id == rider.id, RiderPromo.promo_id == promo.id,
                   RiderPromo.used_trip_id.is_(None))
           .first())
    if not has:
        db.add(RiderPromo(rider_id=rider.id, promo_id=promo.id))
        db.flush()


@handles(APP, "GET", "/rt/lite/account/extras")
def account_extras(call: Call):
    rider = call.subject()
    return {
        "business": _acct_get(call.db, rider, "business", {"active": False}),
        "family": _acct_get(call.db, rider, "family", {"members": [], "code": f"FAM-{rider.id:04d}"}),
        "uberOne": _uber_one_active(call.db, rider),
    }


@handles(APP, "POST", "/rt/lite/account/business")
def save_business(call: Call):
    rider = call.subject()
    active = bool(call.body.get("active", True))
    data = {
        "active": active,
        "companyName": str(call.body.get("companyName") or "")[:120],
        "vat": str(call.body.get("vat") or "")[:30],
        "email": str(call.body.get("email") or "")[:120],
        "costCenter": str(call.body.get("costCenter") or "")[:60],
    }
    _acct_set(call.db, rider, "business", data)
    return {"business": data}


@handles(APP, "POST", "/rt/lite/account/family")
def save_family(call: Call):
    rider = call.subject()
    data = _acct_get(call.db, rider, "family", {"members": [], "code": f"FAM-{rider.id:04d}"})
    action = str(call.body.get("action") or "add")
    phone = str(call.body.get("phone") or "").strip()[:30]
    if action == "remove":
        data["members"] = [m for m in data["members"] if m.get("phone") != phone]
    else:
        name = str(call.body.get("name") or "").strip()[:80]
        if len(phone) < 6 or not name:
            raise RtError(400, "invalid_member", "indique nome e telefone")
        if len(data["members"]) >= 5:
            raise RtError(409, "family_limit", "maximo de 5 membros")
        if not any(m.get("phone") == phone for m in data["members"]):
            data["members"].append({"name": name, "phone": phone,
                                    "teen": bool(call.body.get("teen"))})
    _acct_set(call.db, rider, "family", data)
    return {"family": data}


@handles(APP, "POST", "/rt/lite/account/uber-one")
def uber_one(call: Call):
    rider = call.subject()
    action = str(call.body.get("action") or "subscribe")
    if action == "cancel":
        data = {"active": False, "until": None}
        promo = call.db.query(Promo).filter_by(code="UBERONE").first()
        if promo:
            call.db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id,
                                             RiderPromo.promo_id == promo.id,
                                             RiderPromo.used_trip_id.is_(None)).delete()
    else:
        data = {"active": True, "until": now() + 30 * 86400, "plan": "Uber One mensal"}
    _acct_set(call.db, rider, "uber_one", data)
    return {"uberOne": data}


@handles(APP, "GET", "/rt/lite/places/saved")
def saved_places(call: Call):
    rider = call.subject()
    row = call.db.get(Setting, f"rider_saved:{rider.id}")
    rows = jget(row.value, []) if row else []
    return {"places": [_place(p, rider.lat, rider.lng) for p in rows]}


@handles(APP, "POST", "/rt/lite/places/saved")
def add_saved_place(call: Call):
    db, rider = call.db, call.subject()
    label = str(call.body.get("label") or "").strip()[:60]
    address = str(call.body.get("address") or "").strip()[:200]
    place_id = str(call.body.get("placeId") or "").strip()
    row = db.get(Setting, f"rider_saved:{rider.id}")
    rows = jget(row.value, []) if row else []
    if len(rows) >= 8:
        raise RtError(409, "saved_limit", "maximo de 8 locais guardados")
    place = None
    if place_id:
        place = next((p for p in PLACES if p["id"] == place_id), None)
        if place is None and place_id == HOME_PLACE["id"]:
            place = HOME_PLACE
    if place is None:
        lat, lng = call.body.get("lat"), call.body.get("lng")
        if lat is not None and lng is not None:
            place = {"id": "", "name": label or address, "line1": address, "line2": "",
                     "lat": float(lat), "lng": float(lng)}
        else:
            found = geocode.places_search(address or label, rider.lat, rider.lng)
            if not found:
                raise RtError(404, "place_not_found", "morada nao encontrada")
            place = found
    item = {"id": uuid.uuid4().hex[:12], "name": label or place.get("name") or address,
            "line1": address or place.get("line1", ""), "line2": place.get("line2", ""),
            "lat": place["lat"], "lng": place["lng"]}
    rows.append(item)
    if row:
        row.value = jset(rows)
    else:
        db.add(Setting(key=f"rider_saved:{rider.id}", value=jset(rows)))
    db.flush()
    return {"savedPlace": _place(item, rider.lat, rider.lng)}


@handles(APP, "DELETE", "/rt/lite/places/saved/{placeId}")
def delete_saved_place(call: Call):
    db, rider = call.db, call.subject()
    row = db.get(Setting, f"rider_saved:{rider.id}")
    rows = jget(row.value, []) if row else []
    rows = [p for p in rows if p.get("id") != call.vars["placeId"]]
    if row:
        row.value = jset(rows)
    db.flush()
    return {"ok": True}


@handles(APP, "GET", "/rt/lite/home")
def home(call: Call):
    db, rider = call.db, call.subject()
    city = _city(db)
    saved = _home_place(db, rider)
    lat, lng = rider.lat, rider.lng
    if lat is None or lng is None:
        lat, lng = saved["lat"], saved["lng"]
    eta = _nearest_eta(db, lat, lng)
    return {
        "greeting": "Bom dia" if datetime.now().hour < 12 else ("Boa tarde" if datetime.now().hour < 20 else "Boa noite"),
        "firstName": rider.first_name or "Passageiro",
        "headline": f"O seu motorista pode chegar em {eta} min",
        "etaMin": eta,
        "savedPlace": _place(saved),
        "city": city.name,
        "cash": {"cents": 0, "label": "0,00 €", "currency": city.currency},
        "suggestions": [
            {"id": "ride", "title": "Viajar", "subtitle": "Peça uma viagem", "icon": "car"},
        ],
        "promos": [
            {"id": "bemvindo", "title": "Poupe uma viagem", "subtitle": "Use o código BEMVINDO",
             "action": "Use o código"},
            {"id": "ritmo", "title": "Viaje ao seu ritmo", "subtitle": "Peça quando quiser",
             "action": "Peça uma viagem"},
        ],
    }


@handles(APP, "GET", "/rt/lite/places")
def places(call: Call):
    rider = call.subject()
    q = str(call.query.get("q", "") or "").strip().lower()
    lat, lng = rider.lat, rider.lng
    if q:
        real = geocode.places_search(q, lat, lng) or geocode.forward(q, lat, lng)
        if real:
            out = [_place(p, lat, lng) for p in real]
            if q in "casa home":
                out.insert(0, _place(HOME_PLACE, lat, lng))
            return {"places": out[:10]}
    rows = [p for p in PLACES if not q or q in p["name"].lower() or q in p["line1"].lower()
            or q in p["line2"].lower()]
    if lat is not None and lng is not None:
        rows.sort(key=lambda p: geo.haversine_m(lat, lng, p["lat"], p["lng"]))
    out = [_place(p, lat, lng) for p in rows]
    if q and q in "casa home":
        out.insert(0, _place(HOME_PLACE, lat, lng))
    return {"places": out[:10]}


# ---- estimativa e pedido ---------------------------------------------------------------------
@handles(APP, "POST", "/rt/lite/route")
def route(call: Call):
    """Rota por estrada para o mapa da Rider (designed; OSRM com fallback em linha reta)."""
    pts = routing.points_from(call.body or {})
    if not pts:
        return {"polyline": []}
    r = routing.route(*pts)
    return {"polyline": r["polyline"], "distanceMeters": r["distanceMeters"],
            "durationSeconds": r["durationSeconds"], "source": r["source"]}


@handles(APP, "POST", "/rt/lite/quote")
def quote(call: Call):
    db, rider = call.db, call.subject()
    _ensure_uber_one_promo(db, rider)
    pickup = _point(call.body.get("pickup")) or (
        (rider.lat, rider.lng) if rider.lat is not None else (HOME_PLACE["lat"], HOME_PLACE["lng"]))
    dropoff = _point(call.body.get("dropoff"))
    if not dropoff:
        raise RtError(400, "missing_dropoff", "escolha um destino")
    city = _city(db, *pickup)
    promo = trips._rider_promo(db, rider, city.products[0]) if city.products else None
    rows = []
    for p in [x for x in city.products if x.active]:
        q = pricing.estimate(db, p, pickup[0], pickup[1], dropoff[0], dropoff[1],
                             promo if promo and pricing.promo_valid(promo, p.id) is None else None)
        rows.append({
            "id": p.id, "uuid": p.uuid, "name": p.name, "description": p.description,
            "capacity": p.capacity, "etaMin": _nearest_eta(db, pickup[0], pickup[1], p),
            "cents": q.total, "price": _money(q.total, city.currency), "currency": city.currency,
            "distanceKm": round(q.distance_m / 1000, 1), "durationMin": round(q.duration_s / 60),
            "fastest": False,
        })
    if rows:
        fastest = min(rows, key=lambda r: (r["etaMin"], r["cents"]))
        fastest["fastest"] = True
    return {
        "pickup": {"lat": pickup[0], "lng": pickup[1],
                   "address": str(call.body.get("pickup", {}).get("address") or "")},
        "dropoff": {"lat": dropoff[0], "lng": dropoff[1],
                    "address": str(call.body.get("dropoff", {}).get("address") or "")},
        "products": rows,
        "payment": PAYMENTS.get(rider.default_payment, PAYMENTS["cash"]),
        "promo": {"code": promo.code, "description": promo.description} if promo else None,
    }


def _apply_code(db, rider, code: str):
    code = (code or "").strip().upper()
    if not code:
        return None
    promo = db.query(Promo).filter(Promo.code == code).first()
    why = pricing.promo_valid(promo)
    if why:
        raise RtError(400, "invalid_promotion", why, {"title": "Código promocional", "message": why})
    used = db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id, RiderPromo.promo_id == promo.id).count()
    if used >= promo.per_rider:
        raise RtError(400, "promotion_already_used", "já usou este código")
    if not used:
        db.add(RiderPromo(rider_id=rider.id, promo=promo))
        db.flush()
    return promo


@handles(APP, "POST", "/rt/lite/request")
def request(call: Call):
    db, rider = call.db, call.subject()
    _ensure_uber_one_promo(db, rider)
    pickup = _point(call.body.get("pickup"))
    dropoff = _point(call.body.get("dropoff"))
    if not pickup or not dropoff:
        raise RtError(400, "missing_route", "indique a recolha e o destino")
    product_id = call.body.get("productId") or call.body.get("product_id")
    product = db.get(Product, int(product_id)) if str(product_id or "").isdigit() else None
    city = _city(db, *pickup)
    product = product or next((p for p in city.products if p.active), None)
    if not product:
        raise RtError(400, "product_unavailable", "categoria indisponível")
    code = call.body.get("promoCode") or ""
    if code:
        _apply_code(db, rider, str(code))
    payment = str(call.body.get("payment") or rider.default_payment)
    rider.default_payment = "cash" if payment == "cash" else "card"
    sched = call.body.get("scheduledAt") or call.body.get("scheduled_at")
    scheduled_at = None
    if sched:
        raw = int(sched)
        scheduled_at = raw // 1000 if raw > 10 ** 11 else raw
        if scheduled_at < now() + 300:
            raise RtError(400, "invalid_schedule", "agende com pelo menos 5 minutos")
        if scheduled_at > now() + 30 * 86400:
            raise RtError(400, "invalid_schedule", "maximo de 30 dias")
    address = lambda o: str((o or {}).get("address") or "")
    stops = []
    for raw in (call.body.get("stops") or [])[:3]:
        p = _point(raw)
        if p:
            stops.append({"lat": p[0], "lng": p[1], "address": address(raw)})
    try:
        t = trips.request_trip(db, rider, product, pickup, dropoff, address(call.body.get("pickup")),
                               address(call.body.get("dropoff")), rider.default_payment, pin_required=True,
                               scheduled_at=scheduled_at, stops=stops)
    except TripError as e:
        raise _err(e)
    return {"trip": trip_json(db, t)}


@handles(APP, "GET", "/rt/lite/active")
def active(call: Call):
    rider = call.subject()
    t = _active_or_recent(call.db, rider)
    return {"trip": trip_json(call.db, t) if t else None}


@handles(APP, "GET", "/rt/lite/trips/{tripUUID}")
def trip_detail(call: Call):
    return {"trip": trip_json(call.db, _trip_for(call, call.vars["tripUUID"]))}


@handles(APP, "POST", "/rt/lite/trips/{tripUUID}/cancel")
def cancel(call: Call):
    t = _trip_for(call, call.vars["tripUUID"])
    try:
        trips.cancel(call.db, t, "rider", str(call.body.get("reason") or ""))
    except TripError as e:
        raise _err(e)
    return {"trip": trip_json(call.db, t)}


@handles(APP, "POST", "/rt/lite/trips/{tripUUID}/rate")
def rate(call: Call):
    t = _trip_for(call, call.vars["tripUUID"])
    try:
        trips.rate(call.db, t, "rider", int(call.body.get("stars") or 0), str(call.body.get("comment") or ""))
    except (TripError, ValueError) as e:
        raise RtError(400, "bad_rating", str(e))
    return {"trip": trip_json(call.db, t)}


@handles(APP, "POST", "/rt/lite/trips/{tripUUID}/tip")
def tip(call: Call):
    rider = call.subject()
    t = _trip_for(call, call.vars["tripUUID"])
    if t.state != "completed":
        raise RtError(400, "trip_not_completed", "so viagens concluidas")
    amount = int(call.body.get("amountCents") or 0)
    if amount < 0 or amount > 5000:
        raise RtError(400, "invalid_tip", "gorjeta entre 0 e 50 EUR")
    if t.tip_cents:
        raise RtError(409, "tip_already_set", "gorjeta ja atribuida")
    t.tip_cents = amount
    if amount:
        call.db.add(LedgerEntry(party="driver", party_id=t.driver_id, kind="tip", amount=amount,
                                trip_id=t.id, note="Gorjeta"))
        call.db.add(LedgerEntry(party="rider", party_id=rider.id, kind="tip", amount=-amount,
                                trip_id=t.id, note="Gorjeta"))
    return {"trip": trip_json(call.db, t)}


@handles(APP, "GET", "/rt/lite/trips/{tripUUID}/receipt")
def receipt(call: Call):
    t = _trip_for(call, call.vars["tripUUID"])
    if t.state != "completed":
        raise RtError(400, "trip_not_completed", "recibo so depois do fim")
    base = t.fare if t.fare is not None else t.est_fare
    tip = t.tip_cents or 0
    lines = [{"label": "Viagem", "amountCents": base}]
    if t.discount:
        lines.append({"label": "Desconto aplicado", "amountCents": -t.discount})
    if tip:
        lines.append({"label": "Gorjeta", "amountCents": tip})
    return {"receipt": {
        "uuid": t.uuid,
        "date": datetime.fromtimestamp(t.completed_at or t.requested_at).strftime("%d/%m/%Y %H:%M"),
        "pickup": t.pickup_address, "dropoff": t.dropoff_address,
        "product": t.product.name, "payment": t.payment_method,
        "driverName": t.driver.name if t.driver else "",
        "distanceKm": round((t.distance_m or 0) / 1000, 1),
        "durationMin": round((t.duration_s or 0) / 60),
        "lines": lines, "totalCents": base + tip, "total": present.money(base + tip),
        "tipCents": tip,
    }}


@handles(APP, "POST", "/rt/lite/trips/{tripUUID}/dispute")
def dispute(call: Call):
    rider = call.subject()
    t = _trip_for(call, call.vars["tripUUID"])
    reason = str(call.body.get("reason") or "").strip()[:1000]
    if not reason:
        raise RtError(400, "missing_reason", "descreva o problema")
    th = SupportThread(app="rider", subject_uuid=rider.uuid, subject_name=rider.name,
                       subject_phone=rider.phone, category="pagamento")
    call.db.add(th)
    call.db.flush()
    call.db.add(SupportMessage(thread_id=th.id, sender="user",
                               body=f"Contestação da viagem {t.uuid}: {reason}"))
    return {"thread": {"uuid": th.uuid, "status": th.status}}


# ---- historico -------------------------------------------------------------------------------
@handles(APP, "GET", "/rt/lite/history")
def history(call: Call):
    rider = call.subject()
    rows = (call.db.query(Trip).filter(Trip.rider_id == rider.id)
            .order_by(Trip.requested_at.desc()).limit(50).all())
    out = []
    for t in rows:
        out.append({
            "uuid": t.uuid, "date": datetime.fromtimestamp(t.requested_at).strftime("%d/%m/%Y · %H:%M"),
            "state": t.state, "pickup": t.pickup_address, "dropoff": t.dropoff_address,
            "product": t.product.name, "fare": _fare_json(t),
            "distanceKm": round((t.distance_m or t.est_distance_m or 0) / 1000, 1),
        })
    return {"trips": out}


# ---- pagamentos e promocoes ------------------------------------------------------------------
@handles(APP, "GET", "/rt/lite/wallet")
def wallet(call: Call):
    rider = call.subject()
    profiles = list(PAYMENTS.values())
    cash = rider.wallet_cents or 0
    return {"cash": {"cents": cash, "label": present.money(cash), "currency": "EUR"},
            "payment": PAYMENTS.get(rider.default_payment, PAYMENTS["cash"]),
            "profiles": profiles}


@handles(APP, "POST", "/rt/lite/wallet/topup")
def topup(call: Call):
    """Carregamento simulado do Qolari Cash (cartao de laboratorio)."""
    rider = call.subject()
    amount = int(call.body.get("amountCents") or 0)
    if amount <= 0 or amount > 20000:
        raise RtError(400, "invalid_amount", "valor entre 1 e 200 EUR")
    rider.wallet_cents = (rider.wallet_cents or 0) + amount
    return {"cash": {"cents": rider.wallet_cents, "label": present.money(rider.wallet_cents),
                     "currency": "EUR"}}


@handles(APP, "POST", "/rt/lite/payments/select")
def select_payment(call: Call):
    rider = call.subject()
    pid = str(call.body.get("id") or "cash")
    if pid not in PAYMENTS:
        raise RtError(404, "payment_not_found", "forma de pagamento inexistente")
    rider.default_payment = pid
    return {"payment": PAYMENTS[pid]}


@handles(APP, "GET", "/rt/lite/promotions")
def promotions(call: Call):
    rider = call.subject()
    db = call.db
    rows = db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id).order_by(RiderPromo.id.desc()).all()
    applied = []
    for rp in rows:
        p = rp.promo
        applied.append({"code": p.code, "description": p.description,
                        "valid": pricing.promo_valid(p) is None and rp.used_trip_id is None})
    return {"applied": applied,
            "hint": "Código do laboratório: BEMVINDO (20% na primeira viagem)."}


@handles(APP, "POST", "/rt/lite/promotions/apply")
def promotions_apply(call: Call):
    promo = _apply_code(call.db, call.subject(), str(call.body.get("code") or ""))
    return {"code": promo.code, "description": promo.description}

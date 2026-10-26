# -*- coding: utf-8 -*-
"""API da consola (backoffice React em ../BACKOFFICE): http://127.0.0.1:8300/api/*

Escreve na mesma BD que as apps; todas as mudancas de viagens passam por domain/trips.py.
"""
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_

import config
from console import serial
from console.auth import audit, can, current, issue, user_json
from core import events
from core.db import session_scope, touch
from core.security import hash_password, verify_password
from domain import finance, pricing, settings, trips
from domain.finance import FinanceError
from domain.models import (TRIP_ACTIVE, AdjustmentRequest, AdminUser, AuditLog, AuthSession, City, Device, Document, Driver,
                           FleetUser, LedgerEntry, MapReport, Offer, Organization, Payout, Product, Promo, PushMessage,
                           Rider, SafetyIncident, ScreenShare, SupportMessage, SupportThread, Trip, TripRecording,
                           TrustedContact, Vehicle, jget, jset, now)
from domain.seed import PLACES
from domain.trips import TripError

router = APIRouter(prefix="/api")
api = APIRouter(dependencies=[Depends(current)])
OPS = can("operator")
FIN = can("finance")
ADMIN = can()


def _get(db, model, id_, what="registo"):
    row = db.get(model, id_)
    if not row:
        raise HTTPException(404, f"{what} inexistente")
    return row


def _trip(db, key: str) -> Trip:
    t = db.query(Trip).filter(or_(Trip.uuid == key, Trip.id == (int(key) if key.isdigit() else -1))).first()
    if not t:
        raise HTTPException(404, "viagem inexistente")
    return t


def _bounds(day_from: str | None, day_to: str | None) -> tuple[int, int]:
    try:
        d0 = date.fromisoformat(day_from) if day_from else date.today() - timedelta(days=6)
        d1 = date.fromisoformat(day_to) if day_to else date.today()
    except ValueError:
        raise HTTPException(400, "data invalida (AAAA-MM-DD)")
    start = int(datetime(d0.year, d0.month, d0.day).timestamp())
    end = int(datetime(d1.year, d1.month, d1.day).timestamp()) + 86400
    return start, end


def _today() -> int:
    d = date.today()
    return int(datetime(d.year, d.month, d.day).timestamp())


def _page(q, page: int, size: int):
    total = q.count()
    return total, q.offset(max(page - 1, 0) * size).limit(size).all()


# ---- sessao ----------------------------------------------------------------------------------
class LoginIn(BaseModel):
    email: str
    password: str


@router.post("/auth/login")
def login(body: LoginIn):
    with session_scope() as db:
        u = db.query(AdminUser).filter(AdminUser.email == body.email.strip().lower()).first()
        if not u or not u.active or not verify_password(body.password, u.password_hash):
            raise HTTPException(401, "email ou palavra-passe errados")
        u.last_login_at = now()
        return {"token": issue(u), "user": user_json(u)}


@api.get("/auth/me")
def me(user: dict = Depends(current)):
    return user


class PasswordIn(BaseModel):
    current: str
    new: str = Field(min_length=6)


@api.post("/auth/password")
def change_password(body: PasswordIn, user: dict = Depends(current)):
    with session_scope() as db:
        u = db.get(AdminUser, user["id"])
        if not verify_password(body.current, u.password_hash):
            raise HTTPException(400, "palavra-passe atual errada")
        u.password_hash = hash_password(body.new)
        audit(db, user, "password", "admin", u.id)
    return {"ok": True}


@api.get("/changes")
def changes(since: int | None = None):
    """Long-polling: devolve quando a BD muda (ou ao fim de 25 s)."""
    if since is None or since != events.version():
        return {"version": events.version()}
    return {"version": events.wait(since, 25)}


# ---- painel ----------------------------------------------------------------------------------
@api.get("/dashboard")
def dashboard():
    with session_scope() as db:
        t0 = _today()
        today = db.query(Trip).filter(Trip.requested_at >= t0).all()
        done = [t for t in today if t.state == "completed"]
        gross = sum(t.fare or 0 for t in done)
        commission = -int(db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
            LedgerEntry.party == "driver", LedgerEntry.kind == "commission", LedgerEntry.at >= t0).scalar())
        drivers = db.query(Driver).all()
        days = []
        for i in range(13, -1, -1):
            s = t0 - i * 86400
            rows = db.query(Trip).filter(Trip.completed_at >= s, Trip.completed_at < s + 86400,
                                         Trip.state == "completed")
            days.append({"day": s, "trips": rows.count(),
                         "gross": int(rows.with_entities(func.coalesce(func.sum(Trip.fare), 0)).scalar())})
        by_product = {}
        for t in done:
            by_product.setdefault(t.product.name, {"trips": 0, "gross": 0})
            by_product[t.product.name]["trips"] += 1
            by_product[t.product.name]["gross"] += t.fare or 0
        week = t0 - 6 * 86400
        top = (db.query(Driver, func.count(Trip.id), func.coalesce(func.sum(Trip.fare), 0))
               .join(Trip, Trip.driver_id == Driver.id)
               .filter(Trip.state == "completed", Trip.completed_at >= week)
               .group_by(Driver.id).order_by(func.count(Trip.id).desc()).limit(5).all())
        recent = db.query(Trip).order_by(Trip.requested_at.desc(), Trip.id.desc()).limit(8).all()
        return {
            "kpis": {"trips_today": len(today), "completed_today": len(done),
                     "cancelled_today": sum(1 for t in today if t.state in ("cancelled", "no_drivers")),
                     "gross_today": gross, "commission_today": commission,
                     "active_trips": db.query(Trip).filter(Trip.state.in_(TRIP_ACTIVE)).count(),
                     "searching_trips": db.query(Trip).filter(Trip.state == "requested").count(),
                     "drivers_online": sum(1 for d in drivers if d.availability == "online"),
                     "drivers_on_trip": sum(1 for d in drivers if d.availability == "on_trip"),
                     "drivers_total": len(drivers),
                     "drivers_pending": sum(1 for d in drivers if d.status == "pending"),
                     "docs_pending": db.query(Document).filter(Document.status == "pending").count(),
                     "riders_total": db.query(Rider).count(),
                     "avg_rating": round(sum(d.rating for d in drivers) / len(drivers), 2) if drivers else None},
            "days": days,
            "by_product": [{"name": k, **v} for k, v in sorted(by_product.items())],
            "top_drivers": [{"id": d.id, "name": d.name, "trips": n, "gross": int(g)} for d, n, g in top],
            "recent": [serial.trip_row(t) for t in recent],
        }


@api.get("/map")
def live_map():
    with session_scope() as db:
        drivers = db.query(Driver).filter(Driver.lat.is_not(None)).all()
        active = db.query(Trip).filter(Trip.state.in_(TRIP_ACTIVE)).all()
        city = db.query(City).filter(City.active.is_(True)).first()
        return {"center": [city.center_lat, city.center_lng] if city else [38.7369, -9.1427],
                "drivers": [{"id": d.id, "name": d.name, "lat": d.lat, "lng": d.lng, "heading": d.heading,
                             "availability": d.availability, "status": d.status, "simulated": d.simulated,
                             "vehicle": d.vehicle.label if d.vehicle else None, "location_at": d.location_at}
                            for d in drivers],
                "trips": [{"uuid": t.uuid, "state": t.state, "pickup": [t.pickup_lat, t.pickup_lng],
                           "dropoff": [t.dropoff_lat, t.dropoff_lng] if t.dropoff_lat is not None else None,
                           "driver_id": t.driver_id, "rider": t.rider.name, "pickup_address": t.pickup_address,
                           "dropoff_address": t.dropoff_address} for t in active]}


# ---- viagens ---------------------------------------------------------------------------------
@api.get("/trips")
def list_trips(state: str = "", q: str = "", driver_id: int | None = None, rider_id: int | None = None,
               org_id: int | None = None, day_from: str | None = None, day_to: str | None = None,
               page: int = 1, size: int = 25):
    with session_scope() as db:
        qq = db.query(Trip)
        if state == "active":
            qq = qq.filter(Trip.state.in_(TRIP_ACTIVE))
        elif state:
            qq = qq.filter(Trip.state == state)
        if driver_id:
            qq = qq.filter(Trip.driver_id == driver_id)
        if rider_id:
            qq = qq.filter(Trip.rider_id == rider_id)
        if org_id:
            qq = qq.filter(Trip.org_id == org_id)
        if day_from or day_to:
            s, e = _bounds(day_from, day_to)
            qq = qq.filter(Trip.requested_at >= s, Trip.requested_at < e)
        if q:
            like = f"%{q}%"
            qq = qq.filter(or_(Trip.uuid.like(like), Trip.pickup_address.like(like), Trip.dropoff_address.like(like)))
        total, rows = _page(qq.order_by(Trip.requested_at.desc(), Trip.id.desc()), page, size)
        return {"total": total, "items": [serial.trip_row(t) for t in rows]}


@api.get("/trips/{key}")
def get_trip(key: str):
    with session_scope() as db:
        t = _trip(db, key)
        rows = db.query(LedgerEntry).filter(LedgerEntry.trip_id == t.id).order_by(LedgerEntry.id).all()
        return serial.trip(t, rows)


class PointIn(BaseModel):
    lat: float
    lng: float
    address: str = ""


class TripIn(BaseModel):
    rider_id: int
    product_id: int
    pickup: PointIn
    dropoff: PointIn | None = None
    payment: str | None = None


@api.post("/trips")
def create_trip(body: TripIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        rider = _get(db, Rider, body.rider_id, "passageiro")
        product = _get(db, Product, body.product_id, "categoria")
        try:
            t = trips.request_trip(db, rider, product, (body.pickup.lat, body.pickup.lng),
                                   (body.dropoff.lat, body.dropoff.lng) if body.dropoff else None,
                                   body.pickup.address, body.dropoff.address if body.dropoff else "",
                                   body.payment, actor="admin")
        except TripError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "trip.create", "trip", t.uuid)
        return {"uuid": t.uuid, "state": t.state}


class TripAction(BaseModel):
    action: str
    driver_id: int | None = None
    state: str | None = None
    reason: str = ""
    stars: int | None = None
    by: str = "rider"


@api.post("/trips/{key}/action")
def trip_action(key: str, body: TripAction, user: dict = Depends(OPS)):
    with session_scope() as db:
        t = _trip(db, key)
        a = body.action
        try:
            if a == "offer":
                trips.offer_to(db, t, _get(db, Driver, body.driver_id or 0, "motorista"))
            elif a in ("accept", "reject"):
                o = next((o for o in t.offers if o.state == "pending"), None)
                if not o:
                    raise TripError("sem proposta pendente")
                if a == "accept":
                    trips.accept_offer(db, o, actor="admin")
                else:
                    trips.reject_offer(db, o, actor="admin")
            elif a == "redispatch":
                trips.dispatch(db, t)
            elif a == "arrive":
                trips.arrive(db, t, actor="admin")
            elif a == "start":
                trips.start(db, t, actor="admin")
            elif a == "complete":
                trips.complete(db, t, actor="admin")
            elif a == "cancel":
                trips.cancel(db, t, "admin", body.reason or f"cancelada por {user['email']}")
            elif a == "force":
                trips.force_state(db, t, body.state or "", user["email"])
            elif a == "rate":
                trips.rate(db, t, body.by, body.stars or 5, body.reason)
            else:
                raise HTTPException(400, "acao desconhecida")
        except TripError as e:
            raise HTTPException(400, str(e))
        audit(db, user, f"trip.{a}", "trip", t.uuid, body.model_dump_json())
        rows = db.query(LedgerEntry).filter(LedgerEntry.trip_id == t.id).all()
        return serial.trip(t, rows)


class QuoteIn(BaseModel):
    product_id: int | None = None
    pickup: PointIn
    dropoff: PointIn | None = None


@api.post("/quote")
def quote(body: QuoteIn):
    with session_scope() as db:
        prods = [_get(db, Product, body.product_id)] if body.product_id else \
            db.query(Product).filter(Product.active.is_(True)).order_by(Product.sort_order).all()
        d = body.dropoff
        return [{"product": serial.product(p), "quote": pricing.estimate(
            db, p, body.pickup.lat, body.pickup.lng, d.lat if d else None, d.lng if d else None).as_dict()}
            for p in prods]


@api.get("/places")
def places():
    return [{"name": n, "lat": la, "lng": ln} for n, la, ln in PLACES]


# ---- motoristas ------------------------------------------------------------------------------
@api.get("/drivers")
def list_drivers(status: str = "", availability: str = "", org_id: int | None = None, q: str = ""):
    with session_scope() as db:
        qq = db.query(Driver)
        if status:
            qq = qq.filter(Driver.status == status)
        if availability:
            qq = qq.filter(Driver.availability == availability)
        if org_id == 0:
            qq = qq.filter(Driver.org_id.is_(None))
        elif org_id:
            qq = qq.filter(Driver.org_id == org_id)
        if q:
            like = f"%{q}%"
            qq = qq.filter(or_(Driver.first_name.like(like), Driver.last_name.like(like), Driver.phone.like(like)))
        bals = finance.balances(db, "driver")
        return [serial.driver(d, bals.get(d.id, 0)) for d in qq.order_by(Driver.first_name).all()]


def _driver_detail(db, d: Driver) -> dict:
    docs = db.query(Document).filter(Document.owner_type == "driver", Document.owner_id == d.id).all()
    recent = db.query(Trip).filter(Trip.driver_id == d.id).order_by(Trip.requested_at.desc()).limit(15).all()
    week = _today() - 6 * 86400
    s = finance.summary(db, "driver", d.id, week)["by_kind"]
    sessions = db.query(AuthSession).filter(AuthSession.app == "driver", AuthSession.subject_uuid == d.uuid) \
        .order_by(AuthSession.created_at.desc()).limit(10).all()
    devices = db.query(Device).filter(Device.app == "driver", Device.subject_uuid == d.uuid).all()
    return {**serial.driver(d, finance.balance(db, "driver", d.id)),
            "documents": [serial.document(x) for x in docs],
            "recent_trips": [serial.trip_row(t) for t in recent],
            "week": {"by_kind": s, "trips": db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed",
                                                                  Trip.completed_at >= week).count()},
            "completed_total": db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").count(),
            "sessions": [_session_json(x) for x in sessions],
            "devices": [_device_json(x) for x in devices],
            "pending_offer": serial.offer(o) if (o := trips.pending_offer_for(db, d)) else None,
            "active_trip": serial.trip_row(t) if (t := trips.active_trip_for_driver(db, d)) else None}


@api.get("/drivers/{driver_id}")
def get_driver(driver_id: int):
    with session_scope() as db:
        return _driver_detail(db, _get(db, Driver, driver_id, "motorista"))


class DriverIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    license_number: str | None = None
    status: str | None = None
    org_id: int | None = None
    vehicle_id: int | None = None
    city_id: int | None = None
    clear_org: bool = False
    clear_vehicle: bool = False


DRIVER_STATUS = ("pending", "approved", "suspended", "rejected")


def _apply_driver(db, d: Driver, body: DriverIn):
    from apps.identity import normalize_phone
    for f in ("first_name", "last_name", "email", "license_number", "city_id"):
        v = getattr(body, f)
        if v is not None:
            setattr(d, f, v)
    if body.phone:
        phone = normalize_phone(body.phone)
        other = db.query(Driver).filter(Driver.phone == phone, Driver.id != (d.id or 0)).first()
        if other:
            raise HTTPException(409, "telefone ja usado por outro motorista")
        d.phone = phone
    if body.status:
        if body.status not in DRIVER_STATUS:
            raise HTTPException(400, "estado invalido")
        if body.status != "approved" and d.availability != "offline":
            if d.availability == "on_trip":
                raise HTTPException(409, "motorista em viagem")
            trips.go_offline(db, d)
        d.status = body.status
    if body.clear_org:
        d.org_id = None
    elif body.org_id:
        _get(db, Organization, body.org_id, "frota")
        d.org_id = body.org_id
    try:
        if body.clear_vehicle:
            trips.assign_vehicle(db, d, None)
        elif body.vehicle_id:
            trips.assign_vehicle(db, d, _get(db, Vehicle, body.vehicle_id, "veiculo"))
    except TripError as e:
        raise HTTPException(409, str(e))
    touch(db, "drivers")


@api.post("/drivers")
def create_driver(body: DriverIn, user: dict = Depends(OPS)):
    if not body.first_name or not body.phone:
        raise HTTPException(400, "nome e telefone obrigatorios")
    with session_scope() as db:
        d = Driver(first_name=body.first_name, phone="pendente", status="pending")
        db.add(d)
        db.flush()
        _apply_driver(db, d, body)
        audit(db, user, "driver.create", "driver", d.id)
        return _driver_detail(db, d)


@api.patch("/drivers/{driver_id}")
def update_driver(driver_id: int, body: DriverIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        d = _get(db, Driver, driver_id, "motorista")
        _apply_driver(db, d, body)
        audit(db, user, "driver.update", "driver", d.id, body.model_dump_json(exclude_none=True))
        return _driver_detail(db, d)


class LocationIn(BaseModel):
    lat: float
    lng: float


@api.post("/drivers/{driver_id}/online")
def driver_online(driver_id: int, body: LocationIn | None = None, user: dict = Depends(OPS)):
    with session_scope() as db:
        d = _get(db, Driver, driver_id, "motorista")
        try:
            if body:
                trips.set_location(db, d, body.lat, body.lng, simulated=True)
            trips.go_online(db, d)
        except TripError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "driver.online", "driver", d.id)
        return _driver_detail(db, d)


@api.post("/drivers/{driver_id}/offline")
def driver_offline(driver_id: int, user: dict = Depends(OPS)):
    with session_scope() as db:
        d = _get(db, Driver, driver_id, "motorista")
        try:
            trips.go_offline(db, d)
        except TripError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "driver.offline", "driver", d.id)
        return _driver_detail(db, d)


@api.post("/drivers/{driver_id}/location")
def driver_location(driver_id: int, body: LocationIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        d = _get(db, Driver, driver_id, "motorista")
        trips.set_location(db, d, body.lat, body.lng, simulated=True)
        return serial.driver(d)


# ---- passageiros -----------------------------------------------------------------------------
@api.get("/riders")
def list_riders(q: str = "", status: str = ""):
    with session_scope() as db:
        qq = db.query(Rider)
        if status:
            qq = qq.filter(Rider.status == status)
        if q:
            like = f"%{q}%"
            qq = qq.filter(or_(Rider.first_name.like(like), Rider.last_name.like(like), Rider.phone.like(like),
                               Rider.email.like(like)))
        counts = dict(db.query(Trip.rider_id, func.count(Trip.id)).filter(Trip.state == "completed")
                      .group_by(Trip.rider_id).all())
        return [{**serial.rider(r), "trips": counts.get(r.id, 0)} for r in qq.order_by(Rider.id.desc()).all()]


@api.get("/riders/{rider_id}")
def get_rider(rider_id: int):
    with session_scope() as db:
        r = _get(db, Rider, rider_id, "passageiro")
        recent = db.query(Trip).filter(Trip.rider_id == r.id).order_by(Trip.requested_at.desc()).limit(20).all()
        spent = int(db.query(func.coalesce(func.sum(Trip.fare), 0)).filter(
            Trip.rider_id == r.id, Trip.state == "completed").scalar())
        from domain.models import RiderPromo
        promos = db.query(RiderPromo).filter(RiderPromo.rider_id == r.id).all()
        return {**serial.rider(r), "recent_trips": [serial.trip_row(t) for t in recent], "spent": spent,
                "promos": [{"code": p.promo.code, "used_trip_id": p.used_trip_id, "created_at": p.created_at}
                           for p in promos],
                "sessions": [_session_json(s) for s in db.query(AuthSession).filter(
                    AuthSession.app == "rider", AuthSession.subject_uuid == r.uuid).limit(10).all()]}


class RiderIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    status: str | None = None
    default_payment: str | None = None


@api.post("/riders")
def create_rider(body: RiderIn, user: dict = Depends(OPS)):
    from apps.identity import normalize_phone
    if not body.phone:
        raise HTTPException(400, "telefone obrigatorio")
    with session_scope() as db:
        phone = normalize_phone(body.phone)
        if db.query(Rider).filter_by(phone=phone).first():
            raise HTTPException(409, "telefone ja registado")
        r = Rider(phone=phone, first_name=body.first_name or "", last_name=body.last_name or "",
                  email=body.email or "", default_payment=body.default_payment or "cash")
        db.add(r)
        db.flush()
        audit(db, user, "rider.create", "rider", r.id)
        return serial.rider(r)


@api.patch("/riders/{rider_id}")
def update_rider(rider_id: int, body: RiderIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        r = _get(db, Rider, rider_id, "passageiro")
        for f in ("first_name", "last_name", "email", "default_payment"):
            v = getattr(body, f)
            if v is not None:
                setattr(r, f, v)
        if body.status:
            if body.status not in ("active", "blocked"):
                raise HTTPException(400, "estado invalido")
            r.status = body.status
        audit(db, user, "rider.update", "rider", r.id, body.model_dump_json(exclude_none=True))
        return serial.rider(r)


# ---- frotas ----------------------------------------------------------------------------------
@api.get("/fleets")
def list_fleets():
    with session_scope() as db:
        bals = finance.balances(db, "fleet")
        return [{**serial.organization(o), "balance": bals.get(o.id, 0)}
                for o in db.query(Organization).order_by(Organization.name).all()]


@api.get("/fleets/{org_id}")
def get_fleet(org_id: int):
    with session_scope() as db:
        o = _get(db, Organization, org_id, "frota")
        week = _today() - 6 * 86400
        dbal = finance.balances(db, "driver")
        return {**serial.organization(o), "balance": finance.balance(db, "fleet", o.id),
                "week": finance.summary(db, "fleet", o.id, week),
                "week_trips": db.query(Trip).filter(Trip.org_id == o.id, Trip.state == "completed",
                                                    Trip.completed_at >= week).count(),
                "drivers": [serial.driver(d, dbal.get(d.id, 0)) for d in o.drivers],
                "vehicles": [serial.vehicle(v, db.query(Driver).filter(Driver.vehicle_id == v.id).all())
                             for v in o.vehicles],
                "users": [serial.fleet_user(u) for u in o.users],
                "payouts": [serial.payout(p, o.name) for p in db.query(Payout).filter(
                    Payout.party == "fleet", Payout.party_id == o.id).order_by(Payout.id.desc()).limit(20)]}


class FleetIn(BaseModel):
    name: str | None = None
    tax_id: str | None = None
    email: str | None = None
    phone: str | None = None
    city_id: int | None = None
    fleet_fee_pct: float | None = Field(default=None, ge=0, le=100)
    iban: str | None = None
    status: str | None = None


def _apply(row, body: BaseModel):
    for k, v in body.model_dump(exclude_none=True).items():
        if hasattr(row, k):
            setattr(row, k, v)


@api.post("/fleets")
def create_fleet(body: FleetIn, user: dict = Depends(OPS)):
    if not body.name:
        raise HTTPException(400, "nome obrigatorio")
    with session_scope() as db:
        o = Organization(name=body.name)
        _apply(o, body)
        db.add(o)
        db.flush()
        audit(db, user, "fleet.create", "fleet", o.id)
        return serial.organization(o)


@api.patch("/fleets/{org_id}")
def update_fleet(org_id: int, body: FleetIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        o = _get(db, Organization, org_id, "frota")
        if body.status and body.status not in ("active", "suspended"):
            raise HTTPException(400, "estado invalido")
        _apply(o, body)
        audit(db, user, "fleet.update", "fleet", o.id, body.model_dump_json(exclude_none=True))
        return serial.organization(o)


class FleetUserIn(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    role: str | None = None
    active: bool | None = None


@api.post("/fleets/{org_id}/users")
def create_fleet_user(org_id: int, body: FleetUserIn, user: dict = Depends(OPS)):
    from apps.identity import normalize_phone
    if not body.first_name or not body.phone:
        raise HTTPException(400, "nome e telefone obrigatorios")
    with session_scope() as db:
        _get(db, Organization, org_id, "frota")
        phone = normalize_phone(body.phone)
        if db.query(FleetUser).filter_by(phone=phone).first():
            raise HTTPException(409, "telefone ja usado noutra conta Fleet")
        u = FleetUser(org_id=org_id, first_name=body.first_name, last_name=body.last_name or "", phone=phone,
                      email=body.email or "", role=body.role or "manager")
        db.add(u)
        db.flush()
        audit(db, user, "fleet_user.create", "fleet_user", u.id)
        return serial.fleet_user(u)


@api.patch("/fleet-users/{uid}")
def update_fleet_user(uid: int, body: FleetUserIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        u = _get(db, FleetUser, uid, "utilizador")
        data = body.model_dump(exclude_none=True)
        data.pop("phone", None)
        for k, v in data.items():
            setattr(u, k, v)
        audit(db, user, "fleet_user.update", "fleet_user", u.id, body.model_dump_json(exclude_none=True))
        return serial.fleet_user(u)


# ---- veiculos --------------------------------------------------------------------------------
@api.get("/vehicles")
def list_vehicles(org_id: int | None = None, status: str = "", q: str = ""):
    with session_scope() as db:
        qq = db.query(Vehicle)
        if org_id == 0:
            qq = qq.filter(Vehicle.org_id.is_(None))
        elif org_id:
            qq = qq.filter(Vehicle.org_id == org_id)
        if status:
            qq = qq.filter(Vehicle.status == status)
        if q:
            like = f"%{q}%"
            qq = qq.filter(or_(Vehicle.plate.like(like), Vehicle.make.like(like), Vehicle.model.like(like)))
        by_vehicle = {}
        for d in db.query(Driver).filter(Driver.vehicle_id.is_not(None)).all():
            by_vehicle.setdefault(d.vehicle_id, []).append(d)
        return [serial.vehicle(v, by_vehicle.get(v.id, [])) for v in qq.order_by(Vehicle.plate).all()]


class VehicleIn(BaseModel):
    make: str | None = None
    model: str | None = None
    year: int | None = Field(default=None, ge=1990, le=2100)
    color: str | None = None
    color_hex: str | None = None
    plate: str | None = None
    vin: str | None = None
    seats: int | None = Field(default=None, ge=1, le=60)
    status: str | None = None
    org_id: int | None = None
    owner_driver_id: int | None = None
    product_ids: list[int] | None = None
    clear_org: bool = False


def _apply_vehicle(db, v: Vehicle, body: VehicleIn):
    data = body.model_dump(exclude_none=True)
    if "plate" in data:
        plate = data.pop("plate").upper().strip()
        if db.query(Vehicle).filter(Vehicle.plate == plate, Vehicle.id != (v.id or 0)).first():
            raise HTTPException(409, "matricula ja registada")
        v.plate = plate
    if "status" in data and data["status"] not in ("pending", "active", "inactive"):
        raise HTTPException(400, "estado invalido")
    if "product_ids" in data:
        v.products = jset(data.pop("product_ids"))
    if data.pop("clear_org", False):
        v.org_id = None
    for k, val in data.items():
        setattr(v, k, val)
    touch(db, "vehicles")


@api.post("/vehicles")
def create_vehicle(body: VehicleIn, user: dict = Depends(OPS)):
    if not (body.make and body.model and body.plate):
        raise HTTPException(400, "marca, modelo e matricula obrigatorios")
    with session_scope() as db:
        v = Vehicle(make=body.make, model=body.model, plate="?")
        db.add(v)
        _apply_vehicle(db, v, body)
        db.flush()
        audit(db, user, "vehicle.create", "vehicle", v.id)
        return serial.vehicle(v)


@api.patch("/vehicles/{vehicle_id}")
def update_vehicle(vehicle_id: int, body: VehicleIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        v = _get(db, Vehicle, vehicle_id, "veiculo")
        _apply_vehicle(db, v, body)
        audit(db, user, "vehicle.update", "vehicle", v.id, body.model_dump_json(exclude_none=True))
        return serial.vehicle(v, db.query(Driver).filter(Driver.vehicle_id == v.id).all())


# ---- documentos ------------------------------------------------------------------------------
DOC_KINDS = {"driver": ["carta_conducao", "cartao_cidadao", "certificado_tvde", "registo_criminal", "atestado_medico"],
             "vehicle": ["dua", "seguro", "inspecao", "licenca_tvde"]}


def _owner_name(db, d: Document) -> str:
    if d.owner_type == "driver":
        o = db.get(Driver, d.owner_id)
        return o.name if o else "?"
    o = db.get(Vehicle, d.owner_id)
    return o.label if o else "?"


@api.get("/documents")
def list_documents(status: str = "pending", owner_type: str = "", owner_id: int | None = None):
    with session_scope() as db:
        qq = db.query(Document)
        if status:
            qq = qq.filter(Document.status == status)
        if owner_type:
            qq = qq.filter(Document.owner_type == owner_type)
        if owner_id:
            qq = qq.filter(Document.owner_id == owner_id)
        return {"kinds": DOC_KINDS,
                "items": [serial.document(x, _owner_name(db, x)) for x in qq.order_by(Document.id.desc()).limit(300)]}


class DocIn(BaseModel):
    owner_type: str | None = None
    owner_id: int | None = None
    kind: str | None = None
    number: str | None = None
    expires_on: str | None = None
    status: str | None = None
    notes: str | None = None


@api.post("/documents")
def create_document(body: DocIn, user: dict = Depends(OPS)):
    if body.owner_type not in DOC_KINDS or not body.owner_id or not body.kind:
        raise HTTPException(400, "dono e tipo obrigatorios")
    with session_scope() as db:
        _get(db, Driver if body.owner_type == "driver" else Vehicle, body.owner_id)
        d = Document(owner_type=body.owner_type, owner_id=body.owner_id, kind=body.kind,
                     number=body.number or "", expires_on=body.expires_on, notes=body.notes or "")
        db.add(d)
        db.flush()
        touch(db, "documents")
        audit(db, user, "document.create", "document", d.id)
        return serial.document(d, _owner_name(db, d))


@api.patch("/documents/{doc_id}")
def review_document(doc_id: int, body: DocIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        d = _get(db, Document, doc_id, "documento")
        if body.status:
            if body.status not in ("pending", "approved", "rejected"):
                raise HTTPException(400, "estado invalido")
            d.status, d.reviewed_by, d.reviewed_at = body.status, user["email"], now()
        for f in ("number", "expires_on", "notes"):
            if getattr(body, f) is not None:
                setattr(d, f, getattr(body, f))
        touch(db, "documents")
        audit(db, user, "document.review", "document", d.id, body.model_dump_json(exclude_none=True))
        return serial.document(d, _owner_name(db, d))


@api.put("/documents/{doc_id}/file")
async def upload_document(doc_id: int, request: Request, user: dict = Depends(OPS)):
    ctype = request.headers.get("content-type", "")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "application/pdf": ".pdf"}.get(
        ctype.split(";")[0])
    if not ext:
        raise HTTPException(415, "so JPG, PNG, WEBP ou PDF")
    raw = await request.body()
    if len(raw) > config.UPLOAD_MAX_BYTES:
        raise HTTPException(413, "ficheiro demasiado grande (max. 8 MB)")
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with session_scope() as db:
        d = _get(db, Document, doc_id, "documento")
        name = f"doc-{d.uuid}{ext}"
        (config.UPLOAD_DIR / name).write_bytes(raw)
        d.file_name = name
        touch(db, "documents")
        return serial.document(d, _owner_name(db, d))


@api.get("/documents/{doc_id}/file")
def document_file(doc_id: int):
    with session_scope() as db:
        d = _get(db, Document, doc_id, "documento")
        if not d.file_name:
            raise HTTPException(404, "sem ficheiro")
        return FileResponse(config.UPLOAD_DIR / d.file_name)


# ---- problemas de mapa (Driver -> /rt/support/map-report) -------------------------------------
def _map_report_json(db, r: MapReport) -> dict:
    d = db.get(Driver, r.driver_id)
    labels = {
        "address": "Rua ou morada errada",
        "closed": "Local fechado ou inexistente",
        "outdated": "Mapa desatualizado",
        "other": "Outro problema",
    }
    return {"id": r.id, "uuid": r.uuid, "driver": serial.driver_short(d), "reason": r.reason,
            "reason_label": labels.get(r.reason, r.reason),
            "note": r.note, "latitude": r.latitude, "longitude": r.longitude,
            "created_at": r.created_at, "status": r.status}


@api.get("/map-reports")
def list_map_reports(status: str = "open", page: int = 1, size: int = 50):
    with session_scope() as db:
        qq = db.query(MapReport)
        if status:
            qq = qq.filter(MapReport.status == status)
        total = qq.count()
        rows = (qq.order_by(MapReport.created_at.desc(), MapReport.id.desc())
                .offset(max(0, (page - 1) * size)).limit(min(size, 200)).all())
        return {"total": total, "page": page, "size": size,
                "items": [_map_report_json(db, r) for r in rows]}


class MapReportIn(BaseModel):
    status: str = Field(pattern="^(open|resolved|dismissed)$")


@api.patch("/map-reports/{report_id}")
def update_map_report(report_id: int, body: MapReportIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        r = _get(db, MapReport, report_id, "registo")
        r.status = body.status
        audit(db, user, "map_report.status", "map_report", r.uuid, body.status)
        return _map_report_json(db, r)


# ---- cidades, categorias, promocoes ----------------------------------------------------------
@api.get("/support")
def list_support(status: str = "open"):
    with session_scope() as db:
        qq = db.query(SupportThread)
        if status:
            qq = qq.filter(SupportThread.status == status)
        rows = qq.order_by(SupportThread.updated_at.desc()).limit(200).all()
        out = []
        for t in rows:
            msgs = (db.query(SupportMessage).filter_by(thread_id=t.id)
                    .order_by(SupportMessage.id).all())
            last = msgs[-1] if msgs else None
            out.append({"uuid": t.uuid, "app": t.app, "name": t.subject_name,
                        "phone": t.subject_phone, "category": t.category,
                        "status": t.status, "updated_at": t.updated_at,
                        "last_message": last.body if last else "",
                        "unread": sum(1 for m in msgs if m.sender == "user" and not m.read_by_support)})
        return {"items": out}


class SupportReply(BaseModel):
    message: str = Field(min_length=1, max_length=1000)


@api.get("/support/{uuid}")
def get_support(uuid: str):
    with session_scope() as db:
        t = db.query(SupportThread).filter_by(uuid=uuid).first()
        if not t:
            raise HTTPException(404, "conversa inexistente")
        msgs = db.query(SupportMessage).filter_by(thread_id=t.id).order_by(SupportMessage.id).all()
        for m in msgs:
            if m.sender == "user":
                m.read_by_support = True
        return {"thread": {"uuid": t.uuid, "app": t.app, "name": t.subject_name,
                           "phone": t.subject_phone, "category": t.category, "status": t.status},
                "messages": [{"id": m.id, "sender": m.sender, "body": m.body, "createdAt": m.created_at,
                              "fileName": m.file_name or "", "hasFile": bool(m.file_name)}
                             for m in msgs]}


@api.get("/support/attachment/{name}")
def support_attachment(name: str, user: dict = Depends(OPS)):
    if not name.startswith("support-") or "/" in name or "\\" in name:
        raise HTTPException(404, "anexo inexistente")
    target = config.UPLOAD_DIR / name
    if not target.is_file():
        raise HTTPException(404, "anexo inexistente")
    return FileResponse(target)


@api.get("/recordings")
def list_recordings():
    with session_scope() as db:
        out = []
        for r in db.query(TripRecording).order_by(TripRecording.id.desc()).limit(200):
            t = db.query(Trip).filter_by(uuid=r.trip_uuid).first()
            out.append({"uuid": r.uuid, "trip_uuid": r.trip_uuid, "app": r.app,
                        "driver": t.driver.name if t and t.driver else "",
                        "kind": r.kind, "started_at": r.started_at, "ended_at": r.ended_at,
                        "duration_s": r.duration_s, "has_file": bool(r.file_name)})
        return {"items": out}


@api.get("/recordings/{uuid}/file")
def recording_file(uuid: str, user: dict = Depends(OPS)):
    with session_scope() as db:
        r = db.query(TripRecording).filter_by(uuid=uuid).first()
        if not r or not r.file_name:
            raise HTTPException(404, "gravacao inexistente")
        target = config.UPLOAD_DIR / r.file_name
        if not target.is_file():
            raise HTTPException(404, "gravacao inexistente")
        return FileResponse(target, media_type="audio/mp4")


@api.get("/support/{uuid}/screen-share")
def support_screen_share(uuid: str):
    with session_scope() as db:
        t = db.query(SupportThread).filter_by(uuid=uuid).first()
        if not t:
            raise HTTPException(404, "conversa inexistente")
        s = (db.query(ScreenShare).filter_by(thread_id=t.id)
             .order_by(ScreenShare.id.desc()).first())
        if not s:
            return {"active": False}
        return {"uuid": s.uuid, "active": s.active, "frame_at": s.frame_at,
                "has_frame": bool(s.file_name)}


@api.get("/support/screen-share/{share_uuid}/frame")
def support_screen_frame(share_uuid: str, user: dict = Depends(OPS)):
    with session_scope() as db:
        s = db.query(ScreenShare).filter_by(uuid=share_uuid).first()
        if not s or not s.file_name:
            raise HTTPException(404, "frame inexistente")
        target = config.UPLOAD_DIR / s.file_name
        if not target.is_file():
            raise HTTPException(404, "frame inexistente")
        return FileResponse(target, media_type="image/jpeg")


@api.post("/support/{uuid}/reply")
def reply_support(uuid: str, body: SupportReply, user: dict = Depends(OPS)):
    with session_scope() as db:
        t = db.query(SupportThread).filter_by(uuid=uuid).first()
        if not t:
            raise HTTPException(404, "conversa inexistente")
        m = SupportMessage(thread_id=t.id, sender="support", body=body.message.strip())
        db.add(m)
        t.status, t.updated_at = "open", now()
        audit(db, user, "support.reply", "support", t.uuid)
        db.flush()
        return {"id": m.id, "sender": m.sender, "body": m.body, "createdAt": m.created_at}


class SupportStatus(BaseModel):
    status: str = Field(pattern="^(open|closed)$")


@api.patch("/support/{uuid}")
def close_support(uuid: str, body: SupportStatus, user: dict = Depends(OPS)):
    with session_scope() as db:
        t = db.query(SupportThread).filter_by(uuid=uuid).first()
        if not t:
            raise HTTPException(404, "conversa inexistente")
        t.status, t.updated_at = body.status, now()
        audit(db, user, "support.status", "support", t.uuid, body.status)
        return {"uuid": t.uuid, "status": t.status}


# ---- cidades, categorias, promocoes ----------------------------------------------------------
@api.get("/catalog")
def catalog():
    with session_scope() as db:
        return {"cities": [serial.city(c) for c in db.query(City).all()],
                "products": [serial.product(p) for p in db.query(Product).order_by(Product.city_id, Product.sort_order)]}


class CityIn(BaseModel):
    name: str | None = None
    currency: str | None = None
    center_lat: float | None = None
    center_lng: float | None = None
    radius_km: float | None = Field(default=None, gt=0)
    active: bool | None = None


@api.patch("/cities/{city_id}")
def update_city(city_id: int, body: CityIn, user: dict = Depends(ADMIN)):
    with session_scope() as db:
        c = _get(db, City, city_id, "cidade")
        _apply(c, body)
        audit(db, user, "city.update", "city", c.id, body.model_dump_json(exclude_none=True))
        return serial.city(c)


class ProductIn(BaseModel):
    city_id: int | None = None
    code: str | None = None
    name: str | None = None
    description: str | None = None
    capacity: int | None = Field(default=None, ge=1, le=60)
    base_fare: int | None = Field(default=None, ge=0)
    per_km: int | None = Field(default=None, ge=0)
    per_min: int | None = Field(default=None, ge=0)
    minimum_fare: int | None = Field(default=None, ge=0)
    booking_fee: int | None = Field(default=None, ge=0)
    cancel_fee: int | None = Field(default=None, ge=0)
    surge: float | None = Field(default=None, ge=1, le=5)
    min_vehicle_year: int | None = None
    sort_order: int | None = None
    active: bool | None = None


@api.post("/products")
def create_product(body: ProductIn, user: dict = Depends(ADMIN)):
    if not (body.city_id and body.code and body.name):
        raise HTTPException(400, "cidade, codigo e nome obrigatorios")
    with session_scope() as db:
        _get(db, City, body.city_id, "cidade")
        p = Product(city_id=body.city_id, code=body.code, name=body.name)
        _apply(p, body)
        db.add(p)
        db.flush()
        audit(db, user, "product.create", "product", p.id)
        return serial.product(p)


@api.patch("/products/{product_id}")
def update_product(product_id: int, body: ProductIn, user: dict = Depends(ADMIN)):
    with session_scope() as db:
        p = _get(db, Product, product_id, "categoria")
        _apply(p, body)
        touch(db, "catalog")
        audit(db, user, "product.update", "product", p.id, body.model_dump_json(exclude_none=True))
        return serial.product(p)


@api.get("/promos")
def list_promos():
    with session_scope() as db:
        return [serial.promo(p) for p in db.query(Promo).order_by(Promo.id.desc())]


class PromoIn(BaseModel):
    code: str | None = None
    description: str | None = None
    kind: str | None = None
    value: int | None = Field(default=None, ge=0)
    max_discount: int | None = None
    max_uses: int | None = None
    per_rider: int | None = Field(default=None, ge=1)
    product_id: int | None = None
    valid_from: int | None = None
    valid_to: int | None = None
    active: bool | None = None


@api.post("/promos")
def create_promo(body: PromoIn, user: dict = Depends(OPS)):
    if not body.code or body.value is None or body.kind not in ("percent", "amount"):
        raise HTTPException(400, "codigo, tipo e valor obrigatorios")
    if body.kind == "percent" and body.value > 100:
        raise HTTPException(400, "percentagem acima de 100")
    with session_scope() as db:
        code = body.code.strip().upper()
        if db.query(Promo).filter_by(code=code).first():
            raise HTTPException(409, "codigo ja existe")
        p = Promo(code=code, kind=body.kind, value=body.value)
        _apply(p, body)
        p.code = code
        db.add(p)
        db.flush()
        audit(db, user, "promo.create", "promo", p.id)
        return serial.promo(p)


@api.patch("/promos/{promo_id}")
def update_promo(promo_id: int, body: PromoIn, user: dict = Depends(OPS)):
    with session_scope() as db:
        p = _get(db, Promo, promo_id, "promocao")
        data = body.model_dump(exclude_none=True)
        data.pop("code", None)
        for k, v in data.items():
            setattr(p, k, v)
        audit(db, user, "promo.update", "promo", p.id, body.model_dump_json(exclude_none=True))
        return serial.promo(p)


# ---- financas --------------------------------------------------------------------------------
@api.get("/finance/overview")
def finance_overview(day_from: str | None = None, day_to: str | None = None):
    with session_scope() as db:
        s, e = _bounds(day_from, day_to)

        def total(party, kind):
            return int(db.query(func.coalesce(func.sum(LedgerEntry.amount), 0)).filter(
                LedgerEntry.party == party, LedgerEntry.kind == kind, LedgerEntry.at >= s, LedgerEntry.at < e).scalar())
        completed = db.query(Trip).filter(Trip.state == "completed", Trip.completed_at >= s, Trip.completed_at < e)
        gross = int(completed.with_entities(func.coalesce(func.sum(Trip.fare), 0)).scalar())
        dbal, fbal = finance.balances(db, "driver"), finance.balances(db, "fleet")
        drivers = {d.id: d for d in db.query(Driver).all()}
        orgs = {o.id: o for o in db.query(Organization).all()}
        pend = db.query(Payout).filter(Payout.status == "pending").all()
        return {"from": s, "to": e, "trips": completed.count(), "gross": gross,
                "commission": total("platform", "commission"), "promo_cost": -total("platform", "promo"),
                "fleet_fees": total("fleet", "fleet_fee"), "cash_collected": -total("driver", "cash_collected"),
                "cancel_fees": total("driver", "cancel_fee"),
                "payouts_pending": sum(p.amount for p in pend),
                "payouts_paid": int(db.query(func.coalesce(func.sum(Payout.amount), 0)).filter(
                    Payout.status == "paid", Payout.paid_at >= s, Payout.paid_at < e).scalar()),
                "driver_balances": sorted([{"id": i, "name": drivers[i].name if i in drivers else "?",
                                            "org": drivers[i].organization.name if i in drivers and drivers[i].organization else None,
                                            "balance": b} for i, b in dbal.items()], key=lambda x: -x["balance"]),
                "fleet_balances": sorted([{"id": i, "name": orgs[i].name if i in orgs else "?", "balance": b}
                                          for i, b in fbal.items()], key=lambda x: -x["balance"])}


@api.get("/finance/ledger")
def ledger(party: str = "", party_id: int | None = None, kind: str = "", page: int = 1, size: int = 50):
    with session_scope() as db:
        qq = db.query(LedgerEntry)
        if party:
            qq = qq.filter(LedgerEntry.party == party)
        if party_id:
            qq = qq.filter(LedgerEntry.party_id == party_id)
        if kind:
            qq = qq.filter(LedgerEntry.kind == kind)
        total, rows = _page(qq.order_by(LedgerEntry.id.desc()), page, size)
        uuids = dict(db.query(Trip.id, Trip.uuid).filter(Trip.id.in_({r.trip_id for r in rows if r.trip_id})).all())
        return {"total": total, "items": [{**serial.ledger(r), "trip_uuid": uuids.get(r.trip_id)} for r in rows]}


def _party_name(db, party, pid):
    row = db.get(Driver if party == "driver" else Organization, pid)
    return row.name if row else "?"


@api.get("/adjustments")
def list_adjustments(status: str = ""):
    with session_scope() as db:
        qq = db.query(AdjustmentRequest)
        if status:
            qq = qq.filter(AdjustmentRequest.status == status)
        out = []
        for a in qq.order_by(AdjustmentRequest.id.desc()).limit(200):
            d = db.get(Driver, a.driver_id)
            out.append({"uuid": a.uuid, "driver": d.name if d else "?",
                        "driver_id": a.driver_id, "trip_uuid": a.trip_uuid,
                        "kind": a.kind, "amount": a.amount_cents, "note": a.note,
                        "status": a.status, "created_at": a.created_at,
                        "reviewed_by": a.reviewed_by, "reviewed_at": a.reviewed_at})
        return {"items": out}


@api.patch("/adjustments/{uuid}")
def review_adjustment(uuid: str, body: dict, user: dict = Depends(FIN)):
    with session_scope() as db:
        a = db.query(AdjustmentRequest).filter_by(uuid=uuid).first()
        if not a:
            raise HTTPException(404, "ajuste inexistente")
        status = str(body.get("status") or "")
        if status not in ("approved", "rejected"):
            raise HTTPException(400, "estado invalido")
        if a.status != "pending":
            raise HTTPException(409, "ajuste ja revisto")
        a.status, a.reviewed_by, a.reviewed_at = status, user["email"], now()
        if status == "approved":
            finance.adjust(db, "driver", a.driver_id, a.amount_cents, a.note or f"Ajuste {a.kind}")
        audit(db, user, "adjustment.review", "adjustment", a.id, jset({"status": status}))
        return {"uuid": a.uuid, "status": a.status}


@api.get("/payouts")
def list_payouts(status: str = ""):
    with session_scope() as db:
        qq = db.query(Payout)
        if status:
            qq = qq.filter(Payout.status == status)
        return [serial.payout(p, _party_name(db, p.party, p.party_id)) for p in qq.order_by(Payout.id.desc()).limit(200)]


class PayoutIn(BaseModel):
    party: str
    party_id: int
    amount: int | None = Field(default=None, gt=0)
    reference: str = ""


@api.post("/payouts")
def create_payout(body: PayoutIn, user: dict = Depends(FIN)):
    if body.party not in ("driver", "fleet"):
        raise HTTPException(400, "parte invalida")
    with session_scope() as db:
        try:
            p = finance.create_payout(db, body.party, body.party_id, body.amount, body.reference)
        except FinanceError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "payout.create", "payout", p.id, body.model_dump_json())
        return serial.payout(p, _party_name(db, p.party, p.party_id))


class PayoutClose(BaseModel):
    reference: str = ""


@api.post("/payouts/{pid}/paid")
def payout_paid(pid: int, body: PayoutClose, user: dict = Depends(FIN)):
    with session_scope() as db:
        try:
            p = finance.mark_paid(db, _get(db, Payout, pid, "pagamento"), body.reference)
        except FinanceError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "payout.paid", "payout", p.id)
        return serial.payout(p, _party_name(db, p.party, p.party_id))


@api.post("/payouts/{pid}/cancel")
def payout_cancel(pid: int, user: dict = Depends(FIN)):
    with session_scope() as db:
        try:
            p = finance.cancel_payout(db, _get(db, Payout, pid, "pagamento"))
        except FinanceError as e:
            raise HTTPException(400, str(e))
        audit(db, user, "payout.cancel", "payout", p.id)
        return serial.payout(p, _party_name(db, p.party, p.party_id))


class AdjustIn(BaseModel):
    party: str
    party_id: int
    amount: int
    note: str = Field(min_length=3)


@api.post("/finance/adjust")
def adjust(body: AdjustIn, user: dict = Depends(FIN)):
    if body.party not in ("driver", "fleet"):
        raise HTTPException(400, "parte invalida")
    with session_scope() as db:
        _get(db, Driver if body.party == "driver" else Organization, body.party_id)
        try:
            e = finance.adjust(db, body.party, body.party_id, body.amount, f"{body.note} ({user['email']})")
        except FinanceError as err:
            raise HTTPException(400, str(err))
        db.flush()
        audit(db, user, "finance.adjust", body.party, body.party_id, body.model_dump_json())
        return serial.ledger(e)


# ---- sessoes, dispositivos, mensagens --------------------------------------------------------
def _session_json(s: AuthSession) -> dict:
    return {"id": s.id, "app": s.app, "subject_uuid": s.subject_uuid, "created_at": s.created_at,
            "last_used_at": s.last_used_at, "ip": s.ip, "user_agent": s.user_agent, "revoked": s.revoked}


def _device_json(d: Device) -> dict:
    return {"id": d.id, "app": d.app, "device_key": d.device_key, "subject_uuid": d.subject_uuid, "model": d.model,
            "os_version": d.os_version, "app_version": d.app_version, "has_push_token": bool(d.push_token),
            "ip": d.ip, "first_seen_at": d.first_seen_at, "last_seen_at": d.last_seen_at}


def _subject_names(db) -> dict:
    out = {}
    for model in (Rider, Driver, FleetUser):
        for row in db.query(model).all():
            out[row.uuid] = getattr(row, "name", None) or f"{row.first_name} {row.last_name}".strip()
    return out


@api.get("/sessions")
def sessions(app: str = ""):
    with session_scope() as db:
        qq = db.query(AuthSession)
        if app:
            qq = qq.filter(AuthSession.app == app)
        names = _subject_names(db)
        return [{**_session_json(s), "subject_name": names.get(s.subject_uuid, "?")}
                for s in qq.order_by(AuthSession.last_used_at.desc()).limit(200)]


@api.post("/sessions/{sid}/revoke")
def revoke_session(sid: str, user: dict = Depends(OPS)):
    with session_scope() as db:
        s = _get(db, AuthSession, sid, "sessao")
        s.revoked = True
        touch(db, "sessions")
        audit(db, user, "session.revoke", "session", sid)
        return _session_json(s)


@api.get("/devices")
def devices():
    with session_scope() as db:
        names = _subject_names(db)
        return [{**_device_json(d), "subject_name": names.get(d.subject_uuid or "", "")}
                for d in db.query(Device).order_by(Device.last_seen_at.desc()).limit(200)]


@api.get("/push")
def push_messages(limit: int = 100):
    with session_scope() as db:
        names = _subject_names(db)
        return [{"id": m.id, "app": m.app, "subject": names.get(m.subject_uuid, m.subject_uuid), "topic": m.topic,
                 "payload": jget(m.payload, {}), "created_at": m.created_at, "delivered_at": m.delivered_at}
                for m in db.query(PushMessage).order_by(PushMessage.id.desc()).limit(min(limit, 500))]


# ---- definicoes e administradores ------------------------------------------------------------
@api.get("/settings")
def get_settings():
    with session_scope() as db:
        return {"values": settings.all_values(db), "labels": settings.LABELS,
                "otp_code": config.OTP_CODE, "public_host": config.PUBLIC_HOST,
                "ports": {**config.APP_PORTS, "console": config.CONSOLE_PORT}}


@api.patch("/settings")
def patch_settings(body: dict, user: dict = Depends(ADMIN)):
    with session_scope() as db:
        try:
            vals = settings.update(db, body)
        except KeyError as e:
            raise HTTPException(400, f"parametro desconhecido: {e}")
        except (ValueError, TypeError) as e:
            raise HTTPException(400, str(e))
        touch(db, "settings")
        audit(db, user, "settings.update", "settings", "", jset(body))
        return {"values": vals}


@api.get("/admins")
def list_admins(user: dict = Depends(ADMIN)):
    with session_scope() as db:
        return [user_json(u) for u in db.query(AdminUser).order_by(AdminUser.id)]


class AdminIn(BaseModel):
    email: str | None = None
    name: str | None = None
    role: str | None = None
    password: str | None = Field(default=None, min_length=6)
    active: bool | None = None


@api.post("/admins")
def create_admin(body: AdminIn, user: dict = Depends(ADMIN)):
    if not body.email or not body.password:
        raise HTTPException(400, "email e palavra-passe obrigatorios")
    if body.role and body.role not in ("admin", "operator", "finance"):
        raise HTTPException(400, "papel invalido")
    with session_scope() as db:
        email = body.email.strip().lower()
        if db.query(AdminUser).filter_by(email=email).first():
            raise HTTPException(409, "email ja existe")
        u = AdminUser(email=email, name=body.name or "", role=body.role or "operator",
                      password_hash=hash_password(body.password))
        db.add(u)
        db.flush()
        audit(db, user, "admin.create", "admin", u.id)
        return user_json(u)


@api.patch("/admins/{uid}")
def update_admin(uid: int, body: AdminIn, user: dict = Depends(ADMIN)):
    with session_scope() as db:
        u = _get(db, AdminUser, uid, "utilizador")
        if uid == user["id"] and (body.active is False or (body.role and body.role != "admin")):
            raise HTTPException(400, "nao podes desativar nem despromover a tua propria conta")
        if body.role:
            if body.role not in ("admin", "operator", "finance"):
                raise HTTPException(400, "papel invalido")
            u.role = body.role
        if body.name is not None:
            u.name = body.name
        if body.active is not None:
            u.active = body.active
        if body.password:
            u.password_hash = hash_password(body.password)
        audit(db, user, "admin.update", "admin", u.id, body.model_dump_json(exclude_none=True, exclude={"password"}))
        return user_json(u)


@api.get("/audit")
def audit_log(limit: int = 200):
    with session_scope() as db:
        return [{"id": a.id, "at": a.at, "admin": a.admin_email, "action": a.action, "entity": a.entity,
                 "entity_id": a.entity_id, "detail": a.detail}
                for a in db.query(AuditLog).order_by(AuditLog.id.desc()).limit(min(limit, 1000))]


@api.get("/offers")
def offers_pending():
    with session_scope() as db:
        return [serial.offer(o) for o in db.query(Offer).filter(Offer.state == "pending").all()]


@api.get("/safety")
def safety_incidents(status: str = "", app: str = ""):
    """Alertas de seguranca (SOS) com os contactos de confianca da conta."""
    with session_scope() as db:
        q = db.query(SafetyIncident)
        if status:
            q = q.filter(SafetyIncident.status == status)
        if app:
            q = q.filter(SafetyIncident.app == app)
        out = []
        for i in q.order_by(SafetyIncident.id.desc()).limit(200):
            contacts = (
                db.query(TrustedContact)
                .filter_by(app=i.app, subject_uuid=i.subject_uuid)
                .order_by(TrustedContact.id)
                .all()
            )
            out.append({
                "uuid": i.uuid, "kind": i.kind, "app": i.app,
                "subjectName": i.subject_name, "subjectPhone": i.subject_phone,
                "tripUuid": i.trip_uuid, "latitude": i.latitude, "longitude": i.longitude,
                "note": i.note, "status": i.status, "createdAt": i.created_at,
                "closedAt": i.closed_at,
                "contacts": [{"name": c.name, "phone": c.phone} for c in contacts],
            })
        return {"items": out}


@api.patch("/safety/{uuid}")
def update_safety(uuid: str, body: dict, user: dict = Depends(OPS)):
    with session_scope() as db:
        i = db.query(SafetyIncident).filter_by(uuid=uuid).first()
        if not i:
            raise HTTPException(404, "alerta inexistente")
        status = str(body.get("status") or "").strip()
        if status not in ("open", "closed"):
            raise HTTPException(400, "estado invalido")
        i.status = status
        i.closed_at = now() if status == "closed" else None
        audit(db, user, "safety.update", "safety", i.id, jset({"status": status}))
        return {"uuid": i.uuid, "status": i.status, "closedAt": i.closed_at}


router.include_router(api)

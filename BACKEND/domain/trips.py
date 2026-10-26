# -*- coding: utf-8 -*-
"""Maquina de estados da viagem + despacho + contabilidade. UNICO sitio que muda viagens.

Estados (Trip.state):
    requested ──accept──> accepted ──arrive──> arrived ──start──> in_progress ──complete──> completed
        │                    │                     │                   │
        └── no_drivers       └──────────── cancel (rider | driver | admin) ──> cancelled

Despacho: em `requested` ha no maximo 1 proposta (Offer) pendente. O motorista elegivel mais
proximo recebe-a; recusa/expira -> passa ao seguinte. Sem candidatos durante `search_timeout_s`
(ou `max_offers_per_trip` esgotado) -> no_drivers.

Disponibilidade do motorista (Driver.availability): offline | online | on_trip.
As apps (apps/*.py) e a consola (console/*.py) chamam estas funcoes; erros -> TripError.
"""
import random

from core.db import touch
from domain import geo, pricing, push, settings
from domain.models import (Driver, LedgerEntry, Offer, Organization, Product, Promo, Rider,
                           RiderPromo, Trip, TripEvent, Vehicle, jget, jset, now)

# Raio aceite entre o destino da viagem e o destino escolhido no "modo destino".
DESTINATION_RADIUS_M = 15_000


class TripError(Exception):
    def __init__(self, message: str, code: str = "invalid_state"):
        super().__init__(message)
        self.code = code


# ---- eventos e notificacoes ------------------------------------------------------------------
def _event(db, trip: Trip, kind: str, actor: str, detail: str = ""):
    db.add(TripEvent(trip_id=trip.id, kind=kind, actor=actor, detail=detail[:300]))
    touch(db, "trips", f"trip:{trip.uuid}")


def _notify(db, trip: Trip):
    data = {"tripUUID": trip.uuid, "state": trip.state}
    push.send(db, "rider", trip.rider.uuid if trip.rider else None, "trip_status", data)
    if trip.driver:
        push.send(db, "driver", trip.driver.uuid, "trip_status", data)
        # A Fleet ve o estado da viagem do motorista da sua organizacao (scope de tenant).
        if trip.driver.organization:
            for u in trip.driver.organization.users:
                push.send(db, "fleet", u.uuid, "driver_trip",
                          {"driverUUID": trip.driver.uuid, "tripUUID": trip.uuid, "state": trip.state})


# ---- pedido ----------------------------------------------------------------------------------
def active_trip_for_rider(db, rider: Rider) -> Trip | None:
    return (db.query(Trip).filter(Trip.rider_id == rider.id, Trip.state.in_(
        ("requested", "accepted", "arrived", "in_progress"))).order_by(Trip.id.desc()).first())


def active_trip_for_driver(db, driver: Driver) -> Trip | None:
    return (db.query(Trip).filter(Trip.driver_id == driver.id, Trip.state.in_(
        ("accepted", "arrived", "in_progress"))).order_by(Trip.id.desc()).first())


def _rider_promo(db, rider: Rider, product: Product) -> Promo | None:
    rp = (db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id, RiderPromo.used_trip_id.is_(None))
          .order_by(RiderPromo.id.desc()).first())
    if rp and pricing.promo_valid(rp.promo, product.id) is None:
        return rp.promo
    return None


def request_trip(db, rider: Rider, product: Product, pickup: tuple, dropoff: tuple | None,
                 pickup_address: str = "", dropoff_address: str = "", payment: str | None = None,
                 actor: str = "rider", pin_required: bool = False,
                 scheduled_at: int | None = None, stops: list | None = None) -> Trip:
    """pin_required: so quando o passageiro escolhe verificar a viagem com PIN (por omissao nao ha PIN)."""
    if rider.status != "active":
        raise TripError("conta do passageiro bloqueada", "rider_blocked")
    if not product.active:
        raise TripError("categoria indisponivel", "product_unavailable")
    if active_trip_for_rider(db, rider):
        raise TripError("o passageiro ja tem uma viagem ativa", "already_on_trip")
    city = product.city
    if geo.haversine_m(city.center_lat, city.center_lng, *pickup) > city.radius_km * 1000:
        raise TripError(f"recolha fora da area de servico de {city.name}", "out_of_area")
    promo = _rider_promo(db, rider, product)
    dlat, dlng = dropoff if dropoff else (None, None)
    q = pricing.estimate(db, product, pickup[0], pickup[1], dlat, dlng, promo)
    stops = stops or []
    stop_fee = 50 * len(stops)
    trip = Trip(city_id=city.id, rider=rider, product=product, pickup_lat=pickup[0],
                pickup_lng=pickup[1], pickup_address=pickup_address, dropoff_lat=dlat,
                dropoff_lng=dlng, dropoff_address=dropoff_address, est_distance_m=q.distance_m,
                est_duration_s=q.duration_s, est_fare=q.total + stop_fee, surge=product.surge,
                payment_method=payment or rider.default_payment, pin=f"{random.randint(0, 9999):04d}" if pin_required else "",
                promo_id=promo.id if promo else None, source="console" if actor == "admin" else "rider",
                scheduled_at=scheduled_at, stops=jset([dict(s, done=False) for s in stops]),
                fare_breakdown=jset({"estimate": q.as_dict(), "stops_fee": stop_fee}))
    db.add(trip)
    db.flush()
    _event(db, trip, "requested", actor, f"{product.name} · estimativa {q.total / 100:.2f}")
    dispatch(db, trip)
    _notify(db, trip)
    return trip


# ---- despacho --------------------------------------------------------------------------------
def candidates(db, trip: Trip) -> list[tuple[Driver, float]]:
    """Motoristas elegiveis, do mais proximo para o mais longe."""
    radius = settings.get(db, "dispatch_radius_km") * 1000
    tried = {o.driver_id for o in trip.offers}
    busy = {d for (d,) in db.query(Offer.driver_id).filter(Offer.state == "pending").all()}
    out = []
    for d in (db.query(Driver).filter(Driver.status == "approved", Driver.availability == "online",
                                      Driver.lat.is_not(None)).all()):
        if d.id in tried or d.id in busy:
            continue
        p = d.preferences
        if p:
            if p.break_until and p.break_until > now():
                continue
            if p.destination_mode and p.destination_lat is not None and p.destination_lng is not None \
                    and trip.dropoff_lat is not None and trip.dropoff_lng is not None:
                if geo.haversine_m(p.destination_lat, p.destination_lng,
                                   trip.dropoff_lat, trip.dropoff_lng) > DESTINATION_RADIUS_M:
                    continue
            if p.area_mode and p.area_lat is not None and p.area_lng is not None:
                if geo.haversine_m(p.area_lat, p.area_lng,
                                   trip.pickup_lat, trip.pickup_lng) > p.area_radius_km * 1000:
                    continue
        v = d.vehicle
        if not v or v.status != "active" or (v.product_ids and trip.product_id not in v.product_ids):
            continue
        if v.seats < trip.product.capacity or v.year < trip.product.min_vehicle_year:
            continue
        dist = geo.haversine_m(d.lat, d.lng, trip.pickup_lat, trip.pickup_lng)
        if dist <= radius:
            out.append((d, dist))
    out.sort(key=lambda x: x[1])
    return out


def dispatch(db, trip: Trip) -> Offer | None:
    """Faz a proxima proposta (se nao houver uma pendente)."""
    if trip.state != "requested":
        return None
    if trip.scheduled_at and trip.scheduled_at > now():
        return None
    if any(o.state == "pending" for o in trip.offers):
        return None
    if len(trip.offers) >= settings.get(db, "max_offers_per_trip"):
        return _no_drivers(db, trip, "propostas esgotadas")
    found = candidates(db, trip)
    if not found:
        started = trip.scheduled_at or trip.requested_at
        if now() - started >= settings.get(db, "search_timeout_s"):
            _no_drivers(db, trip, "sem motoristas disponiveis")
        return None
    driver, dist = found[0]
    road = dist * settings.get(db, "road_factor")
    eta = int(road / (settings.get(db, "avg_speed_kmh") / 3.6))
    offer = Offer(trip=trip, driver=driver, pickup_distance_m=int(road), pickup_eta_s=eta,
                  expires_at=now() + settings.get(db, "offer_timeout_s"))
    db.add(offer)
    driver.offers_received += 1
    db.flush()
    _event(db, trip, "offer", "system", f"proposta a {driver.name} ({road / 1000:.1f} km)")
    push.send(db, "driver", driver.uuid, "offer", offer_payload(offer))
    touch(db, "drivers")
    p = driver.preferences
    if p and p.auto_accept:
        try:
            accept_offer(db, offer, actor="system")
        except TripError:
            pass
    return offer


def offer_payload(offer: Offer) -> dict:
    t = offer.trip
    return {"offerUUID": offer.uuid, "tripUUID": t.uuid, "expiresAt": offer.expires_at,
            "pickup": {"latitude": t.pickup_lat, "longitude": t.pickup_lng, "address": t.pickup_address},
            "dropoff": {"latitude": t.dropoff_lat, "longitude": t.dropoff_lng, "address": t.dropoff_address},
            "product": t.product.name, "fare": t.est_fare, "pickupEtaSeconds": offer.pickup_eta_s,
            "riderName": t.rider.first_name, "riderRating": t.rider.rating}


def _no_drivers(db, trip: Trip, why: str):
    trip.state = "no_drivers"
    trip.cancelled_at = now()
    trip.cancelled_by = "system"
    trip.cancel_reason = why
    _event(db, trip, "no_drivers", "system", why)
    _notify(db, trip)
    return None


def pending_offer_for(db, driver: Driver) -> Offer | None:
    return (db.query(Offer).filter(Offer.driver_id == driver.id, Offer.state == "pending",
                                   Offer.expires_at > now()).order_by(Offer.id.desc()).first())


def offer_to(db, trip: Trip, driver: Driver, actor: str = "admin") -> Offer:
    """Proposta manual (consola): retira a pendente e propoe a este motorista."""
    if trip.state != "requested":
        raise TripError("so viagens a procurar motorista")
    if driver.status != "approved" or driver.availability != "online":
        raise TripError("o motorista tem de estar aprovado e online")
    for o in trip.offers:
        if o.state == "pending":
            o.state, o.responded_at = "withdrawn", now()
            push.send(db, "driver", o.driver.uuid, "offer", offer_payload(o))
    offer = Offer(trip=trip, driver=driver, expires_at=now() + settings.get(db, "offer_timeout_s"))
    if driver.lat is not None:
        offer.pickup_distance_m = int(geo.haversine_m(driver.lat, driver.lng, trip.pickup_lat, trip.pickup_lng))
    db.add(offer)
    driver.offers_received += 1
    db.flush()
    _event(db, trip, "offer", actor, f"proposta manual a {driver.name}")
    push.send(db, "driver", driver.uuid, "offer", offer_payload(offer))
    return offer


def accept_offer(db, offer: Offer, actor: str = "driver") -> Trip:
    trip, driver = offer.trip, offer.driver
    if offer.state != "pending" or offer.expires_at <= now():
        raise TripError("a proposta ja nao esta disponivel", "offer_expired")
    if trip.state != "requested":
        raise TripError("a viagem ja nao esta disponivel", "trip_unavailable")
    if driver.availability != "online":
        raise TripError("o motorista nao esta online", "driver_offline")
    t = now()
    offer.state, offer.responded_at = "accepted", t
    driver.offers_accepted += 1
    driver.availability = "on_trip"
    trip.driver, trip.vehicle, trip.org_id = driver, driver.vehicle, driver.org_id
    trip.state, trip.accepted_at = "accepted", t
    _event(db, trip, "accepted", actor, f"{driver.name} · {driver.vehicle.label if driver.vehicle else ''}")
    _notify(db, trip)
    touch(db, "drivers")
    return trip


def reject_offer(db, offer: Offer, actor: str = "driver", expired: bool = False):
    if offer.state != "pending":
        raise TripError("a proposta ja foi respondida", "offer_expired")
    offer.state, offer.responded_at = ("expired" if expired else "rejected"), now()
    trip = offer.trip
    push.send(db, "driver", offer.driver.uuid, "offer", offer_payload(offer))  # a app tira o cartao da proposta
    _event(db, trip, "offer_expired" if expired else "offer_rejected", actor, offer.driver.name)
    db.flush()
    dispatch(db, trip)


# ---- viagem em curso -------------------------------------------------------------------------
def _require(trip: Trip, *states: str):
    if trip.state not in states:
        raise TripError(f"acao invalida no estado '{trip.state}'")


def arrive(db, trip: Trip, actor: str = "driver") -> Trip:
    _require(trip, "accepted")
    trip.state, trip.arrived_at = "arrived", now()
    _event(db, trip, "arrived", actor)
    _notify(db, trip)
    return trip


def pin_verified(db, trip: Trip) -> bool:
    return db.query(TripEvent).filter_by(trip_id=trip.id, kind="pin_verified").first() is not None


def verify_pin(db, trip: Trip, actor: str = "driver") -> Trip:
    """O motorista confirmou o PIN do passageiro (a app Driver compara-o localmente)."""
    _require(trip, "accepted", "arrived")
    if not pin_verified(db, trip):
        _event(db, trip, "pin_verified", actor)
        _notify(db, trip)
    return trip


def start(db, trip: Trip, pin: str | None = None, actor: str = "driver") -> Trip:
    _require(trip, "accepted", "arrived")
    if trip.pin and pin is not None and pin != trip.pin:
        raise TripError("PIN errado", "wrong_pin")
    t = now()
    trip.arrived_at = trip.arrived_at or t
    trip.state, trip.started_at = "in_progress", t
    _event(db, trip, "started", actor)
    _notify(db, trip)
    return trip


def complete_stop(db, trip: Trip, actor: str = "driver") -> Trip:
    """Marca a proxima paragem intermedia como concluida."""
    _require(trip, "in_progress")
    stops = jget(trip.stops, [])
    for s in stops:
        if not s.get("done"):
            s["done"] = True
            trip.stops = jset(stops)
            _event(db, trip, "stop_completed", actor, s.get("address", ""))
            _notify(db, trip)
            return trip
    raise TripError("sem paragens pendentes")


def complete(db, trip: Trip, distance_m: int | None = None, duration_s: int | None = None,
             dropoff: tuple | None = None, actor: str = "driver") -> Trip:
    _require(trip, "in_progress")
    t = now()
    if dropoff:
        trip.dropoff_lat, trip.dropoff_lng = dropoff
    if distance_m is None:
        if trip.dropoff_lat is not None:
            distance_m, _ = geo.road_estimate(trip.pickup_lat, trip.pickup_lng, trip.dropoff_lat,
                                              trip.dropoff_lng, settings.get(db, "road_factor"), 1)
        else:
            distance_m = trip.est_distance_m
    if duration_s is None:
        duration_s = max(t - (trip.started_at or t), 0) or trip.est_duration_s
    promo = db.get(Promo, trip.promo_id) if trip.promo_id else None
    q = pricing.compute(trip.product, distance_m, duration_s,
                        pricing.promo_discount(promo) if promo else None)
    trip.distance_m, trip.duration_s = distance_m, duration_s
    trip.fare, trip.discount = q.total, q.discount
    stops_fee = 50 * len(jget(trip.stops, []))
    trip.fare += stops_fee
    trip.fare_breakdown = jset({**_breakdown(trip), "final": q.as_dict(), "stops_fee": stops_fee})
    trip.state, trip.completed_at = "completed", t
    if promo:
        promo.uses += 1
        rp = (db.query(RiderPromo).filter(RiderPromo.rider_id == trip.rider_id, RiderPromo.promo_id == promo.id,
                                          RiderPromo.used_trip_id.is_(None)).first())
        if rp:
            rp.used_trip_id = trip.id
    _settle(db, trip, gross=q.subtotal + stops_fee, paid=q.total + stops_fee, discount=q.discount)
    _free_driver(db, trip.driver)
    _event(db, trip, "completed", actor, f"{q.total / 100:.2f} · {distance_m / 1000:.1f} km")
    from domain.models import Notification
    if trip.driver:
        db.add(Notification(owner_type="driver", owner_id=trip.driver.id, title="Viagem concluída",
                            body=f"{trip.pickup_address or 'Recolha'} → {trip.dropoff_address or 'Destino'}"))
    _notify(db, trip)
    return trip


def cancel(db, trip: Trip, by: str, reason: str = "") -> Trip:
    _require(trip, "requested", "accepted", "arrived", "in_progress")
    t = now()
    fee = 0
    if (by == "rider" and trip.accepted_at and trip.state in ("accepted", "arrived")
            and t - trip.accepted_at > settings.get(db, "rider_free_cancel_s")):
        fee = trip.product.cancel_fee
    for o in trip.offers:
        if o.state == "pending":
            o.state, o.responded_at = "withdrawn", t
            push.send(db, "driver", o.driver.uuid, "offer", offer_payload(o))
    trip.state, trip.cancelled_at, trip.cancelled_by = "cancelled", t, by
    trip.cancel_reason = reason[:200]
    if fee and trip.driver:
        trip.fare = fee
        trip.fare_breakdown = jset({**_breakdown(trip), "cancel_fee": fee})
        _settle(db, trip, gross=fee, paid=fee, discount=0, kind="cancel_fee")
    if trip.driver:
        _free_driver(db, trip.driver)
    _event(db, trip, "cancelled", by, reason + (f" · taxa {fee / 100:.2f}" if fee else ""))
    _notify(db, trip)
    return trip


def rate(db, trip: Trip, by: str, stars: int, comment: str = "") -> Trip:
    _require(trip, "completed")
    if not 1 <= stars <= 5:
        raise TripError("classificacao de 1 a 5", "bad_rating")
    if by == "rider":
        if trip.rider_to_driver_rating is None and trip.driver:
            trip.driver.rating_sum += stars
            trip.driver.rating_count += 1
        elif trip.driver:
            trip.driver.rating_sum += stars - trip.rider_to_driver_rating
        trip.rider_to_driver_rating, trip.rider_comment = stars, comment[:300]
    else:
        if trip.driver_to_rider_rating is None:
            trip.rider.rating_sum += stars
            trip.rider.rating_count += 1
        else:
            trip.rider.rating_sum += stars - trip.driver_to_rider_rating
        trip.driver_to_rider_rating = stars
    _event(db, trip, "rated", by, f"{stars}★ {comment}".strip())
    return trip


FORCEABLE = ("requested", "accepted", "arrived", "in_progress", "completed", "cancelled")


def force_state(db, trip: Trip, state: str, admin: str) -> Trip:
    """Salto manual (consola) para desbloquear testes. Completar a forca liquida a viagem."""
    if state not in FORCEABLE:
        raise TripError("estado invalido")
    if state == "completed":
        if trip.state != "in_progress":
            trip.state, trip.started_at = "in_progress", trip.started_at or now()
        return complete(db, trip, actor="admin")
    if state == "cancelled":
        return cancel(db, trip, "admin", f"forcado por {admin}")
    if state != "requested" and not trip.driver:
        raise TripError("precisa de motorista atribuido (faz uma proposta primeiro)")
    trip.state = state
    if state == "requested":
        for o in trip.offers:
            if o.state == "pending":
                o.state = "withdrawn"
                push.send(db, "driver", o.driver.uuid, "offer", offer_payload(o))
        if trip.driver:
            _free_driver(db, trip.driver)
        trip.driver = trip.vehicle = None
        trip.requested_at = now()
    _event(db, trip, "forced", "admin", f"{state} por {admin}")
    _notify(db, trip)
    return trip


def _breakdown(trip: Trip) -> dict:
    return jget(trip.fare_breakdown, {})


def _free_driver(db, driver: Driver | None):
    if driver and driver.availability == "on_trip":
        driver.availability = "online"
        if driver.organization:
            for u in driver.organization.users:
                push.send(db, "fleet", u.uuid, "driver_status",
                          {"driverUUID": driver.uuid, "status": "online"})
        touch(db, "drivers")


# ---- dinheiro --------------------------------------------------------------------------------
def _settle(db, trip: Trip, gross: int, paid: int, discount: int, kind: str = "fare"):
    """Lancamentos de uma viagem terminada (ou taxa de cancelamento).

    motorista: +bruto  -comissao  -taxa_frota  (-pago se dinheiro: o motorista ja tem o dinheiro)
    frota:     +taxa_frota          plataforma: +comissao  -desconto (promo paga pela plataforma)
    """
    driver = trip.driver
    if not driver:
        return
    pct = settings.get(db, "platform_commission_pct")
    commission = round(gross * pct / 100)
    org = db.get(Organization, trip.org_id) if trip.org_id else None
    fleet_fee = round((gross - commission) * org.fleet_fee_pct / 100) if org else 0
    entries = [("driver", driver.id, kind, gross, "Tarifa"),
               ("driver", driver.id, "commission", -commission, f"Comissão {pct:g}%"),
               ("platform", None, "commission", commission, "")]
    if fleet_fee:
        entries += [("driver", driver.id, "fleet_fee", -fleet_fee, f"Frota {org.name}"),
                    ("fleet", org.id, "fleet_fee", fleet_fee, driver.name)]
    if discount:
        entries.append(("platform", None, "promo", -discount, "Desconto promocional"))
    if trip.payment_method == "cash":
        entries.append(("driver", driver.id, "cash_collected", -paid, "Recebido em dinheiro"))
    for party, pid, k, amount, note in entries:
        if amount:
            db.add(LedgerEntry(party=party, party_id=pid, kind=k, amount=amount, trip_id=trip.id, note=note))
    touch(db, "finance")


# ---- motoristas ------------------------------------------------------------------------------
def open_session(db, driver: Driver) -> None:
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


def go_online(db, driver: Driver, lat: float | None = None, lng: float | None = None) -> Driver:
    if driver.status != "approved":
        raise TripError("motorista ainda nao aprovado", "driver_not_approved")
    if not driver.vehicle or driver.vehicle.status != "active":
        raise TripError("sem veiculo ativo atribuido", "no_vehicle")
    if lat is not None:
        set_location(db, driver, lat, lng)
    if driver.availability == "offline":
        driver.availability = "online"
        driver.online_since = now()
        open_session(db, driver)
    touch(db, "drivers")
    for u in (driver.organization.users if driver.organization else []):
        push.send(db, "fleet", u.uuid, "driver_status", {"driverUUID": driver.uuid, "status": "online"})
    # viagens a espera de motorista podem ser propostas a este
    for trip in db.query(Trip).filter(Trip.state == "requested").all():
        dispatch(db, trip)
    return driver


def go_offline(db, driver: Driver) -> Driver:
    if driver.availability == "on_trip":
        raise TripError("termina a viagem antes de ficar offline", "on_trip")
    driver.availability = "offline"
    driver.online_since = None
    close_sessions(db, driver)
    for o in db.query(Offer).filter(Offer.driver_id == driver.id, Offer.state == "pending").all():
        reject_offer(db, o, actor="system", expired=True)
    for u in (driver.organization.users if driver.organization else []):
        push.send(db, "fleet", u.uuid, "driver_status", {"driverUUID": driver.uuid, "status": "offline"})
    touch(db, "drivers")
    return driver


def set_location(db, driver: Driver, lat: float, lng: float, heading: float | None = None,
                 simulated: bool | None = None):
    driver.lat, driver.lng = lat, lng
    if heading is not None:
        driver.heading = heading
    driver.location_at = now()
    if simulated is not None:
        driver.simulated = simulated
    _auto_arrive(db, driver)
    touch(db, "drivers")


def _auto_arrive(db, driver: Driver):
    """A app Driver (4.599) nao tem passo "cheguei": deslizar "Recolher" ja inicia a viagem e start-waiting so existe
    no temporizador manual. Como na Uber, a chegada decide-se no servidor pela posicao (o passageiro ve "chegou")."""
    trip = active_trip_for_driver(db, driver)
    if trip and trip.state == "accepted" and driver.lat is not None and             geo.haversine_m(driver.lat, driver.lng, trip.pickup_lat, trip.pickup_lng) <= settings.get(db, "arrive_radius_m"):
        arrive(db, trip, actor="system")


def assign_vehicle(db, driver: Driver, vehicle: Vehicle | None):
    if driver.availability == "on_trip":
        raise TripError("motorista em viagem")
    if vehicle:
        for other in db.query(Driver).filter(Driver.vehicle_id == vehicle.id, Driver.id != driver.id).all():
            if other.availability == "on_trip":
                raise TripError(f"veiculo em uso por {other.name}")
            other.vehicle_id = None
    driver.vehicle = vehicle
    touch(db, "drivers")


# ---- relogio (thread em segundo plano, 1x por segundo) ---------------------------------------
def tick(db) -> None:
    t = now()
    for offer in db.query(Offer).filter(Offer.state == "pending", Offer.expires_at <= t).all():
        reject_offer(db, offer, actor="system", expired=True)
    for trip in db.query(Trip).filter(Trip.state == "requested").all():
        dispatch(db, trip)
    if settings.get(db, "simulate_movement"):
        _simulate(db)


def _simulate(db):
    """Motoristas simulados andam para a recolha / destino (para ver o mapa a mexer)."""
    step = settings.get(db, "avg_speed_kmh") / 3.6     # metros por segundo de relogio
    for trip in db.query(Trip).filter(Trip.state.in_(("accepted", "in_progress"))).all():
        d = trip.driver
        if not d or not d.simulated or d.lat is None:
            continue
        if trip.state == "accepted":
            target = (trip.pickup_lat, trip.pickup_lng)
        elif trip.dropoff_lat is not None:
            target = (trip.dropoff_lat, trip.dropoff_lng)
        else:
            continue
        lat, lng, head, _ = geo.step_towards(d.lat, d.lng, *target, step)
        d.lat, d.lng, d.heading, d.location_at = lat, lng, head, now()
        _auto_arrive(db, d)
        touch(db, "drivers")

# -*- coding: utf-8 -*-
"""Dominio -> JSON da consola (snake_case, dinheiro em centimos, datas em epoch s)."""
from domain.models import (City, Document, Driver, FleetUser, LedgerEntry, Offer, Organization, Payout,
                           Product, Promo, Rider, Trip, TripEvent, Vehicle, jget)


def city(c: City) -> dict:
    return {"id": c.id, "uuid": c.uuid, "name": c.name, "country_iso2": c.country_iso2, "currency": c.currency,
            "timezone": c.timezone, "center_lat": c.center_lat, "center_lng": c.center_lng,
            "radius_km": c.radius_km, "active": c.active}


def product(p: Product) -> dict:
    return {"id": p.id, "uuid": p.uuid, "city_id": p.city_id, "code": p.code, "name": p.name,
            "description": p.description, "capacity": p.capacity, "base_fare": p.base_fare, "per_km": p.per_km,
            "per_min": p.per_min, "minimum_fare": p.minimum_fare, "booking_fee": p.booking_fee,
            "cancel_fee": p.cancel_fee, "surge": p.surge, "min_vehicle_year": p.min_vehicle_year,
            "sort_order": p.sort_order, "active": p.active}


def org_short(o: Organization | None) -> dict | None:
    return {"id": o.id, "name": o.name} if o else None


def vehicle_short(v: Vehicle | None) -> dict | None:
    return {"id": v.id, "uuid": v.uuid, "label": v.label, "plate": v.plate, "make": v.make,
            "model": v.model, "color": v.color, "color_hex": v.color_hex} if v else None


def vehicle(v: Vehicle, drivers: list[Driver] | None = None) -> dict:
    return {**vehicle_short(v), "year": v.year, "vin": v.vin, "seats": v.seats, "status": v.status,
            "product_ids": v.product_ids, "org": org_short(v.organization), "owner_driver_id": v.owner_driver_id,
            "created_at": v.created_at,
            "drivers": [{"id": d.id, "name": d.name} for d in (drivers or [])]}


def driver_short(d: Driver | None) -> dict | None:
    return {"id": d.id, "uuid": d.uuid, "name": d.name, "phone": d.phone, "rating": d.rating} if d else None


def driver(d: Driver, balance: int | None = None) -> dict:
    return {"id": d.id, "uuid": d.uuid, "first_name": d.first_name, "last_name": d.last_name, "name": d.name,
            "phone": d.phone, "email": d.email, "license_number": d.license_number, "status": d.status,
            "availability": d.availability, "org": org_short(d.organization), "city_id": d.city_id,
            "vehicle": vehicle_short(d.vehicle), "lat": d.lat, "lng": d.lng, "heading": d.heading,
            "location_at": d.location_at, "rating": d.rating, "rating_count": d.rating_count,
            "offers_received": d.offers_received, "offers_accepted": d.offers_accepted,
            "acceptance_rate": round(d.offers_accepted / d.offers_received, 3) if d.offers_received else None,
            "created_at": d.created_at, "last_seen_at": d.last_seen_at, "online_since": d.online_since,
            "simulated": d.simulated, "balance": balance}


def rider_short(r: Rider | None) -> dict | None:
    return {"id": r.id, "uuid": r.uuid, "name": r.name, "phone": r.phone, "rating": r.rating} if r else None


def rider(r: Rider) -> dict:
    return {**rider_short(r), "first_name": r.first_name, "last_name": r.last_name, "email": r.email,
            "status": r.status, "rating_count": r.rating_count, "default_payment": r.default_payment,
            "lat": r.lat, "lng": r.lng, "created_at": r.created_at, "last_seen_at": r.last_seen_at}


def fleet_user(u: FleetUser) -> dict:
    return {"id": u.id, "uuid": u.uuid, "org_id": u.org_id, "first_name": u.first_name, "last_name": u.last_name,
            "phone": u.phone, "email": u.email, "role": u.role, "active": u.active, "created_at": u.created_at,
            "last_seen_at": u.last_seen_at}


def organization(o: Organization) -> dict:
    return {"id": o.id, "uuid": o.uuid, "name": o.name, "tax_id": o.tax_id, "email": o.email, "phone": o.phone,
            "city_id": o.city_id, "fleet_fee_pct": o.fleet_fee_pct, "iban": o.iban, "status": o.status,
            "created_at": o.created_at, "drivers_count": len(o.drivers), "vehicles_count": len(o.vehicles),
            "online_count": sum(1 for d in o.drivers if d.availability != "offline")}


def trip_row(t: Trip) -> dict:
    return {"id": t.id, "uuid": t.uuid, "state": t.state, "product": {"id": t.product.id, "name": t.product.name},
            "rider": rider_short(t.rider), "driver": driver_short(t.driver),
            "pickup_address": t.pickup_address, "dropoff_address": t.dropoff_address,
            "est_fare": t.est_fare, "fare": t.fare, "payment_method": t.payment_method,
            "requested_at": t.requested_at, "completed_at": t.completed_at, "cancelled_at": t.cancelled_at,
            "org": {"id": t.org_id} if t.org_id else None, "source": t.source}


def offer(o: Offer) -> dict:
    return {"id": o.id, "uuid": o.uuid, "driver": driver_short(o.driver), "state": o.state,
            "pickup_distance_m": o.pickup_distance_m, "pickup_eta_s": o.pickup_eta_s, "created_at": o.created_at,
            "expires_at": o.expires_at, "responded_at": o.responded_at}


def event(e: TripEvent) -> dict:
    return {"id": e.id, "at": e.at, "kind": e.kind, "actor": e.actor, "detail": e.detail}


def ledger(e: LedgerEntry) -> dict:
    return {"id": e.id, "at": e.at, "party": e.party, "party_id": e.party_id, "kind": e.kind, "amount": e.amount,
            "trip_id": e.trip_id, "payout_id": e.payout_id, "note": e.note}


def trip(t: Trip, ledger_rows: list[LedgerEntry]) -> dict:
    return {**trip_row(t), "city": t.city.name, "currency": t.city.currency, "vehicle": vehicle_short(t.vehicle),
            "pickup": {"lat": t.pickup_lat, "lng": t.pickup_lng},
            "dropoff": {"lat": t.dropoff_lat, "lng": t.dropoff_lng} if t.dropoff_lat is not None else None,
            "est_distance_m": t.est_distance_m, "est_duration_s": t.est_duration_s, "distance_m": t.distance_m,
            "duration_s": t.duration_s, "surge": t.surge, "discount": t.discount, "pin": t.pin,
            "breakdown": jget(t.fare_breakdown, {}), "cancelled_by": t.cancelled_by, "cancel_reason": t.cancel_reason,
            "rider_to_driver_rating": t.rider_to_driver_rating, "driver_to_rider_rating": t.driver_to_rider_rating,
            "rider_comment": t.rider_comment, "accepted_at": t.accepted_at, "arrived_at": t.arrived_at,
            "started_at": t.started_at, "driver_live": {"lat": t.driver.lat, "lng": t.driver.lng,
                                                        "heading": t.driver.heading} if t.driver else None,
            "events": [event(e) for e in t.events], "offers": [offer(o) for o in t.offers],
            "ledger": [ledger(e) for e in ledger_rows]}


def document(d: Document, owner_name: str = "") -> dict:
    return {"id": d.id, "uuid": d.uuid, "owner_type": d.owner_type, "owner_id": d.owner_id, "owner_name": owner_name,
            "kind": d.kind, "number": d.number, "expires_on": d.expires_on, "status": d.status,
            "has_file": bool(d.file_name), "notes": d.notes, "reviewed_by": d.reviewed_by,
            "reviewed_at": d.reviewed_at, "created_at": d.created_at}


def promo(p: Promo) -> dict:
    return {"id": p.id, "code": p.code, "description": p.description, "kind": p.kind, "value": p.value,
            "max_discount": p.max_discount, "max_uses": p.max_uses, "per_rider": p.per_rider, "uses": p.uses,
            "product_id": p.product_id, "valid_from": p.valid_from, "valid_to": p.valid_to, "active": p.active,
            "created_at": p.created_at}


def payout(p: Payout, name: str = "") -> dict:
    return {"id": p.id, "uuid": p.uuid, "party": p.party, "party_id": p.party_id, "party_name": name,
            "amount": p.amount, "status": p.status, "reference": p.reference, "created_at": p.created_at,
            "paid_at": p.paid_at}

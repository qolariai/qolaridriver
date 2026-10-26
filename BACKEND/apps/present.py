# -*- coding: utf-8 -*-
"""Conversoes dominio -> formatos comuns dos modelos thrift das APKs (nomes de campo camelCase)."""
from domain.models import Driver, Rider, Trip, Vehicle


def money(cents: int | None, currency: str = "EUR") -> str:
    if cents is None:
        return ""
    sign = "-" if cents < 0 else ""
    v = f"{abs(cents) / 100:,.2f}".replace(",", " ").replace(".", ",")
    return f"{sign}{v} €" if currency == "EUR" else f"{sign}{v} {currency}"


def amount(cents: int | None) -> str:
    """'12.34' (string decimal, como os campos `total`/`tripEarning` da Fleet)."""
    return f"{(cents or 0) / 100:.2f}"


def ms(ts: int | None) -> int | None:
    return ts * 1000 if ts else None


def phone_parts(phone: str) -> dict:
    """+351912345678 -> {countryCode: '+351', nationalPhoneNumber: '912345678'} (PhoneNumber)."""
    p = phone or ""
    if p.startswith("+351"):
        return {"countryCode": "+351", "nationalPhoneNumber": p[4:]}
    if p.startswith("+") and len(p) > 4:
        return {"countryCode": p[:3], "nationalPhoneNumber": p[3:]}
    return {"countryCode": "", "nationalPhoneNumber": p}


def location(lat, lng, address: str = "", title: str = "") -> dict | None:
    """rtapi.models.location.Location."""
    if lat is None or lng is None:
        return None
    return {"latitude": lat, "longitude": lng, "address": address, "formattedAddress": address,
            "shortAddress": address.split(",")[0] if address else "", "title": title or address,
            "nickname": title}


def rider(r: Rider) -> dict:
    """rtapi.models.rider.Rider."""
    pp = phone_parts(r.phone)
    return {"uuid": r.uuid, "firstName": r.first_name, "lastName": r.last_name, "email": r.email,
            "mobileDigits": pp["nationalPhoneNumber"], "mobileCountryIso2": "PT",
            "claimedMobile": r.phone, "hasConfirmedMobile": True, "hasConfirmedEmail": bool(r.email),
            "rating": r.rating, "displayRating": r.rating, "role": "client", "userType": "client",
            "isAdmin": False, "isTeen": False, "profiles": [], "creditBalances": [], "tripBalances": []}


def vehicle(v: Vehicle | None) -> dict | None:
    if not v:
        return None
    return {"uuid": v.uuid, "make": v.make, "model": v.model, "year": v.year, "licensePlate": v.plate,
            "color": v.color, "colorHexCode": v.color_hex, "vehicleColorName": v.color,
            "desc": f"{v.make} {v.model}", "capacity": v.seats}


def driver(d: Driver | None) -> dict | None:
    if not d:
        return None
    return {"uuid": d.uuid, "name": d.name, "firstName": d.first_name, "lastName": d.last_name,
            "displayName": d.first_name, "rating": d.rating, "mobile": d.phone, "phoneNumber": d.phone,
            "pictureUrl": None, "location": location(d.lat, d.lng) and {**location(d.lat, d.lng), "course": d.heading}}


def trip_state_label(t: Trip) -> str:
    return {"requested": "A procurar motorista", "accepted": "Motorista a caminho",
            "arrived": "O motorista chegou", "in_progress": "Em viagem", "completed": "Viagem concluída",
            "cancelled": "Viagem cancelada", "no_drivers": "Sem motoristas disponíveis"}.get(t.state, t.state)

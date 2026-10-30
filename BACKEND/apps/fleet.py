# -*- coding: utf-8 -*-
"""App Qolari Fleet (base Uber Fleet / vehicle-supplier) -> dominio.

Contratos: contracts/fleet_endpoints.json + fleet_models.json. Enums confirmados no smali:
    supply.fleetmanager.DriverStatus          OFFLINE | ONLINE | ONTRIP
    supply.fleetmanager.OnboardingStatus      ACTIVE | APPLIED | REJECTED | WAITLISTED | ...
    vs_supplier_management.OrganizationOnboardingStatus  COMPLETE | IN_PROGRESS
    vs_compliancemanager.ComplianceStatus     ACTIVE | INACTIVE | INVALID
O utilizador da app e um FleetUser; tudo e filtrado pela sua Organization.
"""
import time as _time

from apps import present
from apps.rtapi import Call, RtError, handles
from core.db import touch
from domain import finance, trips
from domain.models import (Document, Driver, LedgerEntry, Payout, Trip, TripEvent, Vehicle, jset, now)
from domain.trips import TripError

APP = "fleet"

REALTIME = {"offline": "OFFLINE", "online": "ONLINE", "on_trip": "ONTRIP"}
ONBOARDING = {"approved": "ACTIVE", "pending": "APPLIED", "rejected": "REJECTED", "suspended": "WAITLISTED"}


def _org(call: Call):
    user = call.subject()
    if not user.active or user.organization.status != "active":
        raise RtError(403, "forbidden", "frota inativa")
    return user, user.organization


def _driver_of(call: Call, org, uuid) -> Driver:
    d = call.db.query(Driver).filter_by(uuid=str(uuid), org_id=org.id).first() if uuid else None
    if not d:
        raise RtError(404, "driver_not_found", "motorista inexistente nesta frota")
    return d


def _vehicle_of(call: Call, org, uuid) -> Vehicle:
    v = call.db.query(Vehicle).filter_by(uuid=str(uuid), org_id=org.id).first() if uuid else None
    if not v:
        raise RtError(404, "vehicle_not_found", "veiculo inexistente nesta frota")
    return v


def _week_bounds(offset_weeks: int = 0) -> tuple[int, int]:
    lt = _time.localtime()
    today = int(_time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))
    start = today - lt.tm_wday * 86400 - offset_weeks * 7 * 86400
    return start, start + 7 * 86400


def driver_overview(d: Driver) -> dict:
    """supply.fleetmanager.DriverOverview."""
    return {"uuid": d.uuid, "name": d.name, "mobile": d.phone, "email": d.email, "pictureUrl": None,
            "licensePlate": d.vehicle.plate if d.vehicle else None,
            "vehicleUUID": d.vehicle.uuid if d.vehicle else None,
            "realtimeStatus": REALTIME.get(d.availability, "OFFLINE"),
            "onboardingStatus": ONBOARDING.get(d.status, "APPLIED"),
            "lastOnlineTime": present.ms(d.last_seen_at or d.location_at), "waitlistedByFleet": False}


def vehicle_json(db, v: Vehicle) -> dict:
    """vs_vehiclemanager.Vehicle."""
    drivers = db.query(Driver).filter(Driver.vehicle_id == v.id).all()
    docs = db.query(Document).filter(Document.owner_type == "vehicle", Document.owner_id == v.id).all()
    ok = docs and all(x.status == "approved" for x in docs)
    return {"vehicleUUID": v.uuid, "ownerUUID": v.organization.uuid if v.organization else None,
            "make": v.make, "model": v.model, "year": v.year, "licensePlate": v.plate, "vin": v.vin,
            "color": v.color, "colorHexCode": v.color_hex, "imageURL": None,
            "labels": [{"value": v.status}], "lastModified": present.ms(v.created_at),
            "assignments": [{"entityUUID": d.uuid} for d in drivers],
            "compliance": {"status": "ACTIVE" if ok and v.status == "active" else "INACTIVE",
                           "documents": [{"documentType": x.kind, "status": x.status.upper(),
                                          "expiresAt": x.expires_on} for x in docs]}}


def member_json(db, d: Driver, org) -> dict:
    """vs_drivermanager.Driver = {member{user, membership}, associatedVehicles, complianceInfo}."""
    docs = db.query(Document).filter(Document.owner_type == "driver", Document.owner_id == d.id).all()
    done = db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").count()
    return {"member": {
        "user": {"uuid": d.uuid, "name": {"firstName": d.first_name, "lastName": d.last_name},
                 "email": d.email, "phone": present.phone_parts(d.phone), "pictureUrl": None,
                 "isBanned": d.status == "suspended",
                 "driverInfo": {"completedTripsCount": done, "recognitionRating": d.rating,
                                "onboardingStatus": ONBOARDING.get(d.status, "APPLIED")}},
        "membership": {"orgUUID": org.uuid, "userUUID": d.uuid, "linkedAt": present.ms(d.created_at),
                       "labels": []}},
        "associatedVehicles": [vehicle_json(db, d.vehicle)] if d.vehicle else [],
        "complianceInfo": {"status": "ACTIVE" if docs and all(x.status == "approved" for x in docs) else "INACTIVE",
                           "documents": [{"documentType": x.kind, "status": x.status.upper(),
                                          "expiresAt": x.expires_on} for x in docs]}}


# ---- conta e organizacao ---------------------------------------------------------------------
@handles(APP, "POST", "/rt/fleet/get-is-authorized-fleet-partner-v2")
def is_partner(call: Call):
    user = call.subject()
    return {"isAuthorizedFleetPartner": bool(user.active and user.organization.status == "active")}


@handles(APP, "POST", "/rt/fleet/get-partner-info-v2")
def partner_info(call: Call):
    user, org = _org(call)
    city = org.drivers[0].city_id if org.drivers else None
    return {"partnerUUID": org.uuid, "firstName": user.first_name, "lastName": user.last_name,
            "email": user.email or org.email, "phoneNumber": present.phone_parts(user.phone),
            "city": "Lisboa", "cityID": city, "country": "PT", "timezone": "Europe/Lisbon",
            "pictureURL": None, "mobilePluginConfig": {}}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-supplier-management/get-user-organizations")
def user_orgs(call: Call):
    user, org = _org(call)
    return {"orgs": [{"org": {"uuid": org.uuid, "name": org.name, "onboardingStatus": "COMPLETE",
                              "organizationTypes": ["FLEET"], "parentOrgUUID": None},
                      "userRoles": [{"name": user.role.upper()}]}]}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-supplier-context-manager/get-supplier-context")
def supplier_context(call: Call):
    user, org = _org(call)
    return {"properties": {"orgName": {"stringValue": org.name}, "driverCount": {"integerValue": len(org.drivers)},
                           "vehicleCount": {"integerValue": len(org.vehicles)}}}


@handles(APP, "POST", "/rt/fleet/mobile-ack", "/rt/fleet/sign-regulatory-documents",
         "/rt/vehicle-supplier/vs-communication/update-inbox-message", "/rt/fleet/save-survey-answers",
         "/rt/vehicle-supplier/vs-survey/submit-csat-survey")
def ack(call: Call):
    return {}


@handles(APP, "POST", "/rt/fleet/get-pending-regulatory-documents-v2")
def regulatory(call: Call):
    return {"documents": []}


@handles(APP, "POST", "/rt/fleet/get-survey-questions", "/rt/vehicle-supplier/vs-survey/get-csat-surveys")
def surveys(call: Call):
    return {"questions": [], "surveys": []}


# ---- motoristas ------------------------------------------------------------------------------
@handles(APP, "POST", "/rt/fleet/get-fleet-drivers-v2")
def fleet_drivers(call: Call):
    db = call.db
    user, org = _org(call)
    start, end = _week_bounds()
    week = sum(finance.summary(db, "fleet", org.id, start, end)["by_kind"].values())
    drivers = sorted(org.drivers, key=lambda d: (d.availability == "offline", d.first_name))
    return {"drivers": [driver_overview(d) for d in drivers], "driverCount": len(drivers),
            "currentWeeklyEarnings": present.money(week)}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-drivermanager/get-drivers",
         "/rt/vehicle-supplier/vs-drivermanager/search-drivers")
def vs_drivers(call: Call):
    db = call.db
    user, org = _org(call)
    q = str(call.get("query", "searchTerm", "name", default="") or "").lower()
    rows = [d for d in org.drivers if not q or q in d.name.lower() or q in d.phone]
    return {"drivers": [member_json(db, d, org) for d in rows], "orgUUID": org.uuid, "pagingResult": {}}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-drivermanager/get-driver")
def vs_driver(call: Call):
    user, org = _org(call)
    d = _driver_of(call, org, call.get("driverUUID", "userUUID", "uuid"))
    return {"driver": member_json(call.db, d, org)}


def _supply(db, d: Driver) -> dict:
    """supply.armada.GetDriverCurrentSupplyResponse."""
    t = trips.active_trip_for_driver(db, d)
    start, end = _week_bounds()
    day0 = end - 7 * 86400
    s = finance.summary(db, "driver", d.id, day0, end)["by_kind"]
    out = {"driverOverview": driver_overview(d),
           "location": {"point": {"latitude": d.lat, "longitude": d.lng}, "course": d.heading,
                        "realtimeStatus": REALTIME.get(d.availability, "OFFLINE")} if d.lat is not None else None,
           "tripCount": db.query(Trip).filter(Trip.driver_id == d.id, Trip.completed_at >= day0).count(),
           "formattedEarnings": present.money(s.get("fare", 0) + s.get("commission", 0) + s.get("fleet_fee", 0))}
    if t:
        out["supplyOverview"] = {"tripUuid": t.uuid, "tripStatus": t.state.upper(),
                                 "pickup": {"latitude": t.pickup_lat, "longitude": t.pickup_lng},
                                 "pickupAddress": t.pickup_address,
                                 "destination": {"latitude": t.dropoff_lat, "longitude": t.dropoff_lng},
                                 "destinationAddress": t.dropoff_address, "cityName": t.city.name,
                                 "tripStartTime": present.ms(t.started_at or t.accepted_at),
                                 "surge": f"{t.surge:g}x"}
    return out


@handles(APP, "POST", "/rt/fleet/get-driver-current-supply",
         "/rt/vehicle-supplier/driver-supply/get-driver-current-supply")
def current_supply(call: Call):
    user, org = _org(call)
    return _supply(call.db, _driver_of(call, org, call.get("driverUUID", "driverUuid", "uuid")))


@handles(APP, "POST", "/rt/vehicle-supplier/get-driver-events")
def live_map(call: Call):
    """Mapa ao vivo: posicao e estado de todos os motoristas da frota."""
    user, org = _org(call)
    return {"drivers": [{"driverUUID": d.uuid, "name": d.name, "status": REALTIME.get(d.availability, "OFFLINE"),
                         "location": {"latitude": d.lat, "longitude": d.lng, "course": d.heading},
                         "timestamp": present.ms(d.location_at)} for d in org.drivers if d.lat is not None]}


@handles(APP, "POST", "/rt/fleet/get-driver-action-log-v2")
def action_log(call: Call):
    db = call.db
    user, org = _org(call)
    d = _driver_of(call, org, call.get("driverUUID", "driverUuid", "uuid"))
    rows = (db.query(TripEvent).join(Trip, Trip.id == TripEvent.trip_id).filter(Trip.driver_id == d.id)
            .order_by(TripEvent.id.desc()).limit(100).all())
    return {"driverUUID": d.uuid, "driverActions": [
        {"actionType": e.kind.upper(), "timestamp": present.ms(e.at), "description": e.detail} for e in rows]}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-membershipmanager/invite-user-to-org")
def invite(call: Call):
    """Convite = motorista novo (pendente) na frota com esse telefone; entra na app Driver com ele."""
    from apps.identity import normalize_phone
    db = call.db
    user, org = _org(call)
    b = call.body
    phone_obj = b.get("phone") or b.get("phoneNumber") or {}
    phone = normalize_phone((phone_obj.get("countryCode", "") + phone_obj.get("nationalPhoneNumber", ""))
                            if isinstance(phone_obj, dict) else str(phone_obj))
    if len(phone) < 8:
        raise RtError(400, "invalid_phone", "telefone invalido")
    d = db.query(Driver).filter_by(phone=phone).first()
    if d and d.org_id and d.org_id != org.id:
        raise RtError(409, "driver_in_other_fleet", "o motorista ja pertence a outra frota")
    if not d:
        name = b.get("name") if isinstance(b.get("name"), dict) else {}
        d = Driver(phone=phone, first_name=name.get("firstName") or b.get("firstName") or "Convidado",
                   last_name=name.get("lastName") or b.get("lastName") or "", status="pending")
        db.add(d)
    d.org_id = org.id
    db.flush()
    touch(db, "drivers")
    return {"membershipUUID": d.uuid}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-membershipmanager/search-invites")
def invites(call: Call):
    user, org = _org(call)
    return {"invites": [{"membershipUUID": d.uuid, "phone": present.phone_parts(d.phone), "name": d.name,
                         "status": "PENDING", "createdAt": present.ms(d.created_at)}
                        for d in org.drivers if d.status == "pending"]}


# ---- veiculos --------------------------------------------------------------------------------
@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/get-vehicles-by-owner",
         "/rt/vehicle-supplier/vs-vehiclemanager/search-vehicles")
def vehicles(call: Call):
    user, org = _org(call)
    q = str(call.get("query", "searchTerm", "licensePlate", default="") or "").lower()
    rows = [v for v in org.vehicles if not q or q in v.plate.lower() or q in f"{v.make} {v.model}".lower()]
    return {"vehicles": [vehicle_json(call.db, v) for v in rows], "nextPageToken": None}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/get-vehicle")
def vehicle(call: Call):
    user, org = _org(call)
    return {"vehicle": vehicle_json(call.db, _vehicle_of(call, org, call.get("vehicleUUID", "uuid")))}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/create-vehicle")
def create_vehicle(call: Call):
    db = call.db
    user, org = _org(call)
    v = call.body.get("vehicle") if isinstance(call.body.get("vehicle"), dict) else call.body
    plate = str(v.get("licensePlate") or "").upper().strip()
    if not plate or not v.get("make") or not v.get("model"):
        raise RtError(400, "invalid_vehicle", "matricula, marca e modelo obrigatorios")
    if db.query(Vehicle).filter_by(plate=plate).first():
        raise RtError(409, "duplicate_plate", "ja existe um veiculo com esta matricula")
    row = Vehicle(organization=org, plate=plate, make=str(v["make"]), model=str(v["model"]),
                  year=int(v.get("year") or 2020), color=str(v.get("color") or ""),
                  color_hex=str(v.get("colorHexCode") or "#222222")[:7], vin=str(v.get("vin") or ""),
                  status="pending", products=jset([]))
    db.add(row)
    db.flush()
    touch(db, "vehicles")
    return {"vehicle": vehicle_json(db, row)}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/delete-vehicle")
def delete_vehicle(call: Call):
    db = call.db
    user, org = _org(call)
    v = _vehicle_of(call, org, call.get("vehicleUUID", "uuid"))
    for d in db.query(Driver).filter(Driver.vehicle_id == v.id).all():
        if d.availability == "on_trip":
            raise RtError(409, "vehicle_in_use", "veiculo em viagem")
        d.vehicle_id = None
    db.flush()
    if db.query(Trip).filter(Trip.vehicle_id == v.id).count():
        v.status = "inactive"          # tem historico: so desativa
    else:
        db.delete(v)
    touch(db, "vehicles")
    return {}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/assign-vehicle",
         "/rt/vehicle-supplier/vs-vehiclemanager/unassign-vehicle")
def assign(call: Call):
    user, org = _org(call)
    v = _vehicle_of(call, org, call.get("vehicleUUID", "uuid"))
    d = _driver_of(call, org, call.get("driverUUID", "entityUUID", "userUUID"))
    try:
        trips.assign_vehicle(call.db, d, None if call.path.endswith("unassign-vehicle") else v)
    except TripError as e:
        raise RtError(409, e.code, str(e))
    return {"vehicle": vehicle_json(call.db, v)}


@handles(APP, "POST", "/rt/vehicle-supplier/vs-vehiclemanager/modify-vehicle-labels")
def labels(call: Call):
    user, org = _org(call)
    v = _vehicle_of(call, org, call.get("vehicleUUID", "uuid"))
    return {"vehicle": vehicle_json(call.db, v)}


# ---- ganhos ----------------------------------------------------------------------------------
def summary_json(db, party: str, pid: int, start: int, end: int) -> dict:
    """supply.armada.EarningsSummary."""
    s = finance.summary(db, party, pid, start, end)["by_kind"]
    total = sum(v for k, v in s.items() if k != "payout")
    cash = -s.get("cash_collected", 0)
    trip_part = s.get("fare", 0) + s.get("fleet_fee", 0) if party == "fleet" else s.get("fare", 0)
    misc = total - trip_part + cash
    return {"startAt": present.ms(start), "endAt": present.ms(end), "currencyCode": "EUR",
            "timezone": "Europe/Lisbon", "isFinalized": end < now(), "isInstantPayAvailable": False,
            "total": present.amount(total), "formattedTotal": present.money(total),
            "tripEarning": present.amount(trip_part), "formattedTripEarning": present.money(trip_part),
            "cashCollected": present.amount(cash), "formattedCashCollected": present.money(cash),
            "miscTotal": present.amount(misc), "formattedMiscTotal": present.money(misc),
            "bankDeposit": present.amount(-s.get("payout", 0)), "formattedBankDeposit": present.money(-s.get("payout", 0)),
            "estimatedTotal": present.amount(total), "formattedEstimatedTotal": present.money(total),
            "cashouts": "0.00", "formattedCashouts": present.money(0)}


def trip_earnings(db, t: Trip) -> dict:
    entries = db.query(LedgerEntry).filter(LedgerEntry.trip_id == t.id, LedgerEntry.party == "driver").all()
    net = sum(e.amount for e in entries if e.kind != "cash_collected")
    return {"uuid": t.uuid, "driverUuid": t.driver.uuid if t.driver else None,
            "requestAt": present.ms(t.requested_at), "processedAt": present.ms(t.completed_at or t.cancelled_at),
            "pickupAddress": t.pickup_address, "dropoffAddress": t.dropoff_address,
            "total": present.amount(t.fare), "formattedTotal": present.money(t.fare),
            "driverFare": present.amount(net), "formattedDriverFare": present.money(net),
            "formattedCashCollected": present.money(t.fare if t.payment_method == "cash" else 0),
            "formattedDistance": f"{(t.distance_m or 0) / 1000:.1f} km", "duration": float(t.duration_s or 0),
            "vehicleType": t.product.name, "timezone": "Europe/Lisbon",
            "breakdown": [{"description": e.note or e.kind, "amount": present.amount(e.amount),
                           "formattedAmount": present.money(e.amount)} for e in entries]}


@handles(APP, "POST", "/rt/fleet/get-fleet-earnings-v2")
def fleet_earnings(call: Call):
    db = call.db
    user, org = _org(call)
    weeks = int(call.get("weekOffset", default=0) or 0)
    start, end = _week_bounds(weeks)
    ranges = [{"startAt": present.ms(s), "endAt": present.ms(e)} for s, e in (_week_bounds(i) for i in range(8))]
    return {"appliedTimeFilter": ranges[weeks] if weeks < 8 else ranges[0], "pastWeeks": ranges,
            "availableDateRanges": ranges, "dateRanges": ranges, "products": [],
            "driverProfiles": [{"uuid": d.uuid, "firstName": d.first_name, "lastName": d.last_name,
                                "userRating": d.rating} for d in org.drivers],
            "earningInfo": {"startAt": present.ms(start), "endAt": present.ms(end),
                            "partnerStatement": summary_json(db, "fleet", org.id, start, end),
                            "driverStatements": [{"driverUUID": d.uuid, "name": d.name,
                                                  **summary_json(db, "driver", d.id, start, end)}
                                                 for d in org.drivers],
                            "ledger": []}}


@handles(APP, "POST", "/rt/fleet/get-driver-daily-earnings-with-trips",
         "/rt/vehicle-supplier/vs-earnings/get-driver-daily-earnings-with-trips")
def driver_daily(call: Call):
    db = call.db
    user, org = _org(call)
    d = _driver_of(call, org, call.get("driverUUID", "driverUuid", "uuid"))
    lt = _time.localtime()
    start = int(_time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))
    day = call.get("startAt", "date")
    if isinstance(day, (int, float)) and day > 10 ** 11:
        start = int(day // 1000)
    end = start + 86400
    rows = db.query(Trip).filter(Trip.driver_id == d.id, Trip.completed_at >= start, Trip.completed_at < end).all()
    return {"summary": summary_json(db, "driver", d.id, start, end), "breakdown": [],
            "trips": [trip_earnings(db, t) for t in rows]}


@handles(APP, "POST", "/rt/fleet/get-trip-earnings")
def trip_earn(call: Call):
    db = call.db
    user, org = _org(call)
    t = db.query(Trip).filter_by(uuid=str(call.get("tripUUID", "tripUuid", "uuid", default="")), org_id=org.id).first()
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente nesta frota")
    return {"trip": trip_earnings(db, t)}


@handles(APP, "POST", "/rt/fleet/get-partner-statement")
def partner_statement(call: Call):
    db = call.db
    user, org = _org(call)
    start, end = _week_bounds(int(call.get("weekOffset", default=0) or 0))
    days = [summary_json(db, "fleet", org.id, s, s + 86400) for s in range(start, end, 86400)]
    return {"partnerStatement": {"summary": summary_json(db, "fleet", org.id, start, end), "days": days,
                                 "breakdown": []}}


@handles(APP, "POST", "/rt/fleet/get-driver-statement")
def driver_statement(call: Call):
    db = call.db
    user, org = _org(call)
    d = _driver_of(call, org, call.get("driverUUID", "driverUuid", "uuid"))
    start, end = _week_bounds(int(call.get("weekOffset", default=0) or 0))
    return {"driverStatement": {"summary": summary_json(db, "driver", d.id, start, end),
                                "days": [summary_json(db, "driver", d.id, s, s + 86400) for s in range(start, end, 86400)]}}


@handles(APP, "POST", "/rt/fleet/get-partner-statement-history")
def statement_history(call: Call):
    db = call.db
    user, org = _org(call)
    pays = db.query(Payout).filter(Payout.party == "fleet", Payout.party_id == org.id).order_by(Payout.id.desc()).all()
    return {"statements": [summary_json(db, "fleet", org.id, *_week_bounds(i)) for i in range(8)],
            "payouts": [{"uuid": p.uuid, "amount": present.money(p.amount), "status": p.status.upper(),
                         "createdAt": present.ms(p.created_at), "paidAt": present.ms(p.paid_at)} for p in pays]}


# ---- desempenho e avaliacoes -----------------------------------------------------------------
@handles(APP, "POST", "/rt/vehicle-supplier/vs-supplier-management/drivers-performance-analytics",
         "/rt/fleet/get-aggregate-performance-metrics")
def performance(call: Call):
    db = call.db
    user, org = _org(call)
    out = []
    for d in org.drivers:
        done = db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").count()
        canc = db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "cancelled",
                                     Trip.cancelled_by == "driver").count()
        out.append({"driverUUID": d.uuid, "name": d.name, "rating": d.rating, "completedTrips": done,
                    "acceptanceRate": round(d.offers_accepted / d.offers_received, 3) if d.offers_received else 1,
                    "cancellationRate": round(canc / (done + canc), 3) if done + canc else 0})
    return {"drivers": out, "metrics": out}


@handles(APP, "POST", "/rt/fleet/get-drivers-feedback-count")
def feedback_count(call: Call):
    db = call.db
    user, org = _org(call)
    return {"driversFeedbackCount": [{"driverUUID": d.uuid, "count": db.query(Trip).filter(
        Trip.driver_id == d.id, Trip.rider_to_driver_rating > 0).count()} for d in org.drivers]}


@handles(APP, "POST", "/rt/fleet/get-feedback-overview")
def feedback_overview(call: Call):
    db = call.db
    user, org = _org(call)
    rows = (db.query(Trip).filter(Trip.org_id == org.id, Trip.rider_to_driver_rating > 0)
            .order_by(Trip.completed_at.desc()).limit(50).all())
    avg = round(sum(t.rider_to_driver_rating for t in rows) / len(rows), 2) if rows else None
    return {"summary": {"averageRating": avg, "count": len(rows)}, "tagTranslations": {},
            "feedbacks": [{"tripUUID": t.uuid, "driverUUID": t.driver.uuid if t.driver else None,
                           "rating": t.rider_to_driver_rating, "comment": t.rider_comment,
                           "timestamp": present.ms(t.completed_at)} for t in rows]}


@handles(APP, "POST", "/rt/fleet/get-campagin-view", "/rt/fleet/get-partner-campaign-view",
         "/rt/fleet/get-partner-promotion-view", "/rt/vehicle-supplier/vs-incentive/get-supplier-incentive",
         "/rt/vehicle-supplier/vs-incentive/get-incentive-progress",
         "/rt/vehicle-supplier/vs-incentive/get-incentive-vehicle-progress")
def incentives(call: Call):
    return {"campaigns": [], "promotions": [], "incentives": []}

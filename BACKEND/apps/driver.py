# -*- coding: utf-8 -*-
"""App Qolari Driver (base Uber Driver) -> dominio.

Contratos: contracts/driver_paths.txt + driver_models.json. Quase todas as respostas do
marketplacedriver sao `{driverTasks: DriverTasks}` (rtapi.models.driverstasks):

    DriverTasks = {driverState: {online, available, dispatchable, ...},
                   taskScopes: [TaskScope{blockingTasks, nonBlockingTasks, completionTask}],
                   meta: {lastModifiedTimeMs}}

A proposta vai pelo ramen em push_driver_unified_offers_v3 (UnifiedDriverOffers, ver driver_offer); a viagem
aceite e um TaskScope (trip_scope) no DriverTasks, que tambem vai por push_drivers_tasks. Unioes Thrift: o
campo `type` e o nome do campo (ex.: "singleTaskData", "pickupTaskData"); ver tools/enum_names.py.
Validado no telemovel em 12-10: proposta no ecra e accept-offers.
"""
import base64
import binascii
import datetime as dt
import time
import uuid
from pathlib import Path

import config
from apps import common, geocode, present
from apps.rtapi import Call, RtError, handles
from domain import finance, trips
from domain.finance import FinanceError
from domain.models import (AdjustmentRequest, AirportQueue, Document, DriverPreference, LedgerEntry,
                           MapReport, Notification, Offer, Payout, Quest, QuestClaim, Referral,
                           Setting, Trip, Vehicle, jget, jset, now)
from domain.seed import PLACES
from domain.trips import TripError

APP = "driver"

# Motivos canonicos do problema de mapa (a app envia o codigo; a consola mostra o rotulo).
MAP_REPORT_REASONS = {
    "address": "Rua ou morada errada",
    "closed": "Local fechado ou inexistente",
    "outdated": "Mapa desatualizado",
    "other": "Outro problema",
}


def _err(e: TripError) -> RtError:
    return RtError(400, e.code, str(e), {"title": "Qolari Driver", "message": str(e)})


# ---- proposta (push_driver_unified_offers_v3) --------------------------------------------------
# A proposta NAO vem no DriverTasks (UpfrontOfferTaskData so tem offerUuid e ninguem o le). Vem no tópico ramen
# push_driver_unified_offers_v3 = UnifiedDriverOffers (UnifiedDriverOffersPushModel; cg5.h -> cg5.c guarda se
# meta.lastModifiedTimeMs for mais recente) -> offers[].driverOfferData.primaryOffer = DriverOffer, mostrado pelo
# com.qolari.dispatch.DispatchView: offerType JOB|UPFRONT -> CardJobOfferView com offerView.jobOfferViewV3
# (coreInfo obrigatorio); DispatchInteractor tira o tempo de metaData.jobOfferModel.acceptWindow (s).
def _text(text: str, style: str = "LABEL_DEFAULT", weight: str = "NORMAL", color: str = "CONTENT_PRIMARY") -> dict:
    """types.common.ui_component.StyledText."""
    return {"text": text, "font": {"style": style, "weight": weight}, "color": color}


def _label(text: str, **kw) -> dict:
    """offerviewv3.ElementV3 do tipo label (TextLabelV3: text e lineCount obrigatorios)."""
    return {"type": "label", "label": {"text": _text(text, **kw), "lineCount": "WRAP"}}


def _km(m) -> str:
    return f"{(m or 0) / 1000:.1f} km".replace(".", ",")


def _min(s) -> str:
    return f"{max(1, round((s or 0) / 60))} min"


def driver_offer(o: Offer) -> dict:
    """rtapi.models.offer.DriverOffer (offerType JOB + jobOfferModel + jobOfferViewV3)."""
    t = o.trip
    secs = max(1, o.expires_at - now())
    locations = {"pickup": {"latitude": t.pickup_lat, "longitude": t.pickup_lng, "title": t.pickup_address or "",
                            "reference": "pickup"}}
    if t.dropoff_lat is not None:
        locations["dropoff"] = {"latitude": t.dropoff_lat, "longitude": t.dropoff_lng,
                                "title": t.dropoff_address or "", "reference": "dropoff"}
    eta = {"valueInSeconds": o.pickup_eta_s, "valueInMinutes": max(1, round(o.pickup_eta_s / 60)),
           "shortString": _min(o.pickup_eta_s), "longString": f"{_min(o.pickup_eta_s)} ({_km(o.pickup_distance_m)})"}
    job_model = {"acceptWindow": float(secs), "expiresAtEpochMS": float(o.expires_at * 1000),
                 "startLocationRef": "pickup", "endLocationRef": "dropoff" if "dropoff" in locations else None,
                 "locationMap": locations, "etaToStartLocation": eta, "marketplace": "PERSONAL_TRANSPORT",
                 "notificationTitle": f"{t.product.name} · {present.money(t.est_fare, t.city.currency)}",
                 "expiryAction": "EXPIRE"}
    rows = [_label(t.product.name, style="LABEL_SMALL", color="CONTENT_SECONDARY"),
            _label(present.money(t.est_fare, t.city.currency), style="HEADING_LARGE", weight="BOLD"),
            _label(f"{t.rider.first_name} · ★ {(t.rider.rating or 5):.2f}".replace(".", ","), style="LABEL_SMALL",
                   color="CONTENT_SECONDARY"),
            _label(f"{_min(o.pickup_eta_s)} ({_km(o.pickup_distance_m)}) de distância", weight="BOLD"),
            _label(t.pickup_address or "Local de recolha", style="PARAGRAPH_SMALL", color="CONTENT_SECONDARY")]
    if t.dropoff_lat is not None:
        rows += [_label(f"Viagem de {_min(t.est_duration_s)} ({_km(t.est_distance_m)})", weight="BOLD"),
                 _label(t.dropoff_address or "Destino", style="PARAGRAPH_SMALL", color="CONTENT_SECONDARY")]
    view = {"coreInfo": {"type": "simpleView", "simpleView": {"clusters": [
                {"clusterAlignment": "LEADING", "elements": rows}]}},
            "offerAcceptElement": {"type": "acceptButton", "acceptButton": {
                "content": {"type": "textContent", "textContent": {"textContent": {"richTextElements": [
                    {"type": "text", "text": {"text": _text("Aceitar", weight="BOLD")}}]}}},
                "style": {"type": "definedStyle", "definedStyle": "PRIMARY"}, "buttonSize": "LARGE"}}}
    return {"offerUUID": o.uuid, "offerUUIDV2": o.uuid, "jobUUID": t.uuid, "offerType": "JOB",
            "offerStatus": "OPEN" if o.state == "pending" else "INVALID", "sourceType": "PUSH",
            "supportedActions": ["ACCEPT", "REJECT", "EXPIRE"],
            "metaData": {"type": "jobOfferModel", "jobOfferModel": job_model},
            "offerView": {"type": "jobOfferViewV3", "jobOfferViewV3": view}}


def unified_offers(offers: list[Offer]) -> dict:
    """edge.services.offers.UnifiedDriverOffers (so as pendentes; lista vazia = sem proposta no ecra)."""
    live = [o for o in offers if o.state == "pending" and o.expires_at > now()]
    return {"meta": {"lastModifiedTimeMs": float(time.time() * 1000)},
            "offers": [{"offerUUIDs": [o.uuid], "driverOfferData": {"type": "primaryOffer",
                                                                    "primaryOffer": driver_offer(o)}}
                       for o in live]}


def _push_offer(db, payload: dict) -> list:
    o = db.query(Offer).filter_by(uuid=payload.get("offerUUID")).first()
    return [("push_driver_unified_offers_v3", unified_offers([o] if o else []))]


common.TRANSLATORS[(APP, "offer")] = _push_offer


# ---- DriverTasks (viagem aceite) ----------------------------------------------------------------
# rtapi.models.driverstasks (Builders com "X is null!"): todas as unioes levam `type` = nome do campo.
# TaskScope da viagem: completionTask (recolha ate iniciar, entrega em viagem) + nonBlockingTasks; o mapa/morada
# sai do 1.o locationTaskData nao-bloqueante (h88.b), o waypoint do taskDataMap (dw5.b.t). TaskSource nao tem
# TRIP: a viagem e DEMAND_JOB, com o uuid da viagem como TaskSourceUuid.
def _source_key(job_uuid: str) -> dict:
    return {"type": "taskSourceKey", "taskSourceKey": {"taskSource": "DEMAND_JOB", "taskSourceUuid": job_uuid}}


def _task(task_id: str, kind: str, data: dict, job_uuid: str, completed: bool = False) -> dict:
    """DriverTask com singleTaskData (SingleTaskDataUnion `kind`)."""
    return {"taskId": task_id, "isCompleted": completed, "driverTaskDataUnion": {
        "type": "singleTaskData", "singleTaskData": {"taskDataUnion": {"type": kind, kind: data},
                                                     "taskSourceKeyOption": _source_key(job_uuid)}}}


def _product(t: Trip) -> dict:
    """ProductData (GlobalProductType nao tem as nossas categorias: XL -> UBER_XL, resto UBER_X)."""
    return {"globalProductType": "UBER_XL" if "XL" in t.product.name.upper() else "UBER_X", "name": t.product.name}


def trip_scope(t: Trip, pin_ok: bool = False) -> dict:
    cur = t.city.currency
    r = t.rider
    entity = {"firstName": r.first_name, "lastName": (r.last_name or "")[:1], "rating": float(r.rating or 5)}
    stops = jget(t.stops, [])
    next_stop = next((i for i, s in enumerate(stops) if not s.get("done")), None)
    if t.state in ("accepted", "arrived"):
        kind, coalesced, wp = "pickupTaskData", "pickupCoalescedTaskData", "pickup"
        lat, lng, address = t.pickup_lat, t.pickup_lng, t.pickup_address
        title = f"Recolher {r.first_name}"
    elif next_stop is not None:
        s = stops[next_stop]
        kind, coalesced, wp = "dropoffTaskData", "dropoffCoalescedTaskData", f"stop{next_stop}"
        lat, lng, address = s.get("lat"), s.get("lng"), s.get("address", "")
        title = f"Paragem {next_stop + 1} de {len(stops)}"
    else:
        kind, coalesced, wp = "dropoffTaskData", "dropoffCoalescedTaskData", "dropoff"
        lat, lng, address = t.dropoff_lat, t.dropoff_lng, t.dropoff_address
        title = f"Deixar {r.first_name}"
    data = {"entity": entity, "waypoint": {"uuid": f"{t.uuid}-{wp}"},
            "driverUpfrontFare": {"amount": present.money(t.est_fare, cur)},
            "stops": stops, "nextStopIndex": next_stop}
    blocking, non_blocking = [], []
    if t.state == "arrived" and t.pin:
        # So depois de chegar (com a tarefa ja em "accepted" o painel ficava em "A carregar..." sem cartao, 12-10).
        # PinVerificationTaskData (pin, maxAttemptCount, featureIdString, failureAction, viewData obrigatorios): a app
        # pede o PIN ao deslizar "Recolher", compara-o localmente e chama confirm-pin-is-verified.
        blocking.append(_task(f"{t.uuid}-pin", "pinVerificationTaskData", {
            "pin": t.pin, "maxAttemptCount": 3, "featureIdString": "pickup_pin_verification",
            "globalProductType": _product(t)["globalProductType"],
            "failureAction": {"type": "pinEntryFailureActionCancelTrip", "pinEntryFailureActionCancelTrip": {}},
            "viewData": [
                {"type": "pinEntryViewTextRow", "pinEntryViewTextRow": {
                    "text": f"Peça o PIN a {r.first_name}", "size": "H2", "position": "LEADING", "style": "PRIMARY"}},
                {"type": "pinEntryViewTextRow", "pinEntryViewTextRow": {
                    "text": "O passageiro vê o PIN na app Qolari.", "size": "P", "position": "LEADING",
                    "style": "SECONDARY"}},
                {"type": "pinEntryViewPinRow", "pinEntryViewPinRow": {"pinDigitCount": len(t.pin),
                                                                      "position": "CENTER"}},
                {"type": "pinEntryViewErrorTextRow", "pinEntryViewErrorTextRow": {"errorForAttempt": [
                    "PIN errado. Tente outra vez.", "PIN errado. Última tentativa.", "PIN errado."]}}]},
            t.uuid, completed=pin_ok))
    if t.state == "arrived" and t.arrived_at:
        # temporizador de espera na recolha (WaitTimeTaskData.startTimeSec obrigatorio)
        non_blocking.append(_task(f"{t.uuid}-wait", "waitTimeTaskData", {"startTimeSec": float(t.arrived_at)},
                                  t.uuid))
    if lat is not None:
        non_blocking.append(_task(f"{t.uuid}-{wp}-location", "locationTaskData", {
            "latitude": lat, "longitude": lng, "title": address or title, "subtitle": address or ""}, t.uuid))
    completion = {"taskId": f"{t.uuid}-{wp}", "isCompleted": False, "source": "DEMAND_JOB", "taskDataType": kind,
                  "jobOrdering": [t.uuid],
                  "coalescedDataUnion": {"type": coalesced, coalesced: {
                      "product": _product(t), "info": {"title": title, "subtitle": address or ""}}},
                  "taskDataMap": {t.uuid: {"type": kind, kind: data}}}
    return {"blockingTasks": blocking, "nonBlockingTasks": non_blocking, "completionTask": completion,
            "taskScopeMetadata": {"presentationFramework": "DRIVER_TASKS"}}


def driver_tasks(db, d) -> dict:
    """{driverTasks: DriverTasks}: resposta de app-launch/go-online/available/accept/begin/end... e push_drivers_tasks.
    A proposta nao vai aqui (vai em push_driver_unified_offers_v3)."""
    online = d.availability != "offline"
    trip = trips.active_trip_for_driver(db, d)
    # available = a aceitar pedidos (nao "em pausa"): com false durante a viagem a app mostra "Os pedidos foram
    # interrompidos" e manda go-offline ao terminar (visto a 12-10). Sem pausa no dominio: = online.
    return {"driverTasks": {
        "driverState": {"online": online, "available": online,
                        "dispatchable": online and d.status == "approved",
                        "awaitingRequesterConfirmation": False,
                        "preferencesState": {"isEnabled": False, "isSet": False}},
        "taskScopes": [trip_scope(trip, trips.pin_verified(db, trip))] if trip else [],
        "meta": {"lastModifiedTimeMs": float(time.time() * 1000)}}}


def _push_trip_status(db, payload: dict) -> list:
    """trip_status do dominio -> DriverTasks atualizado + lista de propostas (limpa o cartao depois de aceitar)."""
    t = db.query(Trip).filter_by(uuid=payload.get("tripUUID")).first()
    if not t or not t.driver:
        return []
    d = t.driver
    pending = trips.pending_offer_for(db, d)
    tasks = driver_tasks(db, d)["driverTasks"]
    # EarnerTripCoreDomain (gf5.k.g -> jf5.c.c): as mesmas taskScopes, versao em commitTsInNanos
    core = {"commitTsInNanos": time.time_ns(), "taskScopes": tasks["taskScopes"]}
    return [("push_drivers_tasks", tasks), ("push_earner_trip_core_domain", core),
            ("push_driver_unified_offers_v3", unified_offers([pending] if pending else []))]


common.TRANSLATORS[(APP, "trip_status")] = _push_trip_status


def onboarding_status(d) -> str:
    return {"approved": "active", "pending": "pending", "suspended": "inactive",
            "rejected": "rejected"}.get(d.status, d.status)


def apply_locations(call: Call, d):
    """Lote de posicoes (UploadDriverDeviceLocations / positionEvent) -> ultima posicao."""
    b = call.body
    if isinstance(b.get("uploadLocationRequest"), dict):  # /rt/unifiedlocation/uploadpositions
        b = b["uploadLocationRequest"]
    candidates = []
    for key in ("locations", "deviceLocations", "positionEvents", "driverLocations", "positions"):
        if isinstance(b.get(key), list):
            candidates = b[key]
    if not candidates and isinstance(b.get("positionEvent"), dict):
        candidates = [b["positionEvent"]]
    if not candidates and isinstance(b.get("events"), list):  # /rt/surge/supplyInput
        candidates = [e["deviceLocationEvent"] for e in b["events"]
                      if isinstance(e, dict) and isinstance(e.get("deviceLocationEvent"), dict)]
    for item in reversed(candidates):
        loc = item.get("location") if isinstance(item.get("location"), dict) else item
        for k in ("coordinate", "position", "gpsLocation", "point"):
            if isinstance(loc.get(k), dict):
                loc = loc[k]
        lat, lng = loc.get("latitude", loc.get("lat")), loc.get("longitude", loc.get("lng"))
        if lat is not None and lng is not None:
            trips.set_location(call.db, d, float(lat), float(lng),
                               loc.get("course", loc.get("bearing")), simulated=False)
            return True
    return False


@handles(APP, "POST", "/rt/unifiedlocation/uploadpositions", "/rt/surge/supplyInput")
def upload_positions(call: Call):
    """GPS da app a cada 4 s (uploadLocationRequest.positions[].point, entityType SUPPLY) e
    supplyInput (events[].deviceLocationEvent.location, a cada minuto): o motorista deixa de ser simulado.
    As respostas nao sao lidas (12-10, sem efeito no ecra com {})."""
    apply_locations(call, call.subject())
    return {}


# ---- arranque e estado -----------------------------------------------------------------------
@handles(APP, "POST", "/rt/drivers/app-launch")
def app_launch(call: Call):
    d = call.subject()
    return {**driver_tasks(call.db, d), "driverOnboardingStatus": onboarding_status(d), "isAdmin": False,
            "isUberStreetHailEligible": False}


@handles(APP, "POST", "/rt/drivers/v2/available", "/rt/drivers/ack-offers", "/rt/drivers/finalize-offers",
         "/rt/drivers/v2/capabilities", "/rt/drivers/update-driver-feed")
def tasks(call: Call):
    d = call.subject()
    apply_locations(call, d)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/drivers/v2/go-online", "/rt/drivers/{driverUUID}/go-online")
def go_online(call: Call):
    d = call.subject()
    apply_locations(call, d)
    vid = call.get("vehicleId", "vehicleUUID")
    if vid:
        v = call.db.query(Vehicle).filter_by(uuid=str(vid)).first()
        if v and v.status == "active":
            trips.assign_vehicle(call.db, d, v)
    try:
        trips.go_online(call.db, d)
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/drivers/v2/go-offline")
def go_offline(call: Call):
    d = call.subject()
    if d.availability == "on_trip":  # "parar novos pedidos" a meio da viagem: um 400 aqui deixava o painel vazio
        return driver_tasks(call.db, d)
    try:
        trips.go_offline(call.db, d)
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/drivers/v2/fetch-online-blockers")
def online_blockers(call: Call):
    """O que impede de ficar online (DriverCheckIssue)."""
    db = call.db
    d = call.subject()
    issues = []
    if d.status != "approved":
        issues.append({"title": "Conta em verificação", "message": "A tua conta ainda não foi aprovada."})
    if not d.vehicle or d.vehicle.status != "active":
        issues.append({"title": "Sem veículo", "message": "Não tens um veículo ativo atribuído."})
    for doc in db.query(Document).filter(Document.owner_type == "driver", Document.owner_id == d.id,
                                         Document.status != "approved").all():
        issues.append({"title": "Documento pendente", "message": doc.kind.replace("_", " ")})
    return {"issues": [{"issueData": {"displayContent": i}} for i in issues], "futureBlockers": [],
            "driverCheckNudges": []}


@handles(APP, "GET|POST", "/rt/drivers/v2/vehicles")
def vehicles(call: Call):
    d = call.subject()
    q = call.db.query(Vehicle).filter(Vehicle.status == "active")
    q = q.filter(Vehicle.org_id == d.org_id) if d.org_id else q.filter(Vehicle.owner_driver_id == d.id)
    out = []
    for v in q.all():
        out.append({**present.vehicle(v), "isDefault": d.vehicle_id == v.id, "allowsCustomLicensePlate": False,
                    "tags": [], "traits": []})
    return {"vehicles": out}


# ---- propostas -------------------------------------------------------------------------------
def _offer(call: Call, d) -> Offer:
    uuids = call.get("offerUUIDs", "offerUuids", "offers", default=None)
    uuid = None
    if isinstance(uuids, list) and uuids:
        first = uuids[0]
        uuid = first.get("offerUUID") or first.get("uuid") if isinstance(first, dict) else first
    uuid = uuid or call.get("offerUUID", "offerUuid", "uuid")
    o = call.db.query(Offer).filter_by(uuid=str(uuid), driver_id=d.id).first() if uuid else None
    o = o or trips.pending_offer_for(call.db, d)
    if not o:
        raise RtError(404, "offer_not_found", "sem proposta pendente")
    return o


@handles(APP, "POST", "/rt/drivers/accept-offers", "/rt/drivers/v2/pin-accept")
def accept(call: Call):
    d = call.subject()
    try:
        trips.accept_offer(call.db, _offer(call, d))
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/drivers/reject-offers", "/rt/drivers/expire-offers")
def reject(call: Call):
    """Recusa/expiracao. Idempotente: a app manda expire-offers quando o tempo acaba no ecra, muitas vezes
    depois de o relogio do servidor ja a ter expirado (antes dava 400)."""
    d = call.subject()
    try:
        o = _offer(call, d)
        if o.state == "pending":
            trips.reject_offer(call.db, o, expired=call.path.endswith("expire-offers"))
    except RtError:
        pass
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/drivers/get-upfront-offer")
def get_offer(call: Call):
    """GetUpfrontOfferResponse.offerDetails = DriverOffer."""
    o = trips.pending_offer_for(call.db, call.subject())
    return {"offerDetails": driver_offer(o)} if o else {}


@handles(APP, "GET|POST", "/rt/drivers/unified-offers-v3", "/rt/drivers/v2/unified-offer")
def unified_offers_poll(call: Call):
    """GetUnifiedOffersResponseV3 {data: UnifiedDriverOffers, etag, pollingInterval} (cg5.l, sondagem POLL)."""
    o = trips.pending_offer_for(call.db, call.subject())
    return {"data": unified_offers([o] if o else []), "etag": o.uuid if o else "none", "pollingInterval": 4000}


# ---- viagem ----------------------------------------------------------------------------------
def _trip(call: Call, d) -> Trip:
    uuid = call.vars.get("tripUUID") or call.get("tripUUID", "uuid", "jobUUID")
    if not uuid:
        for key in ("beginTripParams", "endTripParams", "cancelTripParams", "params", "trips"):
            v = call.body.get(key)
            v = v[0] if isinstance(v, list) and v else v
            if isinstance(v, dict) and v.get("uuid"):
                uuid = v["uuid"]
                break
    t = call.db.query(Trip).filter_by(uuid=str(uuid), driver_id=d.id).first() if uuid else None
    t = t or trips.active_trip_for_driver(call.db, d)
    if not t:
        raise RtError(404, "trip_not_found", "sem viagem ativa")
    return t


@handles(APP, "POST", "/rt/trips/v2/start-waiting", "/rt/drivers/send-wait-timer-alert")
def arrived(call: Call):
    d = call.subject()
    t = _trip(call, d)
    if t.state == "accepted":
        trips.arrive(call.db, t)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/trips/v2/confirm-pin-is-verified", "/rt/trips/v2/confirm-pin-is-verified-v2")
def pin_ok(call: Call):
    """Resposta vazia (c0 no MarketplaceDriverApi). Fica registado: a tarefa de PIN passa a isCompleted."""
    d = call.subject()
    try:
        trips.verify_pin(call.db, _trip(call, d))
    except TripError as e:
        raise _err(e)
    return {}


@handles(APP, "POST", "/rt/trips/v2/begin", "/rt/trips/{tripUUID}/begin")
def begin(call: Call):
    d = call.subject()
    t = _trip(call, d)
    pin = call.get("pin", "pinCode")
    try:
        trips.start(call.db, t, str(pin) if pin else None)
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/trips/v2/complete-stop")
def complete_stop(call: Call):
    d = call.subject()
    t = _trip(call, d)
    try:
        trips.complete_stop(call.db, t)
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/trips/v2/end", "/rt/drivers/end-trip", "/rt/trips/v2/complete-stops")
def end(call: Call):
    d = call.subject()
    t = _trip(call, d)
    if t.state in ("accepted", "arrived"):
        trips.start(call.db, t)
    pos = (d.lat, d.lng) if d.lat is not None and not d.simulated else None
    try:
        trips.complete(call.db, t, dropoff=pos if t.dropoff_lat is None else None)
    except TripError as e:
        raise _err(e)
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/trips/v2/driver-cancel")
def driver_cancel(call: Call):
    d = call.subject()
    t = _trip(call, d)
    try:
        trips.cancel(call.db, t, "driver", str(call.get("note", "reason", default="") or ""))
    except TripError as e:
        raise _err(e)
    # devolver a viagem ao despacho seria o comportamento Uber; aqui o passageiro volta a pedir
    return driver_tasks(call.db, d)


@handles(APP, "POST", "/rt/trips/v2/driver-rate")
def driver_rate(call: Call):
    d = call.subject()
    b = call.body
    rating = b.get("rating") or (b.get("params") or {}).get("rating")
    uuid = b.get("uuid") or b.get("tripUUID")
    t = call.db.query(Trip).filter_by(uuid=str(uuid), driver_id=d.id).first() if uuid else \
        call.db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").order_by(Trip.id.desc()).first()
    if t and rating:
        try:
            trips.rate(call.db, t, "driver", int(rating))
        except (TripError, ValueError):
            pass
    return {}


# ---- ganhos ----------------------------------------------------------------------------------
def _day_start(ts: int) -> int:
    import time as _t
    lt = _t.localtime(ts)
    return int(_t.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, 0, 0, 0, 0, 0, -1)))


def week_bounds(ts: int) -> tuple[int, int]:
    """Segunda 00:00 e a segunda seguinte 00:00 (hora local), por data de calendario: nao soma 7x86400 s, que
    erra na semana da mudanca de hora."""
    import datetime as _dt
    import time as _t
    day = _dt.date.fromtimestamp(ts)
    monday = day - _dt.timedelta(days=day.weekday())
    nxt = monday + _dt.timedelta(days=7)
    mk = lambda x: int(_t.mktime((x.year, x.month, x.day, 0, 0, 0, 0, 0, -1)))
    return mk(monday), mk(nxt)


def earnings_period(db, d, start: int, end: int) -> dict:
    s = finance.summary(db, "driver", d.id, start, end)["by_kind"]
    rows = (db.query(Trip).filter(Trip.driver_id == d.id, Trip.completed_at >= start, Trip.completed_at < end)
            .order_by(Trip.completed_at.desc()).all())
    net = (s.get("fare", 0) + s.get("cancel_fee", 0) + s.get("commission", 0)
           + s.get("fleet_fee", 0) + s.get("tip", 0))
    return {"startAt": present.ms(start), "endAt": present.ms(end), "currencyCode": "EUR",
            "total": present.amount(net), "formattedTotal": present.money(net),
            "tripEarning": present.amount(s.get("fare", 0)), "formattedTripEarning": present.money(s.get("fare", 0)),
            "tips": present.amount(s.get("tip", 0)), "formattedTips": present.money(s.get("tip", 0)),
            "formattedCommission": present.money(s.get("commission", 0)),
            "formattedFleetFee": present.money(s.get("fleet_fee", 0)),
            "cashCollected": present.amount(-s.get("cash_collected", 0)),
            "formattedCashCollected": present.money(-s.get("cash_collected", 0)),
            "tripCount": len(rows),
            "onlineSeconds": trips.online_seconds(db, d.id, start, end),
            "trips": [{"uuid": t.uuid, "requestAt": present.ms(t.requested_at),
                       "processedAt": present.ms(t.completed_at), "pickupAddress": t.pickup_address,
                       "dropoffAddress": t.dropoff_address, "formattedTotal": present.money(t.fare),
                       "formattedDistance": f"{(t.distance_m or 0) / 1000:.1f} km",
                       "duration": float(t.duration_s or 0), "vehicleType": t.product.name}
                      for t in rows[:100]]}


@handles(APP, "POST", "/rt/earnings/get-daily-earnings-view")
def daily(call: Call):
    d = call.subject()
    start = _day_start(now())
    return earnings_period(call.db, d, start, start + 86400)


@handles(APP, "POST", "/rt/earnings/get-weekly-earnings-view", "/rt/earnings/get-performance-hub-view")
def weekly(call: Call):
    d = call.subject()
    start, end = week_bounds(now())
    return earnings_period(call.db, d, start, end)


@handles(APP, "POST", "/rt/earnings/get-balance-summary")
def balance(call: Call):
    d = call.subject()
    bal = finance.balance(call.db, "driver", d.id)
    return {"balance": present.money(bal), "balanceAmount": present.amount(bal), "currencyCode": "EUR",
            "cashOutEnabled": False}


def _payout_json(p: Payout) -> dict:
    return {"uuid": p.uuid, "amount": present.money(p.amount), "amountCents": p.amount,
            "status": p.status, "reference": p.reference, "createdAt": present.ms(p.created_at),
            "paidAt": present.ms(p.paid_at) if p.paid_at else None}


@handles(APP, "POST", "/rt/earnings/get-payout-methods")
def payout_methods(call: Call):
    d = call.subject()
    bal = finance.balance(call.db, "driver", d.id)
    return {"balance": present.money(bal), "balanceAmount": present.amount(bal), "currencyCode": "EUR",
            "methods": [
                {"id": "iban", "label": "Transferência bancária", "detail": "1 a 2 dias úteis", "instant": False},
                {"id": "instant", "label": "Instant Pay", "detail": "Imediato, taxa 0,00 €", "instant": True},
            ]}


@handles(APP, "POST", "/rt/earnings/request-payout", "/rt/earnings/instant-pay")
def request_payout(call: Call):
    db, d = call.db, call.subject()
    amount = call.get("amountCents", "amount")
    try:
        payout = finance.create_payout(db, "driver", d.id, int(amount) if amount is not None else None)
        if call.path.endswith("instant-pay") or str(call.get("method", default="")) == "instant":
            finance.mark_paid(db, payout, "instant-pay")
        db.flush()
    except (FinanceError, ValueError) as e:
        raise RtError(400, "payout_failed", str(e))
    bal = finance.balance(db, "driver", d.id)
    return {"payout": _payout_json(payout), "balance": present.money(bal),
            "balanceAmount": present.amount(bal)}


@handles(APP, "POST", "/rt/earnings/get-payout-history")
def payout_history(call: Call):
    db, d = call.db, call.subject()
    rows = (db.query(Payout).filter_by(party="driver", party_id=d.id)
            .order_by(Payout.id.desc()).limit(24).all())
    return {"payouts": [_payout_json(p) for p in rows]}


def _month_bounds(year: int, month: int) -> tuple[int, int]:
    start = dt.datetime(year, month, 1).timestamp()
    end = dt.datetime(year + (month == 12), 1 if month == 12 else month + 1, 1).timestamp()
    return int(start), int(end)


@handles(APP, "POST", "/rt/earnings/get-statements")
def statements(call: Call):
    """Extrato dos ultimos 6 meses (bruto, comissao, frota e liquido)."""
    db, d = call.db, call.subject()
    today = dt.date.today()
    year, month = today.year, today.month
    out = []
    for _ in range(6):
        start, end = _month_bounds(year, month)
        s = finance.summary(db, "driver", d.id, start, end)["by_kind"]
        gross = s.get("fare", 0) + s.get("cancel_fee", 0)
        net = gross + s.get("commission", 0) + s.get("fleet_fee", 0)
        count = db.query(Trip).filter(Trip.driver_id == d.id, Trip.completed_at >= start,
                                      Trip.completed_at < end).count()
        out.append({"month": f"{year:04d}-{month:02d}", "gross": present.money(gross),
                    "grossCents": gross, "commission": present.money(-s.get("commission", 0)),
                    "fleetFee": present.money(-s.get("fleet_fee", 0)), "net": present.money(net),
                    "netCents": net, "trips": count})
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return {"statements": out, "currencyCode": "EUR"}


@handles(APP, "POST", "/rt/earnings/get-activity-feed-v3")
def activity(call: Call):
    db = call.db
    d = call.subject()
    rows = (db.query(LedgerEntry).filter(LedgerEntry.party == "driver", LedgerEntry.party_id == d.id)
            .order_by(LedgerEntry.id.desc()).limit(100).all())
    return {"items": [{"uuid": str(e.id), "kind": e.kind, "amount": present.money(e.amount),
                       "timestamp": present.ms(e.at), "description": e.note,
                       "tripUUID": e.trip_id and db.get(Trip, e.trip_id).uuid} for e in rows]}


_NOTE_FIXES = (("comissao", "Comissão"), ("tarifa", "Tarifa"), ("frota", "Frota"), ("recebido em dinheiro", "Recebido em dinheiro"),
               ("desconto promocional", "Desconto promocional"))


def _pretty_note(note: str) -> str:
    """Lancamentos antigos foram gravados sem acentos nem maiuscula; os novos ja vem certos."""
    for old, new in _NOTE_FIXES:
        if note.startswith(old):
            return new + note[len(old):]
    return note[:1].upper() + note[1:]


@handles(APP, "POST", "/rt/earnings/get-trip", "/rt/earnings/v3/trip/{tripUUID}")
def earnings_trip(call: Call):
    db = call.db
    d = call.subject()
    uuid = call.vars.get("tripUUID") or call.get("tripUUID", "uuid")
    t = db.query(Trip).filter_by(uuid=str(uuid), driver_id=d.id).first()
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente")
    entries = db.query(LedgerEntry).filter(LedgerEntry.trip_id == t.id, LedgerEntry.party == "driver").all()
    return {"trip": {"uuid": t.uuid, "pickupAddress": t.pickup_address, "dropoffAddress": t.dropoff_address,
                     "formattedTotal": present.money(sum(e.amount for e in entries if e.kind != "cash_collected")),
                     "breakdown": [{"description": _pretty_note(e.note or e.kind), "formattedAmount": present.money(e.amount)}
                                   for e in entries],
                     "fareBreakdown": jget(t.fare_breakdown, {})}}


ADJ_KINDS = {"tolls", "manual_fare", "other"}


def _adj_json(a: AdjustmentRequest) -> dict:
    return {"uuid": a.uuid, "tripUuid": a.trip_uuid, "kind": a.kind,
            "amount": present.money(a.amount_cents), "amountCents": a.amount_cents,
            "note": a.note, "status": a.status, "createdAt": present.ms(a.created_at),
            "reviewedAt": present.ms(a.reviewed_at) if a.reviewed_at else None}


@handles(APP, "POST", "/rt/earnings/request-adjustment")
def request_adjustment(call: Call):
    db, d = call.db, call.subject()
    kind = str(call.body.get("kind") or "other").strip()
    if kind not in ADJ_KINDS:
        raise RtError(400, "invalid_kind", "tipo de ajuste invalido")
    amount = int(call.body.get("amountCents") or 0)
    if amount <= 0 or amount > 50000:
        raise RtError(400, "invalid_amount", "valor entre 0.01 e 500 EUR")
    trip_uuid = str(call.body.get("tripUuid") or "")[:36]
    if trip_uuid:
        t = db.query(Trip).filter_by(uuid=trip_uuid, driver_id=d.id).first()
        if not t:
            raise RtError(404, "trip_not_found", "viagem inexistente")
    a = AdjustmentRequest(driver_id=d.id, trip_uuid=trip_uuid, kind=kind, amount_cents=amount,
                          note=str(call.body.get("note") or "")[:300])
    db.add(a)
    db.flush()
    return {"adjustment": _adj_json(a)}


@handles(APP, "GET", "/rt/earnings/adjustments")
def adjustments(call: Call):
    rows = (call.db.query(AdjustmentRequest)
            .filter_by(driver_id=call.subject().id)
            .order_by(AdjustmentRequest.id.desc()).limit(30).all())
    return {"adjustments": [_adj_json(a) for a in rows]}


@handles(APP, "POST", "/rt/earnings/get-invoices")
def invoices(call: Call):
    """Faturas mensais (12 meses) com total e IVA estimado."""
    db, d = call.db, call.subject()
    today = dt.date.today()
    year, month = today.year, today.month
    out = []
    for _ in range(12):
        start, end = _month_bounds(year, month)
        s = finance.summary(db, "driver", d.id, start, end)["by_kind"]
        gross = s.get("fare", 0) + s.get("cancel_fee", 0) + s.get("tip", 0)
        net = gross + s.get("commission", 0) + s.get("fleet_fee", 0)
        out.append({"month": f"{year:04d}-{month:02d}", "total": present.money(gross),
                    "totalCents": gross, "net": present.money(net),
                    "tax": present.money(int(round(gross * 0.23 / 1.23))),
                    "status": "paid"})
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    return {"invoices": out, "currencyCode": "EUR"}


@handles(APP, "POST", "/rt/earnings/get-tax-info")
def tax_info(call: Call):
    db, d = call.db, call.subject()
    start = int(dt.datetime(dt.date.today().year, 1, 1).timestamp())
    end = int(dt.datetime(dt.date.today().year + 1, 1, 1).timestamp())
    s = finance.summary(db, "driver", d.id, start, end)["by_kind"]
    gross = s.get("fare", 0) + s.get("cancel_fee", 0) + s.get("tip", 0)
    net = gross + s.get("commission", 0) + s.get("fleet_fee", 0)
    return {"year": dt.date.today().year, "gross": present.money(gross),
            "grossCents": gross, "net": present.money(net), "netCents": net,
            "tax": present.money(int(round(gross * 0.23 / 1.23))),
            "note": "IVA estimado a 23%; valores do laboratorio."}


# ---- perfil ----------------------------------------------------------------------------------
@handles(APP, "POST", "/rt/earner-profile/get-profile-hub", "/rt/earner-profile/get-profile-detail-screen")
def profile_hub(call: Call):
    db = call.db
    d = call.subject()
    trips_done = db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").count()
    acc = round(100 * d.offers_accepted / d.offers_received) if d.offers_received else 100
    return {"profile": {"uuid": d.uuid, "firstName": d.first_name, "lastName": d.last_name,
                        "rating": d.rating, "tripCount": trips_done, "acceptanceRate": acc,
                        "memberSince": present.ms(d.created_at),
                        "vehicle": present.vehicle(d.vehicle),
                        "fleet": d.organization.name if d.organization else None}}


@handles(APP, "POST", "/rt/drivers/get-driver-feed-push", "/rt/drivers/get-opportunities",
         "/rt/earner/heatmapV2", "/rt/earner/zonesmap", "/rt/drivers/driving-hour-limits-clock-v2")
def empty_lists(call: Call):
    return {"items": [], "cards": [], "opportunities": []}


@handles(APP, "POST", "/rt/earner/preferences", "/rt/earner/preferences/views")
def earner_preferences_placeholder(call: Call):
    return {"preferences": []}


# ---- P6 - lacunas vistas no trafego real do servidor (logs de 11 a 17/10) ---------------------------
# Ordem = numero de chamadas (spec: ANDOIRD/DRIVER/endpoints.json -> lacunas_backend). Cada resposta e o MINIMO
# valido do contrato: campos obrigatorios (*) de tools/model_tree.py driver <classe> presentes e listas vazias;
# enums com o nome Java quando a classe nao tem @SerializedName (MentorshipRole, PreferencesEffect,
# DriverOnboardingStatus). Contratos minimos: a app deixa de os tratar como "por mapear", mas falta validar o
# conteudo no telemovel (o painel Glide e as preferencias nao tem celulas/itens).
@handles(APP, "POST", "/rt/offer-experience/upload-earner-experience-state")   # 441 chamadas; resposta rq8.c0 (opaca)
def upload_earner_experience_state(call: Call):
    return {}


@handles(APP, "POST", "/rt/glide/get-earner-dashboard-sections-content")        # 20; requestID e sectionsContent *
def earner_dashboard_sections(call: Call):
    return {"requestID": str(uuid.uuid4()), "sectionsContent": {}}


@handles(APP, "POST", "/rt/drivers/get-checklist-sdui")                          # 19; tudo opcional: sem checklist
def checklist_sdui(call: Call):
    return {}


@handles(APP, "POST", "/rt/vehicle/presentation/driver/vehiclesblocker/set-default-vehicle")   # 18
def set_default_vehicle(call: Call):
    d = call.subject()
    vid = call.get("vehicleUUID", "vehicleUuid", "vehicle_uuid", "uuid")
    if not vid:
        return {}
    q = call.db.query(Vehicle).filter(Vehicle.status == "active", Vehicle.uuid == vid)
    q = q.filter(Vehicle.org_id == d.org_id) if d.org_id else q.filter(Vehicle.owner_driver_id == d.id)
    v = q.first()
    if v is None:
        raise RtError(404, "not_found", "veiculo nao encontrado", {"title": "Qolari Driver", "message": "Veiculo nao encontrado"})
    d.vehicle_id = v.id
    return {}


@handles(APP, "POST", "/rt/transparent-fare-breakdown/get-transparent-fare-breakdown")   # 15; type * = nome do campo
def transparent_fare_breakdown(call: Call):
    return {"transparentFareBreakdown": {"type": "notApplicable", "notApplicable": {}}}


@handles(APP, "GET|POST", "/rt/navigation/v3/route")                             # 10; sem rota (a app trata a ausencia)
def navigation_route(call: Call):
    """Rota entre dois pontos (polilinha, distancia e duracao). Sem coordenadas devolve {} como antes."""
    from apps import routing
    b = call.body or {}
    pts = routing.points_from(b, call.query if hasattr(call, "query") else {})
    if not pts:
        return {}
    return routing.route(*pts)


@handles(APP, "POST", "/rt/v1/driverretention/mentorship/getmentorshipstate")    # 10; role *
def mentorship_state(call: Call):
    return {"role": "NONE", "shouldStopFetchingState": True}


@handles(APP, "GET", "/rt/drivers/{driverUUID}/v2/preferences")                  # 5; feedback * e preferences *
def driver_preferences(call: Call):
    return {"editable": False,
            "feedback": {"effect": "NEUTRAL", "effectText": "", "jobEligibilityRate": 1.0, "title": "",
                         "shouldHideFeedback": True},
            "preferences": []}


@handles(APP, "GET", "/rt/health")                                               # 5
def rt_health(call: Call):
    return {"status": "ok"}


@handles(APP, "POST", "/rt/drivers/learning/fetch-mobile-alerts")                # 3; mobileAlerts *
def fetch_mobile_alerts(call: Call):
    return {"mobileAlerts": []}


@handles(APP, "POST", "/rt/earnings/session-feedback-loop/validate-session-readiness")   # 3
def validate_session_readiness(call: Call):
    return {"sessionExpected": False}


@handles(APP, "GET|POST", "/rt/mobile/recovery-action")                          # 2
def mobile_recovery_action(call: Call):
    return {}


@handles(APP, "GET", "/rt/onboarding/get-onboarding-status")                     # 2; DriverOnboardingStatus * (enum Java)
def onboarding_status_response(call: Call):
    d = call.subject()
    return {"driverOnboardingStatus": {"approved": "ONBOARDED", "pending": "ONBOARDING", "rejected": "REJECTED",
                                       "suspended": "ONBOARDED"}.get(d.status, "UNKNOWN")}


# ---- documentos, notificacoes e rota (pedidos depois do lote 5) --------------------------------------
DOC_TITLES = {"carta_conducao": "Carta de condução", "certificado_tvde": "Certificado de motorista TVDE",
              "registo_criminal": "Certificado de registo criminal", "cartao_cidadao": "Cartão de cidadão",
              "atestado_medico": "Atestado médico",
              "dua": "DUA", "seguro": "Seguro", "inspecao": "Inspeção"}

DRIVER_DOC_KINDS = {"carta_conducao", "cartao_cidadao", "certificado_tvde",
                    "registo_criminal", "atestado_medico"}


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


def _prefs_json(p) -> dict:
    return {
        "destinationMode": bool(p.destination_mode),
        "destinationAddress": p.destination_address or "",
        "destinationLat": p.destination_lat,
        "destinationLng": p.destination_lng,
        "areaMode": bool(p.area_mode),
        "areaLabel": p.area_label or "",
        "areaLat": p.area_lat,
        "areaLng": p.area_lng,
        "areaRadiusKm": p.area_radius_km,
        "autoAccept": bool(p.auto_accept),
        "breakUntil": p.break_until,
        "breakActive": bool(p.break_until and p.break_until > now()),
    }


def _prefs(db, driver_id: int):
    p = db.query(DriverPreference).filter_by(driver_id=driver_id).first()
    if not p:
        p = DriverPreference(driver_id=driver_id)
        db.add(p)
        db.flush()
    return p


@handles(APP, "GET|POST", "/rt/drivers/v2/preferences")
def preferences(call: Call):
    """Modo destino, area, aceitacao automatica e pausa."""
    d = call.subject()
    p = _prefs(call.db, d.id)
    if call.method == "POST":
        b = call.body
        for src, dst in (("destinationMode", "destination_mode"), ("areaMode", "area_mode"),
                         ("autoAccept", "auto_accept")):
            if src in b:
                setattr(p, dst, bool(b[src]))
        for src, dst in (("destinationAddress", "destination_address"), ("areaLabel", "area_label")):
            if src in b:
                setattr(p, dst, str(b[src] or "")[:200])
        for src, dst in (("destinationLat", "destination_lat"), ("destinationLng", "destination_lng"),
                         ("areaLat", "area_lat"), ("areaLng", "area_lng")):
            if src in b:
                setattr(p, dst, b[src])
        if "areaRadiusKm" in b:
            try:
                p.area_radius_km = max(1.0, min(float(b["areaRadiusKm"] or 5), 50.0))
            except (TypeError, ValueError):
                raise RtError(400, "invalid_radius", "raio invalido")
        p.updated_at = now()
    return {"preferences": _prefs_json(p)}


@handles(APP, "POST", "/rt/drivers/v2/break")
def set_break(call: Call):
    d = call.subject()
    p = _prefs(call.db, d.id)
    resume = bool(call.get("resume", "off", default=False))
    try:
        minutes = max(1, min(int(call.get("minutes", default=15) or 15), 120))
    except (TypeError, ValueError):
        raise RtError(400, "invalid_minutes", "minutos invalidos")
    p.break_until = None if resume else now() + minutes * 60
    p.updated_at = now()
    return {"preferences": _prefs_json(p)}


DOC_EXT = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


def _doc_ext(raw: bytes, filename: str) -> str | None:
    suffix = Path(filename or "").suffix.lower()
    if suffix in DOC_EXT:
        return ".jpg" if suffix == ".jpeg" else suffix
    if raw.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if raw.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if raw[:4] == b"RIFF" and raw[8:12] == b"WEBP":
        return ".webp"
    if raw.startswith(b"%PDF"):
        return ".pdf"
    return None


def _save_document(call: Call, kind: str, number: str, expires: str | None,
                   content: str, filename: str) -> Document:
    """Cria/atualiza o documento do motorista e guarda o ficheiro no disco."""
    db, d = call.db, call.subject()
    data = (content or "").strip()
    if "," in data and data.split(",", 1)[0].startswith("data:"):
        data = data.split(",", 1)[1]
    try:
        raw = base64.b64decode(data, validate=True)
    except (binascii.Error, ValueError):
        raise RtError(400, "invalid_file", "ficheiro invalido")
    if not raw:
        raise RtError(400, "empty_file", "ficheiro vazio")
    if len(raw) > config.UPLOAD_MAX_BYTES:
        raise RtError(413, "file_too_large", "maximo de 8 MB")
    ext = _doc_ext(raw, filename)
    if not ext:
        raise RtError(415, "unsupported_file", "so JPG, PNG, WEBP ou PDF")
    doc = (db.query(Document)
           .filter(Document.owner_type == "driver", Document.owner_id == d.id, Document.kind == kind)
           .first())
    if not doc:
        doc = Document(owner_type="driver", owner_id=d.id, kind=kind)
        db.add(doc)
        db.flush()
    config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    name = f"doc-{doc.uuid}{ext}"
    (config.UPLOAD_DIR / name).write_bytes(raw)
    doc.number = (number or doc.number or "")[:60]
    doc.expires_on = expires or doc.expires_on
    doc.file_name = name
    doc.status = "pending"
    doc.notes = ""
    return doc


@handles(APP, "GET|POST", "/rt/drivers/v2/business-profile")
def business_profile(call: Call):
    """Perfil empresarial do motorista e delegados autorizados."""
    db, d = call.db, call.subject()
    row = db.get(Setting, f"driver_business:{d.id}")
    default = {"active": False, "companyName": "", "vat": "", "email": "", "delegates": []}
    data = jget(row.value, default) if row else default
    if call.method == "POST":
        action = str(call.body.get("action") or "save")
        if action == "remove_delegate":
            phone = str(call.body.get("delegatePhone") or "")
            data["delegates"] = [x for x in data.get("delegates", []) if x.get("phone") != phone]
        elif action == "add_delegate":
            name = str(call.body.get("delegateName") or "").strip()[:80]
            phone = str(call.body.get("delegatePhone") or "").strip()[:30]
            if name and len(phone) >= 6 and len(data.get("delegates", [])) < 5:
                data.setdefault("delegates", []).append({"name": name, "phone": phone, "role": "delegate"})
        else:
            data["active"] = bool(call.body.get("active", True))
            data["companyName"] = str(call.body.get("companyName") or "")[:120]
            data["vat"] = str(call.body.get("vat") or "")[:30]
            data["email"] = str(call.body.get("email") or "")[:120]
        if row:
            row.value = jset(data)
        else:
            db.add(Setting(key=f"driver_business:{d.id}", value=jset(data)))
        db.flush()
    return {"business": data}


@handles(APP, "GET|POST", "/rt/drivers/v2/incentives")
def incentives(call: Call):
    """Missoes, pontos/Pro e referral."""
    db, d = call.db, call.subject()
    if db.query(Quest).count() == 0:
        start = now() - 30 * 86400
        end = now() + 30 * 86400
        db.add_all([
            Quest(title="3 viagens esta semana", description="Complete 3 viagens para ganhar 5 EUR.",
                  target_trips=3, reward_cents=500, starts_at=start, ends_at=end),
            Quest(title="10 viagens esta semana", description="Complete 10 viagens para ganhar 20 EUR.",
                  target_trips=10, reward_cents=2000, starts_at=start, ends_at=end),
        ])
        db.flush()
    return _incentives(db, d)


def _incentives(db, d) -> dict:
    completed = db.query(Trip).filter(Trip.driver_id == d.id, Trip.state == "completed").count()
    points = completed * 10 + int(float(d.rating or 5.0) * 10)
    if points >= 300:
        tier, next_points = "Platinum", None
    elif points >= 100:
        tier, next_points = "Gold", 300
    else:
        tier, next_points = "Blue", 100
    quests = []
    for q in db.query(Quest).filter_by(active=True).order_by(Quest.id).all():
        progress = (db.query(Trip)
                    .filter(Trip.driver_id == d.id, Trip.state == "completed",
                            Trip.completed_at >= q.starts_at)
                    .count())
        claimed = db.query(QuestClaim).filter_by(quest_id=q.id, driver_id=d.id).first() is not None
        quests.append({
            "uuid": q.uuid, "title": q.title, "description": q.description,
            "target": q.target_trips, "progress": min(progress, q.target_trips),
            "reward": present.money(q.reward_cents), "rewardCents": q.reward_cents,
            "claimed": claimed, "canClaim": progress >= q.target_trips and not claimed,
        })
    code = f"QOL-{d.uuid[:6].upper()}"
    refs = db.query(Referral).filter_by(owner_driver_id=d.id).all()
    return {
        "points": points, "tier": tier, "nextTierPoints": next_points,
        "trips": completed,
        "quests": quests,
        "referral": {"code": code, "invited": len(refs),
                     "pending": sum(1 for r in refs if r.status == "pending"),
                     "reward": "10,00 EUR por motorista aprovado"},
    }


@handles(APP, "POST", "/rt/drivers/v2/quests/{questUUID}/claim")
def claim_quest(call: Call):
    db, d = call.db, call.subject()
    q = db.query(Quest).filter_by(uuid=call.vars["questUUID"], active=True).first()
    if not q:
        raise RtError(404, "quest_not_found", "missao inexistente")
    if db.query(QuestClaim).filter_by(quest_id=q.id, driver_id=d.id).first():
        raise RtError(409, "already_claimed", "recompensa ja recebida")
    progress = (db.query(Trip)
                .filter(Trip.driver_id == d.id, Trip.state == "completed",
                        Trip.completed_at >= q.starts_at)
                .count())
    if progress < q.target_trips:
        raise RtError(400, "quest_incomplete", "missao ainda nao concluida")
    db.add(QuestClaim(quest_id=q.id, driver_id=d.id))
    try:
        finance.adjust(db, "driver", d.id, q.reward_cents, f"Missao: {q.title}")
    except FinanceError as e:
        raise RtError(400, "reward_failed", str(e))
    return _incentives(db, d)


@handles(APP, "POST", "/rt/drivers/v2/referrals")
def create_referral(call: Call):
    db, d = call.db, call.subject()
    phone = str(call.body.get("phone") or "").strip()[:30]
    if len(phone) < 6:
        raise RtError(400, "invalid_phone", "telefone invalido")
    if phone == d.phone:
        raise RtError(400, "own_phone", "nao pode convidar a propria conta")
    code = f"QOL-{d.uuid[:6].upper()}"
    if not db.query(Referral).filter_by(owner_driver_id=d.id, invited_phone=phone).first():
        db.add(Referral(code=code, owner_driver_id=d.id, invited_phone=phone))
    return _incentives(db, d)


@handles(APP, "GET|POST", "/rt/drivers/v2/airport-queue")
def airport_queue(call: Call):
    """Fila do aeroporto: entrar, sair e ver a posicao."""
    db, d = call.db, call.subject()
    if call.method == "POST":
        action = str(call.body.get("action") or "join").strip().lower()
        row = db.query(AirportQueue).filter_by(driver_id=d.id).first()
        if action == "leave":
            if row:
                db.delete(row)
        else:
            if not d.vehicle or d.vehicle.status != "active":
                raise RtError(400, "no_vehicle", "veiculo ativo necessario")
            if d.availability != "online":
                raise RtError(400, "offline", "fique online para entrar na fila")
            if not row:
                row = AirportQueue(driver_id=d.id, city_id=d.city_id)
                db.add(row)
                db.flush()
    q = db.query(AirportQueue).filter(AirportQueue.status == "waiting")
    if d.city_id:
        q = q.filter(AirportQueue.city_id == d.city_id)
    rows = q.order_by(AirportQueue.joined_at, AirportQueue.id).all()
    position = next((i for i, x in enumerate(rows, 1) if x.driver_id == d.id), None)
    mine = next((x for x in rows if x.driver_id == d.id), None)
    return {
        "joined": position is not None,
        "position": position,
        "waiting": len(rows),
        "joinedAt": mine.joined_at if mine else None,
        "airport": "Aeroporto de Lisboa",
    }


@handles(APP, "POST", "/rt/drivers/v2/documents/upload")
def upload_document(call: Call):
    kind = str(call.get("kind", "documentKind") or "").strip()
    if kind not in DRIVER_DOC_KINDS:
        raise RtError(400, "invalid_kind", "tipo de documento invalido")
    doc = _save_document(
        call, kind,
        str(call.get("number", "documentNumber") or ""),
        call.get("expiresOn", "expires_on"),
        str(call.get("contentBase64", "content", "data") or ""),
        str(call.get("fileName", "filename") or ""),
    )
    call.db.flush()
    return {"document": _doc_json(doc)}


@handles(APP, "POST", "/rt/drivers/v2/verify-identity")
def verify_identity(call: Call):
    """Verificacao de identidade: Cartao de Cidadao + dados; fica pendente de revisao."""
    number = str(call.get("documentNumber", "number") or "")
    expires = call.get("expiresOn", "expires_on")
    content = str(call.get("contentBase64", "content", "data") or "")
    doc = _save_document(call, "cartao_cidadao", number, expires, content,
                         str(call.get("fileName", "filename") or ""))
    call.db.flush()
    return {
        "status": "pending",
        "message": "Documentos recebidos. A verificacao fica em analise.",
        "document": _doc_json(doc),
    }


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


@handles(APP, "GET|POST", "/rt/location/search")
def location_search(call: Call):
    """Pesquisa de locais para o mapa (Google Geocoding; fallback nos pontos do seed)."""
    q = str(call.get("q", "query", "searchTerm", default="") or "").strip()
    lat = call.get("lat", "latitude")
    lng = call.get("lng", "longitude")
    near = (float(lat), float(lng)) if lat is not None and lng is not None else (None, None)
    rows = geocode.places_search(q, near[0], near[1]) if q else []
    if not rows and q:
        rows = geocode.forward(q, near[0], near[1])
    if not rows:
        needle = q.lower()
        rows = [
            {"id": f"seed:{i}", "name": name, "line1": name, "line2": "Lisboa",
             "full": f"{name}, Lisboa", "lat": la, "lng": lo, "provider": "qolari"}
            for i, (name, la, lo) in enumerate(PLACES)
            if not needle or needle in name.lower()
        ]
    return {"places": rows[:8]}


@handles(APP, "POST", "/rt/support/map-report")
def map_report(call: Call):
    """Problema de mapa comunicado pelo motorista; fica para o suporte no backoffice."""
    d = call.subject()
    b = call.body or {}
    raw = str(b.get("reason") or "").strip()
    reason = raw if raw in MAP_REPORT_REASONS else next(
        (code for code, label in MAP_REPORT_REASONS.items() if label.lower() == raw.lower()), "")
    if not reason:
        raise RtError(400, "missing_reason", "indique o motivo")
    note = str(b.get("note") or "").strip()[:500]
    def coord(key: str) -> float | None:
        value = b.get(key)
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None
    r = MapReport(
        driver_id=d.id,
        reason=reason[:80],
        note=note,
        latitude=coord("latitude"),
        longitude=coord("longitude"),
    )
    call.db.add(r)
    call.db.flush()
    return {"ok": True, "reportUUID": r.uuid}

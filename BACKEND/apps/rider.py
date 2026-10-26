# -*- coding: utf-8 -*-
"""App Qolari Rider (base Uber 4.650.10003) -> dominio.

Contratos: contracts/rider_endpoints.json + rider_models.json (nomes de campo dos modelos
rtapi.services.marketplacerider.*, pricing.*, support.*). Estado da app de passageiro:
    ClientStatus.status (RideStatus): Looking | Dispatching | WaitingForPickup | OnTrip
    (valores do servidor Uber; confirmar nos logs da consola se a app mudar de ecra)
Vehicle views (categorias): id numerico = Product.id.
"""
from apps import geocode, present
from apps.rtapi import Call, RtError, handles
from domain import geo, pricing, settings, trips
from domain.models import City, Product, Promo, RiderPromo, Trip, now
from domain.trips import TripError

APP = "rider"

RIDE_STATUS = {"requested": "Dispatching", "accepted": "WaitingForPickup", "arrived": "WaitingForPickup",
               "in_progress": "OnTrip"}
DRIVER_STATUS = {"accepted": "Accepted", "arrived": "Arrived", "in_progress": "DrivingClient"}  # marketplacerider.DriverStatus


def _err(e: TripError) -> RtError:
    return RtError(400, e.code, str(e), {"title": "Qolari", "message": str(e)})


def _city(db, lat=None, lng=None) -> City:
    cities = db.query(City).filter(City.active.is_(True)).all()
    if not cities:
        raise RtError(503, "no_city", "sem cidades ativas")
    if lat is None:
        return cities[0]
    return min(cities, key=lambda c: geo.haversine_m(c.center_lat, c.center_lng, lat, lng))


def _point(obj) -> tuple[float, float] | None:
    """Location/TargetLocation/ClientRequestLocation das apps -> (lat, lng)."""
    if not isinstance(obj, dict):
        return None
    for k in ("targetLocation", "location", "anchorGeolocation", "coordinate"):
        if isinstance(obj.get(k), dict):
            p = _point(obj[k])
            if p:
                return p
    lat = obj.get("latitude", obj.get("lat"))
    lng = obj.get("longitude", obj.get("lng"))
    try:
        return (float(lat), float(lng)) if lat is not None and lng is not None else None
    except (TypeError, ValueError):
        return None


def _address(obj) -> str:
    """Morada de um Location/ClientRequestLocation. O pickup traz-na em anchorGeolocation.location (fullAddress,
    name: o que o resolve-location devolveu); sem morada, geocodificacao inversa das coordenadas."""
    if not isinstance(obj, dict):
        return ""
    for k in ("address", "formattedAddress", "fullAddress", "title", "nickname", "shortAddress", "name"):
        if isinstance(obj.get(k), str) and obj[k]:
            return obj[k]
    for k in ("anchorGeolocation", "rendezvousLocation", "targetLocation", "location"):
        if isinstance(obj.get(k), dict):
            a = _address(obj[k])
            if a:
                return a
    return ""


def _address_or_geocode(obj, p) -> str:
    return _address(obj) or (geocode.reverse(*p)["full"] if p else "")


def vehicle_view(p: Product, city: City) -> dict:
    """rtapi.models.vehicleview.VehicleView (resumo)."""
    return {"id": p.id, "uuid": p.uuid, "displayName": p.name, "description": p.description,
            "capacity": p.capacity, "allowedToSurge": True, "upfrontPriceEnabled": True,
            "isSchedulable": False, "hideProductInApp": False, "groupDisplayName": "Viagens",
            "requestPickupButtonString": f"Pedir {p.name}", "dispatchingStatus": "available",
            "noneAvailableString": "Sem motoristas disponíveis", "waitTimeString": "",
            # vehicleview.ProductFare: id, type, base(Value), minimum, perMinute, cancellation, speedThresholdMps e
            # distanceUnit (enum KM|MILE) sao obrigatorios - faltando um, a app falha a ler o City inteiro e
            # repete o app-launch ~1/s (appLaunchRetryOnNetworkErrorV3)
            "fare": {"id": p.id, "type": "TIME_AND_DISTANCE",
                     "base": present.money(p.base_fare, city.currency), "baseValue": p.base_fare / 100,
                     "perDistanceUnit": present.money(p.per_km, city.currency),
                     "perMinute": present.money(p.per_min, city.currency),
                     "minimum": present.money(p.minimum_fare, city.currency),
                     "cancellation": present.money(p.cancel_fee, city.currency),
                     "bookingFee": present.money(p.booking_fee, city.currency),
                     "speedThresholdMps": 4.47, "distanceUnit": "KM"}}


def city_json(db, city: City) -> dict:
    prods = [p for p in city.products if p.active]
    return {"cityId": city.id, "cityName": city.name, "countryIso2": city.country_iso2,
            "currencyCode": city.currency, "timezone": city.timezone,
            "defaultVehicleViewId": prods[0].id if prods else None,
            "vehicleViews": {str(p.id): vehicle_view(p, city) for p in prods},
            "vehicleViewsOrder": [p.id for p in prods], "productTiersOrder": [],
            "productsUnavailableMessage": "Sem motoristas disponíveis neste momento",
            "isEmergencyLocationSharingAvailable": True}


def eyeball(db, city: City, lat=None, lng=None) -> dict:
    """Carros a volta (nearbyVehicles por vehicle view)."""
    from domain.models import Driver
    near = {}
    for d in db.query(Driver).filter(Driver.availability == "online", Driver.status == "approved",
                                     Driver.lat.is_not(None)).all():
        if lat is not None and geo.haversine_m(lat, lng, d.lat, d.lng) > 10_000:
            continue
        v = d.vehicle
        for p in city.products:
            if p.active and v and (not v.product_ids or p.id in v.product_ids):
                eta = int(geo.haversine_m(lat, lng, d.lat, d.lng) * 1.35 / 7.8) if lat is not None else 300
                n = near.setdefault(str(p.id), {"vehiclePaths": {}, "minEta": eta, "etaString": ""})
                n["vehiclePaths"][d.uuid] = [{"latitude": d.lat, "longitude": d.lng, "course": d.heading,
                                               "epoch": present.ms(d.location_at)}]
                n["minEta"] = min(n["minEta"], eta)
    for n in near.values():
        n["etaString"] = f"{max(1, round(n['minEta'] / 60))} min"
        n["etaStringShort"] = n["etaString"]
    return {"nearbyVehicles": near, "dynamicFares": {}}


def trip_json(db, t: Trip) -> dict:
    """rtapi.services.marketplacerider.Trip (o essencial)."""
    cur = t.city.currency
    d = t.driver
    eta = None
    if d and d.lat is not None and t.state == "accepted":
        eta = int(geo.haversine_m(d.lat, d.lng, t.pickup_lat, t.pickup_lng) * settings.get(db, "road_factor")
                  / (settings.get(db, "avg_speed_kmh") / 3.6))
    out = {"uuid": t.uuid, "clientUUID": t.rider.uuid, "vehicleViewId": t.product_id,
           "currencyCode": cur, "surgeMultiplier": t.surge, "capacity": t.product.capacity,
           "pickupLocation": present.location(t.pickup_lat, t.pickup_lng, t.pickup_address),
           "destination": present.location(t.dropoff_lat, t.dropoff_lng, t.dropoff_address),
           "requestedTime": float(t.requested_at), "assignedTimeInSec": float(t.accepted_at or 0) or None,
           "pickupCompletedTimeInSec": float(t.started_at) if t.started_at else None,
           "driverArrivedTimeMs": present.ms(t.arrived_at),
           "upfrontFareString": present.money(t.est_fare, cur),
           "formattedUpfrontFareString": present.money(t.est_fare, cur),
           "fareEstimateString": present.money(t.est_fare, cur), "useCredits": False,
           "isPoolTrip": False, "isSafetyToolkitEnabled": True, "canShareTripWithContact": True}
    # Obrigatorios nos Builders (faltando um, a app rejeita o Trip inteiro - e com ele o PickupResponse):
    # PinVerificationInfo pin+pinVerificationType; Driver displayCompany/isAccessibilityTripViewEnabled/
    # isCallButtonEnabled/rating; Vehicle exteriorColor/interiorColor/year (+ vehicleType capacity/id/make/model).
    out["tripStatusMessage"] = trip_status_message(t)
    if t.pin and d:
        out["pinVerificationInfo"] = {"pin": t.pin, "pinVerificationType": "PROVIDER_SETTING",
                                      "verificationMethod": "PIN", "shouldShow": True, "isVerified": False}
    if eta is not None:
        out.update({"eta": max(1, round(eta / 60)), "etaString": f"{max(1, round(eta / 60))} min",
                    "etaStringShort": f"{max(1, round(eta / 60))} min"})
    if t.state == "in_progress" and t.dropoff_lat is not None and d and d.lat is not None:
        out["etaToDestination"] = geo.haversine_m(d.lat, d.lng, t.dropoff_lat, t.dropoff_lng) * 1.35 / 7.8
    if d:
        out["driver"] = {**present.driver(d), "rating": float(d.rating or 5.0), "displayCompany": False,
                         "isAccessibilityTripViewEnabled": False, "isCallButtonEnabled": True,
                         "status": DRIVER_STATUS.get(t.state)}
        v = t.vehicle
        out["vehicle"] = {**(present.vehicle(v) or {}), "exteriorColor": (v.color if v else "") or "",
                          "interiorColor": "", "year": int((v.year if v else 0) or 0),
                          "vehicleColorHex": v.color_hex if v else None, "vehicleViewId": t.product_id,
                          "vehicleType": {"id": t.product_id, "capacity": t.product.capacity,
                                          "make": (v.make if v else "") or "", "model": (v.model if v else "") or ""}}
        out["contact"] = {"phoneNumber": d.phone, "smsNumber": d.phone}
    return out


STATUS_DETAIL_MODE = {"requested": "Hidden", "accepted": "MinutesToPickup", "arrived": "IconOnly",
                      "in_progress": "TimeOfDropoff"}  # tripstatustracker.TripStatusDetailMode (@SerializedName)


def trip_status_message(t: Trip) -> dict:
    """tripstatustracker.TripStatusMessage - cabecalho do ecra da viagem. Obrigatorios: messageId, title,
    context.tripUUID, detail.mode (faltando um, o Trip inteiro e rejeitado)."""
    v = t.vehicle
    sub = {"requested": "A ligar ao motorista mais próximo",
           "accepted": f"{v.make} {v.model} · {v.plate}" if v else "O motorista está a caminho",
           "arrived": "O motorista está à sua espera no local de recolha",
           "in_progress": t.dropoff_address or "A caminho do destino"}.get(t.state, "")
    return {"messageId": f"{t.uuid}:{t.state}", "title": present.trip_state_label(t), "subtitle": sub,
            "context": {"tripUUID": t.uuid}, "detail": {"mode": STATUS_DETAIL_MODE.get(t.state, "Hidden")},
            "displaySettings": {"showSubtitle": bool(sub)}}


def client_status(db, rider, trip: Trip | None) -> dict:
    """ClientStatus."""
    if trip and trip.state in RIDE_STATUS:
        return {"status": RIDE_STATUS[trip.state], "statusDescription": present.trip_state_label(trip),
                "isArriving": trip.state == "arrived", "lastRequestJobUUID": trip.uuid}
    last = (db.query(Trip).filter(Trip.rider_id == rider.id).order_by(Trip.id.desc()).first())
    out = {"status": "Looking"}
    if last and last.state in ("cancelled", "no_drivers") and last.cancelled_by != "rider" \
            and now() - (last.cancelled_at or 0) < 60:
        # a app mostra um aviso: titulo = lastRequestNote, texto = lastRequestMsg; lastRequestType e o enum
        # marketplacerider.TripCancellationType (DriverCanceled, RequestExpired, ...)
        if last.state == "no_drivers":
            out.update({"lastRequestNote": "Sem motoristas disponíveis", "lastRequestType": "RequestExpired",
                        "lastRequestMsg": "Não há motoristas perto de si neste momento. Tente novamente daqui a pouco."})
        else:
            out.update({"lastRequestNote": "Viagem cancelada",
                        "lastRequestType": "DriverCanceled" if last.cancelled_by == "driver" else "AutoCanceled",
                        "lastRequestMsg": "A sua viagem foi cancelada. Pode pedir outra."})
    return out


LEGACY_TRIP_STATUS = {"requested": "DISPATCHING", "accepted": "EN_ROUTE", "arrived": "EN_ROUTE",
                      "in_progress": "ON_TRIP"}  # marketplacerider.LegacyTripStatus


def fulfillment_state(db, trip: Trip | None) -> dict:
    """marketplacerider.FulfillmentStateData: a viagem ativa nesta versao da app. O StatusResponse NAO tem `trip`:
    a cada sondagem o k7b.b.c apaga o Trip guardado (riderData.c(null)) e fica com fulfillmentStateData
    (orders[].orderPlan.jobs[].legacyTripData = trip + tripStatus + vehicleView). Sem isto, o Trip do
    PickupResponse dura ate a sondagem seguinte (~1 s) e a app volta a lista de categorias.
    meta: a app so substitui o que tem se o lastModifiedTimeMs for >= (p7b.b.a)."""
    t_ms = float(now() * 1000)
    out = {"meta": {"lastModifiedTimeMs": t_ms, "originTimeMs": t_ms}, "orders": []}
    if trip and trip.state in LEGACY_TRIP_STATUS:
        out["orders"].append({
            "orderId": {"uuid": trip.uuid},
            "orderPlan": {"jobs": [{
                "jobId": {"alternatives": {"type": "transportJobId", "transportJobId": {"uuid": trip.uuid}}},
                "legacyTripData": {"trip": trip_json(db, trip), "tripStatus": LEGACY_TRIP_STATUS[trip.state],
                                   "vehicleView": vehicle_view(trip.product, trip.city)}}]}})
    return out


def rider_app_orders(db, trip: Trip | None) -> dict:
    """mobilityorderpresentation.orders.RiderAppOrdersResponse. A viagem so fica ativa na app (l7b.k1 ->
    ActiveOrder) se houver uma RiderAppOrder cujo TransportJob.id = transportJobId do fulfillmentStateData;
    o estado do ecra sai de jobs.singlePersonalTransport.transport.backwardsCompatibleData.legacyTripState
    (l7b.n1.b). meta.lastModifiedTimeMs obrigatorio (sem ele a encomenda e ignorada)."""
    out = {"orders": [], "meta": {"lastModifiedTimeMs": now() * 1000}, "isConcurrencyEnabled": False}
    if trip and trip.state in LEGACY_TRIP_STATUS:
        out["orders"].append({
            "id": trip.uuid, "state": "ACTIVE", "createdAt": trip.requested_at,
            "jobs": {"type": "singlePersonalTransport", "singlePersonalTransport": {"transport": {
                "id": trip.uuid, "createdAt": trip.requested_at,
                "backwardsCompatibleData": {"legacyTripState": LEGACY_TRIP_STATUS[trip.state]},
                "productContext": product_context(trip.product)}}}})
    return out


def _status_bundle(call: Call) -> dict:
    db = call.db
    rider = call.subject()
    trip = trips.active_trip_for_rider(db, rider)
    loc = _point(call.body.get("targetLocation") or call.body.get("requestPickupLocation") or {})
    if loc:
        rider.lat, rider.lng = loc
    lat, lng = loc or (rider.lat, rider.lng)
    city = _city(db, lat, lng)
    out = {"city": city_json(db, city), "clientStatus": client_status(db, rider, trip),
           "eyeball": eyeball(db, city, lat, lng), "fulfillmentStateData": fulfillment_state(db, trip),
           "riderAppOrdersResponse": rider_app_orders(db, trip),
           "metadata": {"pollingIntervalMs": 4000}}
    if trip:
        out["trip"] = trip_json(db, trip)
        if trip.state == "requested":
            # marketplacerider.DispatchStatus (ecra "A procurar motorista")
            out["dispatchStatus"] = {"title": "A procurar motorista", "isScheduleStatus": False,
                                     "message": "A ligar ao motorista mais próximo"}
    return out


# ---- arranque e estado -----------------------------------------------------------------------
@handles(APP, "POST", "/rt/riders/{riderUUID}/app-launch")
def app_launch(call: Call):
    b = _status_bundle(call)
    rider = call.subject()
    status = {k: b[k] for k in ("clientStatus", "eyeball", "fulfillmentStateData") if k in b}
    if "trip" in b:
        status["trip"] = b["trip"]
    return {"client": present.rider(rider), "city": b["city"], "status": status, "metadata": _synced(call.body),
            "riderAppOrdersResponse": b["riderAppOrdersResponse"]}


def _synced(body) -> dict:
    """BootstrapMetadata: devolve o local de recolha recebido como sincronizado. Sem isto a app considera que
    o servidor nao o recebeu e repete o app-launch em rajadas (~1/s)."""
    loc = body.get("requestPickupLocation")
    out = {}
    if isinstance(loc, dict):
        out["requestPickupLocationSynced"] = loc
        if isinstance(loc.get("targetLocation"), dict):
            out["targetLocationSynced"] = loc["targetLocation"]
    return out


@handles(APP, "POST", "/rt/riders/{riderUUID}/status", "/rt/riders/me/status")
def status(call: Call):
    return _status_bundle(call)


@handles(APP, "POST", "/rt/riders/{riderUUID}/client-status", "/rt/riders/me/client-status")
def client_status_ep(call: Call):
    rider = call.subject()
    return {"clientStatus": client_status(call.db, rider, trips.active_trip_for_rider(call.db, rider))}


@handles(APP, "GET", "/rt/riders/{riderUUID}/dispatch-view")
def dispatch_view(call: Call):
    return present.rider(call.subject())


@handles(APP, "POST", "/rt/riders/{riderUUID}/upload-locations")
def upload_locations(call: Call):
    rider = call.subject()
    locs = call.body.get("locations") or call.body.get("riderLocations") or []
    if isinstance(locs, list) and locs:
        p = _point(locs[-1])
        if p:
            rider.lat, rider.lng = p
    return {}


@handles(APP, "POST", "/rt/session/launch", "/rt/eats/v1/eater-app-launch", "/rt/riders/pre-trip-map",
         "/rt/riders/product-configuration", "/rt/riders/map-change", "/rt/riders/evaluate-market-status",
         "/rt/riders/log-hub-user-interaction", "/rt/riders/verify-device-integrity")
def ack(call: Call):
    return {}


@handles(APP, "GET", "/v1/launch")
def v1_launch(call: Call):
    return {}


@handles(APP, "GET", "/rt/riders/dispatchconfig")
def dispatch_config(call: Call):
    return {"scripts": []}


# ---- local de recolha / destino --------------------------------------------------------------
def _geolocation_result(lat: float, lng: float, g: dict) -> dict:
    """ms.search.generated.GeolocationResult. A app (zv2.e.a) so aceita o lugar com location.id nao vazio
    e usa provider, name/addressLine1/addressLine2/fullAddress (titulo e subtitulo) e coordinate (obrigatoria)."""
    return {"location": {"id": g["id"], "provider": g["provider"], "name": g["name"], "addressLine1": g["line1"],
                         "addressLine2": g["line2"], "fullAddress": g["full"], "locale": geocode.LANG,
                         "coordinate": {"latitude": lat, "longitude": lng}},
            "confidence": "HIGH", "addressFormat": "DEFAULT"}


@handles(APP, "POST", "/rt/riders/{riderUUID}/resolve-location")
def resolve_location(call: Call):
    """marketplacerider.ResolveLocationResponse: resultantLocations (UpdatedPickupSuggestion) e obrigatorio -
    com {} o Builder lanca "resultantLocations is null!" e a app repete o pedido (1 s, 2 s, 4 s, ...) sem nunca
    resolver o ponto de recolha. Quem le (fp6.s): resultantLocations[0].locationSource + anchorGeolocation
    passam para o ClientRequestLocation do pedido; uv2.v (pontos de acesso) so mostra pickups com suggested=true.
    Morada por geocodificacao inversa (apps/geocode.py)."""
    rider = call.subject()
    req = call.body.get("requestLocation") or {}
    p = _point(req.get("targetLocation")) or _point(req) or \
        ((rider.lat, rider.lng) if rider.lat is not None else None)
    if not p:
        raise RtError(400, "missing_location", "sem localizacao")
    lat, lng = p
    g = geocode.reverse(lat, lng)
    anchor = _geolocation_result(lat, lng, g)
    loc = {**present.location(lat, lng, g["full"], g["name"]), "id": g["id"], "subtitle": g["line2"],
           "shortAddress": g["name"]}
    suggestion = {"anchorGeolocation": anchor, "locationSource": req.get("locationSource") or "DefaultDevice",
                  "updatedTimestamp": float(now() * 1000), "pickups": [], "dropoffs": []}
    if call.body.get("context") != "DROPOFF":
        # o proprio pino (sem pontos de acesso sugeridos: suggested=false)
        suggestion["pickups"] = [{"location": loc, "uuid": f"pin-{lat:.6f},{lng:.6f}", "mapLabelText": g["name"],
                                  "primaryDisplayText": g["name"], "secondaryDisplayText": g["line2"],
                                  "suggested": False, "validated": True}]
    return {"resultantLocations": [suggestion], "locationSuggestions": [anchor]}


@handles(APP, "POST", "/rt/venue/get-venue")
def get_venue(call: Call):
    """rt.colosseum.GetVenueResponse (sem obrigatorios): nao ha recintos (aeroportos, estadios) com zonas proprias."""
    return {"hasVenue": False}


@handles(APP, "POST|DELETE", "/rt/navigation/create-route-plan", "/rt/navigation/delete-route-plan/{agentUUID}")
def route_plan(call: Call):
    """RoutePlannerApi.createRoutePlan / deleteRoutePlan: resposta vazia (pec.d0 = Unit)."""
    return {}


# ---- tarifa e pedido -------------------------------------------------------------------------
@handles(APP, "POST", "/rt/request-blockers/get-blockers/")
def request_blockers(call: Call):
    """ucomponent.UComponentResponse: bloqueios antes do pedido (pagamento, verificacao, ...).
    Sem componentes = nada a bloquear; com {} a app nao avanca do "Confirmar recolha"."""
    import uuid as _uuid
    req = call.body.get("request") or {}
    rid = req.get("requestUUID") or str(_uuid.uuid4())
    # componente de contexto (REQUEST_BLOCKERS_CONTEXT) com a lista de bloqueios a mostrar - vazia. Sem ele o
    # fluxo do pedido fica a espera (uc6.x.j -> UComponentDataConsumer) e desiste ao fim de ~15 s.
    payload = {"displayBlockersInfo": [], "displayBlockersUUIDs": [], "requestUuid": rid}
    if isinstance(req.get("vvid"), int):
        payload["vehicleViewId"] = req["vvid"]
    for k in ("pickup", "destination"):
        p = _point(req.get(k))
        if p:
            payload[k] = {"latitude": p[0], "longitude": p[1]}
    # Unioes thrift: o "type" serializa-se com o NOME DO CAMPO (@SerializedName: RIDER_CONTEXT_DATA ->
    # "riderContextData"...). Com os nomes Java o Gson le UNKNOWN, o h18.d nao escolhe o construtor de caminhos
    # (vc6.a) e o contexto fica guardado em "REQUEST_BLOCKERS_CONTEXT" em vez de "..._<requestUuid>", que e onde
    # o uc6.d espera por ele -> spinner ~15 s e volta atras sem pedir a viagem.
    ctx = {"componentKey": {"type": "riderComponentKey", "riderComponentKey": "REQUEST_BLOCKERS_CONTEXT"},
           "context": {"contextData": {"type": "riderContextData", "riderContextData": {
               "type": "requestBlockersContextData", "requestBlockersContextData": {
                   "type": "updatePayloadContextData", "updatePayloadContextData": payload}}}}}
    return {"components": [ctx], "uuid": rid}


def _product_image(call: Call, p: Product) -> str:
    """URL publico da imagem do produto (static/products/<code>.png, servido pelo main.py nesta mesma porta)."""
    import config
    host = call.headers.get("x-forwarded-host") or call.headers.get("host") or "127.0.0.1"
    proto = call.headers.get("x-forwarded-proto") or "http"
    name = p.code if (config.STATIC_DIR / "products" / f"{p.code}.png").is_file() else "default"
    return f"{proto}://{host}/static/products/{name}.png"


def product_context(p: Product, img: dict | None = None) -> dict:
    """mop.models.productcontext.TransportProductContext (legacy.vehicleViewID/UUID obrigatorios para a app)."""
    pres = {"productDisplayName": p.name, "detailedProductDescription": p.description}
    if img:
        pres["productImage"] = img
    return {"legacy": {"vehicleViewID": p.id, "vehicleViewUUID": p.uuid, "allowRidePool": False},
            "presentation": pres}


def _waypoint(req: dict, task: str):
    """GetOrderSelectionRequest.waypointSpecs[] (taskTypes PICKUP / DROP_OFF) -> (lat, lng)"""
    for w in req.get("waypointSpecs") or []:
        if task in (w.get("taskTypes") or []):
            return _point((w.get("locationSpec") or {}).get("point"))
    return None


@handles(APP, "POST", "/rt/shopping-service/order_selection/")
def order_selection(call: Call):
    """mop.orderselection.GetOrderSelectionResponse (FULL_RESPONSE) - o seletor de produtos ("Escolha uma viagem").
    O que a app valida (ridershoppingstream.core.data.n$a.b / ShoppingOrderClientModel.c):
      features.orderSelection.bottomSheetConfiguration obrigatorio; orderGroups[].titleText;
      cada ShoppingOrder: id + jobs.singleTransport.transportJob.productContext.legacy.vehicleViewID
      (+ vehicleViewUUID). Falhando, "Ocorreu um problema ao concluir o seu pedido"."""
    import uuid as _uuid
    db = call.db
    rider = call.subject()
    req = call.body.get("request") or call.body
    pickup = _waypoint(req, "PICKUP") or (rider.lat, rider.lng)
    dest = _waypoint(req, "DROP_OFF")
    city = _city(db, *pickup) if pickup[0] is not None else _city(db)
    promo = trips._rider_promo(db, rider, city.products[0]) if city.products else None
    ctx, req_id = str(_uuid.uuid4()), str(_uuid.uuid4())
    orders, ids = [], []
    for p in sorted((p for p in city.products if p.active), key=lambda p: p.sort_order):
        q = pricing.estimate(db, p, pickup[0], pickup[1], dest[0] if dest else None, dest[1] if dest else None,
                             promo if promo and pricing.promo_valid(promo, p.id) is None else None) \
            if pickup[0] is not None else None
        fare = present.money(q.total, city.currency) if q else ""
        oid = f"so-{p.id}"
        ids.append(oid)
        img = {"dayImageURL": _product_image(call, p), "nightImageURL": _product_image(call, p)}
        orders.append({
            "id": oid,
            "jobs": {"type": "singleTransport", "singleTransport": {"transportJob": {
                "id": f"job-{p.id}",
                "productContext": product_context(p, img),
                "physicalCapacityTotal": {"capacityTotal": p.capacity}}}},
            "fare": {"id": {"context_id": ctx, "lifecycle_id": str(_uuid.uuid4()), "request_id": req_id},
                     "fareDisplays": {"PRE_DEDUCTION": {"displayString": fare, "displayType": "PRE_DEDUCTION"}}},
            # icon obrigatorio: sem imagem a linha nao aparece (m24.z$a.c: "orderIllustration is null")
            "presentation": {"displayName": p.name, "detailedDescription": p.description, "icon": img},
            "eligibility": {"availability": "AVAILABLE"},
        })
    feature = {"bottomSheetConfiguration": {"maxScreenHeightPercentage": 0.6, "middleStateItemCount": 3.0},
               "orderGroups": [{"id": "rides", "titleText": "Viagens", "shoppingOrderIDs": ids,
                                "isHeaderVisibleOnFullState": False, "isHeaderVisibleOnMiddleState": False}]}
    meta = {"shoppingSessionID": str(_uuid.uuid4()), "timeToFetch": now() * 1000,
            "orderSelectionResponseID": req_id}
    return {"response": {"type": "fullResponse", "fullResponse": {
        "shoppingOrders": orders, "features": {"orderSelection": feature}, "metadata": meta}}}



@handles(APP, "POST", "/rt/riders/{riderUUID}/fare-estimate")
def fare_estimate(call: Call):
    db = call.db
    rider = call.subject()
    pickup = _point(call.body.get("pickupLocation")) or (rider.lat, rider.lng)
    if pickup[0] is None:
        raise RtError(400, "missing_pickup", "sem local de recolha")
    dest = _point(call.body.get("destination"))
    city = _city(db, *pickup)
    promo = trips._rider_promo(db, rider, city.products[0]) if city.products else None
    variants = []
    for p in city.products:
        if not p.active:
            continue
        q = pricing.estimate(db, p, pickup[0], pickup[1], dest[0] if dest else None, dest[1] if dest else None,
                             promo if promo and pricing.promo_valid(promo, p.id) is None else None)
        fare = present.money(q.total, city.currency)
        variants.append({
            "vehicleViewId": p.id, "productUuid": p.uuid, "isDefault": p.sort_order == 0,
            "sortWeight": float(p.sort_order),
            "pricingInfo": {"fareInfo": {"upfrontFare": {
                "fare": fare, "fareString": fare, "fareValue": q.total / 100, "currencyCode": city.currency,
                "surgeMultiplier": q.surge, "discountedFare": present.money(q.subtotal, city.currency)
                if q.discount else None, "uuid": f"{p.uuid}:{q.total}"}},
                "fareBreakdown": q.as_dict(), "packageVariantUuid": f"pv-{p.id}"}})
    return {"packageVariants": variants, "vehicleViewIds": [v["vehicleViewId"] for v in variants],
            "uuid": f"fe-{rider.uuid}-{now()}"}


@handles(APP, "POST", "/rt/riders/{riderUUID}/pickup", "/rt/riders/{riderUUID}/v2/pickup")
def pickup(call: Call):
    db = call.db
    rider = call.subject()
    b = call.body
    req = b.get("pickupRequest") if isinstance(b.get("pickupRequest"), dict) else b
    plocobj = req.get("requestPickupLocation") or req.get("pickupLocation") or req.get("userLocation")
    p = _point(plocobj) or ((rider.lat, rider.lng) if rider.lat is not None else None)
    if not p:
        raise RtError(400, "missing_pickup", "sem local de recolha")
    dobj = req.get("requestDestinationLocation") or req.get("destination")
    d = _point(dobj)
    vvid = req.get("vehicleViewId")
    product = db.get(Product, int(vvid)) if str(vvid or "").isdigit() else None
    city = _city(db, *p)
    product = product or next((x for x in city.products if x.active), None)
    if not product:
        raise RtError(400, "product_unavailable", "categoria indisponivel")
    payment = "card" if req.get("paymentProfileUUID") and req.get("paymentProfileUUID") != "cash" else None
    try:
        t = trips.request_trip(db, rider, product, p, d, _address_or_geocode(plocobj, p),
                               _address_or_geocode(dobj, d), payment)
    except TripError as e:
        raise _err(e)
    return {"clientStatus": client_status(db, rider, t), "trip": trip_json(db, t),
            "eyeball": eyeball(db, city, *p)}


@handles(APP, "POST", "/rt/trips/{tripUUID}/rider-cancel")
def rider_cancel(call: Call):
    db = call.db
    rider = call.subject()
    t = db.query(Trip).filter_by(uuid=call.vars["tripUUID"], rider_id=rider.id).first() \
        or trips.active_trip_for_rider(db, rider)
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente")
    try:
        trips.cancel(db, t, "rider", str(call.get("reason", "cancelReason", default="") or ""))
    except TripError as e:
        raise _err(e)
    return {"clientStatus": client_status(db, rider, None), "trip": trip_json(db, t)}


@handles(APP, "POST", "/rt/trips/{tripUUID}/cancellation-info")
def cancellation_info(call: Call):
    db = call.db
    t = db.query(Trip).filter_by(uuid=call.vars["tripUUID"]).first()
    if not t:
        return {}
    fee = 0
    if t.accepted_at and now() - t.accepted_at > settings.get(db, "rider_free_cancel_s"):
        fee = t.product.cancel_fee
    return {"title": "Cancelar viagem?",
            "message": f"Será cobrada uma taxa de {present.money(fee)}." if fee else "Sem custos de cancelamento.",
            "cancellationFee": present.money(fee) if fee else None}


@handles(APP, "POST", "/rt/trips/{tripUUID}/share")
def share(call: Call):
    return {"shareUrl": f"/viagem/{call.vars['tripUUID']}"}


# ---- historico, recibo, avaliacao ------------------------------------------------------------
def past_trip(t: Trip) -> dict:
    cur = t.city.currency
    return {"id": t.uuid, "riderUUID": t.rider.uuid, "riderName": t.rider.name,
            "date": present.ms(t.requested_at), "status": t.state.upper(),
            "pickupAddress": t.pickup_address, "dropoffAddress": t.dropoff_address,
            "fareLocalString": present.money(t.fare if t.fare is not None else t.est_fare, cur),
            "distance": (t.distance_m or t.est_distance_m) / 1000, "duration": t.duration_s or t.est_duration_s,
            "driverName": t.driver.first_name if t.driver else "", "driverId": t.driver.uuid if t.driver else None,
            "driverRating": t.rider_to_driver_rating, "make": t.vehicle.make if t.vehicle else "",
            "model": t.vehicle.model if t.vehicle else "", "isCashTrip": t.payment_method == "cash",
            "isSurgeTrip": t.surge > 1, "hideTipButton": True}


@handles(APP, "POST", "/rt/support/get-trip-history")
def trip_history(call: Call):
    rider = call.subject()
    rows = (call.db.query(Trip).filter(Trip.rider_id == rider.id).order_by(Trip.requested_at.desc()).limit(50).all())
    return {"trips": [past_trip(t) for t in rows], "pagingResult": {}}


@handles(APP, "POST", "/rt/receipts/v1/getreceipt", "/rt/support/get-trip-receipt")
def receipt(call: Call):
    db = call.db
    uuid = call.get("tripUUID", "tripUuid", "uuid", "orderUUID", default="")
    t = db.query(Trip).filter_by(uuid=str(uuid)).first()
    if not t:
        raise RtError(404, "trip_not_found", "viagem inexistente")
    from domain.models import jget
    br = jget(t.fare_breakdown, {}).get("final") or jget(t.fare_breakdown, {}).get("estimate") or {}
    cur = t.city.currency
    lines = [("Tarifa base", br.get("base")), ("Distância", br.get("distance")), ("Tempo", br.get("time")),
             ("Tarifa dinâmica", br.get("surge_amount")), ("Taxa de reserva", br.get("booking_fee")),
             ("Desconto", -br["discount"] if br.get("discount") else None)]
    return {"receipt": {"tripUUID": t.uuid, "total": present.money(t.fare, cur),
                        "items": [{"label": k, "value": present.money(v, cur)} for k, v in lines if v],
                        "paymentMethod": "Dinheiro" if t.payment_method == "cash" else "Cartão"},
            "trip": past_trip(t)}


@handles(APP, "POST", "/rt/feedback/v2", "/rt/feedback/submit", "/rt/feedback/save-feedback")
def feedback(call: Call):
    db = call.db
    rider = call.subject()
    b = call.body
    stars = b.get("rating") or b.get("stars") or (b.get("feedback") or {}).get("rating")
    uuid = b.get("tripUUID") or b.get("jobUUID") or b.get("subjectUUID")
    t = db.query(Trip).filter_by(uuid=str(uuid)).first() if uuid else \
        (db.query(Trip).filter(Trip.rider_id == rider.id, Trip.state == "completed").order_by(Trip.id.desc()).first())
    if t and stars:
        try:
            trips.rate(db, t, "rider", int(stars), str(b.get("comment", "") or ""))
        except (TripError, ValueError):
            pass
    return {}


# ---- promocoes e pagamento -------------------------------------------------------------------
def promo_json(rp: RiderPromo, rider) -> dict:
    p = rp.promo
    disc = f"{p.value}%" if p.kind == "percent" else present.money(p.value)
    return {"uuid": str(rp.id), "promotionUuid": str(p.id), "code": p.code, "clientUuid": rider.uuid,
            "description": p.description or f"{disc} de desconto", "shortDescription": f"{disc} de desconto",
            "displayDiscount": disc, "isValid": pricing.promo_valid(p) is None and rp.used_trip_id is None,
            "trips": 1, "tripsLeft": 0 if rp.used_trip_id else 1,
            "expiresAt": present.ms(p.valid_to), "endsAt": present.ms(p.valid_to)}


@handles(APP, "GET", "/rt/riders/get-client-promotions")
def client_promotions(call: Call):
    rider = call.subject()
    rows = call.db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id).order_by(RiderPromo.id.desc()).all()
    return {"awards": [promo_json(r, rider) for r in rows]}


@handles(APP, "POST", "/rt/users/apply-clients-promotion-v2")
def apply_promo(call: Call):
    db = call.db
    rider = call.subject()
    code = str(call.get("promotionCode", "code", default="")).strip().upper()
    promo = db.query(Promo).filter(Promo.code == code).first()
    why = pricing.promo_valid(promo)
    if why:
        raise RtError(400, "invalid_promotion", why, {"title": "Código promocional", "message": why})
    used = db.query(RiderPromo).filter(RiderPromo.rider_id == rider.id, RiderPromo.promo_id == promo.id).count()
    if used >= promo.per_rider:
        raise RtError(400, "promotion_already_used", "ja usaste este codigo")
    rp = RiderPromo(rider_id=rider.id, promo=promo)
    db.add(rp)
    db.flush()
    return promo_json(rp, rider)


CASH_PROFILE = {"uuid": "cash", "tokenType": "cash", "tokenDisplayName": "Dinheiro", "accountName": "Dinheiro",
                "status": "active", "useCase": "personal", "isExpired": False, "supportedCapabilities": []}
CARD_PROFILE = {"uuid": "card-lab", "tokenType": "card", "tokenDisplayName": "Cartão (simulado)",
                "cardType": "VISA", "cardNumber": "4242", "status": "active", "useCase": "personal",
                "isExpired": False, "supportedCapabilities": []}


@handles(APP, "GET", "/rt/payment/v3/payment-profiles")
def payment_profiles(call: Call):
    rider = call.subject()
    profiles = [CASH_PROFILE, CARD_PROFILE] if rider.default_payment == "cash" else [CARD_PROFILE, CASH_PROFILE]
    return {"paymentProfiles": profiles, "inactivePaymentProfiles": []}


@handles(APP, "POST", "/rt/riders/v2/{riderUUID}/select-payment-profile", "/rt/payment/v3/payment-profiles/default")
def select_payment(call: Call):
    rider = call.subject()
    uuid = str(call.get("paymentProfileUUID", "paymentProfileUuid", "uuid", default="cash"))
    rider.default_payment = "cash" if uuid == "cash" else "card"
    return {}


@handles(APP, "GET", "/rt/riders/{riderUUID}/favorite-drivers")
def favorite_drivers(call: Call):
    return {"favoriteDrivers": []}


@handles(APP, "POST", "/rt/profiles/v2/get-profiles")
def profiles(call: Call):
    return {"profiles": []}

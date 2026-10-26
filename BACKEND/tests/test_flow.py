# -*- coding: utf-8 -*-
"""Ciclo completo pelas 3 apps + consola."""
import json

from tests.conftest import AppClient, login

ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def _driver_id(client, admin, phone):
    return next(d["id"] for d in client.get("/api/drivers", headers=admin).json() if d["phone"] == phone)


def _token(client, app, body):
    return client.post("/rt/identity/oauth2/token", json=body, headers={"X-Qolari-App": app})


def test_login_wrong_code(client):
    r = _token(client, "rider", {"grant_type": "password", "username": "+351910000001", "password": "9999"})
    assert r.status_code == 401 and r.json()["code"] == "rtapi.invalid_grant"


def test_fleet_login_requires_existing_account(client):
    r = _token(client, "fleet", {"grant_type": "password", "username": "+351939999999", "password": "0000"})
    assert r.status_code == 404


def test_unknown_grant_is_refused(client):
    assert _token(client, "rider", {"grant_type": "client_credentials"}).status_code == 400


def test_refresh_and_revoke(client):
    rider = login(client, "rider", "+351910000003")
    refresh = _token(client, "rider", {"grant_type": "password", "username": "+351910000003",
                                       "password": "0000"}).json()["refreshToken"]
    r = _token(client, "rider", {"grant_type": "refresh_token", "refresh_token": refresh})
    assert r.status_code == 200
    assert rider.post("/rt/identity/oauth2/revokesession").status_code == 200


def test_full_trip(client, admin):
    rider = login(client, "rider", "+351910000001")
    driver = login(client, "driver", "+351920000001")     # Carlos, Frota Tejo
    fleet = login(client, "fleet", "+351930000001")       # Rui, dono da Frota Tejo

    # so o Carlos online, junto ao Rossio (os outros motoristas do seed ficam offline)
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    r = driver.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.715, "longitude": -9.14}}})
    assert r.status_code == 200, r.text
    assert r.json()["driverTasks"]["driverState"]["online"] is True

    launch = rider.post("/rt/riders/me/app-launch", {"targetLocation": ROSSIO}).json()
    assert launch["client"]["firstName"] == "Ana"
    assert launch["status"]["clientStatus"]["status"] == "Looking"

    est = rider.post("/rt/riders/me/fare-estimate", {"pickupLocation": ROSSIO, "destination": AEROPORTO}).json()
    assert len(est["packageVariants"]) == 4
    vvid = est["packageVariants"][0]["vehicleViewId"]

    # codigo promocional na conta (20%)
    assert rider.post("/rt/users/apply-clients-promotion-v2", {"promotionCode": "bemvindo"}).status_code == 200

    p = rider.post("/rt/riders/me/v2/pickup", {"pickupRequest": {
        "requestPickupLocation": {"targetLocation": ROSSIO}, "requestDestinationLocation": {"targetLocation": AEROPORTO},
        "vehicleViewId": vvid}})
    assert p.status_code == 200, p.text
    trip_uuid = p.json()["trip"]["uuid"]
    assert p.json()["clientStatus"]["status"] == "Dispatching"

    # a proposta chega a app Driver pelo canal ramen (push_driver_unified_offers_v3), nao no DriverTasks
    assert driver.post("/rt/drivers/v2/available").json()["driverTasks"]["taskScopes"] == []
    msgs = driver.get("/ramen/sessions/s1/messages").json()["msg"]
    m = next(m for m in msgs if m["type"] == "push_driver_unified_offers_v3")
    assert m["interpretType"] == "FULL"
    uo = json.loads(m["msg"])["offers"][0]
    primary = uo["driverOfferData"]["primaryOffer"]
    offer_uuid = primary["offerUUID"]
    assert uo["driverOfferData"]["type"] == "primaryOffer" and uo["offerUUIDs"] == [offer_uuid]
    assert primary["offerType"] == "JOB" and primary["metaData"]["jobOfferModel"]["acceptWindow"] > 0
    assert primary["offerView"]["jobOfferViewV3"]["coreInfo"]["type"] == "simpleView"

    r = driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [offer_uuid]})
    assert r.status_code == 200, r.text
    scope = r.json()["driverTasks"]["taskScopes"][0]
    assert scope["completionTask"]["taskDataType"] == "pickupTaskData"
    ct = scope["completionTask"]
    assert ct["source"] == "DEMAND_JOB" and ct["coalescedDataUnion"]["type"] == "pickupCoalescedTaskData"
    assert ct["taskDataMap"][trip_uuid]["type"] == "pickupTaskData"
    loc = scope["nonBlockingTasks"][0]["driverTaskDataUnion"]["singleTaskData"]["taskDataUnion"]
    assert loc["type"] == "locationTaskData" and loc["locationTaskData"]["latitude"] == ROSSIO["latitude"]
    # depois de aceitar: DriverTasks por push e o cartao da proposta limpo (offers [])
    msgs = driver.get("/ramen/sessions/s1/messages").json()["msg"]
    assert any(m["type"] == "push_drivers_tasks" for m in msgs)
    assert json.loads(next(m for m in msgs if m["type"] == "push_driver_unified_offers_v3")["msg"])["offers"] == []

    st = rider.post("/rt/riders/me/status").json()
    assert st["clientStatus"]["status"] == "WaitingForPickup"
    assert st["trip"]["driver"]["firstName"] == "Carlos"
    pin = client.get(f"/api/trips/{trip_uuid}", headers=admin).json()["pin"]

    # Fleet ve o motorista em viagem
    drivers = fleet.post("/rt/fleet/get-fleet-drivers-v2").json()["drivers"]
    assert next(d for d in drivers if d["name"] == "Carlos Silva")["realtimeStatus"] == "ONTRIP"

    assert driver.post("/rt/trips/v2/start-waiting").status_code == 200
    # por omissao a viagem nao tem PIN (so se o passageiro o pedir): nenhuma tarefa de PIN
    assert pin == "" and not driver.post("/rt/drivers/v2/available").json()["driverTasks"]["taskScopes"][0]["blockingTasks"]
    # "parar novos pedidos" a meio da viagem nao da erro
    assert driver.post("/rt/drivers/v2/go-offline").status_code == 200
    assert driver.post("/rt/trips/v2/begin", {"uuid": trip_uuid, "pin": pin}).status_code == 200
    assert rider.post("/rt/riders/me/status").json()["clientStatus"]["status"] == "OnTrip"
    end = driver.post("/rt/trips/v2/end", {"uuid": trip_uuid})
    assert end.status_code == 200 and end.json()["driverTasks"]["taskScopes"] == []

    t = client.get(f"/api/trips/{trip_uuid}", headers=admin).json()
    assert t["state"] == "completed" and t["discount"] > 0
    kinds = {(e["party"], e["kind"]) for e in t["ledger"]}
    assert {("driver", "fare"), ("driver", "commission"), ("fleet", "fleet_fee"), ("platform", "promo")} <= kinds

    assert rider.post("/rt/feedback/v2", {"tripUUID": trip_uuid, "rating": 5}).status_code == 200
    hist = rider.post("/rt/support/get-trip-history").json()["trips"]
    assert hist[0]["id"] == trip_uuid and hist[0]["driverRating"] == 5

    earn = fleet.post("/rt/fleet/get-fleet-earnings-v2").json()
    assert earn["earningInfo"]["partnerStatement"]["formattedTotal"]
    daily = fleet.post("/rt/fleet/get-driver-daily-earnings-with-trips",
                       {"driverUUID": _carlos_uuid(client, admin)}).json()
    assert any(x["uuid"] == trip_uuid for x in daily["trips"])


def _carlos_uuid(client, admin):
    return next(d["uuid"] for d in client.get("/api/drivers", headers=admin).json() if d["phone"] == "+351920000001")


def test_reject_goes_to_next_driver_and_no_drivers(client, admin):
    rider = login(client, "rider", "+351910000002")
    d1 = login(client, "driver", "+351920000002")    # Marta
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    d1.post("/rt/drivers/v2/go-online", {"positionEvent": {"location": {"latitude": 38.71, "longitude": -9.14}}})
    p = rider.post("/rt/riders/me/pickup", {"requestPickupLocation": ROSSIO, "requestDestinationLocation": AEROPORTO})
    uuid = p.json()["trip"]["uuid"]
    assert d1.post("/rt/drivers/reject-offers").status_code == 200
    t = client.get(f"/api/trips/{uuid}", headers=admin).json()
    assert t["state"] == "requested" and t["offers"][0]["state"] == "rejected"
    # consola: cancelar
    r = client.post(f"/api/trips/{uuid}/action", json={"action": "cancel"}, headers=admin)
    assert r.json()["state"] == "cancelled"
    d1.post("/rt/drivers/v2/go-offline")


def test_console_simulator_and_payout(client, admin):
    rid = client.get("/api/riders", headers=admin).json()[-1]["id"]
    did = _driver_id(client, admin, "+351920000004")     # Diana, independente
    client.post(f"/api/drivers/{did}/online", json={"lat": 38.705, "lng": -9.145}, headers=admin)
    r = client.post("/api/trips", headers=admin, json={
        "rider_id": rid, "product_id": 1, "pickup": {"lat": 38.706, "lng": -9.1446, "address": "Cais do Sodré"},
        "dropoff": {"lat": 38.6979, "lng": -9.2063, "address": "Belém"}})
    uuid = r.json()["uuid"]
    for a in ("accept", "arrive", "start", "complete"):
        r = client.post(f"/api/trips/{uuid}/action", json={"action": a}, headers=admin)
        assert r.status_code == 200, (a, r.text)
    assert r.json()["state"] == "completed"
    bal = next(x for x in client.get("/api/finance/overview", headers=admin).json()["driver_balances"] if x["id"] == did)
    if bal["balance"] > 0:
        p = client.post("/api/payouts", json={"party": "driver", "party_id": did}, headers=admin).json()
        assert client.post(f"/api/payouts/{p['id']}/paid", json={"reference": "TRF-1"}, headers=admin).json()["status"] == "paid"
    else:   # dinheiro: o motorista deve a comissao
        assert client.post("/api/payouts", json={"party": "driver", "party_id": did}, headers=admin).status_code == 400


def test_unmapped_endpoint_is_recorded(client, admin):
    app = AppClient(client, "rider")
    r = app.post("/rt/riders/something-new", {"x": 1})
    assert r.status_code == 200 and r.json() == {}
    rows = client.get("/api/integration/rider/endpoints", params={"filter": "unmapped"}, headers=admin).json()["items"]
    assert any(x["path"] == "/rt/riders/something-new" for x in rows)
    # path com uuid real cai no template do catalogo
    app.post("/rt/trips/1234-abcd/mid-trip-fare-estimate")
    rows = client.get("/api/integration/rider/endpoints", params={"filter": "unmapped"}, headers=admin).json()["items"]
    hit = next(x for x in rows if x["path"] == "/rt/trips/{tripUUID}/mid-trip-fare-estimate")
    assert hit["response"] == "MidTripFareEstimateResponse"
    det = client.get("/api/integration/rider/endpoint", params={"path": hit["path"], "method": "POST"},
                     headers=admin).json()
    assert det["response_model"] and det["response_model"]["fields"]


def test_fleet_vehicles_and_invite(client, admin):
    fleet = login(client, "fleet", "+351930000001")
    v = fleet.post("/rt/vehicle-supplier/vs-vehiclemanager/create-vehicle",
                   {"vehicle": {"licensePlate": "zz-99-zz", "make": "Seat", "model": "Leon", "year": 2021}})
    assert v.status_code == 200, v.text
    assert v.json()["vehicle"]["licensePlate"] == "ZZ-99-ZZ"
    dup = fleet.post("/rt/vehicle-supplier/vs-vehiclemanager/create-vehicle",
                     {"vehicle": {"licensePlate": "ZZ-99-ZZ", "make": "Seat", "model": "Leon"}})
    assert dup.status_code == 409
    inv = fleet.post("/rt/vehicle-supplier/vs-membershipmanager/invite-user-to-org",
                     {"phone": {"countryCode": "+351", "nationalPhoneNumber": "929999999"}, "firstName": "Nuno"})
    assert inv.status_code == 200
    names = [d["name"] for d in fleet.post("/rt/fleet/get-fleet-drivers-v2").json()["drivers"]]
    assert "Nuno" in names
    orgs = fleet.post("/rt/vehicle-supplier/vs-supplier-management/get-user-organizations").json()
    assert orgs["orgs"][0]["org"]["name"] == "Frota Tejo, Lda."


def test_permissions(client, admin):
    r = client.post("/api/admins", headers=admin, json={"email": "fin@q.pt", "password": "segredo1", "role": "finance"})
    assert r.status_code == 200
    tok = client.post("/api/auth/login", json={"email": "fin@q.pt", "password": "segredo1"}).json()["token"]
    fin = {"Authorization": "Bearer " + tok}
    assert client.get("/api/dashboard", headers=fin).status_code == 200
    assert client.patch("/api/settings", json={"offer_timeout_s": 5}, headers=fin).status_code == 403
    assert client.post("/api/drivers", json={"first_name": "X", "phone": "911"}, headers=fin).status_code == 403
    assert client.get("/api/dashboard").status_code == 401


def test_usl_login_page_and_silk_screen(client):
    """Fluxo da app: pagina /v2 -> qolarilogin://auth?session&authCode -> submit-form com o code_verifier."""
    import base64, hashlib
    from urllib.parse import parse_qs, urlparse
    h = {"X-Qolari-App": "driver"}
    verifier = "v" * 50
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    page = client.get("/v2", params={"codeChallenge": challenge, "isEmbedded": "true"}, headers=h)
    assert page.status_code == 200 and "Qual é o seu número de telemóvel" in page.text
    assert client.post("/v2/api/phone", json={"phone": "920000004"}, headers=h).json()["exists"] is True
    bad = client.post("/v2/api/verify", json={"phone": "+351920000004", "code": "1234"}, headers=h).json()
    assert "incorreto" in bad["error"]
    r = client.post("/v2/api/verify", json={"phone": "+351920000004", "code": "0000",
                                             "query": {"codeChallenge": challenge}}, headers=h).json()
    url = urlparse(r["redirect"])
    assert url.scheme == "qolarilogin"
    q = {k: v[0] for k, v in parse_qs(url.query).items()}
    wrong = client.post("/rt/silk-screen/submit-form", headers=h,
                        json={"inAuthSessionID": q["session"], "formAnswer": {"x": "nao-e-o-verifier"}})
    assert wrong.status_code == 400
    r = client.post("/v2/api/verify", json={"phone": "+351920000004", "code": "0000",
                                             "query": {"codeChallenge": challenge}}, headers=h).json()
    q = {k: v[0] for k, v in parse_qs(urlparse(r["redirect"]).query).items()}
    ok = client.post("/rt/silk-screen/submit-form", headers=h, json={
        "inAuthSessionID": q["session"],
        "formAnswer": {"screenAnswers": [{"screenType": "TypeVerifySession", "fieldAnswers": [
            {"sessionVerificationCode": q["authCode"]}, {"codeVerifier": verifier}]}]}})
    assert ok.status_code == 200, ok.text
    info = ok.json()["oAuthInfo"]
    me = AppClient(client, "driver", info["accessToken"])
    assert me.post("/rt/identity/oauth2/user-id-token").status_code == 200


def test_usl_signup_asks_name_and_fleet_needs_account(client):
    h = {"X-Qolari-App": "rider"}
    r = client.post("/v2/api/verify", json={"phone": "+351919999990", "code": "0000"}, headers=h).json()
    assert r == {"needName": True}
    r = client.post("/v2/api/verify", json={"phone": "+351919999990", "code": "0000", "firstName": "Rita"},
                    headers=h).json()
    assert r["redirect"].startswith("qolarilogin://auth?session=")
    f = client.post("/v2/api/phone", json={"phone": "+351939999999"}, headers={"X-Qolari-App": "fleet"}).json()
    assert "Não encontrámos" in f["error"]


def test_rider_resolve_location(client):
    """O ponto de recolha fica resolvido: resultantLocations[0] com anchorGeolocation (id, provider, coordenada)."""
    rider = login(client, "rider", "+351910000002")
    r = rider.post("/rt/riders/me/resolve-location", {"requestLocation": {
        "locationSource": "DefaultDevice", "targetLocation": ROSSIO}, "context": "PICKUP", "requestNearbyLocations": True})
    assert r.status_code == 200, r.text
    s = r.json()["resultantLocations"][0]
    geo = s["anchorGeolocation"]["location"]
    assert geo["id"] and geo["provider"] and geo["coordinate"] == {"latitude": 38.7139, "longitude": -9.1394}
    assert s["locationSource"] == "DefaultDevice" and s["pickups"][0]["location"]["latitude"] == 38.7139
    d = rider.post("/rt/riders/me/resolve-location", {"requestLocation": {"targetLocation": AEROPORTO},
                                                      "context": "DROPOFF"}).json()["resultantLocations"][0]
    assert d["pickups"] == [] and d["anchorGeolocation"]["location"]["coordinate"]["latitude"] == 38.7742
    assert rider.post("/rt/venue/get-venue", {"latitude": 38.7139, "longitude": -9.1394}).json() == {"hasVenue": False}


def test_rider_status_has_active_order_after_pickup(client):
    """Depois do pedido, o StatusResponse traz a viagem como RiderAppOrder + fulfillmentStateData (mesmo uuid)."""
    rider = login(client, "rider", "+351910000003")
    r = rider.post("/rt/riders/me/v2/pickup", {"vehicleViewId": 1, "requestPickupLocation": {
        "targetLocation": ROSSIO, "anchorGeolocation": {"location": {"fullAddress": "Rossio, Lisboa"}}},
        "destination": AEROPORTO})
    assert r.status_code == 200, r.text
    uuid = r.json()["trip"]["uuid"]
    st = rider.post("/rt/riders/me/status", {"targetLocation": ROSSIO}).json()
    order = st["riderAppOrdersResponse"]["orders"][0]
    job = order["jobs"]["singlePersonalTransport"]["transport"]
    assert order["state"] == "ACTIVE" and job["id"] == uuid
    assert job["backwardsCompatibleData"]["legacyTripState"] in ("DISPATCHING", "EN_ROUTE")
    fjob = st["fulfillmentStateData"]["orders"][0]["orderPlan"]["jobs"][0]
    assert fjob["jobId"]["alternatives"]["transportJobId"]["uuid"] == uuid
    assert fjob["legacyTripData"]["trip"]["pickupLocation"]["address"] == "Rossio, Lisboa"
    assert fjob["legacyTripData"]["trip"]["tripStatusMessage"]["context"]["tripUUID"] == uuid
    rider.post(f"/rt/trips/{uuid}/rider-cancel")
    assert rider.post("/rt/riders/me/status", {}).json()["riderAppOrdersResponse"]["orders"] == []


def test_driver_positions_make_driver_real(client, admin):
    """GPS da app Driver (uploadpositions a cada 4 s, supplyInput) -> posicao real, deixa de ser simulado."""
    driver = login(client, "driver", "+351920000004")     # Diana
    r = driver.post("/rt/unifiedlocation/uploadpositions", {"uploadLocationRequest": {"positions": [
        {"point": {"latitude": 38.7572, "longitude": -9.2232}, "course": 59.6}],
        "entity": {"entityType": "SUPPLY"}}})
    assert r.status_code == 200, r.text
    d = next(d for d in client.get("/api/drivers", headers=admin).json() if d["phone"] == "+351920000004")
    assert abs(d["lat"] - 38.7572) < 1e-6 and d["simulated"] is False
    r = driver.post("/rt/surge/supplyInput", {"events": [{"eventType": "DeviceLocation", "deviceLocationEvent": {
        "location": {"latitude": 38.76, "longitude": -9.22}}}], "driverState": "Online"})
    assert r.status_code == 200
    d = next(d for d in client.get("/api/drivers", headers=admin).json() if d["phone"] == "+351920000004")
    assert abs(d["lat"] - 38.76) < 1e-6


def test_driver_expire_offer_is_idempotent(client, admin):
    """A app manda expire-offers quando o tempo acaba no ecra, muitas vezes depois do servidor: nao pode dar 400."""
    driver = login(client, "driver", "+351920000004")
    assert driver.post("/rt/drivers/expire-offers", {"offers": [{"offerUUID": "nao-existe"}]}).status_code == 200
    assert driver.post("/rt/drivers/reject-offers").status_code == 200


def test_driver_arrives_by_position(client, admin):
    """A Driver nao tem passo "cheguei": a posicao a menos de arrive_radius_m da recolha passa a viagem a arrived."""
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    driver = login(client, "driver", "+351920000004")
    rider = login(client, "rider", "+351910000002")
    pos = lambda lat, lng: {"uploadLocationRequest": {"positions": [{"point": {"latitude": lat, "longitude": lng}}]}}
    assert driver.post("/rt/drivers/v2/go-online", pos(38.7200, -9.1450)).status_code == 200
    r = rider.post("/rt/riders/me/v2/pickup", {"vehicleViewId": 1, "requestPickupLocation": {"targetLocation": ROSSIO},
                                                 "destination": AEROPORTO})
    assert r.status_code == 200, r.text
    msgs = driver.get("/ramen/sessions/s2/messages").json()["msg"]
    offers = [json.loads(m["msg"])["offers"] for m in msgs if m["type"] == "push_driver_unified_offers_v3"]
    offer = next(o for o in reversed(offers) if o)[0]
    assert driver.post("/rt/drivers/accept-offers", {"offers": [{"offerUUID": offer["offerUUIDs"][0]}]}).status_code == 200
    trip = r.json()["trip"]["uuid"]
    driver.post("/rt/unifiedlocation/uploadpositions", pos(38.7180, -9.1420))           # ~500 m: ainda nao
    assert client.get(f"/api/trips/{trip}", headers=admin).json()["state"] == "accepted"
    driver.post("/rt/unifiedlocation/uploadpositions", pos(ROSSIO["latitude"] + 0.0003, ROSSIO["longitude"]))  # ~33 m
    assert client.get(f"/api/trips/{trip}", headers=admin).json()["state"] == "arrived"
    scope = driver.post("/rt/drivers/v2/available").json()["driverTasks"]["taskScopes"][0]
    kinds = [t["driverTaskDataUnion"]["singleTaskData"]["taskDataUnion"]["type"] for t in scope["nonBlockingTasks"]]
    assert "waitTimeTaskData" in kinds and not scope["blockingTasks"]
    assert rider.post("/rt/riders/me/status").json()["clientStatus"]["status"] in ("WaitingForPickup", "Arrived")
    # limpeza: os testes seguintes nao podem herdar uma viagem ativa neste passageiro
    rider.post(f"/rt/trips/{trip}/rider-cancel")
    driver.post("/rt/drivers/v2/go-offline")

# -*- coding: utf-8 -*-
"""Qolari Lite (recriacao da User): contrato desenhado e ciclo completo com a Driver.

O fluxo e o "teste dos tres espelhos" do PROMPT_CLONE_MEGA §4.6.7: a User pede, a Driver ve e
aceita, a User ve o estado, a Driver move, a User ve o fim e avalia.
"""
from tests.conftest import login
ANA = "+351910000001"
CARLOS = "+351920000001"   # aprovado, Frota Tejo
ROSSIO = {"lat": 38.71391, "lng": -9.13940, "address": "Praça do Rossio, Lisboa"}
AEROPORTO = {"lat": 38.77425, "lng": -9.13422, "address": "Aeroporto Humberto Delgado, Lisboa"}


def _only_carlos_online(client, admin):
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] == "online":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)


def _offer_for(driver):
    offers = driver.post("/rt/drivers/unified-offers-v3").json()["data"]["offers"]
    assert offers, "a proposta devia ter chegado a Driver"
    return offers[0]["offerUUIDs"][0]


def test_lite_home_and_places(client):
    rider = login(client, "rider", ANA)
    s = rider.get("/rt/lite/session").json()
    assert s["firstName"] == "Ana" and s["riderUUID"] and s["payment"]["id"] in ("cash", "card")

    home = rider.get("/rt/lite/home").json()
    assert "chegar em" in home["headline"] and home["savedPlace"]["id"] == "home"
    assert len(home["suggestions"]) == 1 and home["suggestions"][0]["id"] == "ride"

    # Casa editavel na conta: escolhe uma morada conhecida e o inicio passa a mostra-la.
    changed = rider.post("/rt/lite/account/home", {"placeId": "oriente"}).json()
    assert changed["savedPlace"]["id"] == "oriente"
    assert rider.get("/rt/lite/home").json()["savedPlace"]["id"] == "oriente"
    assert rider.post("/rt/lite/account/home", {"placeId": "nao-existe"}).status_code == 404


def test_lite_account_is_editable(client):
    rider = login(client, "rider", "+351910000002")
    s = rider.patch("/rt/lite/account", {"firstName": "Bruno", "lastName": "Silva",
                                         "email": "bruno@qolari.local"}).json()
    assert s["name"] == "Bruno Silva" and s["email"] == "bruno@qolari.local"
    assert rider.get("/rt/lite/session").json()["email"] == "bruno@qolari.local"
    assert rider.patch("/rt/lite/account", {"email": "sem-arroba"}).status_code == 400
    assert rider.patch("/rt/lite/account", {"firstName": ""}).status_code == 400

    places = rider.get("/rt/lite/places", params={"q": "rossio"}).json()["places"]
    assert places and places[0]["id"] == "rossio"
    assert {"lat", "lng", "line1", "line2"} <= set(places[0])
    assert rider.get("/rt/lite/places", params={"q": "casa"}).json()["places"][0]["id"] == "home"


def test_lite_quote_promo_and_payment(client):
    # Carla: a Ana ja gastou o BEMVINDO no test_full_trip; o teste tem de ser independente da ordem
    rider = login(client, "rider", "+351910000003")
    body = {"pickup": ROSSIO, "dropoff": AEROPORTO}
    q = rider.post("/rt/lite/quote", body).json()
    assert len(q["products"]) == 4
    assert all(p["cents"] > 0 and p["price"].endswith("€") for p in q["products"])
    assert sum(1 for p in q["products"] if p["fastest"]) == 1
    assert q["dropoff"]["address"] == AEROPORTO["address"]

    assert rider.post("/rt/lite/promotions/apply", {"code": "bemvindo"}).status_code == 200
    q2 = rider.post("/rt/lite/quote", body).json()
    assert q2["promo"]["code"] == "BEMVINDO"
    assert min(p["cents"] for p in q2["products"]) < min(p["cents"] for p in q["products"])

    wallet = rider.get("/rt/lite/wallet").json()
    assert wallet["cash"]["label"] == "0,00 €" and len(wallet["profiles"]) == 2
    sel = rider.post("/rt/lite/payments/select", {"id": "card"}).json()
    assert sel["payment"]["id"] == "card"
    assert rider.post("/rt/lite/payments/select", {"id": "nao-existe"}).status_code == 404


def test_lite_empty_history_is_an_array(client):
    rider = login(client, "rider", "+351910000003")
    h = rider.get("/rt/lite/history").json()
    assert isinstance(h["trips"], list)


def test_lite_full_trip_with_driver(client, admin):
    rider = login(client, "rider", ANA)
    driver = login(client, "driver", CARLOS)
    _only_carlos_online(client, admin)
    r = driver.post("/rt/drivers/v2/go-online",
                    {"positionEvent": {"location": {"latitude": ROSSIO["lat"], "longitude": ROSSIO["lng"]}}})
    assert r.status_code == 200 and r.json()["driverTasks"]["driverState"]["online"] is True

    q = rider.post("/rt/lite/quote", {"pickup": ROSSIO, "dropoff": AEROPORTO}).json()
    pid = q["products"][0]["id"]
    req = rider.post("/rt/lite/request", {"pickup": ROSSIO, "dropoff": AEROPORTO, "productId": pid})
    assert req.status_code == 200, req.text
    trip_uuid = req.json()["trip"]["uuid"]
    assert req.json()["trip"]["state"] == "requested"
    assert rider.get("/rt/lite/active").json()["trip"]["uuid"] == trip_uuid

    offer_uuid = _offer_for(driver)
    acc = driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [offer_uuid]})
    assert acc.status_code == 200, acc.text

    active = rider.get("/rt/lite/active").json()["trip"]
    assert active["state"] == "accepted" and active["driver"]["name"] == "Carlos"
    assert active["driver"]["vehicle"]["plate"]
    pin = active["pin"]
    assert pin and len(pin) == 4

    assert driver.post("/rt/trips/v2/start-waiting").status_code == 200
    active = rider.get("/rt/lite/active").json()["trip"]
    assert active["state"] == "arrived" and active["driverEtaMin"] == 0

    assert driver.post("/rt/trips/v2/begin", {"uuid": trip_uuid, "pin": pin}).status_code == 200
    assert rider.get("/rt/lite/active").json()["trip"]["state"] == "in_progress"

    assert driver.post("/rt/trips/v2/end", {"uuid": trip_uuid}).status_code == 200
    done = rider.get("/rt/lite/active").json()["trip"]
    assert done["state"] == "completed" and done["fare"]["cents"] > 0 and done["canRate"] is True

    rated = rider.post(f"/rt/lite/trips/{trip_uuid}/rate", {"stars": 5})
    assert rated.status_code == 200 and rated.json()["trip"]["myRating"] == 5
    assert rider.get("/rt/lite/active").json()["trip"] is None
    history = rider.get("/rt/lite/history").json()["trips"]
    assert any(t["uuid"] == trip_uuid and t["state"] == "completed" for t in history)


def test_lite_cancel_and_no_drivers(client, admin):
    rider = login(client, "rider", "+351910000002")
    _only_carlos_online(client, admin)
    q = rider.post("/rt/lite/quote", {"pickup": ROSSIO, "dropoff": AEROPORTO}).json()
    req = rider.post("/rt/lite/request", {"pickup": ROSSIO, "dropoff": AEROPORTO, "productId": q["products"][0]["id"]})
    assert req.status_code == 200, req.text
    trip_uuid = req.json()["trip"]["uuid"]
    c = rider.post(f"/rt/lite/trips/{trip_uuid}/cancel", {"reason": "teste"})
    assert c.status_code == 200 and c.json()["trip"]["state"] == "cancelled"
    assert c.json()["trip"]["cancelledBy"] == "rider"

# -*- coding: utf-8 -*-
"""Teste dos tres espelhos (MEGA §4.6.7).

Cria no Rider (U), ve no Driver (D) e na Fleet (F), move no Driver, ve no Rider,
intervem no Backoffice (B) e ve de novo em U, D e F. Sem telemovel: TestClient.
"""
import json

from tests.conftest import login

ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def _driver_row(client, admin, phone):
    return next(d for d in client.get("/api/drivers", headers=admin).json() if d["phone"] == phone)


def _ramen(driver, msg_type):
    msgs = driver.get("/ramen/sessions/s1/messages").json()["msg"]
    return [m for m in msgs if m["type"] == msg_type]


def test_tres_espelhos(client, admin):
    rider = login(client, "rider", "+351910000003")     # Carla
    driver = login(client, "driver", "+351920000003")   # Joao (Frota Tejo)
    fleet = login(client, "fleet", "+351930000001")     # Rui (Frota Tejo)
    joao = _driver_row(client, admin, "+351920000003")

    # so o Joao online, junto ao Rossio
    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] != "offline":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    r = driver.post("/rt/drivers/v2/go-online",
                    {"positionEvent": {"location": {"latitude": 38.715, "longitude": -9.14}}})
    assert r.status_code == 200, r.text

    # ---- 1. cria em U ----
    p = rider.post("/rt/riders/me/v2/pickup", {"pickupRequest": {
        "requestPickupLocation": {"targetLocation": ROSSIO},
        "requestDestinationLocation": {"targetLocation": AEROPORTO}}})
    assert p.status_code == 200, p.text
    uuid = p.json()["trip"]["uuid"]
    assert p.json()["clientStatus"]["status"] == "Dispatching"

    # ---- 2. ve em D (oferta) e em B ----
    offers = _ramen(driver, "push_driver_unified_offers_v3")
    assert offers, "a oferta nao chegou ao canal ramen do motorista"
    offer = json.loads(offers[-1]["msg"])["offers"][0]
    offer_uuid = offer["driverOfferData"]["primaryOffer"]["offerUUID"]
    assert client.get(f"/api/trips/{uuid}", headers=admin).json()["state"] == "requested"

    # ---- 3. move em D ----
    r = driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [offer_uuid]})
    assert r.status_code == 200, r.text

    # ---- 4. ve em U, F e B ----
    st = rider.post("/rt/riders/me/status").json()
    assert st["clientStatus"]["status"] == "WaitingForPickup"
    assert st["trip"]["driver"]["firstName"] == "João"
    drivers = fleet.post("/rt/fleet/get-fleet-drivers-v2").json()["drivers"]
    assert next(d for d in drivers if d["name"] == "João Ferreira")["realtimeStatus"] == "ONTRIP"
    supply = fleet.post("/rt/fleet/get-driver-current-supply", {"driverUUID": joao["uuid"]}).json()
    assert supply["supplyOverview"]["tripUuid"] == uuid
    assert supply["supplyOverview"]["tripStatus"] == "ACCEPTED"
    assert client.get(f"/api/trips/{uuid}", headers=admin).json()["state"] == "accepted"

    # ---- 5. intervem em B (cancelamento auditado) ----
    r = client.post(f"/api/trips/{uuid}/action", json={"action": "cancel"}, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["state"] == "cancelled"
    assert r.json()["cancelled_by"] == "admin"

    # ---- 6. ve em U, D e F ----
    st = rider.post("/rt/riders/me/status").json()
    assert st["clientStatus"]["status"] == "Looking"
    assert st["clientStatus"].get("lastRequestNote")      # aviso de cancelamento
    raw = driver.get("/ramen/sessions/s1/messages").json()["msg"]
    assert any(m["type"] == "push_earner_trip_core_domain"
               and json.loads(m["msg"]).get("taskScopes") == [] for m in raw), \
        "o motorista nao recebeu a atualizacao de tarefas depois do cancelamento"
    assert driver.post("/rt/drivers/v2/available").json()["driverTasks"]["taskScopes"] == []
    drivers = fleet.post("/rt/fleet/get-fleet-drivers-v2").json()["drivers"]
    assert next(d for d in drivers if d["name"] == "João Ferreira")["realtimeStatus"] == "ONLINE"
    fleet_msgs = fleet.get("/ramen/sessions/s1/messages").json()["msg"]
    assert any(m["type"] == "driver_trip" and json.loads(m["msg"])["state"] == "cancelled"
               for m in fleet_msgs), "a Fleet nao recebeu o cancelamento por push"
    assert any(m["type"] == "driver_status" and json.loads(m["msg"])["status"] == "online"
               for m in fleet_msgs), "a Fleet nao recebeu o motorista livre por push"
    audit = client.get("/api/audit", headers=admin).json()
    assert any(a["action"] == "trip.cancel" and a["entity_id"] == uuid for a in audit), \
        "a intervencao do backoffice nao ficou auditada"

    # limpeza: o teste seguinte deve encontrar o Joao offline
    driver.post("/rt/drivers/v2/go-offline")

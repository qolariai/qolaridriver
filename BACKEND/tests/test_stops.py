# -*- coding: utf-8 -*-
"""Paragens intermédias: pedido, motorista e conclusão."""
import json

from tests.conftest import login

ROSSIO = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
STOP = {"latitude": 38.7255, "longitude": -9.1500, "address": "Paragem Marquês"}
AEROPORTO = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def _offer(driver):
    msgs = driver.get("/ramen/sessions/s1/messages").json()["msg"]
    offers = [m for m in msgs if m["type"] == "push_driver_unified_offers_v3"]
    assert offers, "oferta não chegou"
    return json.loads(offers[-1]["msg"])["offers"][0]["driverOfferData"]["primaryOffer"]["offerUUID"]


def test_stops_are_completed_in_order(client, admin):
    rider = login(client, "rider", "+351910000003")
    driver = login(client, "driver", "+351920000003")

    for d in client.get("/api/drivers", headers=admin).json():
        if d["availability"] != "offline":
            client.post(f"/api/drivers/{d['id']}/offline", headers=admin)
    driver.post("/rt/drivers/v2/go-online",
                {"positionEvent": {"location": {"latitude": 38.715, "longitude": -9.14}}})

    res = rider.post("/rt/lite/request", {"pickup": ROSSIO, "dropoff": AEROPORTO, "stops": [STOP]})
    assert res.status_code == 200, res.text
    trip = res.json()["trip"]
    uuid = trip["uuid"]
    assert trip["stops"][0]["address"] == "Paragem Marquês"
    assert trip["nextStopIndex"] == 0

    driver.post("/rt/drivers/accept-offers", {"offerUUIDs": [_offer(driver)]})
    driver.post("/rt/trips/v2/begin", {"uuid": uuid, "pin": trip["pin"]})

    before = rider.get(f"/rt/lite/trips/{uuid}").json()["trip"]
    assert before["nextStopIndex"] == 0 and before["stops"][0]["done"] is False

    stop = driver.post("/rt/trips/v2/complete-stop", {"uuid": uuid})
    assert stop.status_code == 200, stop.text
    after = rider.get(f"/rt/lite/trips/{uuid}").json()["trip"]
    assert after["stops"][0]["done"] is True
    assert after["nextStopIndex"] is None

    end = driver.post("/rt/trips/v2/end", {"uuid": uuid})
    assert end.status_code == 200, end.text
    done = client.get(f"/api/trips/{uuid}", headers=admin).json()
    assert done["state"] == "completed"
    assert done["fare"] > 0

# -*- coding: utf-8 -*-
"""Seguranca: contactos de confianca, SOS e partilha de viagem."""
from tests.conftest import login

PICKUP = {"latitude": 38.7139, "longitude": -9.1394, "address": "Rossio"}
DROPOFF = {"latitude": 38.7742, "longitude": -9.1342, "address": "Aeroporto"}


def test_trusted_contacts_and_sos(client, admin):
    d = login(client, "driver", "+351920000002")

    c = d.post("/rt/safety/contacts", {"name": "Maria", "phone": "+351910000099"})
    assert c.status_code == 200, c.text
    uuid = c.json()["contact"]["uuid"]
    assert d.post("/rt/safety/contacts", {"name": "Maria", "phone": "+351910000099"}).status_code == 409

    contacts = d.get("/rt/safety/contacts").json()["contacts"]
    assert any(x["phone"] == "+351910000099" for x in contacts)

    sos = d.post("/rt/safety/sos", {"latitude": 38.71, "longitude": -9.14, "note": "teste"})
    assert sos.status_code == 200, sos.text
    assert sos.json()["incident"]["kind"] == "sos"
    assert sos.json()["contacts"]

    alerts = client.get("/api/safety?status=open", headers=admin).json()["items"]
    alert = next(a for a in alerts if a["uuid"] == sos.json()["incident"]["uuid"])
    assert alert["subjectName"] == "Marta Costa"
    assert alert["contacts"]

    r = client.patch(f"/api/safety/{alert['uuid']}", json={"status": "closed"}, headers=admin)
    assert r.status_code == 200 and r.json()["status"] == "closed"

    assert d.c.delete(f"/rt/safety/contacts/{uuid}", headers=d.headers()).status_code == 200
    assert not any(x["uuid"] == uuid for x in d.get("/rt/safety/contacts").json()["contacts"])


def test_trip_share_public_page(client):
    r = login(client, "rider", "+351910000003")
    trip = r.post("/rt/lite/request", {"pickup": PICKUP, "dropoff": DROPOFF})
    assert trip.status_code == 200, trip.text
    uuid = trip.json()["trip"]["uuid"]

    share = r.post("/rt/safety/share", {"tripUuid": uuid})
    assert share.status_code == 200, share.text
    token = share.json()["token"]
    assert share.json()["path"] == f"/share/{token}"

    page = client.get(f"/share/{token}")
    assert page.status_code == 200
    assert "Estado" in page.text and "Rossio" in page.text

    check = r.post("/rt/safety/ride-check", {"tripUuid": uuid, "status": "ok"})
    assert check.status_code == 200, check.text
    assert check.json()["status"] == "ok"
    assert check.json()["incident"]["kind"] == "ride_check"

    assert client.get("/share/nao-existe").status_code == 404
    r.post(f"/rt/lite/trips/{uuid}/cancel", {"reason": "teste"})
